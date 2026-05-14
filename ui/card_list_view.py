"""
ui/card_list_view.py -- Generic scrollable card list with optional single-selection.

Manages a vertical list of QWidget cards inside a QScrollArea.
Selection is managed by the container (not by individual cards).
"""

from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout,
)
from PySide6.QtCore import Signal, Qt


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

    def __init__(self, *, selectable: bool = True, parent=None):
        super().__init__(parent)
        self._selectable = selectable
        self._cards: list[QWidget] = []
        self._selected_idx: int = -1

        # Scroll area settings
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Inner container
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.addStretch(1)   # R1: stretch at tail keeps cards top-aligned

        self.setWidget(self._container)

    # ── Public API ────────────────────────────────────────────────────────

    def add_card(self, card: QWidget) -> int:
        """Append a card. Returns the new card's index."""
        idx = len(self._cards)
        self._cards.append(card)
        # Insert before the trailing stretch
        self._layout.insertWidget(idx, card)
        self._wire_card(card, idx)
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

    def remove_card(self, index: int):
        """Remove card at ``index``. Emits ``card_removed`` before removal."""
        if index < 0 or index >= len(self._cards):
            return
        self.card_removed.emit(index)
        card = self._cards[index]
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
            self._layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self._selected_idx = -1

    def card_count(self) -> int:
        return len(self._cards)

    def card_at(self, index: int) -> QWidget | None:
        if 0 <= index < len(self._cards):
            return self._cards[index]
        return None

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

    def _wire_card(self, card: QWidget, idx: int):
        """Connect card's ``clicked`` signal if selectable."""
        if self._selectable and hasattr(card, "clicked"):
            card.clicked.connect(lambda c=card: self._on_card_clicked(c))

    def _rewire_all(self):
        """Rewire all cards (called after index shifts from insert/remove)."""
        if not self._selectable:
            return
        for card in self._cards:
            if hasattr(card, "clicked"):
                try:
                    card.clicked.disconnect()
                except RuntimeError:
                    pass
                card.clicked.connect(lambda c=card: self._on_card_clicked(c))

    def _on_card_clicked(self, card: QWidget):
        """Handle card click — find its index and update selection."""
        try:
            new_idx = self._cards.index(card)
        except ValueError:
            return
        self.select_index(new_idx)
