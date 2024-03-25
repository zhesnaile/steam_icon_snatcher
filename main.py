#!/usr/bin/env python3
import os
import platform
import subprocess
import sys

import requests
import vdf

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from loguru import logger


def get_steam_dir():
    if platform.system() == "Windows":
        program_files = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
        program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))

        steam_dir = program_files / "Steam"
        if not steam_dir.exists():
            steam_dir = program_files_x86 / "Steam"

        return steam_dir

    elif platform.system() == "Darwin":
        applications_dir = Path.home() / "Applications"
        return applications_dir / "Steam.app" / "Contents" / "MacOS"

    else:
        home_dir = Path.home()
        return home_dir / ".steam" / "steam"


STEAM_DIR = get_steam_dir()
STEAM_OUTPUT_DIR = STEAM_DIR / "steam" / "games"
STEAM_LIBRARY_FILE = STEAM_DIR / "steamapps" / "libraryfolders.vdf"

def is_downloadable(url):
    """
    Does the url contain a downloadable resource
    """
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if content_type == None:
        return False
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    content_length = header.get('content-length', None)
    if content_length and int(content_length) > 2e6:  # 200 mb approx
        return False
    return True


def get_appids():
    with open(STEAM_LIBRARY_FILE) as f:
        d = vdf.load(f)
        for v in d['libraryfolders'].values():
            for k in v['apps'].keys():
                yield k


def get_appid_filenames(appid):
    proc = subprocess.run(['steamcmd', '+app_info_print', appid, '+quit'], capture_output=True, text=True)

    vdf_start = proc.stdout.find(f'"{appid}"')
    if vdf_start == -1:
        return []

    vdf_data = proc.stdout[vdf_start:]

    app_info = vdf.loads(vdf_data)
    common_info = app_info[appid]["common"]

    icons = []
    if (platform.system() == 'Linux') and "linuxclienticon" in common_info:
        icons.append(common_info["linuxclienticon"] + ".zip")
    if "clienticon" in common_info:
        icons.append(common_info["clienticon"] + ".ico")

    game_name = common_info["name"]

    if len(icons) > 0:
        logger.success(f"{appid} - Found {len(icons)} icons for game: {game_name}")
    else:
        logger.warning(f"{appid} - Found no icons for game: {game_name}")

    return icons


def download_appid_image(appid, file):
    dl_path = f"https://media.steampowered.com/steamcommunity/public/images/apps/{appid}/{file}"
    logger.debug(dl_path)
    output_file = f"{STEAM_OUTPUT_DIR}/{file}"

    if os.path.isfile(output_file) or not is_downloadable(dl_path):
        return

    r = requests.get(dl_path, allow_redirects=True)
    if r.status_code == 200:
        f = open(output_file, 'wb')
        f.write(r.content)
        f.close()


def download_appid_images(appid):
    icons = get_appid_filenames(appid)
    for icon in icons:
        download_appid_image(appid, icon)


def download_all_images(game_ids):
    with ThreadPoolExecutor(max_workers=len(os.sched_getaffinity(0))) as e:
        e.map(download_appid_images, game_ids)


def main():
    game_ids = set(get_appids())

    download_all_images(game_ids)


if __name__=='__main__':
    logger.remove(0)
    logger.add(
        sys.stderr,
        colorize=True,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level: <8}</level> | <level>{message}</level>",
        level="SUCCESS"
    )
    main()
