import asyncio
import re
from contextlib import suppress
from typing import Union

import constants
import discord
from models import Scrim, Tourney

from utils import find_team


def get_slots(slots):
    for slot in slots:
        yield slot.user_id


async def already_reserved(scrim: Scrim):
    return [i.num for i in await scrim.reserved_slots.all()]


async def available_to_reserve(scrim: Scrim):
    reserved = await already_reserved(scrim)
    return sorted([i for i in scrim.available_to_reserve if i not in reserved])


async def cannot_take_registration(message: discord.Message, obj: Union[Scrim, Tourney]):
    assert message.guild is not None

    logschan = obj.logschan

    with suppress(AttributeError, discord.Forbidden):
        embed = discord.Embed(
            color=discord.Color.red(),
            description=f"**Registration couldn't be accepted in {message.channel.mention}**",
        )
        embed.description += (  # type: ignore # line guarded above
            "\nPossible reasons are:\n"
            "> Success Role of tourney has been deleted.\n"
            "> I don't have add reaction permission in the channel\n"
            "> I don't have manage_roles permission in the server\n"
            f"> My top role({message.guild.me.top_role.mention}) is below {obj.role.mention}\n"
            "> I don't have use external emojis permission in the channel."
        )

        await logschan.send(
            content=getattr(obj.modrole, "mention", None),
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )


async def toggle_channel(channel, role, _bool=True) -> bool:
    overwrite = channel.overwrites_for(role)
    overwrite.update(send_messages=_bool)
    try:
        await channel.set_permissions(
            role,
            overwrite=overwrite,
            reason=("Registration is over!", "Open for Registrations!")[_bool],  # False=0, True=1
        )

        return True

    except:
        return False


async def wait_and_purge(channel, *, limit=100, wait_for=15, check=lambda m: True):
    await asyncio.sleep(wait_for)

    with suppress(discord.HTTPException):
        await channel.purge(limit=limit, check=check)


async def delete_denied_message(message: discord.Message, seconds=10):
    with suppress(AttributeError, discord.HTTPException, discord.NotFound, discord.Forbidden):
        await asyncio.sleep(seconds)
        await message.delete()


async def check_scrim_requirements(bot, message: discord.Message, scrim: Scrim) -> bool:
    _bool = True

    if scrim.teamname_compulsion:
        teamname = re.search(r"team.*", message.content)
        if not teamname or not teamname.group().strip():
            _bool = False
            bot.dispatch("scrim_registration_deny", message, constants.RegDeny.noteamname, scrim)

    if scrim.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.botmention, scrim)

    elif not len(message.mentions) >= scrim.required_mentions:
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.nomention, scrim)

    elif message.author.id in await scrim.banned_user_ids():
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.banned, scrim)

    elif len(message.content.splitlines()) < scrim.required_lines:
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.nolines, scrim)

    # elif any(x in banned for x in (i.id for i in message.mentions)):
    #     _bool = False
    #     bot.dispatch("scrim_registration_deny", message, constants.RegDeny.bannedteammate, scrim)

    elif not scrim.multiregister and message.author.id in get_slots(await scrim.assigned_slots.all()):
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.multiregister, scrim)

    elif scrim.no_duplicate_name:
        teamname = find_team(message)
        async for slot in scrim.assigned_slots.all():
            if slot.team_name == teamname:
                _bool = False
                bot.dispatch("scrim_registration_deny", message, constants.RegDeny.duplicate, scrim)
                break
            else:
                continue

    return _bool


async def should_open_scrim(scrim: Scrim):
    guild = scrim.guild
    registration_channel = scrim.registration_channel
    role = scrim.role
    _bool = True

    text = f"Registration of Scrim: `{scrim.id}` couldn't be opened due to the following reason:\n\n"

    if not registration_channel:
        _bool = False
        text += "I couldn't find registration channel. Maybe its deleted or hidden from me."

    elif not registration_channel.permissions_for(guild.me).manage_channels:
        _bool = False
        text += "I do not have `manage_channels` permission in {0}".format(registration_channel.mention)

    elif role is None:
        _bool = False
        text += "I couldn't find success registration role."

    elif not guild.me.guild_permissions.manage_roles or role >= guild.me.top_role:
        _bool = False
        text += "I don't have permissions to `manage roles` in this server or {0} is above my top role ({1}).".format(
            role.mention, guild.me.top_role.mention
        )

    elif scrim.open_role_id and not scrim.open_role:
        _bool = False
        text += "You have setup an open role earlier and I couldn't find it."

    if not _bool:
        logschan = scrim.logschan
        if logschan:
            embed = discord.Embed(color=discord.Color.red())
            embed.description = text
            with suppress(discord.Forbidden, discord.NotFound):
                await logschan.send(
                    content=getattr(scrim.modrole, "mention", None),
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=True),
                )

    return _bool


def scrim_work_role(scrim: Scrim, _type: constants.EsportsRole):
    if _type == constants.EsportsRole.ping:
        role = scrim.ping_role

    elif _type == constants.EsportsRole.open:
        role = scrim.open_role

    if not role:
        return None

    if role == scrim.guild.default_role:
        return "@everyone"
    return getattr(role, "mention", "Role deleted!")
