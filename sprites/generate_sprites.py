"""
Pixel sprite generator for Pixel Timer.
Produces 36 PNG files: 6 characters x 3 states x 2 frames = 36
Canvas: 48x48 RGBA
"""

from pathlib import Path
from PIL import Image, ImageDraw

COLORS = {
    "orange_cat": {"body": (255, 152, 0, 255), "dark": (200, 110, 0, 255), "eye": (30, 30, 30, 255)},
    "white_cat":  {"body": (240, 240, 240, 255), "dark": (189, 189, 189, 255), "eye": (30, 30, 30, 255), "pink": (244, 143, 177, 255)},
    "calico":     {"body": (250, 250, 250, 255), "dark": (158, 158, 158, 255), "eye": (30, 30, 30, 255), "orange": (255, 152, 0, 255), "black": (50, 50, 50, 255)},
    "snoopy":     {"body": (250, 250, 250, 255), "dark": (33, 33, 33, 255), "eye": (30, 30, 30, 255), "collar": (244, 67, 54, 255)},
    "shiba":      {"body": (255, 171, 64, 255), "dark": (121, 85, 72, 255), "eye": (30, 30, 30, 255), "white": (255, 248, 225, 255)},
    "goblin":     {"body": (76, 175, 80, 255), "dark": (40, 120, 45, 255), "eye": (255, 220, 0, 255)},
}

TRANSPARENT = (0, 0, 0, 0)
WHITE       = (255, 255, 255, 255)
SPARKLE     = (255, 240, 80, 255)
W, H = 48, 48

def new_img():
    return Image.new("RGBA", (W, H), TRANSPARENT)

def brighter(color, amount=40):
    r, g, b, a = color
    return (min(255, r + amount), min(255, g + amount), min(255, b + amount), a)

def counting_tint(character):
    return brighter(COLORS[character]["body"], 50)

def draw_orange_cat(img, dy=0, tint=None, sparkles=None):
    d = ImageDraw.Draw(img)
    c = COLORS["orange_cat"]
    body = tint if tint else c["body"]
    dark = c["dark"]
    d.rectangle([16, 24+dy, 31, 38+dy], fill=body)
    d.rectangle([14, 14+dy, 33, 27+dy], fill=body)
    d.polygon([(14, 14+dy), (14, 7+dy), (20, 14+dy)], fill=dark)
    d.polygon([(33, 14+dy), (33, 7+dy), (27, 14+dy)], fill=dark)
    d.rectangle([17, 18+dy, 19, 20+dy], fill=c["eye"])
    d.rectangle([28, 18+dy, 30, 20+dy], fill=c["eye"])
    d.rectangle([22, 22+dy, 25, 23+dy], fill=dark)
    d.rectangle([31, 32+dy, 38, 34+dy], fill=body)
    d.rectangle([36, 28+dy, 38, 33+dy], fill=body)
    d.rectangle([17, 38+dy, 20, 43+dy], fill=dark)
    d.rectangle([27, 38+dy, 30, 43+dy], fill=dark)
    if sparkles:
        for sx, sy in sparkles: d.rectangle([sx, sy, sx+1, sy+1], fill=SPARKLE)

def draw_white_cat(img, dy=0, tint=None, sparkles=None):
    d = ImageDraw.Draw(img)
    c = COLORS["white_cat"]
    body = tint if tint else c["body"]
    dark = c["dark"]
    pink = c["pink"]
    d.rectangle([16, 24+dy, 31, 38+dy], fill=body)
    d.rectangle([14, 14+dy, 33, 27+dy], fill=body)
    d.polygon([(14, 14+dy), (14, 7+dy), (20, 14+dy)], fill=dark)
    d.polygon([(33, 14+dy), (33, 7+dy), (27, 14+dy)], fill=dark)
    d.rectangle([15, 10+dy, 17, 13+dy], fill=pink)
    d.rectangle([30, 10+dy, 32, 13+dy], fill=pink)
    d.rectangle([17, 18+dy, 19, 20+dy], fill=c["eye"])
    d.rectangle([28, 18+dy, 30, 20+dy], fill=c["eye"])
    d.rectangle([22, 22+dy, 25, 23+dy], fill=dark)
    d.rectangle([31, 32+dy, 38, 34+dy], fill=body)
    d.rectangle([36, 28+dy, 38, 33+dy], fill=body)
    d.rectangle([17, 38+dy, 20, 43+dy], fill=dark)
    d.rectangle([27, 38+dy, 30, 43+dy], fill=dark)
    if sparkles:
        for sx, sy in sparkles: d.rectangle([sx, sy, sx+1, sy+1], fill=SPARKLE)

def draw_calico(img, dy=0, tint=None, sparkles=None):
    d = ImageDraw.Draw(img)
    c = COLORS["calico"]
    body = tint if tint else c["body"]
    dark = c["dark"]
    orange = c["orange"]
    black = c["black"]
    d.rectangle([16, 24+dy, 31, 38+dy], fill=body)
    d.rectangle([14, 14+dy, 33, 27+dy], fill=body)
    d.polygon([(14, 14+dy), (14, 7+dy), (20, 14+dy)], fill=dark)
    d.polygon([(33, 14+dy), (33, 7+dy), (27, 14+dy)], fill=dark)
    d.rectangle([14, 14+dy, 22, 22+dy], fill=orange)
    d.rectangle([24, 28+dy, 31, 38+dy], fill=black)
    d.rectangle([31, 32+dy, 38, 34+dy], fill=orange)
    d.rectangle([36, 28+dy, 38, 33+dy], fill=orange)
    d.rectangle([17, 18+dy, 19, 20+dy], fill=c["eye"])
    d.rectangle([28, 18+dy, 30, 20+dy], fill=c["eye"])
    d.rectangle([22, 22+dy, 25, 23+dy], fill=dark)
    d.rectangle([17, 38+dy, 20, 43+dy], fill=dark)
    d.rectangle([27, 38+dy, 30, 43+dy], fill=dark)
    if sparkles:
        for sx, sy in sparkles: d.rectangle([sx, sy, sx+1, sy+1], fill=SPARKLE)

def draw_snoopy(img, dy=0, tint=None, sparkles=None):
    d = ImageDraw.Draw(img)
    c = COLORS["snoopy"]
    body = tint if tint else c["body"]
    dark = c["dark"]
    collar = c["collar"]
    d.rectangle([14, 24+dy, 33, 38+dy], fill=body)
    d.rectangle([12, 13+dy, 35, 27+dy], fill=body)
    d.rectangle([9, 14+dy, 14, 26+dy], fill=dark)
    d.rectangle([34, 14+dy, 39, 26+dy], fill=dark)
    d.rectangle([17, 17+dy, 19, 19+dy], fill=c["eye"])
    d.rectangle([28, 17+dy, 30, 19+dy], fill=c["eye"])
    d.rectangle([19, 21+dy, 28, 21+dy], fill=dark)
    d.rectangle([22, 21+dy, 25, 23+dy], fill=dark)
    d.rectangle([13, 27+dy, 34, 30+dy], fill=collar)
    d.rectangle([33, 27+dy, 36, 30+dy], fill=body)
    d.rectangle([35, 24+dy, 38, 28+dy], fill=body)
    d.rectangle([15, 38+dy, 19, 43+dy], fill=dark)
    d.rectangle([28, 38+dy, 32, 43+dy], fill=dark)
    if sparkles:
        for sx, sy in sparkles: d.rectangle([sx, sy, sx+1, sy+1], fill=SPARKLE)

def draw_shiba(img, dy=0, tint=None, sparkles=None):
    d = ImageDraw.Draw(img)
    c = COLORS["shiba"]
    body = tint if tint else c["body"]
    dark = c["dark"]
    white = c["white"]
    d.rectangle([14, 24+dy, 33, 38+dy], fill=body)
    d.rectangle([12, 13+dy, 35, 27+dy], fill=body)
    d.rectangle([9, 14+dy, 14, 22+dy], fill=dark)
    d.rectangle([34, 14+dy, 39, 22+dy], fill=dark)
    d.rectangle([16, 20+dy, 31, 27+dy], fill=white)
    d.rectangle([17, 27+dy, 30, 36+dy], fill=white)
    d.rectangle([17, 17+dy, 19, 19+dy], fill=c["eye"])
    d.rectangle([28, 17+dy, 30, 19+dy], fill=c["eye"])
    d.rectangle([22, 21+dy, 25, 23+dy], fill=dark)
    d.rectangle([33, 26+dy, 36, 29+dy], fill=body)
    d.rectangle([35, 23+dy, 38, 27+dy], fill=body)
    d.rectangle([15, 38+dy, 19, 43+dy], fill=dark)
    d.rectangle([28, 38+dy, 32, 43+dy], fill=dark)
    if sparkles:
        for sx, sy in sparkles: d.rectangle([sx, sy, sx+1, sy+1], fill=SPARKLE)

def draw_goblin(img, dy=0, tint=None, sparkles=None):
    d = ImageDraw.Draw(img)
    c = COLORS["goblin"]
    body = tint if tint else c["body"]
    dark = c["dark"]
    d.rectangle([16, 25+dy, 31, 38+dy], fill=body)
    d.rectangle([15, 13+dy, 32, 26+dy], fill=body)
    d.polygon([(15, 18+dy), (9, 14+dy), (15, 22+dy)], fill=dark)
    d.polygon([(32, 18+dy), (38, 14+dy), (32, 22+dy)], fill=dark)
    d.rectangle([17, 17+dy, 20, 20+dy], fill=c["eye"])
    d.rectangle([27, 17+dy, 30, 20+dy], fill=c["eye"])
    d.rectangle([19, 23+dy, 28, 24+dy], fill=dark)
    d.rectangle([20, 24+dy, 21, 25+dy], fill=WHITE)
    d.rectangle([26, 24+dy, 27, 25+dy], fill=WHITE)
    d.rectangle([10, 25+dy, 16, 27+dy], fill=body)
    d.rectangle([9, 23+dy, 12, 26+dy], fill=body)
    d.rectangle([31, 25+dy, 37, 27+dy], fill=body)
    d.rectangle([35, 23+dy, 38, 26+dy], fill=body)
    d.rectangle([17, 38+dy, 21, 43+dy], fill=dark)
    d.rectangle([26, 38+dy, 30, 43+dy], fill=dark)
    if sparkles:
        for sx, sy in sparkles: d.rectangle([sx, sy, sx+1, sy+1], fill=SPARKLE)

SPARKLES = {0: [(6,10),(40,8),(8,36),(42,34),(23,5)], 1: [(4,20),(43,14),(5,42),(39,40),(38,22)]}

DRAW_FN = {
    "orange_cat": draw_orange_cat,
    "white_cat":  draw_white_cat,
    "calico":     draw_calico,
    "snoopy":     draw_snoopy,
    "shiba":      draw_shiba,
    "goblin":     draw_goblin,
}

def generate_all(base_path: Path):
    for character, draw_fn in DRAW_FN.items():
        char_dir = base_path / character
        char_dir.mkdir(parents=True, exist_ok=True)
        for frame in (0, 1):
            dy = 0 if frame == 0 else 1
            img = new_img(); draw_fn(img, dy=dy); img.save(char_dir / f"idle_{frame}.png")
        tint = counting_tint(character)
        for frame in (0, 1):
            dy = 0 if frame == 0 else -1
            img = new_img(); draw_fn(img, dy=dy, tint=tint); img.save(char_dir / f"counting_{frame}.png")
        for frame in (0, 1):
            dy = -6 if frame == 0 else -8
            img = new_img(); draw_fn(img, dy=dy, sparkles=SPARKLES[frame]); img.save(char_dir / f"finished_{frame}.png")
        print(f"[generate_sprites] {character}: 6 frames written to {char_dir}")

if __name__ == "__main__":
    base = Path(__file__).parent / "assets"
    generate_all(base)
    expected = [f"{ch}/{st}_{fr}.png" for ch in ("orange_cat","white_cat","calico","snoopy","shiba","goblin") for st in ("idle","counting","finished") for fr in (0,1)]
    missing = [f for f in expected if not (base / f).exists()]
    if missing: print(f"[ERROR] Missing files: {missing}")
    else: print(f"[OK] All {len(expected)} PNG files generated.")
