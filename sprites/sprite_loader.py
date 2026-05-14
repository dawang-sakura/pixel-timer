"""
SpriteLoader — loads and caches sprite PNGs as QPixmap.
Cache key: (character, state, frame)
Falls back to empty QPixmap if the file is missing.
"""

from PySide6.QtGui import QPixmap

from core.paths import SPRITES_DIR


class SpriteLoader:
    """Loads and caches sprite PNGs as QPixmap."""

    def __init__(self):
        self._cache: dict[tuple, QPixmap] = {}
        self._base_path = SPRITES_DIR

    def load(self, character: str, state: str, frame: int) -> QPixmap:
        """Load sprite. Returns empty QPixmap if file missing."""
        key = (character, state, frame)
        if key in self._cache:
            return self._cache[key]

        file_path = self._base_path / character / f"{state}_{frame}.png"
        if file_path.exists():
            pixmap = QPixmap(str(file_path))
        else:
            print(f"[SpriteLoader] Missing sprite: {file_path}")
            pixmap = QPixmap()

        self._cache[key] = pixmap
        return pixmap

    def preload(self, character: str):
        """Preload all frames for a character into cache."""
        states = ("idle", "counting", "finished")
        frames = (0, 1)
        for state in states:
            for frame in frames:
                self.load(character, state, frame)
