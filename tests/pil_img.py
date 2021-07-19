from PIL import Image, ImageDraw, ImageFont

_dict = {
    "1": "Basanti",
    "2": "saways",
    "3": "Changed",
}


_list = []
image = Image.new("RGB", (105, 15), (255, 255, 255))

image.save("rect.png")