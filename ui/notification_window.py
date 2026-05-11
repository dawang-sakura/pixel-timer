from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QPolygon


# Character palette: (border_hex, fill_hex)
_CHARACTER_COLORS = {
    "orange_cat": ("#E65100", "#FFF3E0"),
    "white_cat":  ("#78909C", "#ECEFF1"),
    "calico":     ("#5D4037", "#EFEBE9"),
    "snoopy":     ("#212121", "#FAFAFA"),
    "shiba":      ("#795548", "#FFF8E1"),
    "goblin":     ("#1B5E20", "#E8F5E9"),
}
_DEFAULT_COLORS = ("#37474F", "#ECEFF1")

_TRIANGLE_H = 10  # height of bottom pointer triangle


class NotificationWindow(QWidget):
    dismissed = Signal()

    def __init__(self, message: str, character: str, position: QPoint, parent=None):
        super().__init__(parent)

        self._message = message
        colors = _CHARACTER_COLORS.get(character, _DEFAULT_COLORS)
        self._border_color = QColor(colors[0])
        self._fill_color = QColor(colors[1])

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        width = 200
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

        # Message label inside the bubble
        self._label = QLabel(message, self)
        self._label.setGeometry(8, 8, width - 16, bubble_h - 16)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)

        font = QFont()
        font.setPointSize(9)
        self._label.setFont(font)
        self._label.setStyleSheet(f"color: {colors[0]}; background: transparent;")

        # Auto-dismiss after 5 seconds
        QTimer.singleShot(5000, self.close)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w = self.width()
        bubble_h = self.height() - _TRIANGLE_H

        # Outer border (3px)
        painter.setPen(QPen(self._border_color, 3))
        painter.setBrush(self._fill_color)
        painter.drawRect(2, 2, w - 4, bubble_h - 4)

        # Inner lighter border line (1px inset)
        lighter = self._fill_color.lighter(110)
        painter.setPen(QPen(lighter, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(5, 5, w - 10, bubble_h - 10)

        # Triangle pointer at bottom-center
        cx = w // 2
        triangle = QPolygon([
            QPoint(cx - 8, bubble_h),
            QPoint(cx + 8, bubble_h),
            QPoint(cx, bubble_h + _TRIANGLE_H),
        ])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._border_color)
        painter.drawPolygon(triangle)

        # Triangle fill (slightly inset)
        triangle_fill = QPolygon([
            QPoint(cx - 5, bubble_h - 1),
            QPoint(cx + 5, bubble_h - 1),
            QPoint(cx, bubble_h + _TRIANGLE_H - 3),
        ])
        painter.setBrush(self._fill_color)
        painter.drawPolygon(triangle_fill)

    def closeEvent(self, event):
        self.dismissed.emit()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        self.close()
