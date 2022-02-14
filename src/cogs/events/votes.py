from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from discord import Webhook
from core import Cog

from models import Votes, User, Timer

import constants
import discord


class VotesCog(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.hook = Webhook.from_url(self.bot.config.PUBLIC_LOG, session=self.bot.session)

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """we grant users voter, premium role if they join later."""
        if not member.guild or not member.guild.id == self.bot.server.id:
            return

        if await Votes.get(user_id=member.id, is_voter=True).exists():
            await member.add_roles(discord.Object(id=self.bot.config.VOTER_ROLE))

        if await User.get(pk=member.id, is_premium=True).exists():
            await member.add_roles(discord.Object(id=self.bot.config.PREMIUM_ROLE))

    @Cog.listener()
    async def on_vote_timer_complete(self, timer: Timer):
        user_id = timer.kwargs["user_id"]
        vote = await Votes.get(user_id=user_id)

        await Votes.get(pk=user_id).update(is_voter=False, notified=False)

        member = self.bot.server.get_member(user_id)
        if member is not None:
            await member.remove_roles(discord.Object(id=self.bot.config.VOTER_ROLE), reason="Their vote expired.")

        else:
            member = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)

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
