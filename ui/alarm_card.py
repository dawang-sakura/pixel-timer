"""
ui/alarm_card.py -- RPG-style card widget for a single alarm configuration.

Displays hour:min spinboxes + message input + repeat combo + enabled checkbox
in a single horizontal row.  Uses QPainter for pixel-art border (R2).
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QSpinBox, QLineEdit,
    QPushButton, QCheckBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen

from ui.pixel_theme import (
    pixel_font, BG_MID, BORDER_LO, BORDER_HI,
)

_REPEAT_OPTIONS = [("once", "單次"), ("daily", "每天"), ("weekdays", "平日")]
_CARD_HEIGHT = 56


class AlarmCard(QWidget):
    """Editable card for one alarm entry.

    Signals
    -------
    changed          : emitted on any field edit
    delete_requested : emitted when the ✕ button is clicked
    """

    changed = Signal()
    delete_requested = Signal()

    def __init__(self, alarm_data: dict | None = None, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMouseTracking(True)

        if alarm_data is None:
            alarm_data = {
                "time": "09:00",
                "message": "鬧鐘！",
                "repeat": "daily",
                "enabled": True,
            }

        self._selected = False

        # Parse initial time
        try:
            h_init, m_init = map(int, alarm_data.get("time", "09:00").split(":"))
        except (ValueError, AttributeError):
            h_init, m_init = 9, 0

        self.setFixedHeight(_CARD_HEIGHT)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        # ── Layout ───────────────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # 1. Time block (fixed 130px): [hour_spin] [":"] [min_spin]
        time_widget = QWidget()
        time_widget.setFixedWidth(130)
        time_lay = QHBoxLayout(time_widget)
        time_lay.setContentsMargins(0, 0, 0, 0)
        time_lay.setSpacing(2)

        self._hour_spin = QSpinBox()
        self._hour_spin.setRange(0, 23)
        self._hour_spin.setWrapping(True)
        self._hour_spin.setValue(h_init)
        self._hour_spin.setFixedWidth(50)
        self._hour_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)   # B1
        self._hour_spin.setFont(pixel_font(16, mono=True))

        colon_lbl = QLabel(":")
        colon_lbl.setFont(pixel_font(16, bold=True, mono=True))
        colon_lbl.setFixedWidth(8)
        colon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._min_spin = QSpinBox()
        self._min_spin.setRange(0, 59)
        self._min_spin.setWrapping(True)
        self._min_spin.setValue(m_init)
        self._min_spin.setFixedWidth(50)
        self._min_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)    # B1
        self._min_spin.setFont(pixel_font(16, mono=True))

        time_lay.addWidget(self._hour_spin)
        time_lay.addWidget(colon_lbl)
        time_lay.addWidget(self._min_spin)
        layout.addWidget(time_widget)

        # 2. Message line edit (stretch)
        self._message_edit = QLineEdit(alarm_data.get("message", "鬧鐘！"))
        self._message_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)  # B1
        self._message_edit.setPlaceholderText("鬧鐘！")
        layout.addWidget(self._message_edit, 1)

        # 3. Repeat combo (80px)
        self._repeat_combo = QComboBox()
        self._repeat_combo.setFixedWidth(80)
        for rid, rname in _REPEAT_OPTIONS:
            self._repeat_combo.addItem(rname, rid)
        repeat_id = alarm_data.get("repeat", "daily")
        ridx = self._repeat_combo.findData(repeat_id)
        self._repeat_combo.setCurrentIndex(ridx if ridx >= 0 else 1)
        layout.addWidget(self._repeat_combo)

        # 4. Enabled checkbox (24px container)
        chk_container = QWidget()
        chk_container.setFixedWidth(24)
        chk_lay = QHBoxLayout(chk_container)
        chk_lay.setContentsMargins(0, 0, 0, 0)
        chk_lay.setSpacing(0)
        self._enabled_check = QCheckBox()
        self._enabled_check.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._enabled_check.setChecked(alarm_data.get("enabled", True))
        chk_lay.addStretch()
        chk_lay.addWidget(self._enabled_check)
        chk_lay.addStretch()
        layout.addWidget(chk_container)

        # 5. Delete button (24×24)
        self._delete_btn = QPushButton("✕")
        self._delete_btn.setObjectName("DeleteButton")
        self._delete_btn.setFixedSize(24, 24)
        layout.addWidget(self._delete_btn)

        # ── Signal wiring ────────────────────────────────────────────────
        self._hour_spin.valueChanged.connect(lambda _: self.changed.emit())
        self._min_spin.valueChanged.connect(lambda _: self.changed.emit())
        self._message_edit.textChanged.connect(lambda _: self.changed.emit())
        self._repeat_combo.currentIndexChanged.connect(lambda _: self.changed.emit())
        self._enabled_check.stateChanged.connect(lambda _: self.changed.emit())
        self._delete_btn.clicked.connect(self.delete_requested.emit)

    # ── Public API ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return current field values as a dict."""
        h = self._hour_spin.value()
        m = self._min_spin.value()
        return {
            "time": f"{h:02d}:{m:02d}",
            "message": self._message_edit.text().strip() or "鬧鐘！",
            "repeat": self._repeat_combo.currentData() or "daily",
            "enabled": self._enabled_check.isChecked(),
        }

    def set_selected(self, sel: bool):
        """API compatibility with PetCard — alarm cards do not show selection."""
        self._selected = sel
        self.update()

    # ── Events ────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        """Pixel-art border — no selected state (alarm list is not single-select).

        Hover effect: border colour changes to BORDER_HI when mouse is over.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w, h = self.width(), self.height()

        painter.fillRect(0, 0, w, h, QColor(BG_MID))

        pen = QPen(QColor(BORDER_LO), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(1, 1, w - 2, h - 2)

        painter.end()
