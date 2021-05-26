from core import Cog, Quotient, Context
from discord.ext import commands
from time import perf_counter as pf

__all__ = ("Dev",)


class Dev(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    def cog_check(self, ctx: Context):
        return ctx.author.id in ctx.config.DEVS

    # TODO: add flags for webhooks and embeds

    @commands.command()
    async def broadcast(self, ctx: Context, *, msg):
        message = f"{msg}\n\n- {str(ctx.author)}, Team Quotient"
        records = await ctx.db.fetch("SELECT private_channel FROM guild_data WHERE private_channel IS NOT NULL")
        success, failed = 0, 0
        start = pf()
        for record in records:
            channel = ctx.bot.get_channel(record["private_channel"])
            if channel != None and channel.permissions_for(channel.guild.me).send_messages:
                try:
                    await channel.send(message)
                    success += 1
                except:
                    failed += 1

        end = pf()
        await ctx.send(f"Sent {success}: {failed} finished in {end - start:.3f}s.")
