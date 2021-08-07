from models.models import Autoevent
from .helper import insert_or_update_config
from core import Cog, Context, Quotient
from discord.ext import commands
from utils import emote, checks, simple_convert
from constants import EventType
from .funevents import *
import discord, asyncio


class Fun(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def automeme(self, ctx: Context, *, channel: discord.TextChannel):
        """
        Get the latest and trendy memes served in your server in a definite timespan.
        Must have `manage server` permissions.
        Bot must have `manage webhooks` permission
        """
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
        """
        Want to boost your general knowledge? This command will help you by sending facts automatically.
        Must have `manage server` permissions.
        Bot must have `manage webhooks` permission.
        """
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

        """
        Need something to boost your life up? This command will send worth reading quotes automatically
        Must have `manage server` permissions.
        Bot must have `manage webhooks` permission.
        """
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
        """
        Want to laugh like hell? Get some really funny jokes automatically.
        Must have `manage server` permissions.
        Bot must have `manage webhooks` permission.
        """
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
        """
        Ohh so you are an adult now! So here is some automatic nsfw to rest your liver.
        Must have `manage server` permissions.
        Bot must have `manage webhooks` permission.
        """
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        if channel.is_nsfw() == False:
            return await ctx.error("The channel is not NSFW.")

        record = await insert_or_update_config(ctx, EventType.nsfw, channel)
        if not record:
            await ctx.success(f"AutoNSFW enabled successfully!")
        else:
            await ctx.success(f"AutoNSFW record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autoadvice(self, ctx: Context, *, channel: discord.TextChannel):
        """
        I will take care of everything don't worry honey. I am a consultant too. Get some automatic advises.
        Must have `manage server` permissions.
        Bot must have `manage webhooks` permission.
        """
        if not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

        record = await insert_or_update_config(ctx, EventType.advice, channel)
        if not record:
            await ctx.success(f"Autoadvice enabled successfully!")
        else:
            await ctx.success(f"Autoadvice record updated!")

    # @commands.command()
    # @commands.has_permissions(manage_guild=True)
    # async def autopoem(self, ctx: Context, *, channel: discord.TextChannel):
    #     """
    #     Get some nice poetry automatically.
    #     Must have `manage server` permissions.
    #     Bot must have `manage webhooks` permission.
    #     """
    #     if not channel.permissions_for(ctx.me).manage_webhooks:
    #         return await ctx.error(f"I need `manage_webhooks` permission in **{channel}**")

    #     record = await insert_or_update_config(ctx, EventType.poem, channel)
    #     if not record:
    #         await ctx.success(f"Autopoem enabled successfully!")
    #     else:
    #         await ctx.success(f"Autopeom record updated!")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autotoggle(self, ctx: Context, eventype: str = None):
        """
        Toggle ON/OFF any autoevent.
        """
        valids = (
            "automeme",
            "autofact",
            "autoquote",
            "autojoke",
            "autonsfw",
            "autoadvice",
            # "autopoem",
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
    @checks.is_premium_guild()
    @commands.has_permissions(manage_guild=True)
    async def autointerval(self, ctx: Context, eventype: str = None):
        """
        Change the interval of automatic commands.
        Must have `manage server` permissions and the server must be premium.
        """
        valids = (
            "automeme",
            "autofact",
            "autoquote",
            "autojoke",
            "autonsfw",
            "autoadvice",
            # "autopoem",
        )

        displayable_options = ",".join(map(lambda s: f"`{s}`", valids))

        if eventype is None:
            return await ctx.send(
                f"For what do you want to set interval?\nValid options are: {displayable_options}.\n\nExample: `{ctx.prefix}autointerval automeme`"
            )

        eventype = eventype.lower()

        if eventype not in valids:
            return await ctx.send(
                f"What you chose isn't a valid option mate!\nChoose from: {displayable_options}.\n\nExample: `{ctx.prefix}autointerval autonsfw`"
            )

        real = eventype[4:]
        check = await Autoevent.filter(guild_id=ctx.guild.id, type=EventType(real)).first()
        if not check:
            return await ctx.error(
                f"You haven't setup {eventype.lower()} yet.\n\nDo it like `{ctx.prefix}{eventype.lower()} #{ctx.channel.name}`"
            )

        await ctx.send(
            f"What do you want the interval between {eventype.title()} to be?\n\nExample: Enter `15m` for 15 minutes."
        )

        def check(msg: discord.Message):
            return ctx.author == msg.author and ctx.channel == msg.channel

        try:
            msg = await self.bot.wait_for("message", timeout=60, check=check)
            interval = simple_convert(msg.content)
        except asyncio.TimeoutError:
            return await ctx.error(f"Time's up! Be little fast")

        interval = round(interval / 60)
        await Autoevent.filter(guild_id=ctx.guild.id, type=EventType(real)).update(interval=interval)
        await ctx.success(f"Updated {eventype.title()} interval (`{interval} minutes`)")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def autoconfig(self, ctx: Context):
        """Get config for autocommands."""
        records = await Autoevent.filter(guild_id=ctx.guild.id)
        if not records:
            return await ctx.error(
                f"You don't have any autoevent setup.\n\nSetup autoevents: `{ctx.prefix}automeme #{ctx.channel.name}`"
            )

        text = "**`Toggle`  |  `Type`  |  `Channel`  |  `Interval`**\n\n"
        for idx, record in enumerate(records, start=1):
            emoji = emote.settings_yes if record.toggle else emote.settings_no
            text += f"`{idx:02d}` {emoji} **{record.type.value.title()}** {getattr(record.channel , 'mention', '`Channel Deleted!`')} `{record.interval} mins`\n"

        embed = self.bot.embed(ctx, description=text, title="Autoevents Config")
        await ctx.send(embed=embed)


def setup(bot) -> None:
    bot.add_cog(Fun(bot))
    bot.add_cog(Funevents(bot))
