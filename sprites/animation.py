"""
PetAnimator — animation state machine for a single pet character.

States and frame intervals:
  idle     -> 800ms per frame  (relaxed breathing)
  counting -> 400ms per frame  (faster pulse while timer is running)
  finished -> 300ms per frame  (quick jump celebration)

Usage:
    loader = SpriteLoader()
    animator = PetAnimator(loader, "cat")
    animator.frame_changed.connect(my_label.setPixmap)
    animator.set_state("idle")
    animator.start()
"""

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QPixmap

from sprites.sprite_loader import SpriteLoader

_INTERVALS = {
    "idle": 800,
    "counting": 400,
    "finished": 300,
}


class PetAnimator(QObject):
    frame_changed = Signal(QPixmap)

    STATES = ("idle", "counting", "finished")
    FRAME_COUNT = 2

    def __init__(self, sprite_loader: SpriteLoader, character: str, parent=None):
        super().__init__(parent)
        self._loader = sprite_loader
        self._character = character
        self._state = "idle"
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_state(self, state: str):
        """Switch animation state. Resets frame to 0."""
        if state not in _INTERVALS:
            raise ValueError(f"Unknown state '{state}'. Valid: {list(_INTERVALS)}")
        self._state = state
        self._frame = 0
        self._timer.setInterval(_INTERVALS[state])
        # Emit immediately so the UI updates without waiting for the first tick
        self.frame_changed.emit(self.current_pixmap())

    def start(self):
        """Start animation loop."""
        self._timer.setInterval(_INTERVALS[self._state])
        self._timer.start()

    def stop(self):
        """Stop animation loop."""
        self._timer.stop()

    def current_pixmap(self) -> QPixmap:
        """Get current frame's pixmap."""
        return self._loader.load(self._character, self._state, self._frame)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _next_frame(self):
        """Advance to next frame and emit signal."""
        self._frame = (self._frame + 1) % self.FRAME_COUNT
        self.frame_changed.emit(self.current_pixmap())
