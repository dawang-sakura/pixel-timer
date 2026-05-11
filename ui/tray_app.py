from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QPoint

from ui.settings_window import SettingsWindow
from ui.pet_widget import PetWidget
from ui.notification_window import NotificationWindow
from sprites.sprite_loader import SpriteLoader
from sprites.animation import PetAnimator


class TrayApp(QSystemTrayIcon):
    def __init__(self, config_manager, timer_engine, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.timer = timer_engine
        self._settings_win = None
        self._pets = []           # list of (PetWidget, PetAnimator)
        self._notifications = []  # keep references alive until dismissed
        self._sprite_loader = SpriteLoader()
        self._pets_visible = True

        self._build_icon()
        self._build_menu()
        self._connect_signals()
        self._create_pets()

    # ------------------------------------------------------------------ icon

    def _build_icon(self):
        px = QPixmap(32, 32)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#4CAF50"))
        p.drawRect(4, 4, 24, 4)
        p.drawRect(8, 8, 16, 4)
        p.drawRect(12, 12, 8, 8)
        p.drawRect(8, 20, 16, 4)
        p.drawRect(4, 24, 24, 4)
        p.end()
        self.setIcon(QIcon(px))

    # ------------------------------------------------------------------ menu

    def _build_menu(self):
        menu = QMenu()

        self._status_action = menu.addAction("無進行中計時")
        self._status_action.setEnabled(False)
        menu.addSeparator()

        self._toggle_pets_action = menu.addAction("隱藏桌寵")
        self._toggle_pets_action.triggered.connect(self._toggle_pets_visibility)

        settings_action = menu.addAction("設定")
        settings_action.triggered.connect(self._open_settings)
        menu.addSeparator()

        exit_action = menu.addAction("結束")
        exit_action.triggered.connect(self._exit)

        self.setContextMenu(menu)
        self.setToolTip("Pixel Timer")

    # ------------------------------------------------------------------ signals

    def _connect_signals(self):
        self.timer.timer_finished.connect(self._on_timer_finished)
        self.timer.timer_tick.connect(self._on_timer_tick)

    # ------------------------------------------------------------------ pets

    def _create_pets(self):
        # Destroy existing
        for widget, animator in self._pets:
            animator.stop()
            widget.close()
            widget.deleteLater()
        self._pets.clear()
        PetWidget._auto_position_index = 0

        for pet_cfg in self.config.get_pets():
            character = pet_cfg.get("character", "cat")
            self._sprite_loader.preload(character)

            animator = PetAnimator(self._sprite_loader, character)
            widget = PetWidget(pet_cfg, animator)

            widget.timer_toggled.connect(self._on_pet_timer_toggled)
            widget.position_changed.connect(self._on_pet_position_changed)

            animator.start()

            if self._pets_visible:
                widget.show()

            self._pets.append((widget, animator))

    def _find_pet(self, pet_id: str):
        for widget, animator in self._pets:
            if widget.pet_id == pet_id:
                return widget, animator
        return None, None

    # ------------------------------------------------------------------ pet callbacks

    def _on_pet_timer_toggled(self, pet_id: str):
        widget, animator = self._find_pet(pet_id)
        if widget is None:
            return

        if self.timer.is_running(pet_id):
            self.timer.cancel(pet_id)
            animator.set_state("idle")
            widget.set_counting(False)
        else:
            pet_cfg = self.config.get_pet(pet_id)
            if not pet_cfg:
                return
            self.timer.start(
                pet_id,
                pet_cfg["duration_sec"],
                pet_cfg.get("message", "時間到！"),
                pet_cfg.get("character", "cat"),
            )
            animator.set_state("counting")
            widget.set_counting(True)

    def _on_pet_position_changed(self, pet_id: str, x: int, y: int):
        self.config.update_pet_position(pet_id, x, y)

    # ------------------------------------------------------------------ timer callbacks

    def _on_timer_finished(self, timer_id: str, message: str, character: str):
        self._update_status()

        widget, animator = self._find_pet(timer_id)
        if animator:
            animator.set_state("finished")
        if widget:
            widget.set_counting(False)

        if widget:
            pet_pos = widget.pos()
        else:
            pet_pos = QPoint(100, 100)

        notif = NotificationWindow(message, character, pet_pos)
        self._notifications.append(notif)
        notif.dismissed.connect(lambda tid=timer_id, n=notif: self._on_notification_closed(tid, n))
        notif.show()

    def _on_notification_closed(self, timer_id: str, notif):
        if notif in self._notifications:
            self._notifications.remove(notif)
        notif.deleteLater()
        if not self.timer.is_running(timer_id):
            _, animator = self._find_pet(timer_id)
            if animator:
                animator.set_state("idle")

    def _on_timer_tick(self, timer_id: str, remaining: int):
        self._update_status()
        widget, _ = self._find_pet(timer_id)
        if widget:
            widget.set_tooltip_remaining(remaining)

    # ------------------------------------------------------------------ status

    def _update_status(self):
        active = self.timer.get_active_timers()
        if active:
            parts = []
            for tid, remaining in active.items():
                pet_cfg = self.config.get_pet(tid)
                label = pet_cfg.get("message", tid) if pet_cfg else tid
                m, s = divmod(remaining, 60)
                parts.append(f"{label}: {m:02d}:{s:02d}")
            text = " | ".join(parts)
            self._status_action.setText(text)
            self.setToolTip("Pixel Timer\n" + "\n".join(parts))
        else:
            self._status_action.setText("無進行中計時")
            self.setToolTip("Pixel Timer")

    # ------------------------------------------------------------------ visibility toggle

    def _toggle_pets_visibility(self):
        self._pets_visible = not self._pets_visible
        for widget, _ in self._pets:
            if self._pets_visible:
                widget.show()
            else:
                widget.hide()
        self._toggle_pets_action.setText(
            "隱藏桌寵" if self._pets_visible else "顯示桌寵"
        )

    # ------------------------------------------------------------------ settings

    def _open_settings(self):
        if self._settings_win is not None and self._settings_win.isVisible():
            self._settings_win.raise_()
            self._settings_win.activateWindow()
            return
        self._settings_win = SettingsWindow(self.config)
        self._settings_win.settings_changed.connect(self._on_settings_changed)
        self._settings_win.show()

    def _on_settings_changed(self):
        # Cancel any running timers for pets that may be removed
        active_ids = list(self.timer.get_active_timers().keys())
        for tid in active_ids:
            self.timer.cancel(tid)
        self._create_pets()

    # ------------------------------------------------------------------ exit

    def _exit(self):
        active_ids = list(self.timer.get_active_timers().keys())
        for tid in active_ids:
            self.timer.cancel(tid)
        for widget, animator in self._pets:
            animator.stop()
            widget.close()
            widget.deleteLater()
        self._pets.clear()
        QApplication.quit()
