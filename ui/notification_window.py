from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Signal

from ui.dwm_utils import disable_dwm_frame
from ui.bubble_widget import BubbleWidget, _CHARACTER_ACCENT, _DEFAULT_ACCENT

# Re-export for back-compat (settings_window.py imports from here)
__all__ = ["NotificationWindow", "_CHARACTER_ACCENT", "_DEFAULT_ACCENT"]


class NotificationWindow(QWidget):
    dismissed = Signal()

    def __init__(self, message: str, character: str, position: QPoint, parent=None):
        super().__init__(parent)

        self._full_message = message
        self._char_index = 0
        self._typewriter_done = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bubble = BubbleWidget(
            message=message,
            character=character,
            font_size=16,
            padding=14,
            max_width=280,
            min_width=120,
            tail_side="bottom",
            tail_offset_ratio=0.5,
            show_shadow=False,
            parent=self,
        )
        self._bubble.move(0, 0)

        hint = self._bubble.sizeHint()
        self.setFixedSize(hint.width(), hint.height())
        self._bubble.setFixedSize(hint.width(), hint.height())

        # Position: tail tip at position
        from ui.bubble_widget import TAIL_WIDTH, TAIL_HEIGHT, SHADOW_OFFSET
        body_w = hint.width() - SHADOW_OFFSET
        tail_cx = int(body_w * 0.5)
        tail_tip_x = tail_cx
        tail_tip_y = hint.height() - SHADOW_OFFSET - 1
        x = position.x() - tail_tip_x
        y = position.y() - tail_tip_y - 4
        # Bug B: use the screen the pet widget is actually on, not always primaryScreen
        screen = QGuiApplication.screenAt(position) or QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = max(geom.x(), min(x, geom.right() - hint.width()))
            y = max(geom.y(), y)
        self.move(x, y)

        self._auto_close = QTimer(self)
        self._auto_close.setSingleShot(True)
        self._auto_close.timeout.connect(self.close)

        self._tw_timer = QTimer(self)
        self._tw_timer.timeout.connect(self._typewriter_tick)
        interval = 30 if len(message) > 30 else 40
        # N3: guard empty message -- skip typewriter, go straight to auto-close
        if len(message) > 0:
            self._tw_timer.start(interval)
        else:
            self._typewriter_done = True
            self._auto_close.start(5000)

    def _typewriter_tick(self):
        self._char_index += 1
        self._bubble.set_typewriter_index(self._char_index)
        if self._char_index >= len(self._full_message):
            self._tw_timer.stop()
            self._typewriter_done = True
            self._auto_close.start(5000)

    def showEvent(self, event):
        super().showEvent(event)
        disable_dwm_frame(int(self.winId()))

    def closeEvent(self, event):
        self._auto_close.stop()
        self._tw_timer.stop()
        self.dismissed.emit()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if not self._typewriter_done:
            self._tw_timer.stop()
            self._bubble.set_typewriter_index(-1)
            self._typewriter_done = True
            self._auto_close.start(5000)
        else:
            self.close()
