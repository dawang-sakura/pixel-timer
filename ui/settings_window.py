import uuid

from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QStyledItemDelegate, QLineEdit,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence

import ctypes
import ctypes.wintypes

HOTKEY_COLUMNS = ["快捷鍵", "秒數", "訊息", "角色"]
CHARACTER_OPTIONS = ["cat", "dog", "goblin"]

CORNER_OPTIONS = [
    ("右下", "bottom_right"),
    ("左下", "bottom_left"),
    ("右上", "top_right"),
    ("左上", "top_left"),
]


_KNOWN_SYSTEM_HOTKEYS = {
    "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z", "ctrl+y", "ctrl+a", "ctrl+s",
    "ctrl+shift+esc", "ctrl+alt+delete", "alt+tab", "alt+f4", "alt+space",
    "ctrl+alt+del",
    "win+e", "win+r", "win+d", "win+l", "win+i", "win+s", "win+a",
    "win+tab", "win+x", "win+g", "win+h", "win+k", "win+p", "win+v",
    "win+shift+s", "win+ctrl+d", "win+ctrl+f4",
    "ctrl+shift+t", "ctrl+shift+n", "ctrl+w", "ctrl+t", "ctrl+n",
    "f1", "f5", "f11", "alt+enter",
    "print screen", "alt+print screen",
}

_VK_MAP = {
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45,
    "f": 0x46, "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A,
    "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F,
    "p": 0x50, "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54,
    "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59, "z": 0x5A,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "space": 0x20, "enter": 0x0D, "tab": 0x09, "esc": 0x1B,
    "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "page up": 0x21, "page down": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004


def _check_hotkey_conflict(key_str):
    normalized = key_str.strip().lower()
    if normalized in _KNOWN_SYSTEM_HOTKEYS:
        return f"與 Windows 系統快捷鍵衝突"

    parts = [p.strip() for p in normalized.split("+")]
    modifiers = 0
    vk = None
    for p in parts:
        if p == "ctrl":
            modifiers |= MOD_CONTROL
        elif p == "shift":
            modifiers |= MOD_SHIFT
        elif p == "alt":
            modifiers |= MOD_ALT
        elif p in _VK_MAP:
            vk = _VK_MAP[p]
        else:
            return None

    if vk is None:
        return None

    user32 = ctypes.windll.user32
    hotkey_id = 0xBFFF
    if user32.RegisterHotKey(None, hotkey_id, modifiers, vk):
        user32.UnregisterHotKey(None, hotkey_id)
        return None
    else:
        return "已被其他程式佔用（RegisterHotKey 失敗）"


_QT_KEY_MAP = {
    Qt.Key_Space: "space", Qt.Key_Return: "enter", Qt.Key_Enter: "enter",
    Qt.Key_Escape: "esc", Qt.Key_Tab: "tab", Qt.Key_Backspace: "backspace",
    Qt.Key_Delete: "delete", Qt.Key_Insert: "insert",
    Qt.Key_Home: "home", Qt.Key_End: "end",
    Qt.Key_PageUp: "page up", Qt.Key_PageDown: "page down",
    Qt.Key_Up: "up", Qt.Key_Down: "down", Qt.Key_Left: "left", Qt.Key_Right: "right",
    Qt.Key_F1: "f1", Qt.Key_F2: "f2", Qt.Key_F3: "f3", Qt.Key_F4: "f4",
    Qt.Key_F5: "f5", Qt.Key_F6: "f6", Qt.Key_F7: "f7", Qt.Key_F8: "f8",
    Qt.Key_F9: "f9", Qt.Key_F10: "f10", Qt.Key_F11: "f11", Qt.Key_F12: "f12",
}

_MODIFIER_KEYS = {
    Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta,
    Qt.Key_AltGr, Qt.Key_Super_L, Qt.Key_Super_R,
}


class HotkeyRecorder(QLineEdit):
    recorded = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("按下快捷鍵組合...")
        self.setAlignment(Qt.AlignCenter)
        self._combo = ""

    def keyPressEvent(self, event):
        key = event.key()
        if key in _MODIFIER_KEYS:
            return

        parts = []
        mods = event.modifiers()
        if mods & Qt.ControlModifier:
            parts.append("ctrl")
        if mods & Qt.ShiftModifier:
            parts.append("shift")
        if mods & Qt.AltModifier:
            parts.append("alt")

        if key in _QT_KEY_MAP:
            parts.append(_QT_KEY_MAP[key])
        else:
            name = QKeySequence(key).toString().lower()
            if name:
                parts.append(name)

        if parts and any(p not in ("ctrl", "shift", "alt") for p in parts):
            self._combo = "+".join(parts)
            self.setText(self._combo)
            self.recorded.emit(self._combo)

    def combo(self):
        return self._combo


class HotkeyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return HotkeyRecorder(parent)

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole) or ""
        editor.setText(value)
        editor._combo = value

    def setModelData(self, editor, model, index):
        if editor.combo():
            model.setData(index, editor.combo(), Qt.EditRole)


class CharacterDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(CHARACTER_OPTIONS)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        idx = editor.findText(value)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)


class SettingsWindow(QDialog):
    settings_changed = Signal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager

        self.setWindowTitle("Pixel Timer 設定")
        self.setMinimumSize(520, 400)

        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_hotkey_tab(), "熱鍵")
        self._tabs.addTab(self._build_general_tab(), "一般")
        self._tabs.addTab(self._build_about_tab(), "關於")
        root_layout.addWidget(self._tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_save = QPushButton("儲存")
        self.btn_cancel = QPushButton("取消")

        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)

        root_layout.addLayout(btn_row)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)

    def _build_hotkey_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.hotkey_table = QTableWidget(0, 4)
        self.hotkey_table.setHorizontalHeaderLabels(HOTKEY_COLUMNS)
        self.hotkey_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.hotkey_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._hotkey_delegate = HotkeyDelegate(self.hotkey_table)
        self.hotkey_table.setItemDelegateForColumn(0, self._hotkey_delegate)
        self.hotkey_table.setItemDelegateForColumn(3, CharacterDelegate(self.hotkey_table))

        for hk in self.config.get_hotkeys():
            self._add_hotkey_row(hk)

        layout.addWidget(self.hotkey_table)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("新增")
        btn_delete = QPushButton("刪除")
        btn_add.clicked.connect(self._on_add_hotkey)
        btn_delete.clicked.connect(self._on_delete_hotkey)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return tab

    def _add_hotkey_row(self, hk_data=None):
        row = self.hotkey_table.rowCount()
        self.hotkey_table.insertRow(row)

        if hk_data is None:
            hk_data = {
                "id": f"preset_{uuid.uuid4().hex[:8]}",
                "key": "",
                "duration_sec": 60,
                "message": "時間到！",
                "character": "cat",
            }

        item_key = QTableWidgetItem(hk_data["key"])
        item_key.setData(Qt.UserRole, hk_data["id"])
        self.hotkey_table.setItem(row, 0, item_key)
        self.hotkey_table.setItem(row, 1, QTableWidgetItem(str(hk_data["duration_sec"])))
        self.hotkey_table.setItem(row, 2, QTableWidgetItem(hk_data["message"]))
        self.hotkey_table.setItem(row, 3, QTableWidgetItem(hk_data["character"]))

    def _on_add_hotkey(self):
        self._add_hotkey_row()
        last = self.hotkey_table.rowCount() - 1
        self.hotkey_table.selectRow(last)
        self.hotkey_table.scrollToBottom()

    def _on_delete_hotkey(self):
        rows = sorted(set(idx.row() for idx in self.hotkey_table.selectedIndexes()), reverse=True)
        for row in rows:
            self.hotkey_table.removeRow(row)

    def _build_general_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        glob = self.config.get_global()

        self.chk_sound = QCheckBox()
        self.chk_sound.setChecked(glob.get("sound_enabled", True))
        layout.addRow("啟用音效", self.chk_sound)

        self.cmb_corner = QComboBox()
        current_corner = glob.get("spawn_corner", "bottom_right")
        for label, value in CORNER_OPTIONS:
            self.cmb_corner.addItem(label, value)
        idx = next((i for i, (_, v) in enumerate(CORNER_OPTIONS) if v == current_corner), 0)
        self.cmb_corner.setCurrentIndex(idx)
        layout.addRow("通知角落", self.cmb_corner)

        return tab

    def _build_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Pixel Timer")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(20)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)

        version_label = QLabel("版本 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)

        desc_label = QLabel(
            "Windows 像素風計時提醒器\n全域快捷鍵觸發倒數計時，時間到以桌寵動畫提醒。"
        )
        desc_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addWidget(desc_label)

        return tab

    def _on_save(self):
        hotkeys = []
        seen_keys = set()
        for row in range(self.hotkey_table.rowCount()):
            key = self.hotkey_table.item(row, 0).text().strip()
            dur_text = self.hotkey_table.item(row, 1).text().strip()
            msg = self.hotkey_table.item(row, 2).text().strip()
            char = self.hotkey_table.item(row, 3).text().strip()
            hk_id = self.hotkey_table.item(row, 0).data(Qt.UserRole)

            if not key:
                QMessageBox.warning(self, "錯誤", f"第 {row+1} 行：快捷鍵不能為空")
                return
            try:
                dur = int(dur_text)
                if dur <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "錯誤", f"第 {row+1} 行：秒數必須是正整數")
                return
            if key.lower() in seen_keys:
                QMessageBox.warning(self, "錯誤", f"第 {row+1} 行：快捷鍵 '{key}' 與其他行重複")
                return
            seen_keys.add(key.lower())

            conflict = _check_hotkey_conflict(key)
            if conflict:
                ret = QMessageBox.question(
                    self, "快捷鍵衝突",
                    f"第 {row+1} 行：'{key}' {conflict}\n仍要儲存？",
                )
                if ret != QMessageBox.Yes:
                    return
            if not msg:
                msg = "時間到！"
            if char not in CHARACTER_OPTIONS:
                char = "cat"

            hotkeys.append({
                "id": hk_id,
                "key": key,
                "duration_sec": dur,
                "message": msg,
                "character": char,
            })

        self.config.set_hotkeys(hotkeys)
        self.config.update_global({
            "sound_enabled": self.chk_sound.isChecked(),
            "spawn_corner": self.cmb_corner.currentData(),
        })
        self.settings_changed.emit()
        self.accept()
