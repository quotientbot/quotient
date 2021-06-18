points = """
1 = 20,
2 = 14,
3-5 = 10
"""

result = {}
for line in points.replace("\n", "").split(","):
    line_values = [value.strip() for value in line.split("=")]
    if "-" in line_values[0]:
        range_idx = line_values[0].split("-")
        num_range = [i for i in range(int(range_idx[0]), int(range_idx[1]) + 1)]
        for key in num_range:
            result[key] = int(line_values[1])
    else:
        result[int(line_values[0])] = int(line_values[1])


print(result)
