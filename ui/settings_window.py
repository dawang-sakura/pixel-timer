import uuid

from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QStyledItemDelegate,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

PET_COLUMNS = ["角色", "秒數", "訊息"]
CHARACTER_OPTIONS = ["orange_cat", "white_cat", "calico", "snoopy", "shiba", "goblin"]


class CharacterDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(CHARACTER_OPTIONS)
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.ItemDataRole.DisplayRole)
        idx = editor.findText(value)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


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
        self._tabs.addTab(self._build_pet_tab(), "桌寵")
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

    def _build_pet_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.pet_table = QTableWidget(0, 3)
        self.pet_table.setHorizontalHeaderLabels(PET_COLUMNS)
        self.pet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self._char_delegate = CharacterDelegate(self.pet_table)
        self.pet_table.setItemDelegateForColumn(0, self._char_delegate)

        for pet in self.config.get_pets():
            self._add_pet_row(pet)

        layout.addWidget(self.pet_table)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("新增")
        btn_delete = QPushButton("刪除")
        btn_add.clicked.connect(self._on_add_pet)
        btn_delete.clicked.connect(self._on_delete_pet)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return tab

    def _add_pet_row(self, pet_data=None):
        row = self.pet_table.rowCount()
        self.pet_table.insertRow(row)

        if pet_data is None:
            pet_data = {
                "id": f"pet_{uuid.uuid4().hex[:8]}",
                "character": "orange_cat",
                "duration_sec": 60,
                "message": "時間到！",
                "position": {"x": -1, "y": -1},
            }

        item_char = QTableWidgetItem(pet_data.get("character", "orange_cat"))
        item_char.setData(Qt.ItemDataRole.UserRole, pet_data["id"])
        self.pet_table.setItem(row, 0, item_char)
        self.pet_table.setItem(row, 1, QTableWidgetItem(str(pet_data.get("duration_sec", 60))))
        self.pet_table.setItem(row, 2, QTableWidgetItem(pet_data.get("message", "時間到！")))

    def _on_add_pet(self):
        self._add_pet_row()
        last = self.pet_table.rowCount() - 1
        self.pet_table.selectRow(last)
        self.pet_table.scrollToBottom()

    def _on_delete_pet(self):
        rows = sorted(
            set(idx.row() for idx in self.pet_table.selectedIndexes()),
            reverse=True,
        )
        for row in rows:
            self.pet_table.removeRow(row)

    def _build_general_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        glob = self.config.get_global()

        self.chk_sound = QCheckBox()
        self.chk_sound.setChecked(glob.get("sound_enabled", True))
        layout.addRow("啟用音效", self.chk_sound)

        return tab

    def _build_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Pixel Timer")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(20)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel("版本 3.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(
            "Windows 像素風計時提醒器\n"
            "桌寵常駐工具列旁，雙擊啟動倒數計時\n"
            "時間到桌寵播放動畫並彈出 RPG 對話氣泡"
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addWidget(desc_label)

        return tab

    def _on_save(self):
        pets = []
        for row in range(self.pet_table.rowCount()):
            char_item = self.pet_table.item(row, 0)
            dur_item = self.pet_table.item(row, 1)
            msg_item = self.pet_table.item(row, 2)

            char = (char_item.text().strip() if char_item else "orange_cat")
            dur_text = (dur_item.text().strip() if dur_item else "60")
            msg = (msg_item.text().strip() if msg_item else "時間到！")
            pet_id = char_item.data(Qt.ItemDataRole.UserRole) if char_item else None

            if not pet_id:
                pet_id = f"pet_{uuid.uuid4().hex[:8]}"

            try:
                dur = int(dur_text)
                if dur <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "錯誤", f"第 {row + 1} 行：秒數必須是正整數")
                return

            if not msg:
                msg = "時間到！"
            if char not in CHARACTER_OPTIONS:
                char = "orange_cat"

            # Preserve existing position
            existing = self.config.get_pet(pet_id)
            existing_position = existing.get("position", {"x": -1, "y": -1}) if existing else {"x": -1, "y": -1}

            pets.append({
                "id": pet_id,
                "character": char,
                "duration_sec": dur,
                "message": msg,
                "position": existing_position,
            })

        self.config.set_pets(pets)
        self.config.update_global({
            "sound_enabled": self.chk_sound.isChecked(),
        })
        self.settings_changed.emit()
        self.accept()
