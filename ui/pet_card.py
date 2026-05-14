"""
ui/pet_card.py -- RPG-style card widget for a single pet configuration.

Displays sprite thumbnail + character selector + duration spinbox + message
input in a single horizontal row.  Uses QPainter for pixel-art border instead
of QFrame (R2: avoids QSS background conflicts).
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QSpinBox, QLineEdit, QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QPainter, QColor, QPen

from core.constants import CHARACTER_OPTIONS, CHARACTER_DISPLAY_NAMES
from ui.pixel_theme import (
    pixel_font, BG_MID, BG_LIGHT, BORDER_LO, BORDER_HI, CURSOR_CLR,
)

_CARD_HEIGHT = 60


class PetCard(QWidget):
    """Editable card for one pet entry.

    Signals
    -------
    changed          : emitted on any field edit
    delete_requested : emitted when the ✕ button is clicked
    clicked          : emitted on background click (for CardListView selection)
    """

    changed = Signal()
    delete_requested = Signal()
    clicked = Signal()

    def __init__(self, pet_data: dict, sprite_loader, parent=None):
        super().__init__(parent)
        # R2: disable styled background so paintEvent has full control
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMouseTracking(True)

        self._sprite_loader = sprite_loader
        self._selected = False

        # Pull initial values from pet_data
        self._pet_id: str = pet_data.get("id", "")
        char_id: str = pet_data.get("character", "orange_cat")
        duration: int = pet_data.get("duration_sec", 60)
        message: str = pet_data.get("message", "時間到！")

        self.setFixedHeight(_CARD_HEIGHT)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        # ── Layout ───────────────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # 1. Sprite thumbnail (48×48 QLabel)
        self._sprite_label = QLabel()
        self._sprite_label.setFixedSize(48, 48)
        self._sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._sprite_label)

        # 2. Character combo (100px)
        self._char_combo = QComboBox()
        self._char_combo.setFixedWidth(100)
        for cid in CHARACTER_OPTIONS:
            self._char_combo.addItem(CHARACTER_DISPLAY_NAMES.get(cid, cid), cid)
        # Select current character
        idx = self._char_combo.findData(char_id)
        self._char_combo.setCurrentIndex(idx if idx >= 0 else 0)
        # B1: center displayed text — editable+ReadOnly is the standard PySide trick
        self._char_combo.setEditable(True)
        self._char_combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._char_combo.lineEdit().setReadOnly(True)
        self._char_combo.lineEdit().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(self._char_combo)

        # 3. Duration spinbox (80px)
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 86400)
        self._duration_spin.setValue(duration)
        self._duration_spin.setFixedWidth(80)
        self._duration_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)  # B1
        self._duration_spin.setFont(pixel_font(16, mono=True))
        layout.addWidget(self._duration_spin)

        # 4. Message line edit (stretch)
        self._message_edit = QLineEdit(message)
        self._message_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)   # B1
        self._message_edit.setPlaceholderText("時間到！")
        layout.addWidget(self._message_edit, 1)

        # 5. Delete button (24×24)
        self._delete_btn = QPushButton("✕")
        self._delete_btn.setObjectName("DeleteButton")
        self._delete_btn.setFixedSize(24, 24)
        layout.addWidget(self._delete_btn)

        # ── Initial sprite ────────────────────────────────────────────────
        self._refresh_sprite(char_id)

        # ── Signal wiring ────────────────────────────────────────────────
        self._char_combo.currentIndexChanged.connect(self._on_char_changed)
        self._duration_spin.valueChanged.connect(lambda _: self.changed.emit())
        self._message_edit.textChanged.connect(lambda _: self.changed.emit())
        self._delete_btn.clicked.connect(self.delete_requested.emit)

        # ── Whole-card click (Bug D fix) ──────────────────────────────────
        # Sprite label: transparent to mouse so clicks fall through to card
        self._sprite_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # Input widgets: install event filter so first press also emits clicked
        for child in (self._char_combo, self._duration_spin,
                      self._message_edit, self._delete_btn):
            child.installEventFilter(self)

    # ── Public API ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        """Return current field values as a dict."""
        return {
            "id": self._pet_id,
            "character": self.character_id,
            "duration_sec": self._duration_spin.value(),
            "message": self._message_edit.text().strip() or "時間到！",
        }

    def set_selected(self, sel: bool):
        """Toggle selected state and trigger repaint."""
        self._selected = sel
        self.update()

    @property
    def pet_id(self) -> str:
        return self._pet_id

    @property
    def character_id(self) -> str:
        return self._char_combo.currentData() or "orange_cat"

    @property
    def message(self) -> str:
        return self._message_edit.text().strip()

    # ── Private ───────────────────────────────────────────────────────────

    def _on_char_changed(self):
        self._refresh_sprite(self.character_id)
        self.changed.emit()

    def _refresh_sprite(self, char_id: str):
        if self._sprite_loader is None:
            self._sprite_label.setText("?")
            return
        pm = self._sprite_loader.load(char_id, "idle", 0)
        if pm and not pm.isNull():
            scaled = pm.scaled(
                48, 48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
            self._sprite_label.setPixmap(scaled)
        else:
            self._sprite_label.setText("?")

    # ── Events ────────────────────────────────────────────────────────────

    def eventFilter(self, watched, event):
        """Emit clicked when any child widget is pressed, without blocking the child."""
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.clicked.emit()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        """Emit clicked only when pressing the card background (not a child widget).

        R6: childAt returns non-None for child widgets, so we skip emit in
        those cases and let Qt route the event naturally.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if self.childAt(event.pos()) is None:
                self.clicked.emit()
                event.accept()
                return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        """Pixel-art double-border card background.

        Normal : outer BORDER_LO (2px), fill BG_MID
        Selected: outer CURSOR_CLR (2px), fill BG_LIGHT + left 4px cursor bar
        """
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

            w, h = self.width(), self.height()

            # Background fill
            fill = QColor(BG_LIGHT) if self._selected else QColor(BG_MID)
            painter.fillRect(0, 0, w, h, fill)

            # Outer border 2px
            border_clr = QColor(CURSOR_CLR) if self._selected else QColor(BORDER_LO)
            pen = QPen(border_clr, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(1, 1, w - 2, h - 2)

            # Selected: left 4px gold cursor bar
            if self._selected:
                painter.fillRect(0, 0, 4, h, QColor(CURSOR_CLR))
        finally:
            painter.end()
