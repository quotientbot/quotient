from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from utils import to_async
import requests
import io

from .utils import deny_request, positive

from PIL import Image
import discord


@to_async(executor=None)
def get_image(url):
    try:
        resp = requests.get(url)
    except:
        return False

    else:
        img_bytes = io.BytesIO(resp.content)
        try:
            return Image.open(img_bytes)
        except:
            return False


async def send_ptable(bot: Quotient, payload: dict) -> dict:

    background = payload.get("background")
    if background:
        background = await get_image(payload.get("background"))
        if not background:
            return deny_request("Provided URL wasn't a valid image.")

        background = background.convert("RGBA")

    foreground = await get_image(payload.get("foreground"))
    foreground = foreground.convert("RGBA")

    channel_id = int(payload.get("channel_id"))

    if background:
        background = background.resize(foreground.size, Image.ANTIALIAS)
        background.paste(foreground, (0, 0), foreground)
        ptable = background

    else:
        ptable = foreground

    channel = await bot.getch(bot.get_channel, bot.fetch_channel, channel_id)
    if not channel:
        return deny_request("Quotient couldn't find the points table channel.")

    if not channel.permissions_for(channel.guild.me).embed_links:
        return deny_request(f"Quotient needs embed_links permission in {str(channel)} to send points table.")

    img_bytes = io.BytesIO()
    ptable.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    bot.loop.create_task(channel.send(file=discord.File(img_bytes, "ptable.png")))

    return positive
