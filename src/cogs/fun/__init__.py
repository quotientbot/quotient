from models.models import Autoevent
from .helper import insert_or_update_config
from core import Cog, Context, Quotient
from discord.ext import commands
from utils import EventType, emote, checks
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
    @commands.has_permissions(manage_guild=True)
    async def autotoggle(self, ctx: Context, eventype: str = None):
        valids = (
            "automeme",
            "autofact",
            "autoquote",
            "autojoke",
            "autonsfw",
            "autoadvice",
            "autopoem",
        )

        displayable_options = ",".join(map(lambda s: f"`{s}`", valids))
        if eventype is None:
            return await ctx.send(
                f"Which autoevent do you want to toggle?\nValid options are: {displayable_options}.\n\nExample: `{ctx.prefix}autotoggle automeme`"
            )

        elif eventype.lower() not in valids:
            return await ctx.send(
                f"What you chose isn't a valid option mate!\nChoose from: {displayable_options}.\n\nExample: `{ctx.prefix}autotoggle autofact`"
            )

        real = eventype.lower()[4:]  # we slice 'auto' from eventype because we do not store that

        check = await Autoevent.filter(guild_id=ctx.guild.id, type=EventType(real)).first()
        if not check:
            return await ctx.error(
                f"You haven't setup {eventype.lower()} yet.\n\nDo it like `{ctx.prefix}{eventype.lower()} #{ctx.channel.name}`"
            )

        await Autoevent.filter(guild_id=ctx.guild.id, type=EventType(real)).update(toggle=not (check.toggle))
        await ctx.success(f"{eventype.title()} turned {'ON' if not(check.toggle) else 'OFF'}!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autointerval(self, ctx: Context, eventype: str = None):
        valids = (
            "automeme",
            "autofact",
            "autoquote",
            "autojoke",
            "autonsfw",
            "autoadvice",
            "autopoem",
        )

        displayable_options = ",".join(map(lambda s: f"`{s}`", valids))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autoconfig(self, ctx: Context):
        records = await Autoevent.filter(guild_id=ctx.guild.id)
        if not len(records):
            return await ctx.error(
                f"You don't have any autoevent setup.\n\nSetup autoevents: `{ctx.prefix}automeme #{ctx.channel.name}`"
            )

        text = "**`Toggle`  |  `Type`  |  `Channel`  |  `Interval`**\n\n"
        for idx, record in enumerate(records, start=1):
            emoji = emote.settings_yes if record.toggle else emote.settings_no
            text += f"`{idx:02d}` {emoji} **{record.type.value.title()}** {getattr(record.channel , 'mention', '`Channel Deleted!`')} `{record.interval} mins`"

        embed = self.bot.embed(ctx, description=text, title="Autoevents Config")
        await ctx.send(embed=embed)


def setup(bot) -> None:
    bot.add_cog(Fun(bot))
    bot.add_cog(Funevents(bot))
