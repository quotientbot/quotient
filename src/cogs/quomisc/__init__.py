from core import Cog, Quotient, Context
from discord.ext import commands
from utils import ColorConverter
from collections import Counter
from typing import Optional
from glob import glob
from .dev import *
import inspect
import os


class Quomisc(Cog, name="quomisc"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    async def source(self, ctx: Context, *, search: str = None):
        """Refer to the source code of the bot commands."""
        source_url = "https://github.com/quotientbot/Quotient-Bot"

        if search is None:
            return await ctx.send(source_url)

        command = ctx.bot.get_command(search)

        if not command:
            return await ctx.send("Couldn't find that command.")

        src = command.callback.__code__
        filename = src.co_filename
        lines, firstlineno = inspect.getsourcelines(src)

        location = os.path.relpath(filename).replace("\\", "/")

        final_url = f"<{source_url}/blob/main/src/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        await ctx.send(final_url)

    @commands.command(aliases=["cs"])
    async def codestats(self, ctx: Context):
        """See the code statictics of the bot."""
        ctr = Counter()

        for ctr["files"], f in enumerate(glob("./**/*.py", recursive=True)):
            with open(f, encoding="UTF-8") as fp:
                for ctr["lines"], line in enumerate(fp, ctr["lines"]):
                    line = line.lstrip()
                    ctr["imports"] += line.startswith("import") + line.startswith("from")
                    ctr["classes"] += line.startswith("class")
                    ctr["comments"] += "#" in line
                    ctr["functions"] += line.startswith("def")
                    ctr["coroutines"] += line.startswith("async def")
                    ctr["docstrings"] += line.startswith('"""') + line.startswith("'''")

        await ctx.send(
            embed=ctx.bot.embed(
                ctx,
                title="Code Stats",
                description="\n".join([f"**{k.capitalize()}:** {v}" for k, v in ctr.items()]),
            )
        )

    @commands.command()
    async def support(self, ctx):
        """
        Get the invite link of our support server.
        """
        await ctx.send(self.bot.config.SERVER)

    @commands.command()
    async def invite(self, ctx):
        """Invite ME : )"""
        embed = self.bot.embed(ctx)
        embed.description = f"[Click Here to Invite Me]({self.bot.config.BOT_INVITE})\n[Click Here to join Support Server]({self.bot.config.SERVER_LINK})"
        await ctx.send(embed=embed)

    # @commands.command()
    # async def prefix(self, ctx, *, new_prefix: Optional[str]):
    #     pass

    # @commands.command()
    # async def color(self, ctx, *, new_color: Optional[ColorConverter]):
    #     pass

    # @commands.command()
    # async def footer(self, ctx, *, new_footer: Optional[str]):
    #     pass


def setup(bot):
    bot.add_cog(Quomisc(bot))
    bot.add_cog(Dev(bot))
