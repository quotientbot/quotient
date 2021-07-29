from PIL import Image, ImageDraw, ImageFont

_dict = {
    "1": "Basanti",
    "2": "saways",
    "3": "Changed",
}

image = Image.open("slot-rect.png")
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("robo-bold.ttf", 80)

draw.text((95, 55), "01", font=font)
draw.text((325, 55), "Team is something bro", (0, 0, 0), font=font)
image.show()


