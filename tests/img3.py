from PIL import Image, ImageDraw, ImageFont

image = Image.open("ptable1.jpg")
image = image.resize((1250, 938))
width, height = image.size


rect = Image.open("rect2.png")
rect = rect.convert("RGBA")
rect = rect.resize((round(rect.size[0] / 1.5), round(rect.size[1] / 1.4)))

draw = ImageDraw.Draw(rect)
font = ImageFont.truetype("robo-italic.ttf", 16)

top = 71
fill = (0, 0, 0)

draw.text((16, top), "RANK", fill, font=font)
draw.text((220, top), "TEAM NAME", fill, font=font)
draw.text((485, top), "MATCHES", fill, font=font)
draw.text((616, top), "KILL POINTS", fill, font=font)
draw.text((740, top), "PLACE POINTS", fill, font=font)

draw.text((870, top), "TOTAL POINTS", fill, font=font)

draw.text((1021, top), "WINS", fill, font=font)

image.paste(rect, (40, 220), rect)

top = 280
for i in range(11):
    image.paste(rect, (40, top), rect)
    top += 50

image.show()
