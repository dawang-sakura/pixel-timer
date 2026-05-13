from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPolygon

from ui.dwm_utils import disable_dwm_frame
from ui.pixel_theme import pixel_font, BG_MID, TEXT

_CHARACTER_ACCENT = {
    "orange_cat": "#E65100",
    "white_cat":  "#90A4AE",
    "calico":     "#6D4C41",
    "snoopy":     "#616161",
    "shiba":      "#8D6E63",
    "goblin":     "#2E7D32",
    "chick":      "#F57F17",
    "blue_eyes":  "#1565C0",
}
_DEFAULT_ACCENT = "#C8A96E"
_TRIANGLE_H = 10


class NotificationWindow(QWidget):
    dismissed = Signal()

    def __init__(self, message: str, character: str, position: QPoint, parent=None):
        super().__init__(parent)

        self._full_message = message
        self._char_index = 0
        self._accent = QColor(_CHARACTER_ACCENT.get(character, _DEFAULT_ACCENT))
        self._typewriter_done = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        width = 260
        bubble_h = 100
        total_h = bubble_h + _TRIANGLE_H
        self.setFixedSize(width, total_h)

        x = position.x() - (width - 48) // 2
        y = position.y() - total_h - 4
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = max(geom.x(), min(x, geom.right() - width))
            y = max(geom.y(), y)
        self.move(x, y)

        self._label = QLabel("", self)
        self._label.setGeometry(12, 12, width - 24, bubble_h - 24)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setFont(pixel_font(16))
        self._label.setStyleSheet(f"color: {TEXT}; background: transparent;")

        self._auto_close = QTimer(self)
        self._auto_close.setSingleShot(True)
        self._auto_close.timeout.connect(self.close)

        self._tw_timer = QTimer(self)
        self._tw_timer.timeout.connect(self._typewriter_tick)
        interval = 30 if len(message) > 30 else 40
        self._tw_timer.start(interval)

    def _typewriter_tick(self):
        self._char_index += 1
        self._label.setText(self._full_message[:self._char_index])
        if self._char_index >= len(self._full_message):
            self._tw_timer.stop()
            self._typewriter_done = True
            self._auto_close.start(5000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w = self.width()
        bubble_h = self.height() - _TRIANGLE_H

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BG_MID))
        painter.drawRect(3, 3, w - 6, bubble_h - 6)

        painter.setPen(QPen(self._accent, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(2, 2, w - 4, bubble_h - 4)

        cx = w // 2
        triangle = QPolygon([
            QPoint(cx - 8, bubble_h),
            QPoint(cx + 8, bubble_h),
            QPoint(cx, bubble_h + _TRIANGLE_H),
        ])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._accent)
        painter.drawPolygon(triangle)

        triangle_inner = QPolygon([
            QPoint(cx - 5, bubble_h - 1),
            QPoint(cx + 5, bubble_h - 1),
            QPoint(cx, bubble_h + _TRIANGLE_H - 3),
        ])
        painter.setBrush(QColor(BG_MID))
        painter.drawPolygon(triangle_inner)

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
            self._label.setText(self._full_message)
            self._typewriter_done = True
            self._auto_close.start(5000)
        else:
            self.close()
