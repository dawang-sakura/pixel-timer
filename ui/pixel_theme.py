from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

_FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts"

BG_DEEP = "#F5A623"      # Warm orange — window frame background
BG_MID = "#FFF8E7"       # Cream — content area / inputs
BG_LIGHT = "#FFE4B5"     # Moccasin — hover / alternate rows
BORDER_HI = "#D4820A"    # Deep golden-orange — primary border
BORDER_LO = "#C8A96E"    # Tan — secondary border
TEXT = "#3E2723"          # Dark brown — primary text
TEXT_DIM = "#8D6E63"      # Medium brown — secondary text
CURSOR_CLR = "#E64A19"   # Deep orange-red — cursor / selection
ACCENT_G = "#43A047"     # Green accent
ACCENT_R = "#E53935"     # Red accent
ACCENT_B = "#1E88E5"     # Blue accent

_font_prop = ""
_font_mono = ""
_fonts_loaded = False


def _load_fonts():
    global _font_prop, _font_mono, _fonts_loaded
    if _fonts_loaded:
        return
    _fonts_loaded = True
    for filename, attr in [
        ("ark-pixel-12px-proportional-zh_tw.ttf", "_font_prop"),
        ("ark-pixel-12px-monospaced-zh_tw.ttf", "_font_mono"),
    ]:
        path = _FONTS_DIR / filename
        if not path.exists():
            continue
        fid = QFontDatabase.addApplicationFont(str(path))
        if fid < 0:
            continue
        families = QFontDatabase.applicationFontFamilies(fid)
        if families:
            globals()[attr] = families[0]


def pixel_font(size=16, bold=False, mono=False):
    family = _font_mono if mono else _font_prop
    f = QFont(family or "Consolas")
    f.setPixelSize(size)
    f.setBold(bold)
    f.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return f


def apply_theme(app: QApplication):
    _load_fonts()
    app.setFont(pixel_font(16))

    p = QPalette()
    c = QColor
    p.setColor(QPalette.ColorRole.Window, c(BG_DEEP))
    p.setColor(QPalette.ColorRole.WindowText, c(TEXT))
    p.setColor(QPalette.ColorRole.Base, c(BG_MID))
    p.setColor(QPalette.ColorRole.AlternateBase, c(BG_LIGHT))
    p.setColor(QPalette.ColorRole.Text, c(TEXT))
    p.setColor(QPalette.ColorRole.Button, c(BG_MID))
    p.setColor(QPalette.ColorRole.ButtonText, c(TEXT))
    p.setColor(QPalette.ColorRole.BrightText, c(CURSOR_CLR))
    p.setColor(QPalette.ColorRole.Highlight, c(CURSOR_CLR))
    p.setColor(QPalette.ColorRole.HighlightedText, c(BG_MID))
    p.setColor(QPalette.ColorRole.ToolTipBase, c(BG_MID))
    p.setColor(QPalette.ColorRole.ToolTipText, c(TEXT))
    p.setColor(QPalette.ColorRole.PlaceholderText, c(TEXT_DIM))
    p.setColor(QPalette.ColorRole.Link, c(ACCENT_B))
    p.setColor(QPalette.ColorRole.Light, c(BORDER_HI))
    p.setColor(QPalette.ColorRole.Dark, c(BORDER_LO))
    p.setColor(QPalette.ColorRole.Mid, c(BG_LIGHT))
    p.setColor(QPalette.ColorRole.Shadow, c("#5D4037"))
    app.setPalette(p)
    app.setStyleSheet(_QSS)


_QSS = f"""
QPushButton {{
    background-color: {BG_MID};
    color: {TEXT};
    border: 2px solid {BORDER_LO};
    padding: 6px 16px;
    min-height: 20px;
    font-weight: bold;
}}
QPushButton:hover {{
    border-color: {BORDER_HI};
    background-color: {BG_LIGHT};
}}
QPushButton:pressed {{
    background-color: {CURSOR_CLR};
    border-color: {BORDER_HI};
    color: {BG_MID};
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
    border-color: #D4C4A0;
}}

QTableWidget {{
    background-color: {BG_MID};
    alternate-background-color: {BG_LIGHT};
    border: 2px solid {BORDER_LO};
    gridline-color: {BORDER_LO};
    color: {TEXT};
    selection-background-color: {CURSOR_CLR};
    selection-color: {BG_MID};
}}
QHeaderView::section {{
    background-color: {BG_LIGHT};
    color: {TEXT};
    border: 1px solid {BORDER_LO};
    padding: 4px;
}}

QComboBox {{
    background-color: {BG_MID};
    color: {TEXT};
    border: 2px solid {BORDER_LO};
    padding: 4px 8px;
}}
QComboBox:hover {{
    border-color: {BORDER_HI};
}}
QComboBox::drop-down {{
    border: none;
    background-color: {BG_LIGHT};
    width: 20px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {TEXT};
    width: 0; height: 0;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_MID};
    color: {TEXT};
    border: 2px solid {BORDER_LO};
    selection-background-color: {CURSOR_CLR};
    selection-color: {BG_MID};
}}

QLineEdit {{
    background-color: {BG_MID};
    color: {TEXT};
    border: 2px solid {BORDER_LO};
    padding: 4px;
}}
QLineEdit:focus {{
    border-color: {BORDER_HI};
}}

QSpinBox {{
    background-color: {BG_MID};
    color: {TEXT};
    border: 2px solid {BORDER_LO};
    padding: 2px 4px;
}}
QSpinBox:focus {{
    border-color: {BORDER_HI};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {BG_LIGHT};
    border: 1px solid {BORDER_LO};
    width: 16px;
}}
QSpinBox::up-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 6px solid {TEXT};
    width: 0; height: 0;
}}
QSpinBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {TEXT};
    width: 0; height: 0;
}}

QCheckBox {{
    color: {TEXT};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {BORDER_LO};
    background-color: {BG_MID};
}}
QCheckBox::indicator:checked {{
    background-color: {CURSOR_CLR};
    border-color: {BORDER_HI};
}}

QScrollBar:vertical {{
    background: {BG_LIGHT};
    width: 12px;
    border: 1px solid {BORDER_LO};
}}
QScrollBar::handle:vertical {{
    background: {BORDER_HI};
    border: 1px solid {BORDER_LO};
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {BG_LIGHT};
    height: 12px;
    border: 1px solid {BORDER_LO};
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_HI};
    border: 1px solid {BORDER_LO};
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QToolTip {{
    background-color: {BG_MID};
    color: {TEXT};
    border: 2px solid {BORDER_LO};
    padding: 4px;
}}

QMenu {{
    background-color: {BG_MID};
    color: {TEXT};
    border: 2px solid {BORDER_LO};
}}
QMenu::item:selected {{
    background-color: {CURSOR_CLR};
    color: {BG_MID};
}}

QDialog {{
    background-color: {BG_DEEP};
}}

QMessageBox {{
    background-color: {BG_MID};
}}
QMessageBox QLabel {{
    color: {TEXT};
}}

QLabel {{
    color: {TEXT};
    background: transparent;
}}

QStackedWidget > QWidget {{
    background-color: {BG_MID};
}}
"""
