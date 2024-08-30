from importlib.util import spec_from_file_location, module_from_spec
import os
import sys
import platform
from glob import glob

if platform.system() == "Windows":
    pass
elif platform.system() == "Linux":
    APP_DATA_PATH: str = "/usr/share/deezium/"
else:
    print("Sorry, but your Operating System is not supported.")
    sys.exit()

import_spec = spec_from_file_location('deezloader2', APP_DATA_PATH + 'deezloader2.py')
deezloader2 = module_from_spec(import_spec)
sys.modules['deezloader2'] = deezloader2
import_spec.loader.exec_module(deezloader2)



def download(login: deezloader2.Login2, id, quality="MP3_128") -> str:
    fmat = ".mp3"
    if quality == "FLAC":
        fmat = ".flac"
    os.makedirs(os.path.expanduser("~/.cache/deezium"), exist_ok=True)
    if os.path.exists(os.path.expanduser("~/.cache/deezium/") + f"{id}{fmat}"):
        return os.path.expanduser("~/.cache/deezium/") + f"{id}{fmat}"
    path = login.download_trackdee(
        f"https://www.deezer.com/track/{id}",
        quality=quality,
        output=os.path.expanduser("~/.cache/deezium"),
    )
    return path


def clear_ids(ids):
    for id in ids:
        for file in glob(os.path.expanduser(f"~/.cache/deezium/{id}.*")):
            os.remove(file)


def get_cached() -> list[int]:
    try:
        ids = []
        for file in glob(os.path.expanduser(f"~/.cache/deezium/*.*")):
            if file.endswith(".mp3"):
                ids.append(int(file.removesuffix(".mp3").split("/")[-1]))
            elif file.endswith(".flac"):
                ids.append(int(file.removesuffix(".flac").split("/")[-1]))
        return ids
    except FileNotFoundError:
        return []
