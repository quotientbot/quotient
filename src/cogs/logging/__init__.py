from re import L
from utils import LogType, ColorConverter
from core import Quotient, Cog, Context
from discord.ext import commands
from .dispatchers import *
from models import Logging as LM

from utils import emote
from .events import *
import discord
import typing


class Logging(Cog, name="logging"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.errors.BadArgument):  # raised when invalid LogType is passed.
            await ctx.send("value error")

    async def insert_or_update_config(self, ctx: Context, _type: LogType, channel: discord.TextChannel):
        guild = ctx.guild

        record = await LM.get_or_none(guild_id=guild.id, type=_type)
        if record is None:
            await LM.create(guild_id=guild.id, channel_id=channel.id, type=_type)

        else:
            await LM.filter(guild_id=guild.id, type=_type).update(channel_id=channel.id)

        return record

    @commands.command()
    async def msglog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.msg, channel)
        if not record:
            await ctx.success(f"Msglog enabled successfully!")
        else:
            return await ctx.success(f"Msglog channel updated to **{channel}**")

    @commands.command()
    async def joinlog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.join, channel)
        if not record:
            await ctx.success(f"Joinlog enabled successfully!")
        else:
            return await ctx.success(f"Joinlog channel updated to **{channel}**")

    @commands.command()
    async def leavelog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.leave, channel)
        if not record:
            await ctx.success(f"Leavelog enabled successfully!")
        else:
            return await ctx.success(f"Leavelog channel updated to **{channel}**")

    @commands.command()
    async def actionlog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.action, channel)
        if not record:
            await ctx.success(f"Actionlog enabled successfully!")
        else:
            return await ctx.success(f"Actionlog channel updated to **{channel}**")

    @commands.command()
    async def serverlog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.server, channel)
        if not record:
            await ctx.success(f"Serverlog enabled successfully!")
        else:
            return await ctx.success(f"Serverlog channel updated to **{channel}**")

    @commands.command()
    async def channellog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.channel, channel)
        if not record:
            await ctx.success(f"Channellog enabled successfully!")
        else:
            return await ctx.success(f"Channellog channel updated to **{channel}**")

    @commands.command()
    async def rolelog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.role, channel)
        if not record:
            await ctx.success(f"Rolelog enabled successfully!")
        else:
            return await ctx.success(f"Rolelog channel updated to **{channel}**")

    @commands.command()
    async def memberlog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.member, channel)
        if not record:
            await ctx.success(f"Memberlog enabled successfully!")
        else:
            return await ctx.success(f"Memberlog channel updated to **{channel}**")

    @commands.command()
    async def voicelog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.voice, channel)
        if not record:
            await ctx.success(f"Voicelog enabled successfully!")
        else:
            return await ctx.success(f"Voicelog channel updated to **{channel}**")

    @commands.command()
    async def reactionlog(self, ctx: Context, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.reaction, channel)
        if not record:
            await ctx.success(f"Reactionlog enabled successfully!")
        else:
            return await ctx.success(f"Reactionlog channel updated to **{channel}**")

    @commands.command()
    async def modlog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.mod, channel)
        if not record:
            await ctx.success(f"Modlog enabled successfully!")
        else:
            return await ctx.success(f"Modlog channel updated to **{channel}**")

    @commands.command()
    async def cmdlog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.cmd, channel)
        if not record:
            await ctx.success(f"Cmdlog enabled successfully!")
        else:
            return await ctx.success(f"Cmdlog channel updated to **{channel}**")

    @commands.command()
    async def invitelog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.invite, channel)
        if not record:
            await ctx.success(f"Invitelog enabled successfully!")
        else:
            return await ctx.success(f"Invitelog channel updated to **{channel}**")

    @commands.command()
    async def pinglog(self, ctx: Context, *, channel: discord.TextChannel):
        record = await self.insert_or_update_config(ctx, LogType.ping, channel)
        if not record:
            await ctx.success(f"Pinglog enabled successfully!")
        else:
            return await ctx.success(f"Pinglog channel updated to **{channel}**")

    @commands.command()
    async def logall(self, ctx: Context, *, channel: discord.TextChannel):
        pass

    @commands.command()
    async def logcolor(self, ctx: Context, logtype: LogType, color: ColorConverter):
        color = int(str(color).replace("#", ""), 16)
        if logtype.value == "mod":
            return await ctx.error(
                f"Colors for modlogs cannot be manipulated, they are applied automatically according to the severity of the action."
            )

        check = await LM.get_or_none(guild_id=ctx.guild.id, type=logtype)
        if not check:
            return await ctx.send(
                f"You haven't enabled **`{logtype.value} logging`** yet.\n\nDo it like: `{ctx.prefix}logcolor {logtype.value} <some color>`"
            )

        await LM.filter(guild_id=ctx.guild.id, type=logtype).update(color=color)
        await ctx.message.add_reaction(emote.check)

    @commands.command()
    async def logbots(self, ctx: Context, logtype: LogType):
        check = await LM.get_or_none(guild_id=ctx.guild.id, type=logtype)
        if not check:
            return await ctx.send(
                f"You haven't enabled **`{logtype.value} logging`** yet.\n\nDo it like: `{ctx.prefix}logcolor {logtype.value} <some color>`"
            )

        await LM.filter(guild_id=ctx.guild.id, type=logtype).update(ignore_bots=not (check.ignore_bots))
        await ctx.success(
            f"Bots logging turned {'ON' if not check.ignore_bots else 'OFF'} for {logtype.value.title()} logs."
        )

    @commands.command()
    async def logtoggle(self, ctx: Context, logtype: typing.Union[LogType, str]):
        pass

    @commands.command()
    async def logconfig(self, ctx: Context):
        records = await LM.filter(guild_id=ctx.guild.id).all()
        if not len(records):
            return await ctx.error(f"You haven't set logging yet.")
        text = "**`Toggle` | `Type` | `Channel` | `Ignore Bots` | `Color`**\n\n"

        for idx, record in enumerate(records, start=1):
            emoji = emote.settings_yes if record.toggle else emote.settings_no
            bottoggle = emote.settings_yes if record.ignore_bots else emote.settings_no
            text += f"`{idx:02d}` {emoji} **{record.type.value.title()}** {getattr(record.channel,'mention','Channel Deleted!')} {bottoggle} {record.color}\n"

        embed = self.bot.embed(ctx, description=text)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Logging(bot))
    bot.add_cog(LoggingDispatchers(bot))
    bot.add_cog(LoggingEvents(bot))
