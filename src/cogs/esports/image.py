from models import PointsInfo, PointsTable
from ast import literal_eval
from PIL import Image, ImageFilter, ImageFont, ImageDraw
from pathlib import Path
from utils import split_list
import asyncio, io
import random
import discord


def add_watermark(image, footer):
    width, height = image.size
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(str(Path.cwd() / "src" / "data" / "font" / "Ubuntu-Regular.ttf"), 25)
    textwidth, textheight = draw.textsize(footer, font)

    margin = 20
    x = width - textwidth - margin
    y = height - textheight - margin

    draw.text((x, y), footer, font=font)


def add_title(image, title, second_title=None):

    font = ImageFont.truetype(str(Path.cwd() / "src" / "data" / "font" / "robo-bold.ttf"), 90)

    d1 = ImageDraw.Draw(image)

    w, h = d1.textsize(title.upper(), font)

    left = (image.width - w) / 2
    top = 50
    d1.text((left, top), title.upper(), font=font)

    if second_title:
        w, h = d1.textsize(second_title.upper(), font)
        left = (image.width - w) / 2
        d1.text((left, 150), second_title.upper(), font=font)


def title_rect():
    image = Image.open(str(Path.cwd() / "src" / "data" / "img" / "rectangle.png"))
    image = image.convert("RGBA")

    image = image.resize((round(image.size[0] / 2.8), round(image.size[1] / 2.8)))

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(Path.cwd() / "src" / "data" / "font" / "robo-italic.ttf"), 30)

    top = 8
    fill = (0, 0, 0)

    draw.text((18, top), "Rank", fill, font=font)
    draw.text((250, top), "Team Name", fill, font=font)
    draw.text((610, top), "Place Pt", fill, font=font)
    draw.text((770, top), "Kills Pt", fill, font=font)

    draw.text((905, top), "Total Pt", fill, font=font)

    draw.text((1046, top), "InGame", fill, font=font)
    return image


def rect_list(data):

    fill = (0, 0, 0)
    _list = []

    top = 10
    left = 35

    font = ImageFont.truetype(str(Path.cwd() / "src" / "data" / "font" / "robo-bold.ttf"), 30)

    for idx, item in enumerate(data.items(), start=1):

        image = Image.open(str(Path.cwd() / "src" / "data" / "img" / "rectangle.png"))
        image = image.convert("RGBA")

        image = image.resize((round(image.size[0] / 2.8), round(image.size[1] / 2.8)))

        draw = ImageDraw.Draw(image)

        team = item[0]
        win, place, kill, total = item[1]

        draw.text((left, top), f"#{idx:02}", fill, font=font)
        draw.text((left + 150, top), f"Team {team.title()}", fill, font=font)
        draw.text((left + 610, top), f"{place:02}", fill, font=font)
        draw.text((left + 760, top), f"{kill:02}", fill, font=font)
        draw.text((left + 897, top), f"{total:02}", fill, font=font)
        draw.text((left + 1025, top), f"{'Win' if win else 'Lost'}", fill, font=font)

        _list.append(image)

    return _list


async def ptable_files(points: PointsInfo, data: PointsTable):

    table = literal_eval(data.points_table)

    def wrapper():

        _list = rect_list(table)

        images = []

        number = random.choice(range(1, 15))
        for group in split_list(_list, 10):
            image = Image.open(str(Path.cwd() / "src" / "data" / "img" / f"ptable{number}.jpg"))
            # image = Image.open(str(Path.cwd() / "src" / "data" / "back" / f"9.jpg"))
            image = image.resize((1250, 938))
            image = image.filter(ImageFilter.GaussianBlur(4))
            top = 320

            title_rec = title_rect()
            image.paste(title_rec, (40, 260), title_rec)

            for rect in group:
                image.paste(rect, (40, top), rect)
                top += 50

            add_watermark(image, points.footer)
            add_title(image, points.title, points.secondary_title)

            img_bytes = io.BytesIO()
            image.save(img_bytes, "PNG")
            img_bytes.seek(0)
            images.append(discord.File(img_bytes, "points_table.png"))

        return images

    return await asyncio.get_event_loop().run_in_executor(None, wrapper)
