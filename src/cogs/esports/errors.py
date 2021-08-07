from models import Scrim, Timer, BannedTeam, ReservedSlot, Tourney, AssignedSlot, ArrayAppend, TagCheck
from models.esports import EasyTag
from .utils import (
    get_pretty_slotlist,
    delete_denied_message,
    scrim_work_role,
    tourney_work_role,
)
from constants import EsportsRole, EsportsLog, RegDeny
from discord.ext import commands
from contextlib import suppress
from utils import plural
from core import Cog
import discord


class ScrimError(commands.CommandError):
    pass


class TourneyError(commands.CommandError):
    pass


class PointsError(commands.CommandError):
    pass


class VerifyError(commands.CommandError):
    pass


class SMError(Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def red_embed(description: str):
        embed = discord.Embed(color=discord.Color.red(), description=description)
        return embed

    @Cog.listener()
    async def on_tourney_registration_deny(self, message: discord.Message, _type: RegDeny, tourney: Tourney):

        logschan = tourney.logschan
        if not logschan:
            return await Tourney.filter(id=tourney.id).delete()

        text = f"Registration of [{str(message.author)}]({message.jump_url}) has been denied in {message.channel.mention}\n**Reason:** "

        with suppress(discord.NotFound, discord.NotFound, AttributeError, discord.HTTPException):
            await message.add_reaction("\N{CROSS MARK}")

            if _type == RegDeny.botmention:
                await message.reply(
                    embed=self.red_embed("Don't mention Bots. Mention your real teammates."),
                    delete_after=5,
                )
                text += f"Mentioned Bots."

            elif _type == RegDeny.nomention:
                await message.reply(
                    embed=self.red_embed(
                        f"{str(message.author)}, **`{plural(tourney.required_mentions):mention is |mentions are}`** required for successful registration."
                    ),
                    delete_after=5,
                )

                text += f"Insufficient Mentions (`{len(message.mentions)}/{tourney.required_mentions}`)"

            elif _type == RegDeny.banned:
                await message.reply(
                    embed=self.red_embed(
                        f"{str(message.author)}, You are banned from the tournament. You cannot register."
                    ),
                    delete_after=5,
                )
                text += f"They are banned from tournament."

            elif _type == RegDeny.multiregister:
                await message.reply(
                    embed=self.red_embed(f"{str(message.author)}, This server doesn't allow multiple registerations."),
                    delete_after=5,
                )

                text += f"They have already registered once.\n\nIf you wish to allow multiple registerations,\nuse: `tourney edit {tourney.id}`"

            elif _type == RegDeny.noteamname:
                await message.reply(
                    embed=self.red_embed(f"{str(message.author)}, Team Name is required to register."),
                    delete_after=5,
                )
                text += f"Teamname compulsion is on and I couldn't find teamname in their registration\n\nIf you wish allow without teamname,\nUse: `tourney edit {tourney.id}`"

            embed = discord.Embed(color=discord.Color.red(), description=text)
            with suppress(discord.Forbidden):
                return await logschan.send(embed=embed)

    @Cog.listener()
    async def on_tourney_log(self, _type: EsportsLog, tourney: Tourney, **kwargs):
        """
        Same as on_scrim_log but for tourneys
        """
        logschan = tourney.logschan
        if not logschan:
            return await Tourney.filter(id=tourney.id).delete()

        registration_channel = tourney.registration_channel
        modrole = tourney.modrole

        open_role = tourney_work_role(tourney)
        important = False

        embed = discord.Embed(color=0x00B1FF)
        if _type == EsportsLog.closed:
            permission_updated = kwargs.get("permission_updated")

            embed.description = (
                f"Registration closed for {open_role} in {registration_channel.mention}(TourneyID: `{tourney.id}`)"
            )
            if not permission_updated:
                important = True
                embed.color = discord.Color.red()
                embed.description += f"\nI couldn't close {registration_channel.mention}."

        elif _type == EsportsLog.success:
            message = kwargs.get("message")

            confirmation = tourney.confirm_channel

            if confirmation is not None:
                slot = kwargs.get("assigned_slot")
                num = kwargs.get("num")
                e = discord.Embed(
                    color=self.bot.color,
                    description=f"**{num}) NAME: [{slot.team_name.upper()}]({message.jump_url})**\n",
                )
                if len(message.mentions) > 0:
                    e.description += f"Team: {', '.join([str(m) for m in message.mentions])}"

                await confirmation.send(
                    content=message.author.mention,
                    embed=e,
                    allowed_mentions=discord.AllowedMentions(users=True),
                )

                embed.color = discord.Color.green()
                embed.description = f"Registration of [{message.author}]({message.jump_url}) has been accepted in {message.channel.mention}"

        with suppress(discord.Forbidden, AttributeError):
            await logschan.send(
                content=modrole.mention if modrole is not None and important is True else None,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )

    @Cog.listener()
    async def on_scrim_log(self, _type: EsportsLog, scrim: Scrim, **kwargs):
        """
        A listener that is dispatched everytime registration starts/ends or a registration is accepted.
        """
        logschan = scrim.logschan
        if not logschan:
            return await Scrim.filter(id=scrim.id).delete()

        registration_channel = scrim.registration_channel
        modrole = scrim.modrole

        open_role = scrim_work_role(scrim, EsportsRole.open)

        important = False

        embed = discord.Embed(color=0x00B1FF)
        with suppress(discord.NotFound, discord.Forbidden, AttributeError, discord.HTTPException):

            if _type == EsportsLog.open:
                embed.description = (
                    f"Registration opened for {open_role} in {registration_channel.mention}(ScrimsID: `{scrim.id}`)"
                )

            elif _type == EsportsLog.closed:
                permission_updated = kwargs.get("permission_updated")
                embed.description = f"Registration closed for {open_role} in {registration_channel.mention}(ScrimsID: `{scrim.id}`)\n\nUse `smanager slotlist edit {scrim.id}` to edit the slotlist."

                slotlist = await get_pretty_slotlist(scrim)
                await logschan.send(file=slotlist)

                if not permission_updated:
                    important = True
                    embed.color = discord.Color.red()
                    embed.description += f"\nI couldn't close {registration_channel.mention}."

            elif _type == EsportsLog.success:

                message = kwargs.get("message")

                embed.color = discord.Color.green()
                embed.description = f"Registration of [{message.author}]({message.jump_url}) has been accepted in {message.channel.mention}"

            await logschan.send(
                content=modrole.mention if modrole is not None and important is True else None,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )

    # ==========================================================================================================================
    # ==========================================================================================================================

    @Cog.listener()
    async def on_scrim_registration_deny(self, message: discord.Message, _type: RegDeny, scrim: Scrim):
        logschan = scrim.logschan
        if logschan is None:
            return await Scrim.filter(id=scrim.id).delete()

        text = f"Registration of [{str(message.author)}]({message.jump_url}) has been denied in {message.channel.mention}\n**Reason:** "

        with suppress(discord.NotFound, discord.Forbidden, AttributeError, discord.HTTPException):
            await message.add_reaction("\N{CROSS MARK}")

            if _type == RegDeny.botmention:
                await message.reply(
                    embed=self.red_embed("Don't mention Bots. Mention your real teammates."),
                    delete_after=5,
                )
                text += f"Mentioned Bots."

            elif _type == RegDeny.nomention:
                await message.reply(
                    embed=self.red_embed(
                        f"{str(message.author)}, **`{plural(scrim.required_mentions):mention is |mentions are}`** required for successful registration."
                    ),
                    delete_after=5,
                )
                text += f"Insufficient Mentions (`{len(message.mentions)}/{scrim.required_mentions}`)"

            elif _type == RegDeny.banned:
                await message.reply(
                    embed=self.red_embed(f"{str(message.author)}, You are banned from the scrims. You cannot register."),
                    delete_after=5,
                )
                text += f"They are banned from scrims."

            elif _type == RegDeny.multiregister:
                await message.reply(
                    embed=self.red_embed(f"{str(message.author)}, This server doesn't allow multiple registerations."),
                    delete_after=5,
                )
                text += f"They have already registered once.\n\nIf you wish to allow multiple registerations,\nuse: `smanager toggle {scrim.id} multiregister`"

            elif _type == RegDeny.noteamname:
                await message.reply(
                    embed=self.red_embed(f"{str(message.author)}, Team Name is required to register."),
                    delete_after=5,
                )
                text += f"Teamname compulsion is on and I couldn't find teamname in their registration\n\nIf you wish allow without teamname,\nUse: `smanager edit {scrim.id}`"

            elif _type == RegDeny.duplicate:
                await message.reply(
                    embed=self.red_embed(
                        f"{str(message.author)}, Someone has already registered with the same teamname."
                    ),
                    delete_after=5,
                )
                text += f"No duplicate team names is ON and someone has already registered with the same team name\nIf you wish to allow duplicate team names,\nUse: `smanager edit {scrim.id}`"

            if scrim.autodelete_rejects:
                self.bot.loop.create_task(delete_denied_message(message))

            embed = discord.Embed(color=discord.Color.red(), description=text)
            return await logschan.send(embed=embed)

    # ==========================================================================================================================
    # ==========================================================================================================================

    @Cog.listener()
    async def on_scrim_unban_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]
        user_id = timer.kwargs["user_id"]
        banned_by = timer.kwargs["banned_by"]

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if scrim is None:
            # probably deleted
            await scrim.delete()

        guild = scrim.guild
        if guild is None:  # sed
            await scrim.delete()

        if not user_id in await scrim.banned_user_ids():
            # probably unbanned manually with the command.
            return

        ban = await scrim.banned_teams.filter(user_id=user_id).first()
        await BannedTeam.filter(id=ban.id).delete()

        logschan = scrim.logschan
        if logschan is not None and logschan.permissions_for(guild.me).send_messages:
            banner = guild.get_member(banned_by) or self.bot.get_user(banned_by)
            user = guild.get_member(user_id) or self.bot.get_user(user_id)
            embed = discord.Embed(
                color=discord.Color.green(),
                description=f"{user} ({user_id}) have been unbanned from Scrim (`{scrim.id}`).\nThey were banned by {banner} ({banned_by}).",
            )
            await logschan.send(embed=embed)

    @Cog.listener()
    async def on_scrim_reserve_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]
        team_name = timer.kwargs["team_name"]
        user_id = timer.kwargs["user_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if scrim is None:
            return

        guild = scrim.guild
        if not guild:
            await scrim.delete()

        if not user_id in await scrim.reserved_user_ids():
            return

        team = await scrim.reserved_slots.filter(user_id=user_id).first()

        if team.expires != timer.expires:
            return

        await ReservedSlot.filter(id=team.id).delete()

        logschan = scrim.logschan
        if logschan is not None and logschan.permissions_for(guild.me).send_messages:
            user = self.bot.get_user(user_id)
            embed = discord.Embed(
                color=discord.Color.green(),
                description=f"Reservation period of **{team_name.title()}** ({user}) is now over.\nSlot will not be reserved for them in Scrim (`{scrim_id}`).",
            )

            await logschan.send(embed=embed)

    @Cog.listener()
    async def on_scrim_cmd_log(self, **kwargs):
        ...

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        # will delete scrim/tournament if its registration channel.
        self.bot.eztagchannels.discard(channel.id)
        self.bot.tagcheck.discard(channel.id)
        self.bot.scrim_channels.discard(channel.id)
        self.bot.tourney_channels.discard(channel.id)

        await Scrim.filter(registration_channel_id=channel.id).delete()
        await Tourney.filter(registration_channel_id=channel.id).delete()
        await TagCheck.filter(channel_id=channel.id).delete()
        await EasyTag.filter(channel_id=channel.id).delete()

    @Cog.listener()
    async def on_scrim_registration_delete(self, scrim: Scrim, message: discord.Message, slot):
        self.bot.loop.create_task(message.author.remove_roles(scrim.role))
        await AssignedSlot.filter(id=slot.id).delete()
        await Scrim.filter(id=scrim.id).update(available_slots=ArrayAppend("available_slots", slot.num))
        if scrim.logschan is not None:
            embed = discord.Embed(color=discord.Color.red())
            embed.description = f"Slot of {message.author.mention} was deleted from Scrim: {scrim.id}, because their registration was deleted from {message.channel.mention}"
            await scrim.logschan.send(embed=embed)
