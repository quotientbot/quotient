from PIL import Image
import io

import imagehash
import discord
import pytesseract
from constants import SSType

from models import SSVerify
from utils import to_async

from typing import NamedTuple, Tuple


async def get_image(attch: discord.Attachment):
    image = Image.open(io.BytesIO(await attch.read())).convert("L")

    cropped = []
    cropped.append(image)

    w, h = image.size

    if h >= 1550:
        cropped.append(image.crop((0, 0, w, 1550)))

    if h >= 800:
        cropped.append(image.crop((0, 0, w, 800)))

    return image, cropped


@to_async()
def get_image_string(img):
    width, height = img.size
    img = img.resize((width * 3, height * 3))

    config = "--oem 3 --psm 12"
    return pytesseract.image_to_string(img, lang="eng", config=config)


@to_async()
def get_image_hash(img):
    return imagehash.dhash(img)


def valid_attachments(message: discord.Message):
    return [_ for _ in message.attachments if _.content_type in ("image/png", "image/jpeg", "image/jpg")]


class VerifyResult(NamedTuple):
    reason: str
    verified: bool = False
    hash: str = None


async def verify_image(record: SSVerify, group: Tuple):

    img, cropped = group

    _hash = str(await get_image_hash(img))

    if _match := await record.find_hash(str(_hash)):
        return VerifyResult(f"Already posted by {getattr(_match.author,'mention','Unknown')}.")

    clean_text = ""

    for _ in cropped:
        clean_text += await get_image_string(img)

    _text = clean_text.lower().replace(" ", "")

    name = record.channel_name.lower().replace(" ", "")

    if record.ss_type == SSType.yt:

        if not any(_ in _text for _ in ("subscribe", "videos")):
            return VerifyResult("Not a valid youtube screenshot.")

        elif not name in _text:
            return VerifyResult(f"Screenshot must belong to [`{record.channel_name}`]({record.channel_link}) channel.")

        elif "SUBSCRIBE " in clean_text:
            return VerifyResult(f"You must subscribe [`{record.channel_name}`]({record.channel_link}) to get verified.")

    elif record.ss_type == SSType.insta:
        if not "followers" in _text:
            return VerifyResult("Not a valid instagram screenshot.")

        elif not name in _text:
            return VerifyResult(f"Screenshot must belong to [`{record.channel_name}`]({record.channel_link}) page.")

        elif "Follow " in clean_text:
            return VerifyResult("You must follow the page to get verified.")

    return VerifyResult("Verified Successfully!", True, _hash)
