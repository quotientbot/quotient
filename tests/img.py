from PIL import ImageDraw, Image, ImageFont


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
    text = "Bahot-Hard ESPORTS"
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


def add_rectangles(image, rect):
    top = 320
    rect = rect.resize((round(rect.size[0] / 2.8), round(rect.size[1] / 2.8)))

    image.paste(rect, (40, 260), rect)
    for i in range(10):
        image.paste(rect, (40, top), rect)
        top += 50

    top = 273
    d1 = ImageDraw.Draw(image)
    font = ImageFont.truetype("theboldfont.ttf", 30)
    d1.text((55, top), "Rank", (0, 0, 0), font=font)
    d1.text((300, top), "Team Name", (0, 0, 0), font=font)
    d1.text((652, top), "Posi Pt.", (0, 0, 0), font=font)
    d1.text((800, top), "Kill Pt.", (0, 0, 0), font=font)
    d1.text((950, top), "Total", (0, 0, 0), font=font)
    d1.text((1100, top), "Win", (0, 0, 0), font=font)


image = Image.open("test.jpg")
rect = Image.open("rectangle.png")


rect = rect.convert("RGBA")
image = image.resize((1250, 938))

width, height = image.size


add_title(image)
add_watermark(image)
add_rectangles(image, rect)


image.show()
