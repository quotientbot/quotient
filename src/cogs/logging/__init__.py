from core import Quotient, Cog, Context
from discord.ext import commands
from .dispatchers import *
from utils import LogType
from .events import *
import discord
import typing


class Logging(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    async def msglog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def joinlog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def leavelog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def actionlog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def serverlog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def channellog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def rolelog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def memberlog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def voicelog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def reactionlog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def modlog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def cmdlog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def invitelog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def pinglog(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def logall(self, ctx: Context, channel: discord.TextChannel):
        pass

    @commands.command()
    async def logcolor(self, ctx: Context, logtype: LogType, color):
        pass

    @commands.group(invoke_without_command=True)
    async def logignore(self, ctx: Context):
        pass

    @logignore.command(name="bots")
    async def logignore_bots(self, ctx: Context, logtype: LogType):
        pass

    @logignore.command(name="channel")
    async def logignore_channels(
        self, ctx: Context, logtype: LogType, *, channel: typing.Union[discord.TextChannel, discord.VoiceChannel]
    ):
        pass

    @commands.command()
    async def logtoggle(self, ctx: Context, logtype: typing.Union[LogType, str]):
        pass


def setup(bot):
    bot.add_cog(Logging(bot))
    bot.add_cog(LoggingDispatchers(bot))
    bot.add_cog(LoggingEvents(bot))
