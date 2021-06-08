from prettytable import PrettyTable
from core import Cog, Quotient, Context
from discord.ext import commands
from time import perf_counter as pf
from utils import get_ipm


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
            channel = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, record["private_channel"])

            if channel != None and channel.permissions_for(channel.guild.me).send_messages:
                try:
                    await channel.send(message)
                    success += 1
                except:
                    failed += 1
                    continue

        end = pf()
        await ctx.send(f"Sent {success}: {failed} finished in {end - start:.3f}s.")

    @commands.command()
    async def cmds(self, ctx):
        query = "SELECT SUM(uses) FROM cmd_stats;"
        total_uses = await ctx.db.fetchval(query)

        records = await ctx.db.fetch(
            "SELECT cmd, SUM(uses) FROM cmd_stats GROUP BY cmd ORDER BY SUM (uses) DESC LIMIT 15 "
        )

        table = PrettyTable()
        table.field_names = ["Command", "Invoke Count"]
        for record in records:
            table.add_row([record["cmd"], record["sum"]])

        table = table.get_string()
        embed = self.bot.embed(ctx, title=f"Command Usage ({total_uses})")
        embed.description = f"```{table}```"

        cmds = sum(1 for i in self.bot.walk_commands())

        embed.set_footer(text="Total Commands: {}  | Invoke rate per minute: {}".format(cmds, round(get_ipm(ctx.bot), 2)))

        await ctx.send(embed=embed)
