from models import PointsInfo, PointsTable
from ast import literal_eval
from collections import Counter
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


def add_first_lb_rect(image):
    rect = Image.open(str(Path.cwd() / "src" / "data" / "img" / f"rect2.png"))
    rect = rect.convert("RGBA")
    rect = rect.resize((round(rect.size[0] / 1.5), round(rect.size[1] / 1.4)))

    draw = ImageDraw.Draw(rect)
    font = ImageFont.truetype(str(Path.cwd() / "src" / "data" / "font" / "robo-italic.ttf"), 16)

    top = 71
    fill = (0, 0, 0)

    draw.text((16, top), "RANK", fill, font=font)
    draw.text((220, top), "TEAM NAME", fill, font=font)
    draw.text((492, top), "MATCHES", fill, font=font)
    draw.text((612, top), "PLACE POINTS", fill, font=font)
    draw.text((744, top), "KILL POINTS", fill, font=font)

    draw.text((870, top), "TOTAL POINTS", fill, font=font)

    draw.text((1024, top), "WINS", fill, font=font)

    image.paste(rect, (46, 220), rect)


def lb_rects(_dict, matches) -> list:

    font = ImageFont.truetype(str(Path.cwd() / "src" / "data" / "font" / "robo-bold.ttf"), 25)
    top, left = 68, 16

    _list = []
    for idx, team in enumerate(_dict.items(), start=1):
        image = Image.open(str(Path.cwd() / "src" / "data" / "img" / "rect3.png"))
        image = image.convert("RGBA")

        image = image.resize((round(image.size[0] / 1.5), round(image.size[1] / 1.4)))

        draw = ImageDraw.Draw(image)

        team_name = team[0]
        win, place, kill, total = team[1]

        draw.text((left, top), f"#{idx:02}", (255, 255, 255), font=font)
        draw.text((left + 125, top), f"Team {team_name.title()}", (0, 0, 0), font=font)
        draw.text((left + 503, top), f"{matches.get(team_name):02}", (0, 0, 0), font=font)
        draw.text((left + 624, top), f"{place:02}", (0, 0, 0), font=font)
        draw.text((left + 760, top), f"{kill:02}", (0, 0, 0), font=font)
        draw.text((left + 897, top), f"{total:02}", (0, 0, 0), font=font)
        draw.text((left + 1025, top), f"x {win}", (0, 0, 0), font=font)

        _list.append(image)

    return _list


async def lb_files(points: PointsInfo, records):
    d1 = literal_eval(records[0].points_table)

    ds = [literal_eval(record.points_table) for record in records]

    _dict = {}
    for dict_item in ds:
        for key, value in dict_item.items():
            if key in _dict:
                val = [a + b for a, b in zip(_dict[key], value)]
                _dict[key] = val
            else:
                _dict[key] = value
    _dict.update(dict(sorted(_dict.items(), reverse=True, key=lambda x: x[1][3])))

    matches = Counter([j for i in ds for j in i.keys()])

    def _wrapper():
        _list = lb_rects(_dict, matches)

        images = []
        number = random.choice(range(1, 21))
        for group in split_list(_list, 10):
            image = Image.open(str(Path.cwd() / "src" / "data" / "img" / f"ptable{number}.jpg"))
            image = image.resize((1250, 938))
            image = image.filter(ImageFilter.GaussianBlur(1))
            top = 300

            for rect in group:
                image.paste(rect, (46, top), rect)
                top += 50

            add_first_lb_rect(image)
            add_watermark(image, points.footer)
            add_title(image, points.title, points.secondary_title)
            img_bytes = io.BytesIO()
            image.save(img_bytes, "PNG")
            img_bytes.seek(0)
            images.append(discord.File(img_bytes, "leaderboard.png"))

        return images

    return await asyncio.get_event_loop().run_in_executor(None, _wrapper)
