from core import Cog, Quotient, Context
from discord.ext import commands
from models import Autorole, ArrayAppend, ArrayRemove
from utils import checks
import discord


class Utility(Cog, name="utility"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @checks.is_mod()
    async def autorole(self, ctx, off: str = None):
        """
        Manage Quotient's autoroles.
        """
        if not off or not off.lower() == "off":
            return await ctx.send_help(ctx.command)

        record = await Autorole.get_or_none(guild_id=ctx.guild.id)

        if not record:
            return await ctx.send(
                f"You have not set any autorole yet.\n\nDo it like: `{ctx.prefix}autorole humans @role`"
            )

        elif not any([len(record.humans), len(record.bots)]):
            return await ctx.error("Autoroles already OFF!")

        else:
            prompt = await ctx.prompt("Are you sure you want to turn off autorole?")
            if prompt:
                # await Autorole.filter(guild_id=ctx.guild.id).update(humans=list, bots=list)
                await ctx.db.execute("UPDATE autoroles SET humans = '{}' , bots = '{}' WHERE guild_id = $1", ctx.guild.id)
                await ctx.success("Autoroles turned OFF!")
            else:
                await ctx.success("OK!")

    @autorole.command(name="humans")
    @checks.is_mod()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def autorole_humans(self, ctx: Context, *, role: discord.Role):
        """
        Add/ Remove a role to human autoroles.
        """
        record = await Autorole.get_or_none(pk=ctx.guild.id)
        if record is None:
            await Autorole.create(guild_id=ctx.guild.id, humans=[role.id])
            text = f"Added {role.mention} to human autoroles."

        else:
            func = (ArrayAppend, ArrayRemove)[role.id in record.humans]
            await Autorole.filter(guild_id=ctx.guild.id).update(humans=func("humans", role.id))
            text = (
                f"Added {role.mention} to human autoroles."
                if func == ArrayAppend
                else f"Removed {role.mention} from human autoroles."
            )

        await ctx.success(text)

    @autorole.command(name="bots")
    @checks.is_mod()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def autorole_bots(self, ctx: Context, *, role: discord.Role):
        """
        Add/ Remove a role to bot autoroles.
        """
        record = await Autorole.get_or_none(pk=ctx.guild.id)
        if record is None:
            await Autorole.create(guild_id=ctx.guild.id, bots=[role.id])
            text = f"Added {role.mention} to bot autoroles."

        else:
            func = (ArrayAppend, ArrayRemove)[role.id in record.bots]
            await Autorole.filter(guild_id=ctx.guild.id).update(bots=func("bots", role.id))
            text = (
                f"Added {role.mention} to bot autoroles."
                if func == ArrayAppend
                else f"Removed {role.mention} from bot autoroles."
            )

        await ctx.success(text)

    @autorole.command(name="config")
    @checks.is_mod()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def autorole_config(self, ctx: Context):
        """
        Get autorole config
        """
        record = await Autorole.get_or_none(pk=ctx.guild.id)
        if not record:
            return await ctx.send(
                f"You have not set any autorole yet.\n\nDo it like: `{ctx.prefix}autorole humans @role`"
            )

        humans = ", ".join(record.human_roles) if len(list(record.human_roles)) else "Not Set!"
        bots = ", ".join(record.bot_roles) if len(list(record.bot_roles)) else "Not Set!"

        embed = self.bot.embed(ctx, title="Autorole Config")
        embed.add_field(name="Humans", value=humans, inline=False)
        embed.add_field(name="Bots", value=bots, inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
