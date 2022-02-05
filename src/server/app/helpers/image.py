from ._const import SS
from PIL import Image

import imagehash
import pytesseract

from utils.converters import to_async
from core import bot

import io


async def get_image(attch: SS) -> Image:
    async with bot.session.get(attch.url) as resp:
        if resp.status != 200:
            return None

        return Image.open(io.BytesIO(await resp.read()))


@to_async()
def get_image_string(img):

    _img = img.convert("L")
    w, h = _img.size

    cropped = []
    cropped.append(_img)

    if h >= 1550:
        cropped.append(_img.crop((0, 0, w, 1550)))

    if h >= 800:
        cropped.append(_img.crop((0, 0, w, 800)))

    text = ""
    config = "--oem 3 --psm 12"

    for _ in cropped:
        width, height = _.size
        _ = _.resize((width * 3, height * 3))

        text += pytesseract.image_to_string(img, lang="eng", config=config)

    return text


@to_async()
def get_image_dhash(img, size=64):
    return imagehash.dhash(img, size)


@to_async()
def get_image_phash(img, size=64):
    return imagehash.phash(img, size)
