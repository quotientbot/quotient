from PIL import ImageDraw, Image, ImageFont


_dict = {
    "quotient": (4, 80, 86, 166),
    "butterfly": (8, 134, 56, 112),
    "4pandas": (12, 40, 32, 72),
    "kite": (16, 40, 26, 66),
}


image = Image.open("background.jpg")
rect = Image.open("rectangle.png")
image = image.resize((1250, 938))

width, height = image.size

text = "FANATIC ESPORTS"
font = ImageFont.truetype("theboldfont.ttf", 90)

# adding title
d1 = ImageDraw.Draw(image)
w, h = d1.textsize(text, font)

left = (image.width - w) / 2
top = 50

d1.text((left, top), text, font=font)


# second title
w, h = d1.textsize("Overall Standings", font)
left = (image.width - w) / 2
d1.text((left, 150), "Overall Standings", font=font)

# adding rectangles
rect = rect.convert("RGBA")

top = 320
rect = rect.resize((round(rect.size[0] / 2.8), round(rect.size[1] / 2.8)))

for i in range(10):
    image.paste(rect, (40, top), rect)
    top += 50


image.paste(rect, (40, 260), rect)
d1 = ImageDraw.Draw(rect)
font = ImageFont.truetype("myfont.ttf", 500)
d1.text((45, 260), "Rank", (0, 0, 0), font=font)


# watermark
text = "Quotient • quotientbot.xyz"
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("myfont.ttf", 25)
textwidth, textheight = draw.textsize(text, font)

margin = 20
x = width - textwidth - margin
y = height - textheight - margin

draw.text((x, y), text, font=font)

image.save("final.jpg")

###########################################################
# centering the title

# text = "VIXON LODA"
# font = ImageFont.truetype("theboldfont.ttf", 90)

# d1 = ImageDraw.Draw(image)


# w, h = d1.textsize(text, font)

# left = (image.width - w) / 2
# top = 100

# d1.text((left, top), text, font=font)

# image.show()
# image.save("vixon.jpg")

################################################################
# watermark stuff

# width, height = img.size

# draw = ImageDraw.Draw(img)

# text = "Quotient • quotientbot.xyz"


# font = ImageFont.truetype("myfont.ttf", 25)
# textwidth, textheight = draw.textsize(text, font)

# margin = 20
# x = width - textwidth - margin
# y = height - textheight - margin

# draw.text((x, y), text, font=font)
# img.show()

# img.save("watermark.jpg")
################################################################
