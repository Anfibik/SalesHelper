from math import ceil


def calculate_S_panel(width, length, height):
    height_skate = width / 5 + height
    height = ceil(height / 1.15) * 1.15
    wall_long = length * height
    wall_shot = width * height
    wall_skate = ((width * (height_skate - height)) - ((width * (height_skate - height)) / 4))
    S_panel = ceil(wall_long * 2 + wall_shot * 2 + wall_skate * 2)
    return round(S_panel, 2), height_skate

