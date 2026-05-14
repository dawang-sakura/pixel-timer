import re
import uuid

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QMessageBox, QFrame, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap

from core.constants import CHARACTER_OPTIONS, CHARACTER_DISPLAY_NAMES
from ui.alarm_card import AlarmCard
from ui.bubble_widget import BubbleWidget
from ui.card_list_view import CardListView
from ui.pet_card import PetCard
from ui.title_bar import PixelTitleBar
from ui.dwm_utils import disable_dwm_frame
from ui.pixel_theme import (
    pixel_font, BG_DEEP, BG_MID, BG_LIGHT,
    BORDER_HI, BORDER_LO, TEXT, TEXT_DIM, CURSOR_CLR,
)


def _validate_time(t):
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", t)
    if not m:
        return False
    h, mi = int(m.group(1)), int(m.group(2))
    return 0 <= h <= 23 and 0 <= mi <= 59


# -- RPG Tab Bar --

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
                painter.drawText(x, 0, cursor_w, self.height(),
                                 Qt.AlignmentFlag.AlignVCenter, cursor_text)
                painter.setPen(QColor(TEXT))
                painter.drawText(x + cursor_w, 0, text_w, self.height(),
                                 Qt.AlignmentFlag.AlignVCenter, label)
            else:
                painter.setPen(QColor(TEXT))
                painter.drawText(x + cursor_w, 0, text_w, self.height(),
                                 Qt.AlignmentFlag.AlignVCenter, label)
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


# -- Sprite Preview --

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
        scaled = pm.scaled(64, 64,
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.FastTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)


# -- Settings Window --

class SettingsWindow(QDialog):
    settings_changed = Signal()

    def __init__(self, config_manager, sprite_loader=None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self._sprite_loader = sprite_loader
        self._preview = None
        self._displayed_alarm_row = None
        self._alarms_by_row = {}
        self._checker_cache = None
        self._checker_size = None
        self.setWindowTitle("Pixel Timer 設定")
        self.setFixedSize(560, 520)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._title_bar = PixelTitleBar("Pixel Timer 設定")
        self._title_bar.close_requested.connect(self.reject)
        root.addWidget(self._title_bar)
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(20, 14, 20, 14)
        inner_lay.setSpacing(6)
        self._tab_bar = PixelTabBar(["桌寵", "關於"])
        inner_lay.addWidget(self._tab_bar)
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_pet_tab())
        self._stack.addWidget(self._build_about_tab())
        inner_lay.addWidget(self._stack)
        self._tab_bar.tab_changed.connect(self._stack.setCurrentIndex)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_save = QPushButton("儲存")
        self.btn_cancel = QPushButton("取消")
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        inner_lay.addLayout(btn_row)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)
        root.addWidget(inner)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        w, h = self.width(), self.height()
        if self._checker_cache is None or self._checker_size != (w, h):
            self._checker_size = (w, h)
            pm = QPixmap(w, h)
            c1 = QColor(BG_DEEP)
            c2 = QColor("#E8961E")
            tile_p = QPainter(pm)
            tile_p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            for ty in range(0, h, 8):
                for tx in range(0, w, 8):
                    tile_p.fillRect(tx, ty, 8, 8,
                                    c1 if (tx // 8 + ty // 8) % 2 == 0 else c2)
            tile_p.end()
            self._checker_cache = pm
        painter.drawPixmap(0, 0, self._checker_cache)
        inset = 12
        tb_h = self._title_bar.height()
        inset_top = inset + tb_h
        fw = w - inset * 2
        fh = h - inset_top - inset
        painter.fillRect(inset + 3, inset_top + 3, fw, fh, QColor("#2A1A00"))
        painter.setPen(QPen(QColor(BORDER_HI), 4))
        painter.setBrush(QColor(BG_MID))
        painter.drawRect(inset, inset_top, fw, fh)
        dot_color = QColor(BORDER_HI)
        for dx, dy in [(inset + 8, inset_top + 8), (inset + fw - 12, inset_top + 8),
                       (inset + 8, inset_top + fh - 12),
                       (inset + fw - 12, inset_top + fh - 12)]:
            painter.fillRect(dx, dy, 4, 4, dot_color)
            painter.fillRect(dx + 6, dy, 4, 4, dot_color)

    def showEvent(self, event):
        super().showEvent(event)
        disable_dwm_frame(int(self.winId()))

    def closeEvent(self, event):
        if self._preview:
            self._preview.stop()
        super().closeEvent(event)

    # -- Pet Tab --

    def _build_pet_tab(self):
        tab = self._build_pet_tab_ui()
        self._load_pet_data()
        return tab

    def _build_pet_tab_ui(self):
        """Build the static pet-tab widget tree and wire signals."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)
        top_row = QHBoxLayout()
        self.chk_sound = QCheckBox("啟用音效")
        top_row.addWidget(self.chk_sound)
        top_row.addStretch()
        layout.addLayout(top_row)
        self.pet_list = CardListView(selectable=True)
        self.pet_list.setMinimumHeight(100)
        layout.addWidget(self.pet_list, 1)
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("新增")
        btn_add.clicked.connect(self._on_add_pet)
        btn_layout.addWidget(btn_add)
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
        self.alarm_list = CardListView(selectable=False)
        self.alarm_list.setMinimumHeight(80)
        layout.addWidget(self.alarm_list, 1)
        alarm_btn_layout = QHBoxLayout()
        btn_add_alarm = QPushButton("新增鬧鐘")
        btn_add_alarm.clicked.connect(self._on_add_alarm)
        alarm_btn_layout.addWidget(btn_add_alarm)
        alarm_btn_layout.addStretch()
        layout.addLayout(alarm_btn_layout)
        self.pet_list.selection_changed.connect(self._on_pet_selected)
        return tab

    def _load_pet_data(self):
        """Populate pet list and alarm cache from config."""
        glob = self.config.get_global()
        self.chk_sound.setChecked(glob.get("sound_enabled", True))
        for row_idx, pet in enumerate(self.config.get_pets()):
            self._alarms_by_row[row_idx] = list(pet.get("alarms", []))
            self._add_pet_card(pet)

    # -- Pet card helpers --

    def _add_pet_card(self, pet_data=None):
        if pet_data is None:
            pet_data = {
                "id": f"pet_{uuid.uuid4().hex[:8]}",
                "character": "orange_cat",
                "duration_sec": 60,
                "message": "時間到！",
                "position": {"x": -1, "y": -1},
            }
        card = PetCard(pet_data, self._sprite_loader)
        card.changed.connect(lambda c=card: self._on_pet_card_changed(c))
        card.delete_requested.connect(lambda c=card: self._on_delete_pet_card(c))
        self.pet_list.add_card(card)
        return card

    def _on_pet_card_changed(self, card):
        idx = self.pet_list.selected_index
        if idx >= 0 and self.pet_list.card_at(idx) is card:
            self._refresh_bubble_preview(card)

    def _refresh_bubble_preview(self, card):
        char_id = card.character_id
        if self._preview and char_id in CHARACTER_OPTIONS:
            self._preview.set_character(char_id)
        self._bubble_preview.set_character(char_id)
        self._bubble_preview.set_message(card.message)

    def _on_delete_pet_card(self, card):
        self._sync_alarm_cards_to_data()
        idx = self.pet_list.index_of(card)
        if idx < 0:
            return
        # code-I1: neutralise sync path BEFORE remove_card emits selection_changed(-1)
        self._alarms_by_row.pop(idx, None)
        self._displayed_alarm_row = None
        self.alarm_list.clear()
        self.pet_list.remove_card(idx)
        # py-I3: dict comprehension reindex (keys may be non-contiguous after pop)
        self._alarms_by_row = {
            new_i: alarms
            for new_i, (_, alarms) in enumerate(
                sorted(self._alarms_by_row.items())
            )
        }
        if self._preview:
            self._preview.clear()
        self._bubble_preview.set_message("")
        self._bubble_preview.set_character("orange_cat")

    # -- Pet selection --

    def _on_pet_selected(self, new_idx: int):
        # R4: sync first, then update displayed row, then reload
        self._sync_alarm_cards_to_data()
        self._displayed_alarm_row = new_idx if new_idx >= 0 else None
        self.alarm_list.clear()
        if new_idx < 0:
            if self._preview:
                self._preview.clear()
            self._bubble_preview.set_message("")
            self._bubble_preview.set_character("orange_cat")
            return
        self._load_alarm_cards_for_row(new_idx)
        card = self.pet_list.card_at(new_idx)
        if card is not None:
            self._refresh_bubble_preview(card)

    # -- Alarm card helpers --

    def _load_alarm_cards_for_row(self, row: int):
        for alarm in self._alarms_by_row.get(row, []):
            self._add_alarm_card(alarm)

    def _add_alarm_card(self, alarm_data=None):
        if alarm_data is None:
            alarm_data = {
                "time": "09:00",
                "message": "鬧鐘！",
                "repeat": "daily",
                "enabled": True,
            }
        card = AlarmCard(alarm_data)
        card.changed.connect(self._sync_alarm_cards_to_data)
        card.delete_requested.connect(lambda c=card: self._on_delete_alarm_card(c))
        self.alarm_list.add_card(card)
        return card

    def _on_delete_alarm_card(self, card):
        idx = self.alarm_list.index_of(card)
        if idx < 0:
            return
        self.alarm_list.remove_card(idx)
        self._sync_alarm_cards_to_data()

    def _sync_alarm_cards_to_data(self):
        if self._displayed_alarm_row is None:
            return
        alarms = [card.get_data() for card in self.alarm_list.iter_cards()]
        self._alarms_by_row[self._displayed_alarm_row] = alarms

    # -- Top-level pet/alarm add --

    def _on_add_pet(self):
        self._sync_alarm_cards_to_data()
        self._add_pet_card()
        new_idx = self.pet_list.card_count() - 1
        self._alarms_by_row[new_idx] = []
        self.pet_list.select_index(new_idx)
        self.pet_list.verticalScrollBar().setValue(
            self.pet_list.verticalScrollBar().maximum()
        )

    def _on_add_alarm(self):
        if self._displayed_alarm_row is None:
            QMessageBox.information(self, "提示", "請先選擇一隻桌寵")
            return
        self._sync_alarm_cards_to_data()
        self._add_alarm_card()
        self._sync_alarm_cards_to_data()

    # -- About Tab --

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
            "時間到桌寵播放動畫並彈出 RPG 對話氣泡提醒"
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

    # -- Save --

    def _on_save(self):
        self._sync_alarm_cards_to_data()
        pets = []
        for row, card in enumerate(self.pet_list.iter_cards()):
            data = card.get_data()
            char = data["character"]
            dur = data["duration_sec"]
            msg = data["message"]
            pet_id = data["id"]
            if not pet_id:
                pet_id = f"pet_{uuid.uuid4().hex[:8]}"
            if dur <= 0:
                QMessageBox.warning(
                    self, "錯誤",
                    f"第 {row + 1} 隻桌寵：秒數必須是正整數"
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
                        f"第 {row + 1} 隻桌寵的鬧鐘 #{a_idx + 1}："
                        "時間格式錯誤，請用 HH:MM",
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
        self.config.update_global({"sound_enabled": self.chk_sound.isChecked()})
        self.settings_changed.emit()
        self.accept()
