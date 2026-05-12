from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal


class AlarmEngine(QObject):
    alarm_triggered = Signal(str, str, str, int)  # pet_id, message, character, alarm_index

    SCAN_INTERVAL_MS = 30_000

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._last_fired = {}
        self._timer = QTimer(self)
        self._timer.setInterval(self.SCAN_INTERVAL_MS)
        self._timer.timeout.connect(self._scan)

    def start(self):
        self._scan()
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def clear_fired_cache(self):
        current = datetime.now().strftime("%H:%M")
        self._last_fired = {k: v for k, v in self._last_fired.items() if v == current}

    def _scan(self):
        now = datetime.now()
        current_hhmm = now.strftime("%H:%M")
        current_weekday = now.weekday()

        for pet in self._config.get_pets():
            pet_id = pet["id"]
            character = pet.get("character", "orange_cat")
            for idx, alarm in enumerate(pet.get("alarms", [])):
                if not alarm.get("enabled", False):
                    continue
                if alarm.get("time") != current_hhmm:
                    continue

                repeat = alarm.get("repeat", "daily")
                if repeat == "weekdays" and current_weekday >= 5:
                    continue

                key = (pet_id, idx)
                if self._last_fired.get(key) == current_hhmm:
                    continue
                self._last_fired[key] = current_hhmm

                self.alarm_triggered.emit(
                    pet_id,
                    alarm.get("message", "鬧鐘！"),
                    character,
                    idx,
                )
