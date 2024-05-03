from deezloader2 import Login2 as DWLogin
import deezloader
import deezer
import os as _os
import requests
import numpy as _numpy
import cv2 as _cv2
import math as _math
from glob import glob as _glob


def _sectime(time: int) -> str:
    if time <= 9:
        return f'0{time}'
    else:
        return str(time)
    
    
def convert_sec_to_min(sec):
    ms = sec * 1000
    return ms_to_str(ms)

def _rgb_to_hex(rgb: tuple) -> str: return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def get_oauth_token():
    _os.makedirs(_os.path.expanduser('~/.config/deezium'), exist_ok=True)
    if _os.path.exists(_os.path.expanduser('~/.config/deezium/aro.dat')):
        with open(_os.path.expanduser('~/.config/deezium/aro.dat'), 'r') as f:
            return f.read()
    return False


def gen_oauth_token(forced: bool = False):
    _os.makedirs(_os.path.expanduser('~/.config/deezium'), exist_ok=True)
    if (not _os.path.exists(_os.path.expanduser('~/.config/deezium/aro.dat'))) or forced:
        _os.system('python3 oauth.py')


def get_login_token():
    _os.makedirs(_os.path.expanduser('~/.config/deezium'), exist_ok=True)
    if _os.path.exists(_os.path.expanduser('~/.config/deezium/arl.dat')):
        with open(_os.path.expanduser('~/.config/deezium/arl.dat'), 'r') as f:
            return f.read()
    return False


def download_track(login: DWLogin, id, quality="MP3_128") -> str:
    fmat = '.mp3'
    if quality == 'FLAC':
        fmat = '.flac'
    _os.makedirs(_os.path.expanduser('~/.cache/deezium'), exist_ok=True)
    if _os.path.exists(_os.path.expanduser('~/.cache/deezium/') + f'{id}{fmat}'):
        return _os.path.expanduser('~/.cache/deezium/') + f'{id}{fmat}'
    path = login.download_trackdee(f"https://www.deezer.com/track/{id}", quality=quality, output=_os.path.expanduser('~/.cache/deezium'))
    return path
    

def clean_trackids(ids):
    for id in ids:
        for file in _glob(_os.path.expanduser(f'~/.cache/deezium/{id}.*')):
            _os.remove(file)
            

def clean_albumcovers(ids, size: str):
    for id in ids:
        file = _os.path.expanduser(f'~/.cache/deezium/cover_as{size}/{id}')
        _os.remove(file)
        

def get_cached_tracks() -> list[int]:
    try:
        ids = []
        for file in _glob(_os.path.expanduser(f'~/.cache/deezium/*.*')):
            if file.endswith('.mp3'):
                ids.append(int(file.removesuffix('.mp3').split('/')[-1]))
            elif file.endswith('.flac'):
                ids.append(int(file.removesuffix('.flac').split('/')[-1]))
        return ids
    except FileNotFoundError:
        return []
    
    
def logout():
    if _os.path.exists(_os.path.expanduser('~/.config/deezium/arl.dat')):
        _os.remove(_os.path.expanduser('~/.config/deezium/arl.dat'))
    if _os.path.exists(_os.path.expanduser('~/.config/deezium/aro.dat')):
        _os.remove(_os.path.expanduser('~/.config/deezium/aro.dat'))


def get_cached_albumcovers(size: str) -> list[int]:
    try:
        files = _os.listdir(_os.path.expanduser(f'~/.cache/deezium/cover_as{size}'))
        ids = []
        for file in files:
            ids.append(int(file))
        return ids
    except FileNotFoundError:
        return []


def download_albumcover_s(login: deezer.Client, albumid: int) -> bytes:
    _os.makedirs(_os.path.expanduser('~/.cache/deezium/cover_ass'), exist_ok=True) # "Album Size Small" not the human thingy
    if _os.path.exists(_os.path.expanduser('~/.cache/deezium/cover_ass/') + str(albumid)):
        with open(_os.path.expanduser('~/.cache/deezium/cover_ass/') + str(albumid), 'rb') as f:
            return f.read()
    album = login.get_album(albumid)
    content = requests.get(album.cover_small).content
    with open(_os.path.expanduser('~/.cache/deezium/cover_ass/') + str(albumid), 'wb') as f:
        f.write(content)
    return content


def download_albumcover_m(login: deezer.Client, albumid: int, getpath: bool = False):
    _os.makedirs(_os.path.expanduser('~/.cache/deezium/cover_asm'), exist_ok=True)
    if _os.path.exists(_os.path.expanduser('~/.cache/deezium/cover_asm/') + str(albumid)):
        if getpath:
            return _os.path.expanduser('~/.cache/deezium/cover_asm/') + str(albumid)
        else:
            with open(_os.path.expanduser('~/.cache/deezium/cover_asm/') + str(albumid), 'rb') as f:
                return f.read()
    album = login.get_album(albumid)
    content = requests.get(album.cover_medium).content
    with open(_os.path.expanduser('~/.cache/deezium/cover_asm/') + str(albumid), 'wb') as f:
        f.write(content)
    if getpath:
        return _os.path.expanduser('~/.cache/deezium/cover_asm/') + str(albumid)
    else:
        return content
    
    
def download_playlcover_m(login: deezer.Client, plid: int, getpath: bool = False):
    _os.makedirs(_os.path.expanduser('~/.cache/deezium/cover_psm'), exist_ok=True)
    if _os.path.exists(_os.path.expanduser('~/.cache/deezium/cover_psm/') + str(plid)):
        if getpath:
            return _os.path.expanduser('~/.cache/deezium/cover_psm/') + str(plid)
        else:
            with open(_os.path.expanduser('~/.cache/deezium/cover_psm/') + str(plid), 'rb') as f:
                return f.read()
    pl = login.get_playlist(plid)
    content = requests.get(pl.picture_medium).content
    with open(_os.path.expanduser('~/.cache/deezium/cover_psm/') + str(plid), 'wb') as f:
        f.write(content)
    if getpath:
        return _os.path.expanduser('~/.cache/deezium/cover_psm/') + str(plid)
    else:
        return content


def calc_background_color(data: bytes) -> str:
    numpyarr = _numpy.frombuffer(data, _numpy.uint8)
    img = _cv2.imdecode(numpyarr, _cv2.IMREAD_COLOR)
    height, width, _ = _numpy.shape(img)
    avg_color_per_row = _numpy.average(img, axis=0)
    avg_colors = _numpy.average(avg_color_per_row, axis=0)
    avg_colors[0] -= 100
    colors = []
    for o in avg_colors:
        oi = int(o)
        oi -= 25
        if oi < 0: oi = 0
        colors.append(oi)
    return _rgb_to_hex(colors)


def calc_foreground_color(hexstr: str) -> str:
    rgb = tuple(int(hexstr.removeprefix('#')[i:i+2], 16) for i in (0, 2, 4))
    if (rgb[0] and rgb[1] and rgb[2]) >= 110:
        return '#000000'
    return '#FFFFFF'


def ms_to_str(ms: int) -> str:
    sec = round(ms / 1000)
    if sec >= 3600:
        hr = _math.floor(sec / 3600)
        r = _math.floor(sec % 3600)
        min = _math.floor(r / 60)
        rsec = _math.floor(r % 60)
        return f'{hr}:{_sectime(min)}:{_sectime(rsec)}'
    else:
        min = _math.floor(sec / 60)
        rsec = _math.floor(sec % 60)
        return f'{_sectime(min)}:{_sectime(rsec)}'


def conv_paginated_ids(plist: deezer.PaginatedList) -> list[int]:
    ids = []
    for track in plist:
        ids.append(track.id)
    return ids
