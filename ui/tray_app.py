from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt


class TrayApp(QSystemTrayIcon):
    def __init__(self, config_manager, hotkey_manager, timer_engine, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.hotkeys = hotkey_manager
        self.timer = timer_engine

        self._build_icon()
        self._build_menu()
        self._connect_signals()
        self._register_hotkeys()

    def _build_icon(self):
        px = QPixmap(32, 32)
        px.fill(Qt.transparent)
        p = QPainter(px)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4CAF50"))
        p.drawRect(4, 4, 24, 4)
        p.drawRect(8, 8, 16, 4)
        p.drawRect(12, 12, 8, 8)
        p.drawRect(8, 20, 16, 4)
        p.drawRect(4, 24, 24, 4)
        p.end()
        self.setIcon(QIcon(px))

    def _build_menu(self):
        menu = QMenu()
        self._status_action = menu.addAction("無進行中計時")
        self._status_action.setEnabled(False)
        menu.addSeparator()

        settings_action = menu.addAction("設定")
        settings_action.triggered.connect(self._open_settings)
        menu.addSeparator()

        exit_action = menu.addAction("結束")
        exit_action.triggered.connect(self._exit)

        self.setContextMenu(menu)
        self.setToolTip("Pixel Timer")

    def _connect_signals(self):
        self.hotkeys.bridge.hotkey_triggered.connect(self._on_hotkey)
        self.timer.timer_finished.connect(self._on_timer_finished)
        self.timer.timer_tick.connect(self._on_timer_tick)

    def _register_hotkeys(self):
        self.hotkeys.register_from_config(self.config.get_hotkeys())

    def _on_hotkey(self, hotkey_id):
        hk = self.config.get_hotkey(hotkey_id)
        if not hk:
            return

        if self.timer.is_running(hotkey_id):
            self.timer.cancel(hotkey_id)
            self.showMessage(
                "Pixel Timer",
                f"已取消: {hk['message']}",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        else:
            self.timer.start(
                hotkey_id, hk["duration_sec"], hk["message"], hk.get("character", "cat")
            )
            mins, secs = divmod(hk["duration_sec"], 60)
            time_str = f"{mins}分{secs}秒" if secs else f"{mins}分鐘"
            self.showMessage(
                "Pixel Timer",
                f"開始計時: {time_str} — {hk['message']}",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )

    def _on_timer_finished(self, timer_id, message, character):
        self._update_status()
        msg = QMessageBox()
        msg.setWindowTitle("Pixel Timer")
        msg.setText(f"{message}\n\n角色: {character}")
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        msg.exec()

    def _on_timer_tick(self, timer_id, remaining):
        self._update_status()

    def _update_status(self):
        active = self.timer.get_active_timers()
        if active:
            parts = []
            for tid, remaining in active.items():
                hk = self.config.get_hotkey(tid)
                label = hk["message"] if hk else tid
                m, s = divmod(remaining, 60)
                parts.append(f"{label}: {m:02d}:{s:02d}")
            text = " | ".join(parts)
            self._status_action.setText(text)
            self.setToolTip("Pixel Timer\n" + "\n".join(parts))
        else:
            self._status_action.setText("無進行中計時")
            self.setToolTip("Pixel Timer")

    def _open_settings(self):
        self.showMessage(
            "Pixel Timer",
            "設定視窗尚未實作（Phase 2）",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _exit(self):
        self.hotkeys.unregister_all()
        self.timer.cancel_all()
        QApplication.quit()
