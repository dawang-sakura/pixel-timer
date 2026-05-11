from PySide6.QtWidgets import QWidget, QLabel, QMenu, QApplication
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap


class PetWidget(QWidget):
    timer_toggled = Signal(str)       # pet_id
    position_changed = Signal(str, int, int)  # pet_id, x, y

    # Class-level counter for auto-positioning
    _auto_position_index = 0

    def __init__(self, pet_config: dict, animator, parent=None):
        super().__init__(parent)

        self._pet_id = pet_config["id"]
        self._animator = animator
        self._drag_pos = None
        self._drag_started_pos = None
        self._counting = False

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(48, 48)

        # Sprite label
        self._label = QLabel(self)
        self._label.setGeometry(0, 0, 48, 48)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Connect animator frames
        self._animator.frame_changed.connect(self.update_frame)

        # Set initial pixmap if available
        initial = self._animator.current_pixmap()
        if initial and not initial.isNull():
            self._label.setPixmap(initial)

        # Position
        pos = pet_config.get("position", {"x": -1, "y": -1})
        if pos.get("x", -1) == -1 or pos.get("y", -1) == -1:
            self._auto_place()
        else:
            self.move(pos["x"], pos["y"])

    def _auto_place(self):
        screen = QApplication.primaryScreen()
        geom = screen.availableGeometry()
        idx = PetWidget._auto_position_index
        PetWidget._auto_position_index += 1

        # Stack horizontally from bottom-right, 60px spacing
        spacing = 60
        x = geom.right() - 48 - (idx * spacing)
        y = geom.bottom() - 48
        self.move(x, y)

    # --- Mouse events ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_started_pos = event.globalPosition().toPoint()
            self._drag_pos = self._drag_started_pos - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            end_pos = event.globalPosition().toPoint()
            if self._drag_started_pos and end_pos != self._drag_started_pos:
                new_pos = self.frameGeometry().topLeft()
                self.position_changed.emit(self._pet_id, new_pos.x(), new_pos.y())
            self._drag_pos = None
            self._drag_started_pos = None
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.timer_toggled.emit(self._pet_id)
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        if self._counting:
            cancel_action = menu.addAction("取消計時")
            cancel_action.triggered.connect(lambda: self.timer_toggled.emit(self._pet_id))
        hide_action = menu.addAction("隱藏")
        hide_action.triggered.connect(self.hide)
        menu.exec(event.globalPos())

    # --- Public API ---

    def update_frame(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            self._label.setPixmap(pixmap.scaled(
                48, 48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            ))

    def set_tooltip_remaining(self, remaining_sec: int):
        m, s = divmod(remaining_sec, 60)
        self.setToolTip(f"剩餘 {m:02d}:{s:02d}")

    def set_counting(self, counting: bool):
        self._counting = counting
        if not counting:
            self.setToolTip("")

    @property
    def pet_id(self) -> str:
        return self._pet_id
