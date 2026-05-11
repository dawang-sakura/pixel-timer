import keyboard
from PySide6.QtCore import QObject, Signal


class HotkeyBridge(QObject):
    hotkey_triggered = Signal(str)


class HotkeyManager:
    def __init__(self):
        self.bridge = HotkeyBridge()
        self._registered = {}

    def register(self, hotkey_id, key_str):
        try:
            keyboard.add_hotkey(
                key_str,
                lambda hid=hotkey_id: self.bridge.hotkey_triggered.emit(hid),
            )
            self._registered[key_str] = hotkey_id
            return True
        except Exception as e:
            print(f"[HotkeyManager] 註冊失敗 {key_str}: {e}")
            return False

    def unregister_all(self):
        for key_str in list(self._registered):
            try:
                keyboard.remove_hotkey(key_str)
            except Exception:
                pass
        self._registered.clear()

    def register_from_config(self, hotkeys):
        self.unregister_all()
        for hk in hotkeys:
            self.register(hk["id"], hk["key"])
