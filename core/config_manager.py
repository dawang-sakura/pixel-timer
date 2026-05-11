import copy
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "hotkeys": [
        {
            "id": "preset_1",
            "key": "ctrl+shift+1",
            "duration_sec": 180,
            "message": "休息一下！",
            "character": "cat",
        },
        {
            "id": "preset_2",
            "key": "ctrl+shift+2",
            "duration_sec": 300,
            "message": "時間到！",
            "character": "dog",
        },
        {
            "id": "preset_3",
            "key": "ctrl+shift+3",
            "duration_sec": 1500,
            "message": "番茄鐘結束！",
            "character": "goblin",
        },
    ],
    "global": {
        "sound_enabled": True,
        "spawn_corner": "bottom_right",
    },
}


class ConfigManager:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.json"
        self._path = Path(config_path)
        self._data = {}
        self.load()

    def load(self):
        if self._path.exists():
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = copy.deepcopy(DEFAULT_CONFIG)
            self.save()

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_hotkeys(self):
        return self._data.get("hotkeys", [])

    def get_hotkey(self, hotkey_id):
        for hk in self._data.get("hotkeys", []):
            if hk["id"] == hotkey_id:
                return hk
        return None

    def update_hotkey(self, hotkey_id, data):
        for i, hk in enumerate(self._data["hotkeys"]):
            if hk["id"] == hotkey_id:
                self._data["hotkeys"][i].update(data)
                self.save()
                return True
        return False

    def add_hotkey(self, data):
        self._data["hotkeys"].append(data)
        self.save()

    def remove_hotkey(self, hotkey_id):
        self._data["hotkeys"] = [
            hk for hk in self._data["hotkeys"] if hk["id"] != hotkey_id
        ]
        self.save()

    def set_hotkeys(self, hotkeys):
        self._data["hotkeys"] = hotkeys
        self.save()

    def get_global(self):
        return self._data.get("global", {})

    def update_global(self, data):
        self._data.setdefault("global", {}).update(data)
        self.save()

    @property
    def data(self):
        return self._data
