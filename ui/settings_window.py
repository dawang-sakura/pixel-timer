import re
import uuid

from PySide6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QStyledItemDelegate, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.constants import CHARACTER_OPTIONS, CHARACTER_DISPLAY_NAMES

PET_COLUMNS = ["角色", "秒數", "訊息"]
ALARM_COLUMNS = ["時間", "訊息", "重複", "啟用"]
REPEAT_OPTIONS = [("once", "單次"), ("daily", "每天"), ("weekdays", "平日")]
_CHAR_ID_ROLE = Qt.ItemDataRole.UserRole + 1


def _validate_time(t):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", t)
    if not m:
        return False
    h, mi = int(m.group(1)), int(m.group(2))
    return 0 <= h <= 23 and 0 <= mi <= 59


class CharacterDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        for cid in CHARACTER_OPTIONS:
            combo.addItem(CHARACTER_DISPLAY_NAMES.get(cid, cid), cid)
        return combo

    def setEditorData(self, editor, index):
        char_id = index.data(_CHAR_ID_ROLE) or "orange_cat"
        idx = editor.findData(char_id)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor, model, index):
        char_id = editor.currentData()
        model.setData(index, CHARACTER_DISPLAY_NAMES.get(char_id, char_id), Qt.ItemDataRole.EditRole)
        model.setData(index, char_id, _CHAR_ID_ROLE)


class RepeatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        for rid, rname in REPEAT_OPTIONS:
            combo.addItem(rname, rid)
        return combo

    def setEditorData(self, editor, index):
        repeat_id = index.data(_CHAR_ID_ROLE) or "daily"
        idx = editor.findData(repeat_id)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor, model, index):
        repeat_id = editor.currentData()
        repeat_display = dict(REPEAT_OPTIONS).get(repeat_id, repeat_id)
        model.setData(index, repeat_display, Qt.ItemDataRole.EditRole)
        model.setData(index, repeat_id, _CHAR_ID_ROLE)


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

        self._alarms_by_row = {}
        for row_idx, pet in enumerate(self.config.get_pets()):
            self._add_pet_row(pet)
            self._alarms_by_row[row_idx] = list(pet.get("alarms", []))

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

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        self._alarm_pet_label = QLabel("鬧鐘設定（請選擇桌寵）")
        alarm_label_font = QFont()
        alarm_label_font.setBold(True)
        self._alarm_pet_label.setFont(alarm_label_font)
        layout.addWidget(self._alarm_pet_label)

        self._alarm_table = QTableWidget(0, 4)
        self._alarm_table.setHorizontalHeaderLabels(ALARM_COLUMNS)
        self._alarm_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._alarm_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self._repeat_delegate = RepeatDelegate(self._alarm_table)
        self._alarm_table.setItemDelegateForColumn(2, self._repeat_delegate)

        layout.addWidget(self._alarm_table)

        alarm_btn_layout = QHBoxLayout()
        btn_add_alarm = QPushButton("新增鬧鐘")
        btn_del_alarm = QPushButton("刪除鬧鐘")
        btn_add_alarm.clicked.connect(self._on_add_alarm)
        btn_del_alarm.clicked.connect(self._on_delete_alarm)
        alarm_btn_layout.addWidget(btn_add_alarm)
        alarm_btn_layout.addWidget(btn_del_alarm)
        alarm_btn_layout.addStretch()
        layout.addLayout(alarm_btn_layout)

        self.pet_table.itemSelectionChanged.connect(self._on_pet_selected)

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

        char_id = pet_data.get("character", "orange_cat")
        item_char = QTableWidgetItem(CHARACTER_DISPLAY_NAMES.get(char_id, char_id))
        item_char.setData(Qt.ItemDataRole.UserRole, pet_data["id"])
        item_char.setData(_CHAR_ID_ROLE, char_id)
        self.pet_table.setItem(row, 0, item_char)
        self.pet_table.setItem(row, 1, QTableWidgetItem(str(pet_data.get("duration_sec", 60))))
        self.pet_table.setItem(row, 2, QTableWidgetItem(pet_data.get("message", "時間到！")))

    # --- Alarm table management ---

    def _on_pet_selected(self):
        self._sync_alarm_table_to_data()
        rows = self.pet_table.selectionModel().selectedRows()
        if not rows:
            self._alarm_pet_label.setText("鬧鐘設定（請選擇桌寵）")
            self._alarm_table.setRowCount(0)
            return
        row = rows[0].row()
        char_item = self.pet_table.item(row, 0)
        char_id = char_item.data(_CHAR_ID_ROLE) if char_item else "?"
        char_name = CHARACTER_DISPLAY_NAMES.get(char_id, char_id)
        self._alarm_pet_label.setText(f"鬧鐘設定 — {char_name}")
        self._load_alarms_for_row(row)

    def _load_alarms_for_row(self, row):
        self._alarm_table.setRowCount(0)
        for alarm in self._alarms_by_row.get(row, []):
            self._add_alarm_row(alarm)

    def _add_alarm_row(self, alarm_data=None):
        if alarm_data is None:
            alarm_data = {"time": "09:00", "message": "鬧鐘！", "repeat": "daily", "enabled": True}

        row = self._alarm_table.rowCount()
        self._alarm_table.insertRow(row)

        self._alarm_table.setItem(row, 0, QTableWidgetItem(alarm_data.get("time", "09:00")))
        self._alarm_table.setItem(row, 1, QTableWidgetItem(alarm_data.get("message", "鬧鐘！")))

        repeat_id = alarm_data.get("repeat", "daily")
        repeat_display = dict(REPEAT_OPTIONS).get(repeat_id, repeat_id)
        repeat_item = QTableWidgetItem(repeat_display)
        repeat_item.setData(_CHAR_ID_ROLE, repeat_id)
        self._alarm_table.setItem(row, 2, repeat_item)

        chk_item = QTableWidgetItem()
        chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        chk_item.setCheckState(
            Qt.CheckState.Checked if alarm_data.get("enabled", True) else Qt.CheckState.Unchecked
        )
        self._alarm_table.setItem(row, 3, chk_item)

    def _on_add_alarm(self):
        rows = self.pet_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "提示", "請先選擇一隻桌寵")
            return
        self._sync_alarm_table_to_data()
        self._add_alarm_row()

    def _on_delete_alarm(self):
        self._sync_alarm_table_to_data()
        alarm_rows = sorted(
            set(idx.row() for idx in self._alarm_table.selectedIndexes()),
            reverse=True,
        )
        for row in alarm_rows:
            self._alarm_table.removeRow(row)

    def _sync_alarm_table_to_data(self):
        rows = self.pet_table.selectionModel().selectedRows()
        if not rows:
            return
        pet_row = rows[0].row()
        alarms = []
        for r in range(self._alarm_table.rowCount()):
            time_item = self._alarm_table.item(r, 0)
            msg_item = self._alarm_table.item(r, 1)
            repeat_item = self._alarm_table.item(r, 2)
            enabled_item = self._alarm_table.item(r, 3)
            alarms.append({
                "time": time_item.text().strip() if time_item else "09:00",
                "message": msg_item.text().strip() if msg_item else "鬧鐘！",
                "repeat": (repeat_item.data(_CHAR_ID_ROLE) if repeat_item else None) or "daily",
                "enabled": enabled_item.checkState() == Qt.CheckState.Checked if enabled_item else True,
            })
        self._alarms_by_row[pet_row] = alarms

    # --- Pet table management ---

    def _on_add_pet(self):
        self._sync_alarm_table_to_data()
        self._add_pet_row()
        last = self.pet_table.rowCount() - 1
        self._alarms_by_row[last] = []
        self.pet_table.selectRow(last)
        self.pet_table.scrollToBottom()

    def _on_delete_pet(self):
        self._sync_alarm_table_to_data()
        rows = sorted(
            set(idx.row() for idx in self.pet_table.selectedIndexes()),
            reverse=True,
        )
        for row in rows:
            self.pet_table.removeRow(row)
            self._alarms_by_row.pop(row, None)
        old_data = dict(self._alarms_by_row)
        self._alarms_by_row = {}
        for new_idx, old_idx in enumerate(sorted(old_data.keys())):
            self._alarms_by_row[new_idx] = old_data[old_idx]
        self._on_pet_selected()

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
        self._sync_alarm_table_to_data()
        pets = []
        for row in range(self.pet_table.rowCount()):
            char_item = self.pet_table.item(row, 0)
            dur_item = self.pet_table.item(row, 1)
            msg_item = self.pet_table.item(row, 2)

            char = (char_item.data(_CHAR_ID_ROLE) if char_item else None) or "orange_cat"
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

            row_alarms = self._alarms_by_row.get(row, [])
            for a_idx, alarm in enumerate(row_alarms):
                t = alarm.get("time", "")
                if not _validate_time(t):
                    QMessageBox.warning(
                        self, "錯誤",
                        f"第 {row + 1} 隻桌寵的鬧鐘 #{a_idx + 1}：時間格式錯誤，請用 HH:MM",
                    )
                    return
                h, m = map(int, t.split(":"))
                alarm["time"] = f"{h:02d}:{m:02d}"

            existing = self.config.get_pet(pet_id)
            existing_position = existing.get("position", {"x": -1, "y": -1}) if existing else {"x": -1, "y": -1}

            pets.append({
                "id": pet_id,
                "character": char,
                "duration_sec": dur,
                "message": msg,
                "alarms": row_alarms,
                "position": existing_position,
            })

        self.config.set_pets(pets)
        self.config.update_global({
            "sound_enabled": self.chk_sound.isChecked(),
        })
        self.settings_changed.emit()
        self.accept()
