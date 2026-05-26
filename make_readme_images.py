"""
Generate README images for Pixel Timer GitHub page.
Outputs:
  docs/screenshots/all_characters.png
  docs/screenshots/desktop.png
  docs/screenshots/bubble.png
  docs/screenshots/settings.png
  docs/preview.gif
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math, os

ROOT       = Path(__file__).parent
SPRITES    = ROOT / "sprites" / "assets"
FONTS_DIR  = ROOT / "assets" / "fonts"
OUT        = ROOT / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
(ROOT / "docs").mkdir(exist_ok=True)

# ── colour palette (warm retro theme) ──────────────────────────────────────
BG_ORANGE   = (245, 166, 35)       # #F5A623  checkered light tile
BG_DARK     = (220, 148, 28)       # checkered dark tile
CREAM       = (255, 241, 200)      # #FFF1C8  bubble fill
DARK_BLUE   = (26, 26, 46)         # #1A1A2E  desktop / RPG dark
BORDER_HI   = (226, 226, 226)      # #E2E2E2  bright border
BORDER_LO   = (136, 136, 170)      # #8888AA  dim border
TEXT_WARM   = (255, 241, 232)      # #FFF1E8  PICO-8 warm white
GOLD        = (255, 215, 0)        # #FFD700  gold accent
TASKBAR     = (30, 30, 50)

CHARACTERS = [
    ("orange_cat", "橘貓"),
    ("white_cat",  "白貓"),
    ("calico",     "三花貓"),
    ("snoopy",     "史努比"),
    ("shiba",      "柴犬"),
    ("goblin",     "哥布林"),
    ("chick",      "小雞"),
    ("blue_eyes",  "青眼白龍"),
]

CHARACTER_ACCENT = {
    "orange_cat": (230, 120, 30),
    "white_cat":  (180, 200, 220),
    "calico":     (200, 150, 100),
    "snoopy":     (60,  60,  60),
    "shiba":      (210, 140, 60),
    "goblin":     (80,  160, 80),
    "chick":      (240, 200, 40),
    "blue_eyes":  (30,  100, 220),
}

def load_font(size=12, mono=True):
    variant = "monospaced" if mono else "proportional"
    for px in (12, 16):
        p = FONTS_DIR / f"ark-pixel-{px}px-{variant}-zh_tw.ttf"
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    return ImageFont.load_default()

def load_cjk_font(size=14):
    """System CJK font with full Traditional Chinese coverage."""
    candidates = [
        "C:/Windows/Fonts/msjh.ttc",    # Microsoft JhengHei (Traditional Chinese)
        "C:/Windows/Fonts/msyh.ttc",    # Microsoft YaHei (Simplified Chinese, still covers most TC)
        "C:/Windows/Fonts/simsun.ttc",  # SimSun
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return load_font(size)

def load_sprite(char, state="idle", frame=0, scale=1):
    p = SPRITES / char / f"{state}_{frame}.png"
    img = Image.open(p).convert("RGBA")
    if scale != 1:
        w, h = img.size
        img = img.resize((w * scale, h * scale), Image.NEAREST)
    return img

def checkerboard(w, h, tile=8):
    img = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            c = BG_ORANGE if ((x // tile + y // tile) % 2 == 0) else BG_DARK
            draw.rectangle([x, y, x + tile - 1, y + tile - 1], fill=c)
    return img

def pixel_border(draw, rect, color, width=2):
    x0, y0, x1, y1 = rect
    for i in range(width):
        draw.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], outline=color)

# ── 1. ALL CHARACTERS banner ────────────────────────────────────────────────
def make_all_characters():
    SCALE    = 3        # 48 → 144 px per sprite (leaves room for labels)
    CELL_W   = 200
    CELL_H   = 240
    PADDING  = 16
    LABEL_H  = 40
    COLS     = 4
    ROWS     = 2

    W = COLS * CELL_W + PADDING * 2
    H = ROWS * CELL_H + PADDING * 2 + 60   # +60 for title

    canvas = checkerboard(W, H, tile=10)
    draw   = ImageDraw.Draw(canvas)

    # title
    font_title = load_cjk_font(18)
    title = "[ Pixel Timer — 角色陣容 ]"
    tw = draw.textlength(title, font=font_title)
    draw.text(((W - tw) // 2, PADDING), title, font=font_title, fill=GOLD)

    font_label = load_cjk_font(16)
    font_sub   = load_font(12, mono=False)

    for idx, (char, name) in enumerate(CHARACTERS):
        col = idx % COLS
        row = idx // COLS
        cx  = PADDING + col * CELL_W + CELL_W // 2
        cy  = PADDING + 60 + row * CELL_H

        # card background
        card_x0 = cx - CELL_W // 2 + 8
        card_y0 = cy
        card_x1 = cx + CELL_W // 2 - 8
        card_y1 = cy + CELL_H - 8

        # card fill (semi-dark)
        card_bg = Image.new("RGBA", (card_x1 - card_x0, card_y1 - card_y0), (20, 20, 40, 200))
        canvas.alpha_composite(card_bg, (card_x0, card_y0))

        # accent border
        accent = CHARACTER_ACCENT.get(char, BORDER_HI)
        d2 = ImageDraw.Draw(canvas)
        pixel_border(d2, (card_x0, card_y0, card_x1, card_y1), accent, 2)
        pixel_border(d2, (card_x0 + 3, card_y0 + 3, card_x1 - 3, card_y1 - 3), BORDER_LO, 1)

        # sprite (idle_0), seated in the upper part of the card
        sprite = load_sprite(char, "idle", 0, scale=SCALE)
        sw, sh = sprite.size
        sx = cx - sw // 2
        sy = card_y0 + 18
        canvas.alpha_composite(sprite, (sx, sy))

        # labels anchored to the card bottom so they always sit inside the border
        name_w = draw.textlength(name, font=font_label)
        draw.text((cx - name_w // 2, card_y1 - 48), name, font=font_label, fill=TEXT_WARM)

        eng_w = draw.textlength(char, font=font_sub)
        draw.text((cx - eng_w // 2, card_y1 - 26), char, font=font_sub, fill=(GOLD[0], GOLD[1], GOLD[2], 160))

    # outer border
    pixel_border(draw, (2, 2, W - 3, H - 3), BORDER_HI, 2)
    pixel_border(draw, (5, 5, W - 6, H - 6), BORDER_LO, 1)

    out_path = OUT / "all_characters.png"
    canvas.save(out_path)
    print(f"Saved: {out_path}")

# ── 2. DESKTOP mockup ───────────────────────────────────────────────────────
def make_desktop():
    W, H = 800, 500
    canvas = Image.new("RGBA", (W, H), DARK_BLUE)
    draw   = ImageDraw.Draw(canvas)

    # subtle grid lines (desktop feel)
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=(40, 40, 70, 60))
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=(40, 40, 70, 60))

    # taskbar
    TB = 36
    taskbar = Image.new("RGBA", (W, TB), TASKBAR)
    tb_draw = ImageDraw.Draw(taskbar)
    tb_draw.line([(0, 0), (W, 0)], fill=BORDER_LO)
    canvas.alpha_composite(taskbar, (0, H - TB))

    # system tray clock
    font_sm = load_font(12)
    draw.text((W - 70, H - 26), "22:00", font=font_sm, fill=TEXT_WARM)

    # top-left desktop label
    font_cjk_sm = load_cjk_font(13)
    draw.text((20, 16), "Pixel Timer  ·  系統匣常駐中", font=font_cjk_sm, fill=BORDER_LO)

    # pets standing on the taskbar (feet rest on taskbar top, never clipped)
    SCALE  = 3
    feet_y = H - TB
    pets_placed = [
        ("orange_cat", "idle",     0, 150),
        ("shiba",      "idle",     0, 380),
        ("chick",      "counting", 0, 600),
    ]
    chick_cx = chick_top = None
    for char, state, frame, px in pets_placed:
        sprite = load_sprite(char, state, frame, scale=SCALE)
        sw, sh = sprite.size
        py = feet_y - sh
        canvas.alpha_composite(sprite, (px, py))
        if char == "chick":
            chick_cx, chick_top = px + sw // 2, py

    # notification bubble above the chick — tail points down onto its head
    bw, bh = 240, 64
    bx = chick_cx - bw + 24      # _draw_bubble tail sits at bx+bw-20 ≈ chick_cx
    by = chick_top - bh - 18
    _draw_bubble(canvas, bx, by, bw, bh, "時間到！休息一下～", "chick")

    out_path = OUT / "desktop.png"
    canvas.save(out_path)
    print(f"Saved: {out_path}")

def _draw_bubble(canvas, bx, by, bw, bh, text, char):
    draw = ImageDraw.Draw(canvas)
    accent = CHARACTER_ACCENT.get(char, BORDER_HI)

    # shadow
    shadow = Image.new("RGBA", (bw + 4, bh + 4), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([0, 0, bw + 3, bh + 3], radius=4, fill=(0, 0, 0, 100))
    canvas.alpha_composite(shadow, (bx + 2, by + 2))

    # bubble fill
    bubble = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bubble)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=4, fill=CREAM)
    # accent border (3px)
    for i in range(3):
        bd.rounded_rectangle([i, i, bw - 1 - i, bh - 1 - i], radius=4 - i,
                               outline=accent if i == 0 else (*accent, 180) if i == 1 else BORDER_LO)
    canvas.alpha_composite(bubble, (bx, by))

    # tail pointing down-right
    tail_pts = [(bx + bw - 30, by + bh - 1),
                (bx + bw - 15, by + bh + 14),
                (bx + bw - 10, by + bh - 1)]
    draw.polygon(tail_pts, fill=CREAM, outline=accent)

    # text
    font = load_cjk_font(14)
    draw.text((bx + 12, by + (bh - 18) // 2), text, font=font, fill=(40, 30, 20))

# ── 3. BUBBLE close-up ──────────────────────────────────────────────────────
def make_bubble():
    W, H = 520, 280
    canvas = Image.new("RGBA", (W, H), DARK_BLUE)
    draw   = ImageDraw.Draw(canvas)

    # bg grid
    for x in range(0, W, 32):
        draw.line([(x, 0), (x, H)], fill=(50, 50, 80, 80))
    for y in range(0, H, 32):
        draw.line([(0, y), (W, y)], fill=(50, 50, 80, 80))

    # caption (top) — drawn first so nothing else sits in this band
    font_cjk_sm = load_cjk_font(13)
    draw.text((14, 12), "RPG 對話氣泡  ·  打字機逐字效果  ·  點擊關閉",
              font=font_cjk_sm, fill=BORDER_LO)

    SCALE = 3
    # pet (orange_cat finished), feet near bottom
    sprite = load_sprite("orange_cat", "finished", 0, scale=SCALE)
    sw, sh = sprite.size
    pet_x = 70
    pet_y = H - sh - 40
    canvas.alpha_composite(sprite, (pet_x, pet_y))

    # star effect — clustered above the pet's head, safely below the caption band
    star_font = load_cjk_font(16)
    head_cx = pet_x + sw // 2
    for sx, sy in [(head_cx - 38, pet_y - 20),
                   (head_cx + 22, pet_y - 28),
                   (head_cx - 6,  pet_y - 38)]:
        draw.text((sx, sy), "★", font=star_font, fill=(255, 230, 70))

    # bubble — right of the pet, vertically centred on it
    bw, bh = 250, 84
    bx = pet_x + sw + 20
    by = pet_y + (sh - bh) // 2
    text = "休息一下！(^▽^)/"
    _draw_bubble(canvas, bx, by, bw, bh, text, "orange_cat")

    # typewriter cursor — measured, placed right after the text
    font_txt = load_cjk_font(14)
    tw = draw.textlength(text, font=font_txt)
    draw.text((bx + 12 + tw + 3, by + (bh - 18) // 2), "▌", font=font_txt, fill=GOLD)

    # outer border
    pixel_border(draw, (2, 2, W - 3, H - 3), BORDER_HI, 2)

    out_path = OUT / "bubble.png"
    canvas.save(out_path)
    print(f"Saved: {out_path}")

# ── 4. SETTINGS window mockup ────────────────────────────────────────────────
def make_settings():
    W, H = 540, 470

    # checkerboard base (warm retro)
    canvas = checkerboard(W, H, tile=10)
    draw   = ImageDraw.Draw(canvas)

    font_cjk_title = load_cjk_font(15)
    font_cjk       = load_cjk_font(14)
    font_cjk_sm    = load_cjk_font(12)
    font_eng_sm    = load_font(12, mono=False)

    # ── pixel title bar ──
    TB_H = 34
    title_bar = Image.new("RGBA", (W, TB_H), TASKBAR)
    tb = ImageDraw.Draw(title_bar)
    tb.text((12, (TB_H - 18) // 2), "Pixel Timer  —  設定", font=font_cjk_title, fill=TEXT_WARM)
    # pixel close button
    cb = TB_H - 8
    cx0 = W - cb - 6
    cy0 = 4
    tb.rectangle([cx0, cy0, cx0 + cb, cy0 + cb], fill=(180, 60, 60))
    for i in range(2):
        tb.rectangle([cx0 + i, cy0 + i, cx0 + cb - i, cy0 + cb - i], outline=BORDER_HI)
    tb.line([(cx0 + 8, cy0 + 8), (cx0 + cb - 8, cy0 + cb - 8)], fill=TEXT_WARM, width=2)
    tb.line([(cx0 + cb - 8, cy0 + 8), (cx0 + 8, cy0 + cb - 8)], fill=TEXT_WARM, width=2)
    canvas.alpha_composite(title_bar, (0, 0))

    # ── tab row ──
    TAB_Y = TB_H + 6
    TAB_H = 30
    tabs = [("桌寵", True), ("一般", False), ("關於", False)]
    tx = 12
    for label, active in tabs:
        tw = int(draw.textlength(label, font=font_cjk)) + 28
        rect = (tx, TAB_Y, tx + tw, TAB_Y + TAB_H)
        if active:
            d = ImageDraw.Draw(canvas)
            d.rectangle(rect, fill=CREAM)
            pixel_border(d, rect, GOLD, 2)
            draw.text((tx + 14, TAB_Y + (TAB_H - 18) // 2), label, font=font_cjk, fill=(40, 30, 20))
        else:
            d = ImageDraw.Draw(canvas)
            tab_bg = Image.new("RGBA", (tw, TAB_H), (20, 20, 40, 200))
            canvas.alpha_composite(tab_bg, (tx, TAB_Y))
            pixel_border(ImageDraw.Draw(canvas), rect, BORDER_LO, 1)
            draw.text((tx + 14, TAB_Y + (TAB_H - 18) // 2), label, font=font_cjk, fill=BORDER_LO)
        tx += tw + 6

    # ── pet cards ──
    cards = [
        ("orange_cat", "橘貓", "180 秒", "「休息一下！」"),
        ("chick",      "小雞", "1500 秒", "「番茄鐘結束！」"),
        ("shiba",      "柴犬", "300 秒", "「喝水時間到～」"),
    ]
    card_x0 = 14
    card_x1 = W - 14
    card_h  = 84
    gap     = 10
    cy      = TAB_Y + TAB_H + 12

    for char, name, dur, msg in cards:
        # card body (semi-dark)
        card_bg = Image.new("RGBA", (card_x1 - card_x0, card_h), (20, 20, 40, 205))
        canvas.alpha_composite(card_bg, (card_x0, cy))
        accent = CHARACTER_ACCENT.get(char, BORDER_HI)
        dd = ImageDraw.Draw(canvas)
        pixel_border(dd, (card_x0, cy, card_x1, cy + card_h), accent, 2)
        pixel_border(dd, (card_x0 + 3, cy + 3, card_x1 - 3, cy + card_h - 3), BORDER_LO, 1)

        # sprite thumbnail (native 48px, vertically centered)
        sprite = load_sprite(char, "idle", 0, scale=1)
        sw, sh = sprite.size
        canvas.alpha_composite(sprite, (card_x0 + 16, cy + (card_h - sh) // 2))

        text_x = card_x0 + 16 + sw + 18
        # name + english id
        draw.text((text_x, cy + 12), name, font=font_cjk, fill=TEXT_WARM)
        nw = draw.textlength(name, font=font_cjk)
        draw.text((text_x + nw + 10, cy + 14), char, font=font_eng_sm, fill=(GOLD[0], GOLD[1], GOLD[2], 170))
        # duration + message
        draw.text((text_x, cy + 38), f"倒數 {dur}", font=font_cjk_sm, fill=GOLD)
        draw.text((text_x, cy + 58), msg, font=font_cjk_sm, fill=TEXT_WARM)

        # delete button [×]
        db = 22
        dx0 = card_x1 - db - 12
        dy0 = cy + 12
        dd.rectangle([dx0, dy0, dx0 + db, dy0 + db], fill=(80, 30, 30))
        pixel_border(dd, (dx0, dy0, dx0 + db, dy0 + db), BORDER_LO, 1)
        dd.line([(dx0 + 6, dy0 + 6), (dx0 + db - 6, dy0 + db - 6)], fill=(220, 120, 120), width=2)
        dd.line([(dx0 + db - 6, dy0 + 6), (dx0 + 6, dy0 + db - 6)], fill=(220, 120, 120), width=2)

        cy += card_h + gap

    # ── "+ 新增桌寵" button ──
    btn_w = 150
    btn_h = 32
    bx0 = (W - btn_w) // 2
    by0 = cy + 6
    bd = ImageDraw.Draw(canvas)
    btn_bg = Image.new("RGBA", (btn_w, btn_h), (40, 90, 50, 220))
    canvas.alpha_composite(btn_bg, (bx0, by0))
    pixel_border(bd, (bx0, by0, bx0 + btn_w, by0 + btn_h), (120, 200, 120), 2)
    plus_txt = "+ 新增桌寵"
    pw = bd.textlength(plus_txt, font=font_cjk)
    bd.text((bx0 + (btn_w - pw) // 2, by0 + (btn_h - 18) // 2), plus_txt, font=font_cjk, fill=TEXT_WARM)

    # ── window outer border ──
    pixel_border(draw, (1, 1, W - 2, H - 2), BORDER_HI, 2)

    out_path = OUT / "settings.png"
    canvas.save(out_path)
    print(f"Saved: {out_path}")

# ── 5. ANIMATED GIF preview ─────────────────────────────────────────────────
def make_preview_gif():
    W, H   = 640, 200
    SCALE  = 3
    FRAMES = []

    # show 4 pets in a row, cycling through idle/counting/finished
    pets_row = [
        ("orange_cat", 340),
        ("chick",      440),
        ("shiba",      200),
        ("goblin",     540),
    ]

    def make_frame(states_frames):
        canvas = Image.new("RGBA", (W, H), DARK_BLUE)
        draw   = ImageDraw.Draw(canvas)
        for x in range(0, W, 32):
            draw.line([(x, 0), (x, H)], fill=(40, 40, 65, 70))
        for y in range(0, H, 32):
            draw.line([(0, y), (W, y)], fill=(40, 40, 65, 70))

        font_gif = load_cjk_font(13)
        draw.text((12, 10), "Pixel Timer  —  桌面常駐中", font=font_gif, fill=BORDER_LO)

        for (char, px), (state, frame) in zip(pets_row, states_frames):
            sprite = load_sprite(char, state, frame, scale=SCALE)
            sw, sh = sprite.size
            py = H - sh - 10
            canvas.alpha_composite(sprite, (px, py))
        return canvas.convert("P", palette=Image.ADAPTIVE, colors=256)

    # sequence: idle flicker × 6, then counting × 6, then finished × 4
    sequence = []
    for _ in range(6):
        sequence.append([("idle", 0)] * 4)
        sequence.append([("idle", 1)] * 4)
    for _ in range(6):
        sequence.append([("counting", 0)] * 4)
        sequence.append([("counting", 1)] * 4)
    for _ in range(4):
        sequence.append([("finished", 0)] * 4)
        sequence.append([("finished", 1)] * 4)

    frames = [make_frame(sf) for sf in sequence]

    out_path = ROOT / "docs" / "preview.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=300,
        disposal=2,
    )
    print(f"Saved: {out_path}")

# ── run all ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating README images...")
    make_all_characters()
    make_desktop()
    make_bubble()
    make_settings()
    make_preview_gif()
    print("Done!")
