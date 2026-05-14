"""
ui/card_list_view.py -- Generic scrollable card list with optional single-selection.

Manages a vertical list of QWidget cards inside a QScrollArea.
Selection is managed by the container (not by individual cards).

Note: external callers must not connect to ``card.clicked`` directly; CardListView
manages that signal internally via _wire_card / _rewire_all.
"""

from __future__ import annotations

from typing import Iterator

from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPainter, QColor

from ui.pixel_theme import BG_DEEP


class _CheckerWidget(QWidget):
    """Inner container that paints the orange checker pattern as its background.

    The checker matches SettingsWindow's outer-frame pattern (BG_DEEP +
    #E8961E, 8px tile), so cards visually sit on the same backdrop instead of
    the cream content fill.
    """

    _TILE = 8
    _C1 = BG_DEEP        # #F5A623 warm orange
    _C2 = "#E8961E"      # darker orange

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            w, h = self.width(), self.height()
            c1 = QColor(self._C1)
            c2 = QColor(self._C2)
            tile = self._TILE
            for ty in range(0, h, tile):
                for tx in range(0, w, tile):
                    painter.fillRect(
                        tx, ty, tile, tile,
                        c1 if (tx // tile + ty // tile) % 2 == 0 else c2,
                    )
        finally:
            painter.end()


class CardListView(QScrollArea):
    """Scrollable list of card widgets with optional single-selection support.

    Parameters
    ----------
    selectable : bool
        If True, connects each card's ``clicked`` signal (if present) to
        the internal selection mechanism and emits ``selection_changed``.
    """

    selection_changed = Signal(int)   # new selected index; -1 = none
    card_removed = Signal(int)        # index of removed card (before removal)

    def __init__(self, *, selectable: bool = True,
                 card_height: int | None = None, max_visible: int = 3,
                 parent=None):
        super().__init__(parent)
        self._selectable = selectable
        self._cards: list[QWidget] = []
        self._selected_idx: int = -1
        self._card_h = card_height          # None = legacy fixed-height mode (caller sets size)
        self._max_visible = max_visible
        self._footer: QWidget | None = None

        # Scroll area settings
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Transparent QScrollArea frame + viewport — let inner _CheckerWidget paint the bg
        self.setStyleSheet("CardListView { background: transparent; border: 2px solid #C8A96E; }")
        self.viewport().setAutoFillBackground(False)

        # Inner container draws the checker pattern itself (does not rely on transparency chain)
        self._container = _CheckerWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(2, 2, 2, 2)
        # NOTE: no trailing stretch in dynamic-height mode — list height is fit to cards.
        # In legacy fixed-height mode caller decides; we keep top-aligned by default.
        if self._card_h is None:
            self._layout.addStretch(1)

        self.setWidget(self._container)

        self._update_dynamic_height()

    def set_footer(self, widget: QWidget):
        """Embed a widget at the bottom of the list, inside the same border frame.

        Used so an action button (e.g. 新增) sits flush against the cards with
        no gap and no border conflict — they share the QScrollArea's outer
        border and the checker background.
        """
        if self._footer is not None:
            self._layout.removeWidget(self._footer)
            self._footer.setParent(None)
            self._footer.deleteLater()
        self._footer = widget
        # Append at the very end (after cards, after the stretch in legacy mode)
        self._layout.addWidget(widget)
        self._update_dynamic_height()

    # ── Public API ────────────────────────────────────────────────────────

    def add_card(self, card: QWidget) -> int:
        """Append a card. Returns the new card's index."""
        idx = len(self._cards)
        self._cards.append(card)
        # Insert before the trailing stretch
        self._layout.insertWidget(idx, card)
        self._wire_card(card)
        self._update_dynamic_height()
        return idx

    def insert_card(self, index: int, card: QWidget):
        """Insert a card at position ``index``."""
        self._cards.insert(index, card)
        self._layout.insertWidget(index, card)
        # Rewire all cards to get correct index closures
        self._rewire_all()
        # Adjust selected index
        if self._selected_idx >= index:
            self._selected_idx += 1
        self._update_dynamic_height()

    def remove_card(self, index: int):
        """Remove card at ``index``. Emits ``card_removed`` before removal."""
        if index < 0 or index >= len(self._cards):
            return
        self.card_removed.emit(index)
        card = self._cards[index]
        # Disconnect the slot we own before destroying the widget
        self._unwire_card(card)
        self._layout.removeWidget(card)
        card.setParent(None)
        card.deleteLater()
        self._cards.pop(index)

        # Update selection bookkeeping
        if self._selected_idx == index:
            self._selected_idx = -1
            self.selection_changed.emit(-1)
        elif self._selected_idx > index:
            self._selected_idx -= 1

        # Rewire remaining cards (index closures are stale)
        self._rewire_all()
        self._update_dynamic_height()

    def remove_selected(self) -> int:
        """Remove the currently selected card. Returns its former index, -1 if none."""
        idx = self._selected_idx
        if idx < 0:
            return -1
        self.remove_card(idx)
        return idx

    def set_cards(self, cards: list):
        """Replace the entire list with ``cards``."""
        self.clear()
        for card in cards:
            self.add_card(card)

    def clear(self):
        """Remove all cards."""
        for card in list(self._cards):
            self._unwire_card(card)
            self._layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self._selected_idx = -1
        self._update_dynamic_height()

    def card_count(self) -> int:
        return len(self._cards)

    def card_at(self, index: int) -> QWidget | None:
        if 0 <= index < len(self._cards):
            return self._cards[index]
        return None

    def index_of(self, card: QWidget) -> int:
        """Return the index of ``card``, or -1 if not found."""
        try:
            return self._cards.index(card)
        except ValueError:
            return -1

    def iter_cards(self) -> Iterator[QWidget]:
        """Iterate over cards in order."""
        return iter(self._cards)

    @property
    def selected_index(self) -> int:
        return self._selected_idx

    @property
    def selected_card(self) -> QWidget | None:
        if self._selected_idx >= 0:
            return self._cards[self._selected_idx]
        return None

    def select_index(self, index: int):
        """Programmatically select card at ``index`` (-1 to deselect).

        Guard against re-emitting if already selected (R3: prevents signal loops).
        """
        if index == self._selected_idx:
            return
        old_idx = self._selected_idx
        self._selected_idx = index

        # Deselect old
        if 0 <= old_idx < len(self._cards):
            card = self._cards[old_idx]
            if hasattr(card, "set_selected"):
                card.set_selected(False)

        # Select new
        if 0 <= index < len(self._cards):
            card = self._cards[index]
            if hasattr(card, "set_selected"):
                card.set_selected(True)

        self.selection_changed.emit(index)

    # ── Internal ─────────────────────────────────────────────────────────

    def _wire_card(self, card: QWidget):
        """Connect card's ``clicked`` signal to our handler and store the slot ref."""
        if self._selectable and hasattr(card, "clicked"):
            slot = lambda c=card: self._on_card_clicked(c)
            card._listview_slot = slot      # keep ref so we can disconnect precisely
            card.clicked.connect(slot)

    def _unwire_card(self, card: QWidget):
        """Disconnect only the slot we connected in _wire_card, leaving others intact."""
        if self._selectable and hasattr(card, "clicked"):
            slot = getattr(card, "_listview_slot", None)
            if slot is not None:
                try:
                    card.clicked.disconnect(slot)
                except RuntimeError:
                    pass
                card._listview_slot = None

    def _rewire_all(self):
        """Rewire all cards (called after index shifts from insert/remove)."""
        if not self._selectable:
            return
        for card in self._cards:
            if hasattr(card, "clicked"):
                self._unwire_card(card)
                self._wire_card(card)

    def _on_card_clicked(self, card: QWidget):
        """Handle card click — find its index and update selection."""
        try:
            new_idx = self._cards.index(card)
        except ValueError:
            return
        self.select_index(new_idx)

    def _update_dynamic_height(self):
        """Resize self to fit card count (clamped to max_visible) + footer.

        In legacy fixed-height mode (card_height=None), this is a no-op so
        callers can still setFixedHeight() externally.
        """
        if self._card_h is None:
            return
        # Always show at least 1 row's worth of space so empty lists don't collapse.
        n = max(1, min(len(self._cards), self._max_visible))
        spacing = self._layout.spacing()
        m = self._layout.contentsMargins()
        inner_h = n * self._card_h + max(0, n - 1) * spacing + m.top() + m.bottom()
        # Footer (if any) sits inside the same border frame
        if self._footer is not None:
            inner_h += self._footer.sizeHint().height() + spacing
        # 2px stylesheet border on each side
        border = 2 * 2
        self.setFixedHeight(inner_h + border)
