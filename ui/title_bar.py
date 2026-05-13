"""
ui/title_bar.py -- Reusable pixel-art title bar widget for frameless windows.

Provides drag-to-move and a pixel X close button with hover/press states.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap

from ui.pixel_theme import pixel_font, BG_LIGHT, BORDER_HI, TEXT, BG_MID, CURSOR_CLR

_BAR_HEIGHT = 28


class PixelTitleBar(QWidget):
    close_requested = Signal()

    def __init__(self, title: str, icon_pixmap: QPixmap | None = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._icon_pixmap = icon_pixmap
        self._drag_start: QPoint | None = None
        self._close_hover = False
        self._close_pressed = False
        self.setFixedHeight(_BAR_HEIGHT)
        self.setMouseTracking(True)
        self._close_rect = QRect(0, 0, 16, 16)  # updated in paintEvent

    # ---- Paint ----

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w = self.width()

        # Background
        painter.fillRect(0, 0, w, _BAR_HEIGHT, QColor(BG_LIGHT))

        # Bottom border 2px
        painter.fillRect(0, _BAR_HEIGHT - 2, w, 2, QColor(BORDER_HI))

        # Title icon (optional) + text
        font = pixel_font(14, bold=True)
        painter.setFont(font)
        painter.setPen(QColor(TEXT))
        if self._icon_pixmap is not None and not self._icon_pixmap.isNull():
            painter.drawPixmap(8, 6, 16, 16, self._icon_pixmap)
            title_x = 36
        else:
            title_x = 12
        painter.drawText(title_x, 0, w - title_x - 24, _BAR_HEIGHT, Qt.AlignmentFlag.AlignVCenter, self._title)

        # X button region: 16x16 at (w-22, 6)
        x_x = w - 22
        x_y = 6
        self._close_rect = QRect(x_x, x_y, 16, 16)

        if self._close_pressed:
            painter.fillRect(self._close_rect, QColor(CURSOR_CLR))
            stroke_color = QColor(BG_MID)
        elif self._close_hover:
            painter.fillRect(self._close_rect, QColor(BG_MID))
            stroke_color = QColor(CURSOR_CLR)
        else:
            stroke_color = QColor(TEXT)

        # Draw X as two pairs of lines (NoAntialias pixel art)
        pen = QPen(stroke_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.SquareCap)
        painter.setPen(pen)
        # Diagonal strokes inside 16x16 box with 3px inset
        x0, y0 = x_x + 3, x_y + 3
        x1, y1 = x_x + 12, x_y + 12
        painter.drawLine(x0, y0, x1, y1)
        painter.drawLine(x1, y0, x0, y1)

        painter.end()

    # ---- Mouse events ----

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._close_rect.contains(event.position().toPoint()):
                self._close_pressed = True
                self.update()
                return
            pos = event.globalPosition().toPoint()
            self._drag_start = pos - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_start is not None:
            if self._close_hover:
                self._close_hover = False
                self.update()
            self.window().move(event.globalPosition().toPoint() - self._drag_start)
            return
        # Hover detection
        old_hover = self._close_hover
        self._close_hover = self._close_rect.contains(event.position().toPoint())
        if self._close_hover != old_hover:
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._close_pressed and self._close_rect.contains(event.position().toPoint()):
                self._close_pressed = False
                self.update()
                self.close_requested.emit()
                return
            self._close_pressed = False
            self._drag_start = None
            self.update()

    def leaveEvent(self, event):
        if self._close_hover:
            self._close_hover = False
            self.update()
