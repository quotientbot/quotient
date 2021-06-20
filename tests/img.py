from PIL import ImageDraw, Image, ImageFont

image = Image.open("background.jpg")
rect = Image.open("rectangle.png")

width, height = image.size

text = "FANATIC ESPORTS"
font = ImageFont.truetype("theboldfont.ttf", 90)

d1 = ImageDraw.Draw(image)
w, h = d1.textsize(text, font)

left = (image.width - w) / 2
top = 100

d1.text((left, top), text, font=font)

rect = rect.convert("RGBA")

top = 212
rect = rect.resize((round(rect.size[0] / 2.8), round(rect.size[1] / 2.8)))

for i in range(10):
    image.paste(rect, (40, top), rect)
    top += 58


# watermark
text = "Quotient • quotientbot.xyz"
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("myfont.ttf", 25)
textwidth, textheight = draw.textsize(text, font)

margin = 20
x = width - textwidth - margin
y = height - textheight - margin

draw.text((x, y), text, font=font)

image.save("psycho.jpg")

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
