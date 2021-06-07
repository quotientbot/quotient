from contextlib import suppress
import io
from typing import NoReturn, Union

from prettytable.prettytable import PrettyTable

from models import Scrim, Tourney
from datetime import datetime, timedelta
from utils import inputs
import constants
import discord
import config
import asyncio
import re


def get_slots(slots):
    for slot in slots:
        yield slot.user_id


def get_tourney_slots(slots):
    for slot in slots:
        yield slot.leader_id


async def add_role_and_reaction(ctx, role):
    with suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await ctx.author.add_roles(role)


async def already_reserved(scrim: Scrim):
    return list(i.num for i in await scrim.reserved_slots.all())


async def available_to_reserve(scrim: Scrim):
    reserved = await already_reserved(scrim)
    return list(i for i in scrim.available_to_reserve if i not in reserved)


async def cannot_take_registration(message: discord.Message, obj: Union[Scrim, Tourney]):
    logschan = obj.logschan

    with suppress(AttributeError, discord.Forbidden):
        embed = discord.Embed(
            color=discord.Color.red(), description=f"**Registration couldn't be accepted in {message.channel.mention}**"
        )
        embed.description += f"\nPossible reasons are:\n> I don't have add reaction permission in the channel\n> I don't have manage_roles permission in the server\n> My top role({message.guild.me.top_role.mention}) is below {obj.role.mention}"
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


async def scrim_end_process(ctx, scrim: Scrim) -> NoReturn:
    closed_at = datetime.now(tz=constants.IST)

    registration_channel = scrim.registration_channel
    open_role = scrim.open_role

    await Scrim.filter(pk=scrim.id).update(opened_at=None, closed_at=closed_at)

    channel_update = await toggle_channel(registration_channel, open_role, False)

    await registration_channel.send(
        embed=discord.Embed(color=config.COLOR, description="**Registration is now Closed!**")
    )

    ctx.bot.dispatch("scrim_log", constants.EsportsLog.closed, scrim, permission_updated=channel_update)

    if scrim.autoslotlist and len(await scrim.teams_registered):
        embed, channel = await scrim.create_slotlist()
        with suppress(AttributeError, discord.Forbidden):
            slotmsg = await channel.send(embed=embed)
            await Scrim.filter(pk=scrim.id).update(slotlist_message_id=slotmsg.id)


async def tourney_end_process(ctx, tourney: Tourney) -> NoReturn:
    closed_at = datetime.now(tz=constants.IST)

    registration_channel = tourney.registration_channel
    open_role = tourney.open_role

    await Tourney.filter(pk=tourney.id).update(started_at=None, closed_at=closed_at)
    channel_update = await toggle_channel(registration_channel, open_role, False)
    await registration_channel.send(
        embed=discord.Embed(color=ctx.bot.color, description="**Registration is now closed!**")
    )

    ctx.bot.dispatch("tourney_log", constants.EsportsLog.closed, tourney, permission_updated=channel_update)


async def purge_channels(channels):
    for channel in channels:
        if channel != None and channel.permissions_for(channel.guild.me).manage_messages:
            try:
                await channel.purge(limit=100, check=lambda x: not x.pinned)
            except:
                continue


async def purge_roles(roles):
    for role in roles:
        if role != None and role.guild.me.guild_permissions.manage_roles:
            if not role.guild.chunked:
                await role.guild.chunk()

            for member in role.members:
                try:
                    await member.remove_roles(role, reason="Scrims Manager Auto Role Remove in progress!")
                except:
                    continue


async def delete_denied_message(message: discord.Message, seconds=10):
    with suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
        await asyncio.sleep(seconds)
        await inputs.safe_delete(message)


def before_registrations(message: discord.Message, role: discord.Role) -> bool:
    me = message.guild.me
    channel = message.channel

    if (
        not me.guild_permissions.manage_roles
        or role > message.guild.me.top_role
        or not channel.permissions_for(me).add_reactions
    ):
        return False

    else:
        return True


async def check_tourney_requirements(bot, message: discord.Message, tourney: Tourney) -> bool:
    _bool = True

    if tourney.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
        _bool = False
        bot.dispatch("tourney_registration_deny", message, constants.RegDeny.botmention, tourney)

    elif not len(message.mentions) >= tourney.required_mentions:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, constants.RegDeny.nomention, tourney)

    elif message.author.id in tourney.banned_users:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, constants.RegDeny.banned, tourney)

    elif message.author.id in get_tourney_slots(await tourney.assigned_slots.all()) and not tourney.multiregister:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, constants.RegDeny.multiregister, tourney)

    return _bool


async def check_scrim_requirements(bot, message: discord.Message, scrim: Scrim) -> bool:
    _bool = True

    if scrim.teamname_compulsion:
        teamname = re.search(r"team.*", message.content)
        if not teamname or not teamname.group().strip():
            _bool = False
            bot.dispatch("scrim_registration_deny", message, constants.RegDeny.noteamname, scrim)

    elif scrim.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.botmention, scrim)

    elif not len(message.mentions) >= scrim.required_mentions:
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.nomention, scrim)

    elif message.author.id in await scrim.banned_user_ids():
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.banned, scrim)

    elif not scrim.multiregister and message.author.id in get_slots(await scrim.assigned_slots.all()):
        _bool = False
        bot.dispatch("scrim_registration_deny", message, constants.RegDeny.multiregister, scrim)

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

    role = scrim.ping_role if _type == constants.EsportsRole.ping else scrim.open_role

    if not role:
        return None

    if role == scrim.guild.default_role:
        return "@everyone"

    else:
        return role.mention


def tourney_work_role(tourney: Tourney):
    role = tourney.open_role
    if role == tourney.guild.default_role:
        return "@everyone"

    else:
        return role.mention


async def get_pretty_slotlist(scrim: Scrim):
    guild = scrim.guild

    table = PrettyTable()
    table.field_names = ["Slot", "Team Name", "Leader", "Jump URL"]
    for i in await scrim.teams_registered:
        member = guild.get_member(i.user_id)
        table.add_row([i.num, i.team_name, str(member), i.jump_url])

    fp = io.BytesIO(table.get_string().encode())
    return discord.File(fp, filename="slotlist.txt")
