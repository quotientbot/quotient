from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Cog
from ..schemas import SockResponse

from models import Votes
import discord
from contextlib import suppress
import constants


class SockSettings(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.hook = discord.Webhook.from_url(self.bot.config.PUBLIC_LOG, session=self.bot.session)

    @Cog.listener()
    async def on_request__prefix_change(self, u, data: dict):
        guild_id = data.get("guild_id")
        await self.bot.cache.update_guild_cache(int(guild_id))
        await self.bot.sio.emit("prefix_change__{0}".format(u), SockResponse().dict())

    @Cog.listener()
    async def on_request__new_vote(self, u, data: dict):
        print(data)
        user_id = int(data.get("user_id"))
        record = await Votes.get(pk=user_id)

        await self.bot.reminders.create_timer(record.expire_time, "vote", user_id=record.user_id)

        member = self.bot.server.get_member(record.user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config.VOTER_ROLE), reason="They voted for me.")

        else:
            member = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, record.pk)

        with suppress(discord.HTTPException, AttributeError):

            embed = discord.Embed(color=discord.Color.green(), description=f"Thanks **{member}** for voting.")
            embed.set_image(url=constants.random_thanks())
            embed.set_footer(text=f"Your total votes: {record.total_votes + 1}")
            await self.hook.send(embed=embed, username="vote-logs", avatar_url=self.bot.user.display_avatar.url)

    @Cog.listener()
    async def on_request__get_usernames(self, u, data: dict):
        _dict = {}
        for _ in data.get("users"):
            _dict[str(_)] = str(await self.bot.getch(self.bot.get_user, self.bot.fetch_user, int(_)))

        await self.bot.sio.emit("get_usernames__{0}".format(u), SockResponse(data=_dict).dict())
