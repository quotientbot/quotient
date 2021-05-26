from .helper import insert_or_update_config
from core import Cog, Context, Quotient
from discord.ext import commands
from utils import EventType
from .funevents import *
import discord


class Fun(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def automeme(self, ctx: Context, *, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        record = await insert_or_update_config(ctx, EventType.meme, channel)
        if not record:
            await ctx.success(f"Automeme enabled successfully!")
        else:
            await ctx.success(f"Automeme record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autofact(self, ctx: Context, *, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        record = await insert_or_update_config(ctx, EventType.fact, channel)
        if not record:
            await ctx.success(f"Autofact enabled successfully!")
        else:
            await ctx.success(f"Autofact record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autoquote(self, ctx: Context, *, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        record = await insert_or_update_config(ctx, EventType.quote, channel)
        if not record:
            await ctx.success(f"Autoquotes enabled successfully!")
        else:
            await ctx.success(f"Autoquote record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autojoke(self, ctx: Context, *, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        record = await insert_or_update_config(ctx, EventType.joke, channel)
        if not record:
            await ctx.success(f"Autojokes enabled successfully!")
        else:
            await ctx.success(f"Autojoke record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autonsfw(self, ctx: Context, *, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        if channel.is_nsfw == False:
            return await ctx.error("The channel is not NSFW.")

        record = await insert_or_update_config(ctx, EventType.meme, channel)
        if not record:
            await ctx.success(f"AutoNSFW enabled successfully!")
        else:
            await ctx.success(f"AutoNSFW record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autoadvice(self, ctx: Context, *, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        record = await insert_or_update_config(ctx, EventType.advice, channel)
        if not record:
            await ctx.success(f"Autoadvice enabled successfully!")
        else:
            await ctx.success(f"Autoadvice record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autopoem(self, ctx: Context, *, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        record = await insert_or_update_config(ctx, EventType.poem, channel)
        if not record:
            await ctx.success(f"Autopoem enabled successfully!")
        else:
            await ctx.success(f"Autopeom record updated!")

    @commands.command()
    async def autotoggle(self, ctx: Context, eventype: str = None):
        pass

    @commands.command()
    async def autoconfig(self, ctx: Context):
        pass

    @commands.command()
    async def autointerval(self, ctx: Context, eventype: str = None):
        pass


def setup(bot) -> None:
    bot.add_cog(Fun(bot))
    bot.add_cog(Funevents(bot))
