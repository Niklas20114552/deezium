import os
import deezer
import requests


def clear_ids(ids, size: str):
    for id in ids:
        file = os.path.expanduser(f"~/.cache/deezium/cover_as{size}/{id}")
        os.remove(file)


def get_cached(size: str) -> list[int]:
    try:
        files = os.listdir(os.path.expanduser(f"~/.cache/deezium/cover_as{size}"))
        ids = []
        for file in files:
            ids.append(int(file))
        return ids
    except FileNotFoundError:
        return []


def download_small(login: deezer.Client, albumid: int) -> bytes:
    os.makedirs(
        os.path.expanduser("~/.cache/deezium/cover_ass"), exist_ok=True
    )  # "Album Size Small" not the human thingy
    if os.path.exists(os.path.expanduser("~/.cache/deezium/cover_ass/") + str(albumid)):
        with open(
            os.path.expanduser("~/.cache/deezium/cover_ass/") + str(albumid), "rb"
        ) as f:
            return f.read()
    album = login.get_album(albumid)
    content = requests.get(album.cover_small).content
    with open(
        os.path.expanduser("~/.cache/deezium/cover_ass/") + str(albumid), "wb"
    ) as f:
        f.write(content)
    return content


def download_medium(login: deezer.Client, albumid: int, getpath: bool = False):
    os.makedirs(os.path.expanduser("~/.cache/deezium/cover_asm"), exist_ok=True)
    if os.path.exists(os.path.expanduser("~/.cache/deezium/cover_asm/") + str(albumid)):
        if getpath:
            return os.path.expanduser("~/.cache/deezium/cover_asm/") + str(albumid)
        else:
            with open(
                os.path.expanduser("~/.cache/deezium/cover_asm/") + str(albumid), "rb"
            ) as f:
                return f.read()
    album = login.get_album(albumid)
    content = requests.get(album.cover_medium).content
    with open(
        os.path.expanduser("~/.cache/deezium/cover_asm/") + str(albumid), "wb"
    ) as f:
        f.write(content)
    if getpath:
        return os.path.expanduser("~/.cache/deezium/cover_asm/") + str(albumid)
    else:
        return content
