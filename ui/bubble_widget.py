"""
ui/bubble_widget.py -- Reusable RPG-style speech bubble widget.

Module-level authoritative sources for character accent colours:
  _CHARACTER_ACCENT  -- dict[str, str]  (hex colour strings)
  _DEFAULT_ACCENT    -- str             (fallback hex)

re-exported by notification_window.py for back-compat.
"""

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QFontMetrics

from ui.pixel_theme import pixel_font, BG_MID, BG_LIGHT, TEXT, TEXT_DIM

# -- Character accent palette (authoritative) --

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

# -- Layout constants --

OUTER_BORDER_W = 2
MID_BORDER_W   = 3
INNER_BORDER_W = 1
FRAME_TOTAL    = OUTER_BORDER_W + MID_BORDER_W + INNER_BORDER_W  # = 6

SHADOW_OFFSET  = 4
SHADOW_COLOR   = QColor("#2A1A00")

TAIL_WIDTH     = 16
TAIL_HEIGHT    = 10
CORNER_BITE    = 2

_MAX_LINES     = 8


class BubbleWidget(QWidget):
    """Pixel-art speech bubble -- embeddable, no WA_TranslucentBackground needed.

    Parameters
    ----------
    message           : displayed text (empty -> placeholder "...")
    character         : character id for accent colour
    font_size         : pixel size for pixel_font()
    padding           : inner content padding (px)
    max_width         : maximum total widget width including shadow
    min_width         : minimum body width
    tail_side         : bottom or top or none
    tail_offset_ratio : 0.0 = left edge, 1.0 = right edge of body
    show_shadow       : draw 4px drop shadow
    """

    def __init__(
        self,
        message: str = "",
        character: str = "orange_cat",
        font_size: int = 16,
        padding: int = 14,
        max_width: int = 280,
        min_width: int = 120,
        tail_side: str = "bottom",
        tail_offset_ratio: float = 0.5,
        show_shadow: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._message           = message
        self._typewriter_idx    = -1          # -1 = show all
        self._font_size         = font_size
        self._padding           = padding
        self._max_width         = max_width
        self._min_width         = min_width
        self._tail_side         = tail_side
        self._tail_offset_ratio = tail_offset_ratio
        self._show_shadow       = show_shadow
        self._show_placeholder  = True
        self._accent            = QColor(_CHARACTER_ACCENT.get(character, _DEFAULT_ACCENT))

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    # -- Public API --

    def set_message(self, text: str) -> None:
        self._message = text
        self._typewriter_idx = -1
        self.updateGeometry()
        self.update()

    def set_character(self, character_id: str) -> None:
        self._accent = QColor(_CHARACTER_ACCENT.get(character_id, _DEFAULT_ACCENT))
        self.update()

    def set_typewriter_index(self, idx: int) -> None:
        self._typewriter_idx = idx
        self.update()

    def current_displayed_text(self) -> str:
        text = self._message
        if self._typewriter_idx >= 0:
            text = text[:self._typewriter_idx]
        return text

    # -- Size hint --

    def sizeHint(self) -> QSize:
        return self._compute_size()

    def minimumSizeHint(self) -> QSize:
        return self._compute_size()

    def _compute_size(self) -> QSize:
        shadow_extra = SHADOW_OFFSET if self._show_shadow else 0
        tail_h = TAIL_HEIGHT if self._tail_side != "none" else 0

        inner_w_cap = self._max_width - shadow_extra - 2 * self._padding - 2 * FRAME_TOTAL
        inner_w_cap = max(inner_w_cap, self._min_width - 2 * self._padding - 2 * FRAME_TOTAL)

        fm = QFontMetrics(pixel_font(self._font_size))
        text = self._message or "..."
        rect = fm.boundingRect(
            0, 0, inner_w_cap, 0,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            text,
        )

        line_h = fm.height()
        text_h = min(rect.height(), line_h * _MAX_LINES)
        text_w = min(rect.width(), inner_w_cap)

        body_w = text_w + 2 * self._padding + 2 * FRAME_TOTAL
        body_h = text_h + 2 * self._padding + 2 * FRAME_TOTAL

        body_w = max(self._min_width, (body_w + 1) & ~1)
        body_h = max(28, (body_h + 1) & ~1)

        total_w = body_w + shadow_extra
        total_h = body_h + tail_h + shadow_extra
        return QSize(total_w, total_h)
    # -- Paint --

    def paintEvent(self, event):
        size = self._compute_size()
        shadow_extra = SHADOW_OFFSET if self._show_shadow else 0
        tail_h = TAIL_HEIGHT if self._tail_side != "none" else 0

        body_w = size.width() - shadow_extra
        body_h = size.height() - tail_h - shadow_extra

        tail_cx = int(body_w * self._tail_offset_ratio)
        tail_cx = max(TAIL_WIDTH // 2 + 4, min(body_w - TAIL_WIDTH // 2 - 4, tail_cx))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        if self._show_shadow:
            if self._tail_side == "bottom":
                painter.fillRect(SHADOW_OFFSET, SHADOW_OFFSET, body_w, body_h + tail_h, SHADOW_COLOR)
            else:
                painter.fillRect(SHADOW_OFFSET, SHADOW_OFFSET, body_w, body_h, SHADOW_COLOR)
        bx, by = 0, 0
        painter.fillRect(bx, by, body_w, body_h, QColor(TEXT))
        painter.fillRect(bx + OUTER_BORDER_W, by + OUTER_BORDER_W, body_w - 2 * OUTER_BORDER_W, body_h - 2 * OUTER_BORDER_W, self._accent)
        inset = OUTER_BORDER_W + MID_BORDER_W
        painter.fillRect(bx + inset, by + inset, body_w - 2 * inset, body_h - 2 * inset, QColor(BG_MID))
        for cx_, cy_ in [(bx, by), (bx + body_w - CORNER_BITE, by), (bx, by + body_h - CORNER_BITE), (bx + body_w - CORNER_BITE, by + body_h - CORNER_BITE)]:
            painter.fillRect(cx_, cy_, CORNER_BITE, CORNER_BITE, SHADOW_COLOR)
        highlight = QColor(BG_LIGHT)
        painter.fillRect(bx + inset, by + inset, body_w - 2 * inset, 1, highlight)
        painter.fillRect(bx + inset, by + inset, 1, body_h - 2 * inset, highlight)
        if self._tail_side == "bottom":
            self._draw_tail_bottom(painter, bx, by, body_w, body_h, tail_cx)
        elif self._tail_side == "top":
            self._draw_tail_top(painter, bx, by, body_w, tail_cx)
        self._draw_text(painter, bx, by, body_w, body_h)
        painter.end()
    def _draw_tail_bottom(self, painter, bx, by, body_w, body_h, tail_cx):
        th = TAIL_HEIGHT; tw = TAIL_WIDTH
        for i in range(th):
            half = max((tw // 2) - i, 0)
            x0 = bx + tail_cx - half; x1 = bx + tail_cx + half
            painter.fillRect(x0, by + body_h + i, x1 - x0, 1, QColor(TEXT))
        for i in range(th - 1):
            half = max((tw // 2 - 1) - i, 0)
            x0 = bx + tail_cx - half; x1 = bx + tail_cx + half
            if x1 > x0:
                painter.fillRect(x0, by + body_h + i, x1 - x0, 1, self._accent)
        for i in range(th - 2):
            half = max((tw // 2 - 2) - i, 0)
            x0 = bx + tail_cx - half; x1 = bx + tail_cx + half
            if x1 > x0:
                painter.fillRect(x0, by + body_h + i, x1 - x0, 1, QColor(BG_MID))

    def _draw_tail_top(self, painter, bx, by, body_w, tail_cx):
        th = TAIL_HEIGHT; tw = TAIL_WIDTH
        for i in range(th):
            row = th - 1 - i; half = max((tw // 2) - i, 0)
            x0 = bx + tail_cx - half; x1 = bx + tail_cx + half
            painter.fillRect(x0, by - th + row, x1 - x0, 1, QColor(TEXT))
        for i in range(th - 1):
            row = th - 1 - i; half = max((tw // 2 - 1) - i, 0)
            x0 = bx + tail_cx - half; x1 = bx + tail_cx + half
            if x1 > x0:
                painter.fillRect(x0, by - th + row, x1 - x0, 1, self._accent)
        for i in range(th - 2):
            row = th - 1 - i; half = max((tw // 2 - 2) - i, 0)
            x0 = bx + tail_cx - half; x1 = bx + tail_cx + half
            if x1 > x0:
                painter.fillRect(x0, by - th + row, x1 - x0, 1, QColor(BG_MID))

    def _draw_text(self, painter, bx, by, body_w, body_h):
        inset = OUTER_BORDER_W + MID_BORDER_W
        text_x = bx + inset + self._padding
        text_y = by + inset + self._padding
        text_w = body_w - 2 * (inset + self._padding)
        text_h = body_h - 2 * (inset + self._padding)
        displayed = self.current_displayed_text()
        if not displayed:
            if self._show_placeholder:
                painter.setPen(QColor(TEXT_DIM))
                painter.setFont(pixel_font(self._font_size))
                painter.drawText(
                    text_x, text_y, text_w, text_h,
                    Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                    "...",
                )
            return
        fm = QFontMetrics(pixel_font(self._font_size))
        line_h = fm.height()
        max_h = line_h * _MAX_LINES
        if fm.boundingRect(0, 0, text_w, 0, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, displayed).height() > max_h:
            words = displayed.split()
            while words:
                candidate = " ".join(words) + "..."
                if fm.boundingRect(0, 0, text_w, 0, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, candidate).height() <= max_h:
                    displayed = candidate
                    break
                words.pop()
            else:
                displayed = "..."
        painter.setPen(QColor(TEXT))
        painter.setFont(pixel_font(self._font_size))
        painter.drawText(
            text_x, text_y, text_w, text_h,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            displayed,
        )
