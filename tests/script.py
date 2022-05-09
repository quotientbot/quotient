import PIL.Image

# ASCII_CHARS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
ASCII_CHARS = [" ", "#", "%", "?", "*", "+", ":", ","]


def resize_image(image, new_width=50):
    width, height = image.size
    ratio = height / width
    new_height = int(new_width * ratio - 10)
    return image.resize((new_width, new_height))


def greyify(image):
    return image.convert("L")


def pixels_to_ascii(image):
    pixels = image.getdata()
    return "".join([ASCII_CHARS[pixel // 25] for pixel in pixels])


def main(new_width=50):
    path = input("enter image path bruh: ")
    try:
        image = PIL.Image.open(path)
        image = image.convert("RGBA")
    except:
        print(path, " is not a valid path")

    new_image_data = pixels_to_ascii(greyify(resize_image(image)))

    count = len(new_image_data)
    ascii_image = "\n".join(new_image_data[i : (i + new_width)] for i in range(0, count, new_width))

    print(ascii_image)


main()
