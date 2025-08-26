#!/usr/bin/env python3

"""
fsutils.py: Filesystem utilities for not1mm.
@kyleboyle
"""
# pylint: disable=invalid-name

import os
import platform
import sys
import subprocess
from pathlib import Path
from appdata import AppDataPaths

WORKING_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = WORKING_PATH
APP_DATA_PATH = MODULE_PATH / "../data"
DATA_PATH = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
DATA_PATH += "/not1mm-server"
USER_DATA_PATH = Path(DATA_PATH)
HOME_PATH = os.environ.get("XDG_DATA_HOME", str(Path.home()))
_CONFIG_PATH = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
_CONFIG_PATH += "/not1mm-server"
CONFIG_PATH = Path(_CONFIG_PATH)
CONFIG_FILE = CONFIG_PATH / "not1mm-server.json"
LOG_FILE = USER_DATA_PATH / "not1mm-server_debug.log"
# print(f"{WORKING_PATH=}\n{HOME_PATH=}\n{APP_DATA_PATH=}\n{DATA_PATH=}\n{USER_DATA_PATH=}\n{CONFIG_PATH=}\n")
# Create directories if they do not exist on Linux systems
if platform.system() not in ["Windows", "Darwin"]:
    try:
        os.mkdir(CONFIG_PATH)
    except FileExistsError:
        ...
    try:
        os.mkdir(USER_DATA_PATH)
    except FileExistsError:
        ...

# Define and create directories if they do not exist on Windows or Mac systems
if platform.system() in ["Windows", "Darwin"]:
    _app_paths = AppDataPaths(name="not1mm-server")
    _app_paths.setup()
    LOG_FILE = _app_paths.get_log_file_path(name="appplication.log")
    _DATA_PATH = Path(_app_paths.app_data_path)
    USER_DATA_PATH = _DATA_PATH
    CONFIG_PATH = USER_DATA_PATH
    CONFIG_FILE = CONFIG_PATH / "not1mm-server.json"


def openFileWithOS(file):
    """Open a file with the default program for that OS."""
    if sys.platform == "win32":
        os.startfile(file)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", file])
    else:
        subprocess.Popen(["xdg-open", file])
