from discord import Webhook, AsyncWebhookAdapter
from datetime import datetime, timedelta
from core import Cog, Quotient
from models.models import Autoevent
import constants
import models, discord

from utils.time import strtime


class Votes(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.hook = Webhook.from_url(self.bot.config.PUBLIC_LOG, adapter=AsyncWebhookAdapter(self.bot.session))

    @property
    def reminders(self):
        return self.bot.get_cog("Reminders")

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """we grant users voter, premium role if they join later."""
        if not member.guild or not member.guild.id == self.bot.server.id:
            return

        votecheck = await models.Votes.get_or_none(user_id=member.id)
        if votecheck is not None and votecheck.is_voter:
            await member.add_roles(discord.Object(id=self.bot.config.VOTER_ROLE))

        premiumcheck = await models.User.get_or_none(user_id=member.id)
        if premiumcheck is not None and premiumcheck.is_premium:
            await member.add_roles(discord.Object(id=self.bot.config.PREMIUM_ROLE))

    @Cog.listener()
    async def on_vote(self, record: models.Votes):
        await models.Votes.filter(user_id=record.user_id).update(notified=True)
        await self.reminders.create_timer(record.expire_time, "vote", user_id=record.user_id)
        member = self.bot.server.get_member(record.user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config.VOTER_ROLE), reason="They voted for me.")

        member = member if member is not None else await self.bot.fetch_user(record.user_id)

        await self.hook.send(
            content=f"{str(member)} just voted!", username="vote-logs", avatar_url=self.bot.user.avatar_url
        )

    @Cog.listener()
    async def on_vote_timer_complete(self, timer: models.Timer):
        user_id = timer.kwargs["user_id"]
        vote = await models.Votes.filter(user_id=user_id).first()

        member = self.bot.server.get_member(user_id)
        if member is not None:
            await member.remove_roles(discord.Object(id=self.bot.config.VOTER_ROLE), reason="Their vote expired.")

        member = member if member is not None else await self.bot.fetch_user(user_id)
        if vote.reminder:

            embed = discord.Embed(
                color=self.bot.color,
                description=f"{constants.random_greeting()}, You asked me to remind you to vote.",
                title="Vote Expired!",
                url="https://quotientbot.xyz/vote",
            )
            try:
                await member.send(embed=embed)
            except:
                pass

        await models.Votes.filter(user_id=user_id).update(is_voter=False)

    @Cog.listener()
    async def on_premium_purchase(self, record: models.Premium):
        await models.Premium.filter(order_id=record.order_id).update(is_notified=True)
        member = self.bot.server.get_member(record.user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config.PREMIUM_ROLE), reason="They voted for me.")

        member = member if member is not None else await self.bot.fetch_user(record.user_id)

        await self.hook.send(
            content=f"{str(member)} just purchased Quotient Premium!",
            username="premium-logs",
            avatar_url=self.bot.config.PREMIUM_AVATAR,
        )

        embed = discord.Embed(
            color=self.bot.color,
            title="Premium Purchase Successful",
            description=f"{constants.random_greeting()} {member.mention},\nThanks for purchasing Quotient Premium.\nYou have now access to all Premium Perks and A special role in our server.",
        )
        if member not in self.bot.server.members:
            embed.description += f"\n\nI notice you are not in our support server. Join it by [clicking here]({self.bot.config.SERVER_LINK}) to get special role."

        embed.description += f"You can upgrade a server by using `qboost` command in that server or you can use `qhelp premium` command to get a list of commands related to Quotient Premium."

        try:
            await member.send(embed=embed)
        except:
            pass

        # we create a timer to remind the user that their premium is expiring soon and a timer of the actual expire_time
        await self.reminders.create_timer(
            datetime.now(tz=constants.IST) + timedelta(days=26), "user_premium_reminder", user_id=record.user_id
        )
        await self.reminders.create_timer(
            datetime.now(tz=constants.IST) + timedelta(days=30), "user_premium", user_id=record.user_id
        )

    @Cog.listener()
    async def on_user_premium_reminder_timer_complete(self, timer: models.Timer):
        user_id = timer.kwargs["user_id"]
        record = await models.User.get(user_id=user_id)
        if not record.premium_expire_time < datetime.now(tz=constants.IST) + timedelta(days=4):
            return  # this means they have already renewed

        user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
        if user is not None:
            em = discord.Embed(color=discord.Color.red(), title="Quotient Premium Ending Soon")
            em.description = f"{constants.random_greeting()},\nThis is to remind you that your quotient premium is going to end very soon. You can [click here]({self.bot.config.WEBSITE}/premium) to renew. \n\nPremium will expire on `{strtime(record.premium_expire_time)}`"

            try:
                await user.send(embed=em)
            except:
                pass

    @Cog.listener()
    async def on_server_premium_reminder_timer_complete(self, timer: models.Timer):
        guild_id = timer.kwargs["guild_id"]
        record = await models.Guild.get_or_none(guild_id=guild_id)
        if not record:
            return

        if not record.premium_end_time < datetime.now(tz=constants.IST) + timedelta(days=4):
            return

        guild = self.bot.get_guild(guild_id)
        if guild is not None:
            embed = discord.Embed(color=discord.Color.red(), title="Quotient Premium expiring soon!")
            embed.description = f"{constants.random_greeting()},\nThis is to remind you that your server ({guild.name})'s Quotient premium is endling soon. You can [click here]({self.bot.config.WEBSITE}/premium) to renew. \n\nPremium will expire on `{strtime(record.premium_end_time)}`"

            try:
                await guild.owner.send(embed=embed)
            except:
                pass

    @Cog.listener()
    async def on_server_premium_timer_complete(self, timer: models.Timer):
        guild_id = timer.kwargs["guild_id"]
        record = await models.Guild.get_or_none(guild_id)
        if not record:
            return

        if timer.expires != record.premium_end_time:
            return

        await models.Guild.filter(guild_id=guild_id).update(is_premium=False)
        guild = self.bot.get_guild(guild_id)
        if guild != None:
            embed = discord.Embed(color=discord.Color.red(), title="Server Premium Ended!")
            embed.description = f"This is to inform you that Quotient Premium subscription of your server has been ended.\nYou can purchase awesome Quotient-Premium again [here]({self.bot.config.WEBSITE}/premium)"
            try:
                await guild.owner.send(embed=embed)
            except:
                pass

        # we are gonna remove extra scrims , tourneys , color , etc
        scrims = (await models.Scrim.filter(guild_id=guild_id).all())[3:]
        tourneys = (await models.Tourney.filter(guild_id=guild_id).all())[2:]

        if len(scrims):
            await models.Scrim.filter(id__in=(scrim.id for scrim in scrims)).delete()

        if len(tourneys):
            await models.Tourney.filter(id__in=(tourney.id for tourney in tourneys)).delete()

        # TODO: remove this from cache too maybe
        await models.Guild.filter(guild_id=guild_id).update(
            embed_color=self.bot.color, embed_footer=self.bot.config.FOOTER
        )
        await Autoevent.filter(guild_id=guild_id).update(interval=30)

    @Cog.listener()
    async def on_user_premium_timer_complete(self, timer: models.Timer):
        user_id = timer.kwargs["user_id"]
        record = await models.User.get(user_id)
        if timer.expires != record.premium_expire_time:
            return

        await models.User.filter(user_id=user_id).update(is_premium=False, made_premium=[], premiums=0)
        user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
        if user is not None:
            embed = discord.Embed(color=discord.Color.red(), title="Quotient Premium Ended!")
            embed.description = f"This is to inform you that your subscription of Quotient Premium has been ended,\nYou can purchase awesome Quotient-Premium again [here]({self.bot.congig.WEBSITE}/premium)"
            try:
                await user.send(embed=embed)
            except:
                pass

        member = self.bot.server.get_member(user_id)
        if member != None:
            await member.remove_roles(discord.Object(id=self.bot.config.PREMIUM_ROLE))
