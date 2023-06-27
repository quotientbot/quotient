from PIL import Image, ImageDraw, ImageFont


def add_watermark(image):
    text = "Quotient • quotientbot.xyz"
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype("myfont.ttf", 25)
    textwidth, textheight = draw.textsize(text, font)

    margin = 20
    x = width - textwidth - margin
    y = height - textheight - margin

    draw.text((x, y), text, font=font)


def add_title(image):
    text = "Yo Bro ESPORTS"
    font = ImageFont.truetype("theboldfont.ttf", 90)

    d1 = ImageDraw.Draw(image)
    w, h = d1.textsize(text, font)

    left = (image.width - w) / 2
    top = 50

    d1.text((left, top), text, font=font)

    # second title
    w, h = d1.textsize("Overall Standings", font)
    left = (image.width - w) / 2
    d1.text((left, 150), "Overall Standings", font=font)


image = Image.open("rectangle.png")
image = image.convert("RGBA")

image = image.resize((round(image.size[0] / 2.8), round(image.size[1] / 2.8)))

draw = ImageDraw.Draw(image)
font = ImageFont.truetype("roboto/italic.ttf", 30)

top = 8
fill = (0, 0, 0)

draw.text((18, top), "Rank", fill, font=font)
draw.text((250, top), "Team Name", fill, font=font)
draw.text((610, top), "Place Pt", fill, font=font)
draw.text((770, top), "Kills Pt", fill, font=font)

draw.text((905, top), "Total Pt", fill, font=font)

draw.text((1060, top), "Win?", fill, font=font)

_list = []

_list.append(image)


_dict = {
    "quotient": [1, 20, 20, 40],
    "butterfly": [2, 14, 14, 28],
    "4pandas": [3, 10, 8, 18],
    "kite": [4, 10, 5, 15],
    "quotient2": [1, 20, 20, 40],
    "butterfly2": [2, 14, 14, 28],
    "4pandas2": [3, 10, 8, 18],
    "kite2": [4, 10, 5, 15],
    "quotient3": [1, 20, 20, 40],
    "butterfly3": [2, 14, 14, 28],
}

font = ImageFont.truetype("roboto/Roboto-Bold.ttf", 30)

top = 10
left = 35

for idx, item in enumerate(_dict.items(), start=1):
    image = Image.open("rectangle.png")
    image = image.convert("RGBA")

    image = image.resize((round(image.size[0] / 2.8), round(image.size[1] / 2.8)))

    draw = ImageDraw.Draw(image)

    team = item[0]
    win, place, kill, total = item[1]

    draw.text((left, top), f"#{idx:02}", fill, font=font)
    draw.text((left + 150, top), f"Team {team.title()}", fill, font=font)
    draw.text((left + 610, top), str(place), fill, font=font)
    draw.text((left + 760, top), str(kill), fill, font=font)
    draw.text((left + 897, top), str(total), fill, font=font)
    draw.text((left + 1025, top), f"{'Yes!' if win else 'No!'}", fill, font=font)

    _list.append(image)


image = Image.open("test.jpg")
image = image.resize((1250, 938))
width, height = image.size
top = 320

for i in _list:
    if _list.index(i) == 0:
        image.paste(i, (40, 260), i)
    else:
        image.paste(i, (40, top), i)
        top += 50

add_watermark(image)
add_title(image)


image.save("points.jpg")
# for image in _list:
#     image.show()


_list = [
    {"a": [1, 20, 20, 40], "b": [0, 14, 14, 28]},
    {"a": [2, 20, 20, 40], "b": [2, 14, 14, 28]},
    {"c": [1, 20, 20, 40], "d": [0, 14, 14, 28]},
]
