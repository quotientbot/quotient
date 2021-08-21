from models import Guild, Tourney, Scrim, Autorole
from discord import Webhook
from core import Cog, Quotient
from contextlib import suppress
from constants import random_greeting
import discord, config
import re

from models.models import Autoevent, Giveaway, Lockdown, Logging, Tag


class MainEvents(Cog, name="Main Events"):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.bot.loop.create_task(self.super_important_job())

    async def super_important_job(self):
        await self.bot.wait_until_ready()
        guild = await self.bot.getch(self.bot.get_guild, self.bot.fetch_guild, config.SERVER_ID)
        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())
        with suppress(AttributeError, discord.ClientException):
            await guild.get_channel(844178791735885824).connect()

    # incomplete?, I know
    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        with suppress(AttributeError):
            await Guild.create(guild_id=guild.id)
            self.bot.guild_data[guild.id] = {"prefix": "q", "color": self.bot.color, "footer": config.FOOTER}
            await guild.chunk()

            embed = discord.Embed(color=discord.Color.green(), title=f"I've joined a guild ({guild.member_count})")
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.add_field(
                name="__**General Info**__",
                value=f"**Guild Name:** {guild.name} [{guild.id}]\n**Guild Owner:** {guild.owner} [{guild.owner.id}]\n",
            )

            with suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
                webhook = Webhook.from_url(config.JOIN_LOG, session=self.bot.session)
                await webhook.send(embed=embed, avatar_url=self.bot.user.avatar.url)

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        with suppress(AttributeError):
            check = await Guild.get_or_none(guild_id=guild.id)
            if check and not check.is_premium:
                await Guild.filter(guild_id=guild.id).delete()

            await Scrim.filter(guild_id=guild.id).delete()
            await Tourney.filter(guild_id=guild.id).delete()
            await Autorole.filter(guild_id=guild.id).delete()
            await Tag.filter(guild_id=guild.id).delete()
            await Lockdown.filter(guild_id=guild.id).delete()
            await Autoevent.filter(guild_id=guild.id).delete()
            await Giveaway.filter(guild_id=guild.id).delete()

            try:
                self.bot.guild_data.pop(guild.id)
            except KeyError:
                pass

            embed = discord.Embed(color=discord.Color.red(), title=f"I have left a guild ({guild.member_count})")
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.add_field(
                name="__**General Info**__",
                value=f"**Guild name:** {guild.name} [{guild.id}]\n**Guild owner:** {guild.owner} [{guild.owner.id if guild.owner is not None else 'Not Found!'}]\n",
            )
            with suppress(discord.HTTPException, discord.NotFound, discord.Forbidden):
                webhook = Webhook.from_url(config.JOIN_LOG, session=self.bot.session)
                await webhook.send(embed=embed, avatar_url=self.bot.user.avatar.url)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if re.match(f"^<@!?{self.bot.user.id}>$", message.content):
            self.bot.dispatch("mention", ctx)

    @Cog.listener()
    async def on_mention(self, ctx):
        prefix = self.bot.guild_data[ctx.guild.id]["prefix"] or "q"
        await ctx.send(
            f"{random_greeting()}, You seem lost. Are you?\n"
            f"Current prefix for this server is: `{prefix}`.\n\nUse it like: `{prefix}help`"
        )
