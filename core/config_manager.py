import copy
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "pets": [
        {
            "id": "pet_1",
            "character": "cat",
            "duration_sec": 180,
            "message": "休息一下！",
            "position": {"x": -1, "y": -1},
        },
        {
            "id": "pet_2",
            "character": "dog",
            "duration_sec": 300,
            "message": "時間到！",
            "position": {"x": -1, "y": -1},
        },
        {
            "id": "pet_3",
            "character": "goblin",
            "duration_sec": 1500,
            "message": "番茄鐘結束！",
            "position": {"x": -1, "y": -1},
        },
    ],
    "global": {
        "sound_enabled": True,
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
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = copy.deepcopy(DEFAULT_CONFIG)
                self.save()
        else:
            self._data = copy.deepcopy(DEFAULT_CONFIG)
            self.save()

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # --- Pet accessors ---

    def get_pets(self):
        return self._data.get("pets", [])

    def get_pet(self, pet_id):
        for pet in self._data.get("pets", []):
            if pet["id"] == pet_id:
                return pet
        return None

    def update_pet(self, pet_id, data):
        for i, pet in enumerate(self._data.get("pets", [])):
            if pet["id"] == pet_id:
                self._data["pets"][i].update(data)
                self.save()
                return True
        return False

    def add_pet(self, data):
        self._data["pets"].append(data)
        self.save()

    def remove_pet(self, pet_id):
        self._data["pets"] = [
            pet for pet in self._data["pets"] if pet["id"] != pet_id
        ]
        self.save()

    def set_pets(self, pets):
        self._data["pets"] = pets
        self.save()

    def update_pet_position(self, pet_id, x, y):
        """Convenience method: update position for a single pet."""
        return self.update_pet(pet_id, {"position": {"x": x, "y": y}})

    # --- Global accessors ---

    def get_global(self):
        return self._data.get("global", {})

    def update_global(self, data):
        self._data.setdefault("global", {}).update(data)
        self.save()

    @property
    def data(self):
        return self._data
