import sys
from PySide6.QtWidgets import QApplication
from core.config_manager import ConfigManager
from core.timer_engine import TimerEngine
from core.alarm_engine import AlarmEngine
from ui.tray_app import TrayApp


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Pixel Timer")

    config = ConfigManager()
    timer = TimerEngine()
    alarm = AlarmEngine(config)
    tray = TrayApp(config, timer, alarm)
    tray.show()
    alarm.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
