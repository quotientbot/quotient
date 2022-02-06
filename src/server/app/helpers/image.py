from ._const import SS


import imagehash
import pytesseract

from utils.converters import to_async
from core import bot

import io

from PIL import Image


async def get_image(attch: SS) -> Image:
    async with bot.session.get(attch.url) as resp:
        if resp.status != 200:
            return None

        return Image.open(io.BytesIO(await resp.read()))


def slice_image(img, height: int = 400):
    _l = []
    imgwidth, imgheight = img.size
    for i in range(imgheight // height):
        for j in range(imgwidth // imgwidth):
            box = (j * imgwidth, i * height, (j + 1) * imgwidth, (i + 1) * height)
            _l.append(img.crop(box))

    return _l


@to_async()
def get_image_string(img):

    _img = img.convert("L")

    cropped = slice_image(_img)
    cropped.append(_img)

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
