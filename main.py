import sys
from PySide6.QtWidgets import QApplication
from core.config_manager import ConfigManager
from core.timer_engine import TimerEngine
from ui.tray_app import TrayApp


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Pixel Timer")

    config = ConfigManager()
    timer = TimerEngine()
    tray = TrayApp(config, timer)
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
