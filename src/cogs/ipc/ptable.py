from __future__ import annotations

import typing, base64, io

if typing.TYPE_CHECKING:
    from core import Quotient


from .base import IpcCog
from discord.ext import ipc

from PIL import Image
import discord


class PtableIpc(IpcCog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @ipc.server.route()
    async def send_ptable(self, payload):
        data = payload.data

        _bytes = base64.b64decode(data.get("image"))
        channel_id = int(data.get("channel_id"))
        size = data.get("size")

        channel = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, channel_id)
        if not channel:
            return self.deny_request("Quotient couldn't find the points table channel.")
        
        if not channel.permissions_for(channel.guild.me).embed_links:
            return self.deny_request(f"Quotient needs embed_links permission in {str(channel)} to send points table.")

        image = Image.frombytes("RGBA", size, _bytes, "raw")
        img_bytes = io.BytesIO()
        image.save(img_bytes, "PNG")
        img_bytes.seek(0)

        msg = await channel.send(file=discord.File(img_bytes, "ptable.png"))

        return {"ok": True, "image": msg.attachments[0].proxy_url}
