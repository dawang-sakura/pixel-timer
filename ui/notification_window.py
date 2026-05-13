from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPolygon

from ui.dwm_utils import disable_dwm_frame
from ui.pixel_theme import pixel_font, BG_DEEP, BORDER_HI, BORDER_LO, TEXT

_CHARACTER_ACCENT = {
    "orange_cat": "#E65100",
    "white_cat":  "#78909C",
    "calico":     "#5D4037",
    "snoopy":     "#424242",
    "shiba":      "#795548",
    "goblin":     "#1B5E20",
    "chick":      "#F9A825",
    "blue_eyes":  "#1565C0",
}
_DEFAULT_ACCENT = "#8888AA"
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

        width = 220
        bubble_h = 80
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
        self._label.setGeometry(10, 10, width - 20, bubble_h - 20)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setFont(pixel_font(10))
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
        painter.setBrush(QColor(BG_DEEP))
        painter.drawRect(3, 3, w - 6, bubble_h - 6)

        painter.setPen(QPen(QColor(BORDER_HI), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(2, 2, w - 4, bubble_h - 4)

        painter.setPen(QPen(self._accent, 1))
        painter.drawRect(6, 6, w - 12, bubble_h - 12)

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
        painter.setBrush(QColor(BG_DEEP))
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
