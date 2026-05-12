# Pixel Timer — Windows 像素風計時提醒器

## 專案概述
Windows 桌面小工具：工具列旁的像素桌寵觸發倒數計時，時間到後桌寵播放動畫 + RPG 對話氣泡提醒。

## 技術棧
- Python 3.12+ / PySide6（GUI + 動畫 + 系統匣）
- Pillow（sprite 素材生成）
- JSON 配置檔
- PyInstaller 打包

## 專案結構
```
pixel_timer/
  main.py                     # 入口
  core/config_manager.py      # 設定讀寫（pets + alarms schema）+ atomic save
  core/timer_engine.py        # QTimer 計時引擎
  core/alarm_engine.py        # QTimer 30s 掃描 HH:MM 鬧鐘觸發
  ui/tray_app.py              # QSystemTrayIcon 系統匣 + 桌寵管理 + alarm signal 整合
  ui/settings_window.py       # 設定 GUI（桌寵/一般/關於 三 Tab）+ 鬧鐘子區塊
  ui/pet_widget.py            # 桌寵浮動視窗（無框透明、拖曳、雙擊觸發、鬧鐘 tooltip）
  ui/notification_window.py   # RPG 對話氣泡通知
  sprites/sprite_loader.py    # PNG 載入 + 快取
  sprites/animation.py        # 動畫狀態機（idle/counting/finished）
  sprites/generate_sprites.py # Pillow 素材生成腳本
  sprites/assets/             # 像素素材（7 角色 × 3 state × 2 frame = 42 PNG）
  config/settings.json        # 使用者設定（gitignore）
```

## 開發階段
- Phase 1: 核心引擎（系統匣 + 熱鍵 + 計時 + QMessageBox 通知）✅
- Phase 2: 設定 GUI（PySide6 三 Tab 設定視窗 + 熱鍵錄製 + 衝突偵測）✅
- Phase 3: 桌寵觸發系統 + 像素動畫 ✅
- Phase 3.5: 強制置頂（Win32 SetWindowPos）+ 角色換血（6 角色）✅
- Phase 4: Bug 修復 + 角色增強（置頂 event hook + 描邊閃爍 + 小雞 + 中文名 + 史奴比重繪）✅
- Phase 4.1: Snoopy outline-first 重繪 + 動畫行為調整 + 死碼清理 ✅
- Phase 4.2: Snoopy BRIK 像素圖案直抄 + 42×40 尺寸對齊 ✅
- Phase 5: Cron 鬧鐘功能（每隻桌寵定時自動提醒 + 設定 GUI）✅
- Phase 6: GUI 像素風古早遊戲介面
- Phase 7: PyInstaller 打包

## 開發指令
```bash
# 還原 .venv（重開機後或首次 clone）
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt

# 啟動
.venv/Scripts/python main.py
```

## 架構重點
- 單一 PySide6 事件迴圈，不混用 threading/pygame
- 支援多組計時器同時運行
- 每隻桌寵 = 獨立 QWidget，自行管理拖曳與點擊事件
- 桌寵強制置頂：Win32 `SetWindowPos(HWND_TOPMOST)` 每 2 秒 re-assert
- 桌寵位置記錄在 config 中，重啟還原
- 可用角色：`orange_cat` / `white_cat` / `calico` / `snoopy` / `shiba` / `goblin` / `chick`
- 角色中文名對照：`core/constants.py` 的 `CHARACTER_DISPLAY_NAMES`
- 舊 config 自動遷移（`cat` → `orange_cat`、`dog` → `shiba`）

## 注意事項
- `config/settings.json` 在 `.gitignore` 中，首次執行自動生成預設值
