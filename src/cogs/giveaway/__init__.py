from utils.time import FutureTime
from .functions import cancel_giveaway, gembed, create_giveaway, GiveawayConverter, GiveawayError, end_giveaway
from datetime import datetime, timedelta
from core import Cog, Context, Quotient
from discord.ext import commands
from .gevents import Gevents
from models import Giveaway
from constants import IST
import utils, discord
from time import time
import random


class Giveaways(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot


    def can_use_giveaways():
        async def predicate(ctx:Context):
            if ctx.author.guild_permissions.manage_guild or "giveaways" in (role.name.lower() for role in ctx.author.roles):
                return True
            
            else:
                return await ctx.error("You either need `giveaways` role or `manage server` permissions to use this command.")

        return commands.check(predicate)

        
    async def cog_command_error(self, ctx, error):
        if isinstance(error, GiveawayError):
            embed = discord.Embed(color=discord.Color.red(), title="Whoopsi-Doopsi", description=error)
            return await ctx.send(embed=embed)

    @commands.command(aliases=("start",))
    @can_use_giveaways()
    async def gcreate(self, ctx: Context):
        """
        Create a giveaway interactively.
        """

        def check(message: discord.Message):
            if message.content.strip().lower() == "cancel":
                raise GiveawayError("Alright, reverting all process.")

            return message.author == ctx.author and ctx.channel == message.channel

        count = await Giveaway.filter(guild_id=ctx.guild.id, ended_at__not_isnull=True).count()
        if count >= 5 and not await ctx.is_premium_guild():
            return await ctx.error(
                "You cannot host more than 5 giveaways concurrently on free tier.\n"
                "However, Quotient Premium allows you to host unlimited giveaways.\n\n"
                f"Checkout awesome Quotient Premium [here]({ctx.config.WEBSITE}/premium)"
            )

        giveaway = Giveaway(guild_id=ctx.guild.id, host_id=ctx.author.id)

        await gembed(
            ctx,
            1,
            "How long do you want the giveaway to last?\n\n`Please enter the duration of the giveaway under this message.`\n\nYou can use `m` for minutes, `h` for hours, `d` for days.",
        )

        giveaway.end_at = utils.FutureTime(await utils.string_input(ctx, check)).dt
        t1 = time()
        if giveaway.end_at < (datetime.now(tz=IST) + timedelta(seconds=55)):
            raise GiveawayError("You cannot host a giveaway of less than 1 minute.")

        elif giveaway.end_at > (datetime.now(tz=IST) + timedelta(days=90)):
            raise GiveawayError("You cannot keep the duration longer than 3 months.")

        await gembed(
            ctx, 2, "What is the prize for this giveaway?\n\n`Please enter the giveaway prize under this message.`"
        )
        prize = await utils.string_input(ctx, check)
        if len(prize) > 50:
            raise GiveawayError("Character length of prize cannot exceed 50 characters.")

        giveaway.prize = prize

        await gembed(ctx, 3, "How many winners do you want me to pick?\n\n`Please enter a number between 1 and 15.`")
        giveaway.winners = await utils.integer_input(ctx, check, limits=(1, 15))

        await gembed(
            ctx,
            4,
            "In which channel do you want to host this giveaway?\n\n`Please mention or type the name of the channel you want to host the giveaway in.`",
        )
        channel = await utils.channel_input(ctx, check)

        perms = channel.permissions_for(ctx.me)

        if not all((perms.add_reactions, perms.manage_messages, perms.send_messages, perms.embed_links)):
            raise GiveawayError(
                f"Kindly Make sure I have all of these permissions in {channel.mention}:\n\n"
                "- send messages\n"
                "- embed links\n"
                "- add reactions\n"
                "- manage messages\n"
            )

        giveaway.channel_id = channel.id

        await gembed(
            ctx,
            5,
            "How many messages do users need to join the giveaway?\n\n`Reply with 'None' if you do not want this to be a requirement.`",
        )
        msg_req = await utils.string_input(ctx, check)
        if msg_req.lower() == "none":
            giveaway.required_msg = 0

        else:
            try:
                giveaway.required_msg = int(msg_req)
                if giveaway.required_msg > 5000:
                    raise GiveawayError(f"`5000` is the max value you can pick.")

            except ValueError:
                raise GiveawayError("You didn't answer it right.\n\nEither send no. of required messages or none")

        await gembed(
            ctx,
            6,
            "Which role is required to participate in the giveaway?\n\n`Reply with 'None' if you do not want this to be a requirement`",
        )
        role = await utils.string_input(ctx, check)
        if role.lower() == "none":
            giveaway.required_role_id = None

        else:
            try:
                role = await commands.RoleConverter().convert(ctx, role)
                if role.managed:
                    raise GiveawayError(f"{role.mention} is a managed role, you cannot choose this.")
                giveaway.required_role_id = role.id
            except:
                raise commands.RoleNotFound(role)

        giveaway.end_at = giveaway.end_at + (timedelta(seconds=time() - t1))
        msg = await create_giveaway(giveaway)

        giveaway.started_at, giveaway.message_id, giveaway.jump_url = datetime.now(tz=IST), msg.id, msg.jump_url
        await giveaway.save()

        await self.bot.reminders.create_timer(giveaway.end_at, "giveaway", message_id=msg.id)

        end_at = utils.human_timedelta(giveaway.end_at, suffix=False, brief=False, accuracy=2)
        embed = discord.Embed(title="Giveaway Started!", color=self.bot.color)
        embed.description = (
            f"The giveaway for {giveaway.prize} has been created in {msg.channel.mention} and will last for {end_at}."
            f"\n[Click me to Jump there!]({msg.jump_url})"
        )
        await ctx.send(embed=embed)

    @commands.command()
    @can_use_giveaways()
    @commands.bot_has_permissions(manage_messages=True, add_reactions=True, embed_links=True)
    async def gquick(self, ctx: Context, duration: FutureTime, winners: int, *, prize: str):
        """Quickly create a giveaway in current channel."""
        count = await Giveaway.filter(guild_id=ctx.guild.id, ended_at__not_isnull=True).count()
        if count >= 5 and not await ctx.is_premium_guild():
            return await ctx.error(
                "You cannot host more than 5 giveaways concurrently on free tier.\n"
                "However, Quotient Premium allows you to host unlimited giveaways.\n\n"
                f"Checkout awesome Quotient Premium [here]({ctx.config.WEBSITE}/premium)"
            )

        if winners > 15:
            raise GiveawayError("Giveaway winner count must not exceed 15.")

        if len(prize) > 50:
            raise GiveawayError("Character length of prize cannot exceed 50 characters.")

        if duration.dt < (datetime.now(tz=IST) + timedelta(seconds=55)):
            raise GiveawayError("You cannot host a giveaway of less than 1 minute.")

        elif duration.dt > (datetime.now(tz=IST) + timedelta(days=90)):
            raise GiveawayError("You cannot keep the duration longer than 3 months.")

        giveaway = Giveaway(
            guild_id=ctx.guild.id,
            host_id=ctx.author.id,
            channel_id=ctx.channel.id,
            prize=prize,
            winners=winners,
            end_at=duration.dt,
        )
        await ctx.message.delete()
        msg = await create_giveaway(giveaway)
        giveaway.message_id, giveaway.jump_url, giveaway.started_at = msg.id, msg.jump_url, datetime.now(tz=IST)
        await giveaway.save()
        await self.bot.reminders.create_timer(giveaway.end_at, "giveaway", message_id=msg.id)

    @commands.command()
    @can_use_giveaways()
    @commands.bot_has_permissions(embed_links=True)
    async def greroll(self, ctx: Context, msg_id: GiveawayConverter):
        """Reroll a giveaway."""
        g = msg_id
        if not g.ended_at:
            raise GiveawayError(
                f"The giveaway hasn't yet. Either wait for it to end or use `{ctx.prefix}gend {g.message_id}`"
            )

        if not g.participants:
            raise GiveawayError(f"The giveaway has no valid participant.")

        def check(msg: discord.Message):
            return msg.author == ctx.author and ctx.channel == msg.channel

        await ctx.simple(
            "How Many winners do you want for the giveaway?\n\n**Note:** You must choose a number between 1 and 15."
        )
        number = await utils.integer_input(ctx, check, limits=(1, 15))

        participants = [participant for participant in g.real_participants if participant is not None]
        if number >= len(participants):
            winners = participants

        else:
            winners = random.sample(participants, g.winners)

        winners = ", ".join((win.mention for win in winners))
        await g.message.reply(
            content=f"**CONGRATULATIONS** {winners}",
            embed=discord.Embed(color=self.bot.color, description=f"You have won **{g.prize}**!"),
        )

    @commands.command()
    @can_use_giveaways()
    @commands.bot_has_permissions(manage_messages=True, embed_links=True, add_reactions=True)
    async def gend(self, ctx: Context, msg_id: GiveawayConverter):
        """End a giveaway early"""
        g = msg_id
        if g.ended_at:
            raise GiveawayError(
                f"This giveaway has already ended. \nYou you wish to pick new winners, use: `{ctx.prefix}greroll {g.message_id}`"
            )

        if not g.channel:
            raise GiveawayError("I couldn't find the giveaway channel, Maybe it is hidden from me.")

        await end_giveaway(g)
        await ctx.success(f"Success")

    @commands.command()
    @can_use_giveaways()
    async def glist(self, ctx: Context):
        """Get a list of all running giveaways."""
        records = await Giveaway.filter(guild_id=ctx.guild.id)
        if not records:
            raise GiveawayError(
                f"There isn't any running giveaway on this server.\n\nUse `{ctx.prefix}gcreate` to create one."
            )

        text = ""
        for idx, record in enumerate(records, start=1):
            end_at = utils.human_timedelta(record.end_at, suffix=False, brief=True, accuracy=2)

            text += f"`{idx:02}.` | {record.prize} | [{record.message_id}]({record.jump_url}) | **{end_at}**\n"

        embed = self.bot.embed(ctx, title=f"Total Giveaways: ({len(records)})")
        embed.description = text
        await ctx.send(embed=embed, embed_perms=True)

    @commands.command(aliases=("gdelete",))
    @can_use_giveaways()
    @commands.bot_has_guild_permissions(manage_messages=True)
    async def gcancel(self, ctx: Context, msg_id: GiveawayConverter):
        """Commit a crime."""
        prompt = await ctx.prompt(f"Are you sure you want to cancel [this giveaway]({msg_id.jump_url})?")
        if prompt:
            await Giveaway.filter(message_id=msg_id.message_id).delete()
            await cancel_giveaway(msg_id, ctx.author)
            await ctx.success(f"Successfully cancelled.")
        else:
            await ctx.success(f"ok Aborting")


def setup(bot):
    bot.add_cog(Giveaways(bot))
    bot.add_cog(Gevents(bot))
