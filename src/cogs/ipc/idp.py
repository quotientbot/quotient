from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from .base import IpcCog
from discord.ext import ipc

from models import Scrim
import discord, asyncio
from contextlib import suppress


class IdpIpc(IpcCog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def delete_idp_message(self, message: discord.Message, seconds):
        with suppress(AttributeError, discord.HTTPException, discord.NotFound, discord.Forbidden):
            await asyncio.sleep(seconds)
            await message.delete()

    @ipc.server.route()
    async def send_idp(self, payload):
        data = payload.data

        guild = self.bot.get_guild(int(data.get("guild_id")))
        if not guild:
            return self.deny_request("Quotient was removed from your server.")

        channel = guild.get_channel(int(data.get("channel_id")))
        if not channel:
            return self.deny_request(
                "Quotient cannot see send `Id/pass channel`, kindly make sure it has appropriate permissions."
            )

        perms = channel.permissions_for(guild.me)
        if not all((perms.send_messages, perms.embed_links)):
            return self.deny_request(
                f"Kindly make sure Quotient has `send_messages` and `embed_links` permission in {str(channel)}"
            )

        embed = discord.Embed.from_dict(data.get("embed"))

        ping_role_id = data.get("ping_role_id")

        role = None
        if ping_role_id:
            role = getattr(guild.get_role(int(ping_role_id)), "mention", "")

        msg = await channel.send(
            content=role if role else "",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        delete_in = data.get("delete_in")
        if delete_in:
            self.bot.loop.create_task(self.delete_idp_message(msg, int(delete_in) * 30))

        if data.get("slotlist"):
            scrim_id = int(data.get("scrim_id"))
            if scrim_id:
                scrim = await Scrim.get_or_none(id=scrim_id, guild_id=guild.id)
                if scrim and await scrim.teams_registered.count():
                    embed, schannel = await scrim.create_slotlist()
                    smsg = await channel.send(embed=embed)
                    if delete_in:
                        self.bot.loop.create_task(self.delete_idp_message(smsg, int(delete_in) * 30))

        return self.positive
