from models import Guild, Tourney, Scrim, Autorole, TMSlot
from core import Cog, Quotient
from constants import random_greeting
import discord, config
import re


class MainEvents(Cog, name="Main Events"):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.bot.loop.create_task(self.super_important_job())

    async def super_important_job(self):
        await self.bot.wait_until_ready()
        await self.bot.get_channel(844178791735885824).connect()

    # incomplete?, I know
    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await Guild.create(guild_id=guild.id)
        self.bot.guild_data[guild.id] = {"prefix": "q", "color": self.bot.color, "footer": config.FOOTER}
        await guild.chunk()

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await Guild.filter(guild_id=guild.id).delete()
        await Scrim.filter(guild_id=guild.id).delete()
        await Tourney.filter(guild_id=guild.id).delete()
        await Autorole.filter(guild_id=guild.id).delete()
        try:
            self.bot.guild_data.pop(guild.id)
        except KeyError:
            pass

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if re.match(f"^<@!?{self.bot.user.id}>$", message.content):
            self.bot.dispatch("mention", ctx)

    @Cog.listener()
    async def on_mention(self, ctx):
        prefix = "q"
        await ctx.send(
            f"{random_greeting()}, You seem lost. Are you?\n"
            f"Current prefix for this server is: `{prefix}`.\n\nUse it like: `{prefix}help`"
        )
