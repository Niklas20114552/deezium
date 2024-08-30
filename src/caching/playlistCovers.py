import os

import deezer
import requests


def download_medium(login: deezer.Client, plid: int, getpath: bool = False):
    os.makedirs(os.path.expanduser("~/.cache/deezium/cover_psm"), exist_ok=True)
    if os.path.exists(os.path.expanduser("~/.cache/deezium/cover_psm/") + str(plid)):
        if getpath:
            return os.path.expanduser("~/.cache/deezium/cover_psm/") + str(plid)
        else:
            with open(
                os.path.expanduser("~/.cache/deezium/cover_psm/") + str(plid), "rb"
            ) as f:
                return f.read()
    pl = login.get_playlist(plid)
    content = requests.get(pl.picture_medium).content
    with open(os.path.expanduser("~/.cache/deezium/cover_psm/") + str(plid), "wb") as f:
        f.write(content)
    if getpath:
        return os.path.expanduser("~/.cache/deezium/cover_psm/") + str(plid)
    else:
        return content
