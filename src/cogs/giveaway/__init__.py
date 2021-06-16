from .functions import gembed, create_giveaway
from datetime import datetime, timedelta
from core import Cog, Context, Quotient
from discord.ext import commands
from .gevents import Gevents
from models import Giveaway
from constants import IST
import utils, discord


class GiveawayError(commands.CommandError):
    pass


class Giveaways(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    async def gcreate(self, ctx: Context):
        def check(message: discord.Message):
            if message.content.strip().lower() == "cancel":
                raise GiveawayError("Alright, reverting all process.")

            return message.author == ctx.author and ctx.channel == message.channel

        count = await Giveaway.filter(guild_id=ctx.guild.id, ended_at__not_isnull=True).count()
        if count >= 5 and not await ctx.is_premium():
            return await ctx.error(
                "You cannot host more than 5 giveaways concurrently on free tier.\n"
                "However, Quotient Premium allows you to host unlimited giveaways.\n\n"
                f"Checkout awesome Quotient Premium [here]({ctx.config.WEBSITE}/premium)"
            )

        giveaway = Giveaway(guild_id=ctx.guild.id, host_id=ctx.author.id)

        await gembed(ctx, 1, "How long do you want the giveaway to last?")
        giveaway.end_at = utils.FutureTime(await utils.string_input(ctx, check))

        if giveaway.end_at < (datetime.now(tz=IST) + timedelta(seconds=60)):
            raise GiveawayError("You cannot host a giveaway of less than 1 minute.")

        elif giveaway.end_at > (datetime.now(tz=IST) + timedelta(days=90)):
            raise GiveawayError("You cannot keep the duration longer than 3 months.")

        await gembed(ctx, 2, "What is the prize for this giveaway?")
        prize = await utils.string_input(ctx, check)
        if len(prize) > 50:
            raise GiveawayError("Character length of prize cannot exceed 50 characters.")

        giveaway.prize = prize

        await gembed(ctx, 3, "How many winners do you want me to pick?\n> 15 is the max value you can choose.")
        giveaway.winners = await utils.integer_input(ctx, check, limits=(1, 15))

        await gembed(ctx, 4, "In which channel do you want to host this giveaway?")
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

        giveaway.channel_id(channel.id)

        await gembed(
            ctx,
            4,
            "How many messages do users need to join the giveaway?\n> Reply with 'None' if you do not want this to be a requirement.",
        )
        msg_req = await utils.string_input(ctx, check)
        if msg_req.lower() == "none":
            giveaway.required_msg = 0

        else:
            try:
                giveaway.required_msg = int(msg_req)
            except ValueError:
                raise GiveawayError("You didn't answer it right.\n\nEither send no. of required messages or none")

        await gembed(
            ctx,
            5,
            "Which role is required to participate in the giveaway?\n> Reply with 'None' if you do not want this to be a requirement.",
        )
        role = await utils.string_input(ctx, check)
        if role.lower() == "none":
            giveaway.required_role_id = None

        else:
            try:
                role = await commands.RoleConverter().convert(ctx, role)
                giveaway.required_role_id = role.id
            except:
                raise commands.RoleNotFound(role)

        await create_giveaway()

    @commands.command()
    async def gstart(self, ctx: Context):
        pass

    @commands.command()
    async def greroll(self, ctx: Context):
        pass

    @commands.command()
    async def gend(self, ctx: Context):
        pass

    @commands.command()
    async def glist(self, ctx: Context):
        pass

    @commands.command()
    async def gcancel(self, ctx: Context):
        pass

    @commands.command()
    async def gschedule(self, ctx: Context):
        pass


def setup(bot):
    bot.add_cog(Giveaways(bot))
    bot.add_cog(Gevents(bot))
