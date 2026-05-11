# Pixel Timer — Windows 像素風計時提醒器

## 專案概述
Windows 桌面小工具：全域快捷鍵觸發倒數計時，時間到後以 8-bit 像素風桌寵從螢幕角落走出、顯示 RPG 對話氣泡提醒。

## 技術棧
- Python 3.12+ / PySide6（GUI + 動畫 + 系統匣）
- `keyboard` 套件（全域熱鍵）
- JSON 配置檔
- PyInstaller 打包

## 專案結構
```
pixel_timer/
  main.py                     # 入口
  core/config_manager.py      # 設定讀寫
  core/timer_engine.py        # QTimer 計時引擎
  core/hotkey_manager.py      # 全域熱鍵（keyboard 套件 + Qt signal bridge）
  ui/tray_app.py              # QSystemTrayIcon 系統匣主程式
  ui/settings_window.py       # [Phase 2] 設定 GUI
  ui/notification_window.py   # [Phase 3] 桌寵通知視窗
  sprites/sprite_loader.py    # [Phase 3] Sprite sheet 解析
  sprites/animation.py        # [Phase 3] 動畫狀態機
  sprites/assets/             # 像素素材（cat/dog/goblin）
  config/settings.json        # 使用者設定（gitignore）
```

## 開發階段
- Phase 1: 核心引擎（系統匣 + 熱鍵 + 計時 + QMessageBox 通知）✅
- Phase 2: 設定 GUI（PySide6 三 Tab 設定視窗）
- Phase 3: 像素動畫系統（透明視窗 + sprite 動畫 + 對話氣泡 + 狀態機）
- Phase 4: PyInstaller 打包

## 開發指令
```bash
# 啟動
.venv/Scripts/python main.py

# 安裝依賴
.venv/Scripts/pip install -r requirements.txt
```

## 架構重點
- 單一 PySide6 事件迴圈，不混用 threading/pygame
- `keyboard` 套件 callback 在背景執行緒 → 透過 `HotkeyBridge(QObject)` 的 Signal 派發到主執行緒
- 同一快捷鍵再按一次 = 取消計時（toggle 行為）
- 支援多組計時器同時運行

## 注意事項
- `keyboard` 套件在某些環境需要管理員權限
- `config/settings.json` 在 `.gitignore` 中，首次執行自動生成預設值
