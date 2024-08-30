import math
import cv2
import deezer
import numpy


def conv_0_to_00(time: int) -> str:
    if time <= 9:
        return f"0{time}"
    else:
        return str(time)


def convert_sec_to_min(sec):
    ms = sec * 1000
    return ms_to_str(ms)


def rgb_to_hex(rgb: tuple) -> str:
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def ms_to_str(ms: int) -> str:
    sec = round(ms / 1000)
    if sec >= 3600:
        hr = math.floor(sec / 3600)
        r = math.floor(sec % 3600)
        min = math.floor(r / 60)
        rsec = math.floor(r % 60)
        return f"{hr}:{conv_0_to_00(min)}:{conv_0_to_00(rsec)}"
    else:
        min = math.floor(sec / 60)
        rsec = math.floor(sec % 60)
        return f"{conv_0_to_00(min)}:{conv_0_to_00(rsec)}"


def calc_background_color(data: bytes) -> str:
    numpyarr = numpy.frombuffer(data, numpy.uint8)
    img = cv2.imdecode(numpyarr, cv2.IMREAD_COLOR)
    height, width, _ = numpy.shape(img)
    avg_color_per_row = numpy.average(img, axis=0)
    avg_colors = numpy.average(avg_color_per_row, axis=0)
    avg_colors[0] -= 100
    colors = []
    for o in avg_colors:
        oi = int(o)
        oi -= 25
        if oi < 0:
            oi = 0
        colors.append(oi)
    return rgb_to_hex(colors)


def calc_foreground_color(hexstr: str) -> str:
    rgb = tuple(int(hexstr.removeprefix("#")[i : i + 2], 16) for i in (0, 2, 4))
    if (rgb[0] and rgb[1] and rgb[2]) >= 150:
        return "#000000"
    return "#FFFFFF"


def conv_paginated_ids(plist: deezer.PaginatedList) -> list[int]:
    ids = []
    for track in plist:
        ids.append(track.id)
    return ids
