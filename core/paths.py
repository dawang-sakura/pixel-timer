import sys
from pathlib import Path


def _bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return Path(__file__).resolve().parent.parent


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BUNDLE_DIR = _bundle_dir()
APP_DIR = _app_dir()

SPRITES_DIR = BUNDLE_DIR / "sprites" / "assets"
FONTS_DIR = BUNDLE_DIR / "assets" / "fonts"
CONFIG_PATH = APP_DIR / "config" / "settings.json"
