import ctypes
import ctypes.wintypes

from datetime import datetime

from PySide6.QtWidgets import QWidget, QLabel, QMenu, QApplication
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBitmap, QColor, QPainter, QPixmap

from core.constants import CHARACTER_DISPLAY_NAMES

_HWND_TOPMOST = -1
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001
_SWP_NOACTIVATE = 0x0010
_SWP_FLAGS = _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE

_EVENT_SYSTEM_FOREGROUND = 0x0003
_WINEVENT_OUTOFCONTEXT = 0x0000

_user32 = ctypes.windll.user32
_user32.SetWindowPos.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.HWND,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.wintypes.UINT,
]
_user32.SetWindowPos.restype = ctypes.wintypes.BOOL

_WINEVENTPROC = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.c_long,
    ctypes.c_long,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)

_user32.SetWinEventHook.argtypes = [
    ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
    ctypes.wintypes.HMODULE, _WINEVENTPROC,
    ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
]
_user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

_user32.UnhookWinEvent.argtypes = [ctypes.wintypes.HANDLE]
_user32.UnhookWinEvent.restype = ctypes.wintypes.BOOL

_dwmapi = ctypes.windll.dwmapi


class _MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    ]


class PetWidget(QWidget):
    timer_toggled = Signal(str)       # pet_id
    position_changed = Signal(str, int, int)  # pet_id, x, y

    _auto_position_index = 0
    _all_widgets = []
    _fg_hook = None
    _fg_hook_proc = None

    def __init__(self, pet_config: dict, animator, parent=None):
        super().__init__(parent)

        self._pet_id = pet_config["id"]
        self._animator = animator
        self._alarms = pet_config.get("alarms", [])
        self._character_name = pet_config.get("character", "")
        self._drag_pos = None
        self._drag_started_pos = None
        self._counting = False
        self._last_mask_key = -1

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(48, 48)

        self._label = QLabel(self)
        self._label.setGeometry(0, 0, 48, 48)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._animator.frame_changed.connect(self.update_frame)

        initial = self._animator.current_pixmap()
        if initial and not initial.isNull():
            self._label.setPixmap(initial)
            self._apply_mask(initial)

        pos = pet_config.get("position", {"x": -1, "y": -1})
        if pos.get("x", -1) == -1 or pos.get("y", -1) == -1:
            self._auto_place()
        else:
            self.move(pos["x"], pos["y"])

        self._update_idle_tooltip()

        PetWidget._all_widgets.append(self)
        PetWidget._install_hook()

    # ------------------------------------------------------------------ topmost

    @classmethod
    def _install_hook(cls):
        if cls._fg_hook is not None:
            return

        def _on_foreground(hWinEventHook, event, hwnd, idObject, idChild, idEventThread, dwmsEventTime):
            for w in list(cls._all_widgets):
                if w.isVisible():
                    w._ensure_topmost()

        cls._fg_hook_proc = _WINEVENTPROC(_on_foreground)
        cls._fg_hook = _user32.SetWinEventHook(
            _EVENT_SYSTEM_FOREGROUND, _EVENT_SYSTEM_FOREGROUND,
            None, cls._fg_hook_proc, 0, 0, _WINEVENT_OUTOFCONTEXT,
        )

    @classmethod
    def _uninstall_hook(cls):
        if cls._fg_hook:
            _user32.UnhookWinEvent(cls._fg_hook)
            cls._fg_hook = None
            cls._fg_hook_proc = None

    def _ensure_topmost(self):
        if self.isVisible():
            hwnd = int(self.winId())
            _user32.SetWindowPos(
                hwnd, _HWND_TOPMOST, 0, 0, 0, 0, _SWP_FLAGS
            )

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_topmost()
        self._enable_transparency()

    def _enable_transparency(self):
        hwnd = int(self.winId())
        margins = _MARGINS(-1, -1, -1, -1)
        _dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), QColor(0, 0, 0, 0))
        p.end()

    def closeEvent(self, event):
        if self in PetWidget._all_widgets:
            PetWidget._all_widgets.remove(self)
        if not PetWidget._all_widgets:
            PetWidget._uninstall_hook()
        super().closeEvent(event)

    def _auto_place(self):
        screen = QApplication.primaryScreen()
        geom = screen.availableGeometry()
        idx = PetWidget._auto_position_index
        PetWidget._auto_position_index += 1

        spacing = 60
        x = geom.right() - 48 - (idx * spacing)
        y = geom.bottom() - 48
        self.move(x, y)

    # --- Mouse events ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_started_pos = event.globalPosition().toPoint()
            self._drag_pos = self._drag_started_pos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            end_pos = event.globalPosition().toPoint()
            if self._drag_started_pos and end_pos != self._drag_started_pos:
                new_pos = self.frameGeometry().topLeft()
                self.position_changed.emit(self._pet_id, new_pos.x(), new_pos.y())
            self._drag_pos = None
            self._drag_started_pos = None
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.timer_toggled.emit(self._pet_id)
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        if self._counting:
            cancel_action = menu.addAction("取消計時")
            cancel_action.triggered.connect(lambda: self.timer_toggled.emit(self._pet_id))
        hide_action = menu.addAction("隱藏")
        hide_action.triggered.connect(self.hide)
        menu.exec(event.globalPos())

    # --- Public API ---

    def update_frame(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                48, 48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            self._label.setPixmap(scaled)
            self._apply_mask(scaled)

    def _apply_mask(self, pixmap: QPixmap):
        if not pixmap or pixmap.isNull():
            return
        key = pixmap.cacheKey()
        if key == self._last_mask_key:
            return
        self._last_mask_key = key
        mask_image = pixmap.toImage().createAlphaMask()
        if not mask_image.isNull():
            self.setMask(QBitmap.fromImage(mask_image))

    def set_tooltip_remaining(self, remaining_sec: int):
        m, s = divmod(remaining_sec, 60)
        self.setToolTip(f"剩餘 {m:02d}:{s:02d}")

    def set_counting(self, counting: bool):
        self._counting = counting
        if not counting:
            self._update_idle_tooltip()

    def _update_idle_tooltip(self):
        char_name = CHARACTER_DISPLAY_NAMES.get(self._character_name, self._character_name)
        next_alarm = self._compute_next_alarm()
        if next_alarm:
            self.setToolTip(f"{char_name}\n下個鬧鐘: {next_alarm}")
        else:
            self.setToolTip(char_name)

    def _compute_next_alarm(self):
        now = datetime.now()
        current_weekday = now.weekday()
        now_minutes = now.hour * 60 + now.minute
        best = None

        for alarm in self._alarms:
            if not alarm.get("enabled", False):
                continue
            t = alarm.get("time", "")
            repeat = alarm.get("repeat", "daily")
            try:
                alarm_hour, alarm_min = map(int, t.split(":"))
            except (ValueError, AttributeError):
                continue

            alarm_minutes = alarm_hour * 60 + alarm_min

            fires_today = True
            if repeat == "weekdays" and current_weekday >= 5:
                fires_today = False

            if fires_today and alarm_minutes > now_minutes:
                delta = alarm_minutes - now_minutes
            elif repeat == "once":
                continue
            else:
                if repeat == "weekdays" and current_weekday == 4:
                    delta = (alarm_minutes - now_minutes) + 3 * 1440
                elif repeat == "weekdays" and current_weekday >= 5:
                    days_until_monday = 7 - current_weekday
                    delta = alarm_minutes + days_until_monday * 1440 - now_minutes
                else:
                    delta = (alarm_minutes - now_minutes) + 1440

            if best is None or delta < best[0]:
                best = (delta, t)

        return best[1] if best else None

    def refresh_alarms(self, alarms):
        self._alarms = alarms
        if not self._counting:
            self._update_idle_tooltip()

    @property
    def pet_id(self) -> str:
        return self._pet_id
