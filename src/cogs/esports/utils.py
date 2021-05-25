from typing import NoReturn, Union
from models import Scrim, Tourney
from datetime import datetime, timedelta
from utils import constants
import discord
import humanize
import config


def get_slots(slots):
    for slot in slots:
        yield slot.user_id


async def cannot_take_registration(message: discord.Message, type: str, obj: Union[Scrim, Tourney]):
    logschan = obj.logschan
    if logschan is not None and logschan.permissions_for(message.guild.me).embed_links:
        embed = discord.Embed(
            color=discord.Color.red(), description=f"**Registration couldn't be accepted in {message.channel.mention}**"
        )
        embed.description += f"\nPossible reasons are:\n> I don't have add reaction permission in the channel\n> I don't have manage_roles permission in the server\n> My top role({message.guild.me.top_role.mention}) is below {obj.role.mention}"
        await logschan.send(
            content=getattr(obj.modrole, "mention", None),
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )


async def is_valid_scrim(bot, scrim) -> bool:
    guild = scrim.guild
    registration_channel = scrim.registration_channel
    role = scrim.role
    _bool = True
    embed = discord.Embed(color=discord.Color.red())
    embed.description = f"Registration of `scrim {scrim.id}` couldn't be opened due to the following reason:\n"

    if not registration_channel:
        embed.description += "I couldn't find registration channel. Maybe its deleted or hidden from me."
        _bool = False

    elif not registration_channel.permissions_for(guild.me).manage_channels:
        embed.description += "I don't have permissions to manage {0}".format(registration_channel.mention)
        _bool = False

    elif scrim.role is None:
        embed.description += "I couldn't find success role."
        _bool = False

    elif not guild.me.guild_permissions.manage_roles or role.position >= guild.me.top_role.position:
        embed.description += (
            "I don't have permissions to `manage roles` in this server or {0} is above my top role ({1}).".format(
                role.mention, guild.me.top_role.mention
            )
        )
        _bool = False

    elif scrim.open_role_id and not scrim.open_role:
        embed.description += "You have set a custom open role which is deleted."
        _bool = False

    if not _bool:
        logschan = scrim.logschan
        if logschan and logschan.permissions_for(guild.me).send_messages:
            await logschan.send(
                content=getattr(scrim.modrole, "mention", None),
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )

    return _bool


async def postpone_scrim(bot, scrim) -> NoReturn:
    reminder = bot.get_cog("Reminders")

    await Scrim.filter(pk=scrim.id).update(open_time=scrim.open_time + timedelta(hours=24))
    await scrim.refresh_from_db(("open_time",))

    await reminder.create_timer(
        scrim.open_time,
        "scrim_open",
        scrim_id=scrim.id,
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
    opened_at = scrim.opened_at
    closed_at = datetime.now(tz=constants.IST)

    registration_channel = scrim.registration_channel
    open_role = scrim.open_role

    await Scrim.filter(pk=scrim.id).update(opened_at=None, closed_at=closed_at)

    channel_update = await toggle_channel(registration_channel, open_role, False)

    await registration_channel.send(
        embed=discord.Embed(color=config.COLOR, description="**Registration is now Closed!**")
    )

    ctx.bot.dispatch("scrim_log", "closed", scrim, permission_updated=channel_update)

    if scrim.autoslotlist and len(await scrim.teams_registered):
        time_taken = closed_at - opened_at
        delta = datetime.now() - timedelta(seconds=time_taken.total_seconds())

        time_taken = humanize.precisedelta(delta)

        embed, channel = await scrim.create_slotlist()

        embed.set_footer(text="Registration took: {0}".format(time_taken))
        embed.color = config.COLOR

        if channel != None and channel.permissions_for(ctx.me).send_messages:
            slotmsg = await channel.send(embed=embed)
            await Scrim.filter(pk=scrim.id).update(slotlist_message_id=slotmsg.id)


async def tourney_end_process(ctx, tourney: Tourney) -> NoReturn:
    started_at = tourney.started_at
    closed_at = datetime.now(tz=constants.IST)

    registration_channel = tourney.registration_channel
    open_role = tourney.open_role

    await Tourney.filter(pk=tourney.id).update(started_at=None, closed_at=closed_at)
    channel_update = await toggle_channel(registration_channel, open_role, False)
    await registration_channel.send(
        embed=discord.Embed(color=ctx.bot.color, description="**Registration is now closed!**")
    )

    ctx.bot.dispatch("tourney_log", "closed", tourney, permission_updated=channel_update)


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
            for member in role.members:
                try:
                    await member.remove_roles(role, reason="Scrims Manager Auto Role Remove in progress!")
                except:
                    continue
