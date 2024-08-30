import os
import platform


def get_oauth_token():
    os.makedirs(os.path.expanduser("~/.config/deezium"), exist_ok=True)
    if os.path.exists(os.path.expanduser("~/.config/deezium/aro.dat")):
        with open(os.path.expanduser("~/.config/deezium/aro.dat"), "r") as f:
            return f.read()
    return False


def gen_oauth_token(datapath: str, forced: bool = False):
    os.makedirs(os.path.expanduser("~/.config/deezium"), exist_ok=True)
    if (
        not os.path.exists(os.path.expanduser("~/.config/deezium/aro.dat"))
    ) or forced:
        os.system(
            f'python{'3' if platform.system() != 'Windows' else ''} "{datapath}oauth.py"'
        )


def get_login_token():
    os.makedirs(os.path.expanduser("~/.config/deezium"), exist_ok=True)
    if os.path.exists(os.path.expanduser("~/.config/deezium/arl.dat")):
        with open(os.path.expanduser("~/.config/deezium/arl.dat"), "r") as f:
            return f.read()
    return False


def logout():
    if os.path.exists(os.path.expanduser("~/.config/deezium/arl.dat")):
        os.remove(os.path.expanduser("~/.config/deezium/arl.dat"))
    if os.path.exists(os.path.expanduser("~/.config/deezium/aro.dat")):
        os.remove(os.path.expanduser("~/.config/deezium/aro.dat"))
