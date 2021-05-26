from core import Cog, Quotient, Context
from discord.ext import commands
from models import Snipes
from models import Autorole, ArrayAppend, ArrayRemove, Tag
from utils import checks, human_timedelta
from typing import Optional
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

    # @commands.command()
    # @commands.bot_has_permissions(embed_links=True)
    # async def snipe(self, ctx, *, channel: Optional[discord.TextChannel]):
    #     """Snipe last deleted message of a channel."""

    #     channel = channel or ctx.channel

    #     snipe = await Snipes.filter(channel_id=channel.id).order_by("delete_time").first()
    #     if not snipe:
    #         return await ctx.send(f"There's nothing to snipe :c")

    #     elif snipe.nsfw and not channel.is_nsfw():
    #         return await ctx.send(f"The snipe is marked NSFW but the current channel isn't.")

    #     content = (
    #         snipe.content
    #         if len(snipe.content) < 128
    #         else f"[Click me to see]({str(await ctx.bot.binclient.post(snipe.content))})"
    #     )
    #     embed = self.bot.embed(ctx)
    #     embed.description = f"Message sent by **{snipe.author}** was deleted in {channel.mention}"
    #     embed.add_field(name="**__Message Content__**", value=content)
    #     embed.set_footer(text=f"Deleted {human_timedelta(snipe.delete_time)}")
    #     await ctx.send(embed=embed)

    ####################
    
    @commands.group(invoke_without_command=True)
    async def tag(self, ctx: Context, *, TagName = None):
        # TODO: Add support for attachments with text.
        # TODO: Make tag usages work actually, am lazy.
        
        if TagName is None:
            return await ctx.send_help(ctx.command)
        
        record = await Tag.get_or_none(guild_id=ctx.guild.id)
        
        if record is None:
            return await ctx.error(f"No tag **{TagName}** found.\nCreate one with the `{ctx.prefix}tag create` command.")
        
        nsfw = record["is_nsfw"]
        content = record["content"]
        embed = record["is_embed"]
        
        if not ctx.channel.is_nsfw() and nsfw is True:
            return await ctx.error("This tag can only be used in NSFW channels.", delete_after=5)
        
        if embed is True:
            embed_msg = discord.Embed(**content)
            return await ctx.send(embed = embed_msg, reference = ctx.replied_reference)
        
    @tag.command(name="make")
    async def make_tag(self, ctx):
        # Will get back to dis later in lyf.
        ...
        
    @tag.command(name="claim")
    async def claim_tag(self, ctx, *, tag = None):
        if tag is None:
            return await ctx.send_help(ctx.command)
        
    @tag.command(name="create")
    async def create_tag_command(self, ctx, *, args):
        
        args = args.partition(", ")
        tag_name = args[2].lower().strip()
        
        first_word, _, _ = tag_name.partition(' ')
        root = ctx.bot.get_command('tag')
        
        if first_word in root.all_commands:
            return await ctx.error("abey saale bot ko chutiya banyega?")
        
        await ctx.success(f"name = {args[0]} content = {args[2]}")
        
        
    

def setup(bot):
    bot.add_cog(Utility(bot))
