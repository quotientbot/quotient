from PIL import Image
import io

import imagehash
import discord
import pytesseract
from constants import SSType

from models import SSVerify

from typing import NamedTuple


async def get_image(attch: discord.Attachment):
    return Image.open(io.BytesIO(await attch.read())).convert("L")


async def get_image_string(img):
    width, height = img.size
    img = img.resize((width * 2, height * 2))
    config = "--oem 3 --psm 11"
    return pytesseract.image_to_string(img, lang="eng", config=config)


async def get_image_hash(img):
    return imagehash.dhash(img)


def valid_attachments(message: discord.Message):
    return [_ for _ in message.attachments if _.content_type in ("image/png", "image/jpeg", "image/jpg")]


class VerifyResult(NamedTuple):
    reason: str
    verified: bool = False
    hash: str = None


async def verify_image(record: SSVerify, img: Image):
    _text = (await get_image_string(img)).lower().replace(" ", "")
    name = record.channel_name.lower().replace(" ", "")

    _hash = str(await get_image_hash(img))

    if _match := await record.find_hash(str(_hash)):
        return VerifyResult(f"Already posted by {getattr(_match.author,'mention','Unknown')}")

    if record.ss_type == SSType.yt:
        if not all(("subscribers" in _text, "videos" in _text)):
            return VerifyResult("Not a valid youtube screenshot.")

        elif not name in _text:
            return VerifyResult(f"Screenshot must belong to `{record.channel_name}` channel.")

        elif not "subscribed" in _text:
            return VerifyResult("You must subscribe to get verified.")

        return VerifyResult("Verified Successfully!", True, _hash)

    elif record.ss_type == SSType.insta:
        ...
