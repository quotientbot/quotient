from contextlib import suppress
import io
from typing import Optional, Union

from prettytable.prettytable import PrettyTable
from ast import literal_eval
from models import Scrim, Tourney
from datetime import datetime
import constants, humanize

from utils import find_team, strtime, QuoUser, plural, human_timedelta
import discord
import config
import asyncio
import re

from core import Context
from constants import ScrimBanType, IST


def get_slots(slots):
    for slot in slots:
        yield slot.user_id


async def log_scrim_ban(channel, scrims, status: ScrimBanType, user: QuoUser, **kwargs):
    mod = kwargs.get("mod")
    reason = kwargs.get("reason") or "No Reason Provided..."
    format = ", ".join((f"{getattr(scrim.registration_channel, 'mention','deleted-channel')}" for scrim in scrims))

    if status == ScrimBanType.ban:
        expire_time = kwargs.get("expire_time")

        embed = discord.Embed(color=discord.Color.red(), title=f"🔨 Banned from {plural(len(scrims)):Scrim|Scrims}")
        embed.add_field(name="User", value=f"{user} ({getattr(user, 'mention','unknown-user')})")
        embed.add_field(name="Moderator", value=mod)
        embed.add_field(name="Effected Scrims", value=format, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)

        if expire_time:
            embed.set_footer(text=f"Expires in {human_timedelta(expire_time)}")

    else:
        embed = discord.Embed(color=discord.Color.green(), title=f"🍃 Unbanned from {plural(len(scrims)):Scrim|Scrims}")
        embed.add_field(name="User", value=f"{user} ({getattr(user, 'mention','unknown-user')})")
        embed.add_field(name="Moderator", value=mod)
        embed.add_field(name="Effected Scrims", value=format, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)

    with suppress(AttributeError, discord.HTTPException, discord.Forbidden):
        embed.timestamp = datetime.now(tz=IST)
        await channel.send(content=getattr(user, "mention", "unknown-user"), embed=embed)


async def add_role_and_reaction(ctx, role):
    with suppress(discord.HTTPException):
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await ctx.author.add_roles(role)


async def already_reserved(scrim: Scrim):
    return [i.num for i in await scrim.reserved_slots.all()]


async def available_to_reserve(scrim: Scrim):
    reserved = await already_reserved(scrim)
    return sorted([i for i in scrim.available_to_reserve if i not in reserved])


async def cannot_take_registration(message: discord.Message, obj: Union[Scrim, Tourney]):
    logschan = obj.logschan

    with suppress(AttributeError, discord.Forbidden):
        embed = discord.Embed(
            color=discord.Color.red(), description=f"**Registration couldn't be accepted in {message.channel.mention}**"
        )
        embed.description += (
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


async def scrim_end_process(ctx: Context, scrim: Scrim):
    closed_at = datetime.now(tz=constants.IST)

    registration_channel = scrim.registration_channel
    open_role = scrim.open_role

    delta = humanize.precisedelta(closed_at - scrim.opened_at)

    await Scrim.filter(pk=scrim.id).update(opened_at=None, time_elapsed=delta, closed_at=closed_at)

    channel_update = await toggle_channel(registration_channel, open_role, False)

    await scrim.refresh_from_db(("time_elapsed",))  # refreshing our instance to get time_elapsed

    _e = registration_close_embed(scrim)

    await registration_channel.send(embed=_e)

    ctx.bot.dispatch("scrim_log", constants.EsportsLog.closed, scrim, permission_updated=channel_update)

    if scrim.autoslotlist and await scrim.teams_registered:
        from ..views import SlotlistEditButton

        embed, channel = await scrim.create_slotlist()

        _v = SlotlistEditButton(ctx.bot, scrim)
        with suppress(AttributeError, discord.Forbidden):
            _v.message = await channel.send(embed=embed, view=_v)
            await Scrim.filter(pk=scrim.id).update(slotlist_message_id=_v.message.id)

    if scrim.autodelete_extras:
        msg_ids = (i.message_id for i in await scrim.assigned_slots.all())
        check = lambda x: all(
            (not x.pinned, not x.reactions, not x.embeds, not x.author == ctx.bot.user, not x.id in msg_ids)
        )
        ctx.bot.loop.create_task(wait_and_purge(ctx.channel, check=check, wait_for=20))


async def purge_channel(channel):
    with suppress(AttributeError, discord.Forbidden, discord.NotFound, discord.HTTPException):
        await channel.purge(limit=100, check=lambda x: not x.pinned)


async def purge_role(role):
    with suppress(AttributeError, discord.Forbidden, discord.HTTPException):
        if not role.guild.chunked:
            await role.guild.chunk()

        for member in role.members:
            await member.remove_roles(role, reason="Scrims Manager Autoclean!")


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

    elif message.author.id in (banned := await scrim.banned_user_ids()):
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.banned, scrim)

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


async def embed_or_content(ctx, _type: constants.RegMsg) -> Optional[int]:
    m = await ctx.simple(
        f"Do you want the {_type.value} message to be an embed or normal text/image ?"
        "\n\n`Reply with 1 for embed and 2 for simple text/image`"
    )

    try:
        option = await ctx.bot.wait_for(
            "message", check=lambda msg: msg.channel == ctx.channel and msg.author == ctx.author, timeout=20
        )

        await delete_denied_message(m, 0)
    except asyncio.TimeoutError:
        return await ctx.error(f"You ran out of time, Kindly try again")

    else:
        try:
            option = int(option.content)
        except ValueError:
            return await ctx.error("You didn't enter a valid number, you had to choose between 1 and 2.")

        if option not in (1, 2):
            return await ctx.error("You didn't enter a valid number, You had to choose between 1 and 2.")

        return option


async def registration_open_embed(scrim: Scrim) -> discord.Embed:
    _dict = scrim.open_message
    reserved_count = await scrim.reserved_slots.all().count()

    if len(_dict) <= 1:
        embed = discord.Embed(
            color=config.COLOR,
            title="Registration is now open!",
            description=f"📣 **`{scrim.required_mentions}`** mentions required.\n"
            f"📣 Total slots: **`{scrim.total_slots}`** [`{reserved_count}` slots reserved]",
        )

    else:
        text = str(_dict)
        text = text.replace("<<mentions>>", str(scrim.required_mentions))
        text = text.replace("<<slots>>", str(scrim.total_slots))
        text = text.replace("<<reserved>>", str(reserved_count))
        text = text.replace("<<slotlist>>", getattr(scrim.slotlist_channel, "mention", "Not Found"))
        text = text.replace("<<multireg>>", "Enabled" if scrim.multiregister else "Not Enabled")
        text = text.replace("<<teamname>>", "Yes" if scrim.teamname_compulsion else "No")
        text = text.replace(
            "<<mention_banned>>",
            ", ".join(
                map(lambda x: getattr(x, "mention", "Left"), map(scrim.guild.get_member, await scrim.banned_user_ids()))
            ),
        )
        text = text.replace(
            "<<mention_reserved>>",
            ", ".join(
                map(lambda x: getattr(x, "mention", "Left"), map(scrim.guild.get_member, await scrim.reserved_user_ids()))
            ),
        )

        embed = discord.Embed.from_dict(literal_eval(text))

    return embed


def registration_close_embed(scrim: Scrim):
    _dict = scrim.close_message

    if len(_dict) <= 1:
        embed = discord.Embed(color=config.COLOR, description="**Registration is now Closed!**")

    else:
        text = str(_dict)
        text = text.replace("<<slots>>", str(scrim.total_slots))
        text = text.replace("<<filled>>", str(scrim.total_slots - len(scrim.available_slots)))
        if scrim.time_elapsed:
            text = text.replace("<<time_taken>>", scrim.time_elapsed)
        text = text.replace("<<open_time>>", strtime(scrim.open_time))
        embed = discord.Embed.from_dict(literal_eval(text))

    return embed
