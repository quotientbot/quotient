from core import Quotient, Cog, Context
from models import Logging
from constants import LogType
from contextlib import suppress
from utils.regex import INVITE_RE
import discord, re

__all__ = ("LoggingDispatchers",)


class LoggingDispatchers(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    # ====================================================================================
    # ==================================================================================== MESSAGE (DELETE, BULK DELETE, EDIT) EVENTS
    # ====================================================================================

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # not using raw_message_delete because if cached_message is None , there is nothing to log.
        self.bot.dispatch("snipe_deleted", message)
        guild = message.guild

        check = await Logging.get_or_none(guild_id=guild.id, type=LogType.msg)
        if check:
            if message.author.bot and check.ignore_bots:
                return
            else:
                self.bot.dispatch("log", LogType.msg, message=message, subtype="single")

    @Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages[0].guild:
            return

        guild = messages[0].guild
        check = await Logging.get_or_none(guild_id=guild.id, type=LogType.msg)
        if check:
            if messages[0].author.bot and check.ignore_bots:
                return
            else:
                self.bot.dispatch("log", LogType.msg, message=messages, subtype="bulk")

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild:
            return

        with suppress(AttributeError):
            if before.content == after.content:
                return

        check = await Logging.get_or_none(guild_id=before.guild.id, type=LogType.msg)
        if check:
            if before.author.bot and check.ignore_bots:
                return

            else:
                self.bot.dispatch("log", LogType.msg, message=(before, after))

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        check = await Logging.get_or_none(guild_id=guild.id, type=LogType.join)
        if check:
            if member.bot and check.ignore_bots:
                return
            else:
                self.bot.dispatch("log", LogType.join, member=member)

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild

        check = await Logging.get_or_none(guild_id=guild.id, type=LogType.leave)
        if check:
            if member.bot and check.ignore_bots:
                return
            else:
                self.bot.dispatch("log", LogType.leave, member=member)

    @Cog.listener(name="on_message")
    async def on_invite_post(self, message: discord.Message):
        if not message.guild:
            return

        invites = re.findall(INVITE_RE, message.content)
        if invites:
            check = await Logging.get_or_none(guild_id=message.guild.id, type=LogType.invite)
            if check:
                if message.author.bot and check.ignore_bots:
                    return
                else:
                    for invite in invites:
                        try:
                            inv = await self.bot.fetch_invite(invite)

                            self.bot.dispatch("log", LogType.invite, invite=inv, message=message)

                        except (discord.NotFound, discord.HTTPException):
                            continue

    @Cog.listener()
    async def on_invite_create(self, invite):
        if not invite.guild:
            return

        check = await Logging.get_or_none(guild_id=invite.guild.id, type=LogType.invite)
        if check:
            if invite.inviter.bot and check.ignore_bots:
                return

            else:
                self.bot.dispatch("log", LogType.invite, invite=invite, subtype="create")

    @Cog.listener()
    async def on_invite_delete(self, invite):
        if not invite.guild:
            return

        check = await Logging.get_or_none(guild_id=invite.guild.id, type=LogType.invite)
        if check:
            self.bot.dispatch("log", LogType.invite, invite=invite, subtype="delete")

    @Cog.listener(name="on_message")
    async def on_ping_message(self, message: discord.Message):
        if not message.guild:
            return

        mentions = set()

        if message.mention_everyone:
            mentions.add("@everyone")

        for m in message.mentions + message.role_mentions:
            mentions.add(m.mention)

        if mentions:
            check = await Logging.get_or_none(guild_id=message.guild.id, type=LogType.ping)
            if check:

                if message.author.bot and check.ignore_bots:
                    return
                else:
                    self.bot.dispatch("log", LogType.ping, message=message, mentions=mentions)

    @Cog.listener()
    async def on_command(self, ctx):
        if not ctx.guild:
            return

        check = await Logging.get_or_none(guild_id=ctx.guild.id, type=LogType.cmd)
        if check:
            self.bot.dispatch("log", LogType.cmd, ctx=ctx)

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild:
            return

        check = await Logging.get_or_none(guild_id=member.guild.id, type=LogType.voice)
        if check:
            if member.bot and check.ignore_bots:
                return

            else:
                self.bot.dispatch("log", LogType.voice, member=member, before=before, after=after)

    @Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        check = await Logging.get_or_none(guild_id=role.guild.id, type=LogType.role)
        if check:
            self.bot.dispatch("log", LogType.role, role=role, subtype="create")

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        check = await Logging.get_or_none(guild_id=role.guild.id, type=LogType.role)
        if check:
            self.bot.dispatch("log", LogType.role, role=role, subtype="delete")

    @Cog.listener()
    async def on_guild_role_update(self, before, after):
        check = await Logging.get_or_none(guild_id=before.guild.id, type=LogType.role)
        if not check:
            return  
