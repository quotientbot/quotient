# from PIL import Image


# def slice_image(filename, N):

#     i = Image.open(filename)


#     width = i.width
#     height = i.height

#     global _l
#     _l = []

#     for x in range(N):

#         for y in range(N):
#             img = i.crop((x * width / N, y * height / N, x * width / N + width / N, y * height / N + height / N))

#             _l.append(img)


# slice_image("ss3.jpg", 2)

# for i in _l:
#     i.show()
# def crop(infile, height, width):

#     global _l
#     _l = []
#     im = Image.open(infile)
#     imgwidth, imgheight = im.size
#     for i in range(imgheight // height):
#         for j in range(imgwidth // imgwidth):
#             box = (j * imgwidth, i * height, (j + 1) * imgwidth, (i + 1) * height)
#             _l.append(im.crop(box))

#     return _l


# crop("ss1.png", 1400, 200)

# for i in _l:
#     i.show()
