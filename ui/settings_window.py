import re
import uuid

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QStyledItemDelegate, QFrame, QStackedWidget,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap

from core.constants import CHARACTER_OPTIONS, CHARACTER_DISPLAY_NAMES
from ui.bubble_widget import BubbleWidget
from ui.pixel_theme import (
    pixel_font, BG_DEEP, BG_MID, BG_LIGHT,
    BORDER_HI, BORDER_LO, TEXT, TEXT_DIM, CURSOR_CLR,
)

PET_COLUMNS = ["角色", "秒數", "訊息"]
ALARM_COLUMNS = ["時間", "訊息", "重複", "啟用"]
REPEAT_OPTIONS = [("once", "單次"), ("daily", "每天"), ("weekdays", "平日")]
_CHAR_ID_ROLE = Qt.ItemDataRole.UserRole + 1
_REPEAT_ID_ROLE = Qt.ItemDataRole.UserRole + 2


def _validate_time(t):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", t)
    if not m:
        return False
    h, mi = int(m.group(1)), int(m.group(2))
    return 0 <= h <= 23 and 0 <= mi <= 59


# ── RPG Tab Bar ──────────────────────────────────────────────────────────

class PixelTabBar(QWidget):
    tab_changed = Signal(int)

    def __init__(self, labels, parent=None):
        super().__init__(parent)
        self._labels = labels
        self._current = 0
        self._tab_rects = []
        self._font = pixel_font(18, bold=True)
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        painter.fillRect(self.rect(), QColor(BG_LIGHT))

        painter.setPen(QPen(QColor(BORDER_HI), 2))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

        painter.setFont(self._font)
        fm = painter.fontMetrics()

        self._tab_rects = []
        x = 16
        cursor_text = "▶ "
        cursor_w = fm.horizontalAdvance(cursor_text)

        for i, label in enumerate(self._labels):
            text_w = fm.horizontalAdvance(label)
            total_w = cursor_w + text_w

            if i == self._current:
                painter.setPen(QColor(CURSOR_CLR))
                painter.drawText(
                    x, 0, cursor_w, self.height(),
                    Qt.AlignmentFlag.AlignVCenter, cursor_text,
                )
                painter.setPen(QColor(TEXT))
                painter.drawText(
                    x + cursor_w, 0, text_w, self.height(),
                    Qt.AlignmentFlag.AlignVCenter, label,
                )
            else:
                painter.setPen(QColor(TEXT))
                painter.drawText(
                    x + cursor_w, 0, text_w, self.height(),
                    Qt.AlignmentFlag.AlignVCenter, label,
                )

            self._tab_rects.append((x, total_w))
            x += total_w + 32

    def mousePressEvent(self, event):
        click_x = event.pos().x()
        for i, (rx, rw) in enumerate(self._tab_rects):
            if rx <= click_x <= rx + rw + 16:
                if i != self._current:
                    self._current = i
                    self.tab_changed.emit(i)
                    self.update()
                return

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            new = max(0, self._current - 1)
        elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            new = min(len(self._labels) - 1, self._current + 1)
        else:
            super().keyPressEvent(event)
            return
        if new != self._current:
            self._current = new
            self.tab_changed.emit(new)
            self.update()


# ── Sprite Preview ───────────────────────────────────────────────────────

class SpritePreview(QWidget):
    def __init__(self, sprite_loader, parent=None):
        super().__init__(parent)
        self._loader = sprite_loader
        self._pixmaps = []
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self.setFixedSize(80, 80)

    def set_character(self, character):
        self._timer.stop()
        self._pixmaps = []
        for frame_idx in range(2):
            pm = self._loader.load(character, "idle", frame_idx)
            if pm and not pm.isNull():
                self._pixmaps.append(pm)
        self._frame = 0
        if self._pixmaps:
            self._timer.start(600)
        self.update()

    def clear(self):
        self._timer.stop()
        self._pixmaps = []
        self.update()

    def stop(self):
        self._timer.stop()

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)

    def _next_frame(self):
        if self._pixmaps:
            self._frame = (self._frame + 1) % len(self._pixmaps)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        painter.setPen(QPen(QColor(BORDER_LO), 2))
        painter.setBrush(QColor(BG_MID))
        painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

        if not self._pixmaps:
            painter.setPen(QColor(TEXT_DIM))
            painter.setFont(pixel_font(16))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "預覽")
            return

        pm = self._pixmaps[self._frame]
        scaled = pm.scaled(
            64, 64,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)



# ── Time Delegate (pixel spinner) ────────────────────────────────────────

class TimeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(2)

        hour_spin = QSpinBox()
        hour_spin.setRange(0, 23)
        hour_spin.setWrapping(True)
        hour_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hour_spin.setFont(pixel_font(16, mono=True))
        hour_spin.setFixedWidth(52)

        colon = QLabel(":")
        colon.setFont(pixel_font(16, bold=True, mono=True))
        colon.setFixedWidth(10)
        colon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        min_spin = QSpinBox()
        min_spin.setRange(0, 59)
        min_spin.setWrapping(True)
        min_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        min_spin.setFont(pixel_font(16, mono=True))
        min_spin.setFixedWidth(52)

        layout.addWidget(hour_spin)
        layout.addWidget(colon)
        layout.addWidget(min_spin)

        widget._hour = hour_spin
        widget._min = min_spin
        return widget

    def setEditorData(self, editor, index):
        time_str = index.data(Qt.ItemDataRole.EditRole) or "09:00"
        try:
            h, m = map(int, time_str.split(":"))
        except (ValueError, AttributeError):
            h, m = 9, 0
        editor._hour.setValue(h)
        editor._min.setValue(m)

    def setModelData(self, editor, model, index):
        h = editor._hour.value()
        m = editor._min.value()
        model.setData(index, f"{h:02d}:{m:02d}", Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# ── Existing Delegates (preserved) ───────────────────────────────────────

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
        repeat_id = index.data(_REPEAT_ID_ROLE) or "daily"
        idx = editor.findData(repeat_id)
        editor.setCurrentIndex(idx if idx >= 0 else 0)

    def setModelData(self, editor, model, index):
        repeat_id = editor.currentData()
        repeat_display = dict(REPEAT_OPTIONS).get(repeat_id, repeat_id)
        model.setData(index, repeat_display, Qt.ItemDataRole.EditRole)
        model.setData(index, repeat_id, _REPEAT_ID_ROLE)


# ── Settings Window ──────────────────────────────────────────────────────

class SettingsWindow(QDialog):
    settings_changed = Signal()

    def __init__(self, config_manager, sprite_loader=None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self._sprite_loader = sprite_loader
        self._preview = None

        self._displayed_alarm_row = None
        self._populating = False

        self.setWindowTitle("Pixel Timer 設定")
        self.setMinimumSize(540, 480)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(6)

        self._tab_bar = PixelTabBar(["桌寵", "關於"])
        root.addWidget(self._tab_bar)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_pet_tab())
        self._stack.addWidget(self._build_about_tab())
        root.addWidget(self._stack)

        self._tab_bar.tab_changed.connect(self._stack.setCurrentIndex)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_save = QPushButton("儲存")
        self.btn_cancel = QPushButton("取消")
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        root.addLayout(btn_row)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w, h = self.width(), self.height()
        c1 = QColor(BG_DEEP)
        c2 = QColor("#E8961E")
        for ty in range(0, h, 8):
            for tx in range(0, w, 8):
                painter.fillRect(tx, ty, 8, 8, c1 if (tx // 8 + ty // 8) % 2 == 0 else c2)

        inset = 12
        fw = w - inset * 2
        fh = h - inset * 2
        painter.fillRect(inset + 3, inset + 3, fw, fh, QColor("#2A1A00"))

        painter.setPen(QPen(QColor(BORDER_HI), 4))
        painter.setBrush(QColor(BG_MID))
        painter.drawRect(inset, inset, fw, fh)

        dot_color = QColor(BORDER_HI)
        for dx, dy in [(inset + 8, inset + 8), (inset + fw - 12, inset + 8),
                        (inset + 8, inset + fh - 12), (inset + fw - 12, inset + fh - 12)]:
            painter.fillRect(dx, dy, 4, 4, dot_color)
            painter.fillRect(dx + 6, dy, 4, 4, dot_color)

    def closeEvent(self, event):
        if self._preview:
            self._preview.stop()
        super().closeEvent(event)

    # ── Pet Tab ──────────────────────────────────────────────────────────

    def _build_pet_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        glob = self.config.get_global()
        self.chk_sound = QCheckBox("啟用音效")
        self.chk_sound.setChecked(glob.get("sound_enabled", True))
        top_row.addWidget(self.chk_sound)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.pet_table = QTableWidget(0, 3)
        self.pet_table.setHorizontalHeaderLabels(PET_COLUMNS)
        pet_header = self.pet_table.horizontalHeader()
        pet_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        pet_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        pet_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.pet_table.setColumnWidth(0, 120)
        self.pet_table.setColumnWidth(1, 80)
        self.pet_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.pet_table.setAlternatingRowColors(True)
        self.pet_table.setEditTriggers(
            QTableWidget.EditTrigger.CurrentChanged
            | QTableWidget.EditTrigger.SelectedClicked
        )

        self._char_delegate = CharacterDelegate(self.pet_table)
        self.pet_table.setItemDelegateForColumn(0, self._char_delegate)

        self._alarms_by_row = {}
        self._populating = True
        for row_idx, pet in enumerate(self.config.get_pets()):
            self._add_pet_row(pet)
            self._alarms_by_row[row_idx] = list(pet.get("alarms", []))
        self._populating = False

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
        separator.setStyleSheet(f"color: {BORDER_LO};")
        separator.setFixedHeight(2)
        layout.addWidget(separator)

        header_row = QHBoxLayout()
        if self._sprite_loader:
            self._preview = SpritePreview(self._sprite_loader)
            header_row.addWidget(self._preview)

        self._bubble_preview = BubbleWidget(
            message="", character="orange_cat",
            font_size=14, padding=10,
            max_width=200, min_width=140,
            tail_side="bottom", tail_offset_ratio=0.25,
            show_shadow=False,
        )
        self._bubble_preview.setMinimumHeight(70)
        header_row.addWidget(self._bubble_preview)
        layout.addLayout(header_row)

        self._alarm_table = QTableWidget(0, 4)
        self._alarm_table.setHorizontalHeaderLabels(ALARM_COLUMNS)
        alarm_header = self._alarm_table.horizontalHeader()
        alarm_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        alarm_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        alarm_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        alarm_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._alarm_table.setColumnWidth(0, 100)
        self._alarm_table.setColumnWidth(2, 80)
        self._alarm_table.setColumnWidth(3, 50)
        self._alarm_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._alarm_table.setAlternatingRowColors(True)
        self._alarm_table.setEditTriggers(
            QTableWidget.EditTrigger.CurrentChanged
            | QTableWidget.EditTrigger.SelectedClicked
        )

        self._time_delegate = TimeDelegate(self._alarm_table)
        self._alarm_table.setItemDelegateForColumn(0, self._time_delegate)

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
        self.pet_table.itemChanged.connect(self._on_pet_item_changed)
        return tab

    def _add_pet_row(self, pet_data=None):
        row = self.pet_table.rowCount()
        self.pet_table.insertRow(row)
        self._populating = True

        if pet_data is None:
            pet_data = {
                "id": f"pet_{uuid.uuid4().hex[:8]}",
                "character": "orange_cat",
                "duration_sec": 60,
                "message": "時間到！",
                "position": {"x": -1, "y": -1},
            }

        char_id = pet_data.get("character", "orange_cat")
        item_char = QTableWidgetItem(
            CHARACTER_DISPLAY_NAMES.get(char_id, char_id)
        )
        item_char.setData(Qt.ItemDataRole.UserRole, pet_data["id"])
        item_char.setData(_CHAR_ID_ROLE, char_id)
        item_char.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_table.setItem(row, 0, item_char)

        item_dur = QTableWidgetItem(str(pet_data.get("duration_sec", 60)))
        item_dur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_table.setItem(row, 1, item_dur)

        item_msg = QTableWidgetItem(pet_data.get("message", "時間到！"))
        item_msg.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pet_table.setItem(row, 2, item_msg)

        self._populating = False
    # ── Alarm table management ───────────────────────────────────────────

    def _on_pet_selected(self):
        self._sync_alarm_table_to_data()
        rows = self.pet_table.selectionModel().selectedRows()
        if not rows:
            self._displayed_alarm_row = None
            self._alarm_table.setRowCount(0)
            if self._preview:
                self._preview.clear()
            self._bubble_preview.set_message("")
            self._bubble_preview.set_character("orange_cat")
            return
        row = rows[0].row()
        char_item = self.pet_table.item(row, 0)
        char_id = char_item.data(_CHAR_ID_ROLE) if char_item else "orange_cat"
        msg_item = self.pet_table.item(row, 2)
        msg = msg_item.text().strip() if msg_item else ""
        self._load_alarms_for_row(row)
        self._displayed_alarm_row = row

        if self._preview and char_id in CHARACTER_OPTIONS:
            self._preview.set_character(char_id)
        self._bubble_preview.set_character(char_id)
        self._bubble_preview.set_message(msg)

    def _on_pet_item_changed(self, item):
        if self._populating:
            return
        if item.column() == 0:
            char_id = item.data(_CHAR_ID_ROLE) or "orange_cat"
            if char_id in CHARACTER_OPTIONS:
                if self._preview:
                    self._preview.set_character(char_id)
                self._bubble_preview.set_character(char_id)
            return
        if item.column() != 2:
            return
        rows = self.pet_table.selectionModel().selectedRows()
        if not rows or rows[0].row() != item.row():
            return
        self._bubble_preview.set_message(item.text().strip())

    def _load_alarms_for_row(self, row):
        self._alarm_table.setRowCount(0)
        for alarm in self._alarms_by_row.get(row, []):
            self._add_alarm_row(alarm)

    def _add_alarm_row(self, alarm_data=None):
        if alarm_data is None:
            alarm_data = {
                "time": "09:00", "message": "鬧鐘！",
                "repeat": "daily", "enabled": True,
            }

        row = self._alarm_table.rowCount()
        self._alarm_table.insertRow(row)

        time_item = QTableWidgetItem(alarm_data.get("time", "09:00"))
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._alarm_table.setItem(row, 0, time_item)

        msg_item = QTableWidgetItem(alarm_data.get("message", "鬧鐘！"))
        msg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._alarm_table.setItem(row, 1, msg_item)

        repeat_id = alarm_data.get("repeat", "daily")
        repeat_display = dict(REPEAT_OPTIONS).get(repeat_id, repeat_id)
        repeat_item = QTableWidgetItem(repeat_display)
        repeat_item.setData(_REPEAT_ID_ROLE, repeat_id)
        repeat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._alarm_table.setItem(row, 2, repeat_item)

        chk_item = QTableWidgetItem()
        chk_item.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
        )
        chk_item.setCheckState(
            Qt.CheckState.Checked
            if alarm_data.get("enabled", True)
            else Qt.CheckState.Unchecked
        )
        chk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._alarm_table.setItem(row, 3, chk_item)

    def _on_add_alarm(self):
        rows = self.pet_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "提示", "請先選擇一隻桌寵")
            return
        self._sync_alarm_table_to_data()
        self._add_alarm_row()

    def _on_delete_alarm(self):
        alarm_rows = sorted(
            set(idx.row() for idx in self._alarm_table.selectedIndexes()),
            reverse=True,
        )
        for row in alarm_rows:
            self._alarm_table.removeRow(row)
        self._sync_alarm_table_to_data()

    def _sync_alarm_table_to_data(self):
        if self._displayed_alarm_row is None:
            return
        pet_row = self._displayed_alarm_row
        alarms = []
        for r in range(self._alarm_table.rowCount()):
            time_item = self._alarm_table.item(r, 0)
            msg_item = self._alarm_table.item(r, 1)
            repeat_item = self._alarm_table.item(r, 2)
            enabled_item = self._alarm_table.item(r, 3)
            alarms.append({
                "time": time_item.text().strip() if time_item else "09:00",
                "message": msg_item.text().strip() if msg_item else "鬧鐘！",
                "repeat": (
                    repeat_item.data(_REPEAT_ID_ROLE) if repeat_item else None
                ) or "daily",
                "enabled": (
                    enabled_item.checkState() == Qt.CheckState.Checked
                    if enabled_item else True
                ),
            })
        self._alarms_by_row[pet_row] = alarms

    # ── Pet table management ─────────────────────────────────────────────

    def _on_add_pet(self):
        self._sync_alarm_table_to_data()
        self._add_pet_row()
        last = self.pet_table.rowCount() - 1
        self._alarms_by_row[last] = []
        self.pet_table.selectRow(last)
        self.pet_table.scrollToBottom()

    def _on_delete_pet(self):
        self._sync_alarm_table_to_data()
        self._displayed_alarm_row = None
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

    # ── About Tab ────────────────────────────────────────────────────────

    def _build_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Pixel Timer")
        title.setFont(pixel_font(28, bold=True))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel("版本 3.0.0")
        version.setFont(pixel_font(16))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "Windows 像素風計時提醒器\n"
            "桌寵常駐工具列旁，雙擊啟動倒數計時\n"
            "時間到桌寵播放動畫並彈出 RPG 對話氣泡"
        )
        desc.setFont(pixel_font(16))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {TEXT_DIM};")

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(version)
        layout.addSpacing(16)
        layout.addWidget(desc)

        return tab

    # ── Save ─────────────────────────────────────────────────────────────

    def _on_save(self):
        self._sync_alarm_table_to_data()
        pets = []
        for row in range(self.pet_table.rowCount()):
            char_item = self.pet_table.item(row, 0)
            dur_item = self.pet_table.item(row, 1)
            msg_item = self.pet_table.item(row, 2)

            char = (
                char_item.data(_CHAR_ID_ROLE) if char_item else None
            ) or "orange_cat"
            dur_text = dur_item.text().strip() if dur_item else "60"
            msg = msg_item.text().strip() if msg_item else "時間到！"
            pet_id = (
                char_item.data(Qt.ItemDataRole.UserRole) if char_item else None
            )

            if not pet_id:
                pet_id = f"pet_{uuid.uuid4().hex[:8]}"

            try:
                dur = int(dur_text)
                if dur <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(
                    self, "錯誤", f"第 {row + 1} 行：秒數必須是正整數"
                )
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
            existing_pos = (
                existing.get("position", {"x": -1, "y": -1})
                if existing else {"x": -1, "y": -1}
            )

            pets.append({
                "id": pet_id,
                "character": char,
                "duration_sec": dur,
                "message": msg,
                "alarms": row_alarms,
                "position": existing_pos,
            })

        self.config.set_pets(pets)
        self.config.update_global({
            "sound_enabled": self.chk_sound.isChecked(),
        })
        self.settings_changed.emit()
        self.accept()
