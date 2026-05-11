# Pixel Timer — Windows 像素風計時提醒器

## 專案概述
Windows 桌面小工具：工具列旁的像素桌寵觸發倒數計時，時間到後桌寵播放動畫 + RPG 對話氣泡提醒。

## 技術棧
- Python 3.12+ / PySide6（GUI + 動畫 + 系統匣）
- JSON 配置檔
- PyInstaller 打包
- 注：`keyboard` 套件保留於 Phase 1 遺留代碼，Phase 3 起將移除，改用桌寵點擊觸發

## 專案結構
```
pixel_timer/
  main.py                     # 入口
  core/config_manager.py      # 設定讀寫
  core/timer_engine.py        # QTimer 計時引擎
  core/hotkey_manager.py      # [遺留] 全域熱鍵，Phase 3 後移除
  ui/tray_app.py              # QSystemTrayIcon 系統匣主程式
  ui/settings_window.py       # [Phase 2] 設定 GUI ✅
  ui/pet_widget.py            # [Phase 3] 桌寵浮動視窗（觸發器）
  ui/notification_window.py   # [Phase 3] 計時結束通知動畫
  sprites/sprite_loader.py    # [Phase 3] Sprite sheet 解析
  sprites/animation.py        # [Phase 3] 動畫狀態機
  sprites/assets/             # 像素素材（cat/dog/goblin）
  config/settings.json        # 使用者設定（gitignore）
```

## 開發階段
- Phase 1: 核心引擎（系統匣 + 熱鍵 + 計時 + QMessageBox 通知）✅
- Phase 2: 設定 GUI（PySide6 三 Tab 設定視窗 + 熱鍵錄製 + 衝突偵測）✅
- Phase 3: 桌寵觸發系統 + 像素動畫（方向重定義，見下方說明）
- Phase 4: PyInstaller 打包

## Phase 3 方向重定義（2026-05-11 決定）
**原方案：** 快捷鍵觸發 → 桌寵從角落走出通知
**新方案：** 桌寵常駐工具列旁 → 雙擊觸發計時 → 計時結束桌寵播放通知動畫

核心變更：
- 桌寵從「通知角色」變成「觸發器 + 通知角色」
- 每組計時器綁定一隻桌寵（如：狗=3分鐘、貓=5分鐘、鳥=25分鐘）
- 桌寵為無框透明浮動視窗（FramelessWindowHint + WindowStaysOnTopHint）
- 可拖曳擺放位置（mousePressEvent/mouseMoveEvent）
- 雙擊 = 開始/取消計時（toggle）
- 計時中桌寵有視覺反饋（動畫/顏色變化）
- `keyboard` 套件 + `hotkey_manager.py` 可移除，不再需要管理員權限
- 設定 GUI 的「熱鍵」Tab 改為「桌寵」Tab（綁定角色 + 時長 + 訊息）

## 開發指令
```bash
# 啟動
.venv/Scripts/python main.py

# 安裝依賴
.venv/Scripts/pip install -r requirements.txt
```

## 架構重點
- 單一 PySide6 事件迴圈，不混用 threading/pygame
- 支援多組計時器同時運行
- 每隻桌寵 = 獨立 QWidget，自行管理拖曳與點擊事件
- 桌寵位置記錄在 config 中，重啟還原

## 注意事項
- `config/settings.json` 在 `.gitignore` 中，首次執行自動生成預設值
