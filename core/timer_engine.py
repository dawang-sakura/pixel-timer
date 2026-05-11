from PySide6.QtCore import QObject, QTimer, Signal


class TimerEngine(QObject):
    timer_finished = Signal(str, str, str)  # timer_id, message, character
    timer_tick = Signal(str, int)  # timer_id, remaining_sec

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timers = {}  # timer_id -> {timer, remaining, message, character}

    def start(self, timer_id, duration_sec, message="時間到！", character="cat"):
        if timer_id in self._timers:
            self.cancel(timer_id)

        timer = QTimer(self)
        timer.setInterval(1000)
        self._timers[timer_id] = {
            "timer": timer,
            "remaining": duration_sec,
            "message": message,
            "character": character,
        }
        timer.timeout.connect(lambda tid=timer_id: self._tick(tid))
        timer.start()

    def _tick(self, timer_id):
        entry = self._timers.get(timer_id)
        if not entry:
            return

        entry["remaining"] -= 1
        self.timer_tick.emit(timer_id, entry["remaining"])

        if entry["remaining"] <= 0:
            entry["timer"].stop()
            message = entry["message"]
            character = entry["character"]
            del self._timers[timer_id]
            self.timer_finished.emit(timer_id, message, character)

    def cancel(self, timer_id):
        entry = self._timers.pop(timer_id, None)
        if entry:
            entry["timer"].stop()

    def cancel_all(self):
        for timer_id in list(self._timers):
            self.cancel(timer_id)

    def is_running(self, timer_id=None):
        if timer_id is not None:
            return timer_id in self._timers
        return len(self._timers) > 0

    def get_remaining(self, timer_id):
        entry = self._timers.get(timer_id)
        return entry["remaining"] if entry else 0

    def get_active_timers(self):
        return {tid: e["remaining"] for tid, e in self._timers.items()}
