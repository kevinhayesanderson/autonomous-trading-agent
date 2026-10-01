#!/usr/bin/env python3
"""
Autonomous Quantitative Trading Agent - Moody Luxury Social Preview Generator
Generates an iconic, world-class institutional 1280x640 social preview banner
grounded in the Moody Luxury Color Palette: Champagne, Rose Gold & Black Cherry.

Exact Swatches:
- Champagne:         #EFE1CE (239, 225, 206)
- Champagne Bright:  #FAF3EA (250, 243, 234)
- Rose Gold:         #B9857C (185, 133, 124)
- Rose Gold Light:   #D69E94 (214, 158, 148)
- Black Cherry:      #721D35 (114, 29, 53)
- Black Cherry Dark: #42121F (66, 18, 31)
- Near Black:        #1C0B12 (28, 11, 18)
- Velvet Noir:       #10050A (16, 5, 10)
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_PATH = os.path.join(REPO_ROOT, "assets", "social_preview.jpg")

W_FINAL, H_FINAL = 1280, 640
SCALE = 2
W, H = W_FINAL * SCALE, H_FINAL * SCALE

# Luxury Palette Constants
COLOR_CHAMPAGNE = (239, 225, 206)        # #EFE1CE
COLOR_CHAMPAGNE_BRIGHT = (250, 243, 234) # #FAF3EA
COLOR_ROSE_GOLD = (185, 133, 124)        # #B9857C
COLOR_ROSE_GOLD_LIGHT = (214, 158, 148)  # #D69E94
COLOR_BLACK_CHERRY = (114, 29, 53)       # #721D35
COLOR_BLACK_CHERRY_DARK = (66, 18, 31)   # #42121F
COLOR_BLACK_CHERRY_VIVID = (138, 30, 60) # Rich illuminated velvet
COLOR_NEAR_BLACK = (28, 11, 18)          # #1C0B12
COLOR_VELVET_NOIR = (16, 5, 10)          # #10050A
COLOR_CASHMERE = (204, 182, 172)         # Muted taupe cashmere for subtext

def create_brand_banner():
    # 1. Base Canvas - Deep Velvet Noir
    base = Image.new("RGBA", (W, H), (*COLOR_VELVET_NOIR, 255))
    base_draw = ImageDraw.Draw(base)

    # Base horizontal gradient: Velvet Noir to Near Black
    for x in range(0, W, 4):
        t = x / W
        blend = math.sin(t * math.pi) ** 1.3
        r = int(COLOR_VELVET_NOIR[0] + (COLOR_NEAR_BLACK[0] - COLOR_VELVET_NOIR[0]) * blend)
        g = int(COLOR_VELVET_NOIR[1] + (COLOR_NEAR_BLACK[1] - COLOR_VELVET_NOIR[1]) * blend)
        b = int(COLOR_VELVET_NOIR[2] + (COLOR_NEAR_BLACK[2] - COLOR_VELVET_NOIR[2]) * blend)
        base_draw.line([(x, 0), (x, H)], fill=(r, g, b, 255), width=4)

    # 2. Rich Moody Ambient Lighting
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    # Major Bloom 1: Left Black Cherry / Wine Velvet behind Emblem
    cx1, cy1 = int(W * 0.16), int(H * 0.50)
    for r in range(int(H * 0.85), 0, -10):
        factor = (1.0 - (r / (H * 0.85))) ** 1.3
        alpha = int(80 * factor)
        glow_draw.ellipse((cx1 - r, cy1 - r, cx1 + r, cy1 + r), fill=(*COLOR_BLACK_CHERRY_VIVID, alpha))
    for r in range(int(H * 0.45), 0, -8):
        factor = (1.0 - (r / (H * 0.45))) ** 1.2
        alpha = int(60 * factor)
        glow_draw.ellipse((cx1 - r, cy1 - r, cx1 + r, cy1 + r), fill=(*COLOR_BLACK_CHERRY, alpha))
    for r in range(int(H * 0.25), 0, -6):
        factor = (1.0 - (r / (H * 0.25))) ** 1.1
        alpha = int(45 * factor)
        glow_draw.ellipse((cx1 - r, cy1 - r, cx1 + r, cy1 + r), fill=(*COLOR_ROSE_GOLD, alpha))

    # Major Bloom 2: Center-Top Atmospheric Warmth
    cx_mid, cy_mid = int(W * 0.50), int(H * 0.08)
    for r in range(int(H * 0.65), 0, -12):
        factor = (1.0 - (r / (H * 0.65))) ** 1.4
        alpha = int(40 * factor)
        glow_draw.ellipse((cx_mid - r, cy_mid - r, cx_mid + r, cy_mid + r), fill=(*COLOR_BLACK_CHERRY_DARK, alpha))
    for r in range(int(H * 0.35), 0, -8):
        factor = (1.0 - (r / (H * 0.35))) ** 1.2
        alpha = int(24 * factor)
        glow_draw.ellipse((cx_mid - r, cy_mid - r, cx_mid + r, cy_mid + r), fill=(*COLOR_CHAMPAGNE, alpha))

    # Major Bloom 3: Far Right Quadrant behind Alpha Curve
    cx2, cy2 = int(W * 0.90), int(H * 0.35)
    for r in range(int(H * 0.75), 0, -10):
        factor = (1.0 - (r / (H * 0.75))) ** 1.4
        alpha = int(60 * factor)
        glow_draw.ellipse((cx2 - r, cy2 - r, cx2 + r, cy2 + r), fill=(*COLOR_BLACK_CHERRY, alpha))
    for r in range(int(H * 0.45), 0, -8):
        factor = (1.0 - (r / (H * 0.45))) ** 1.2
        alpha = int(48 * factor)
        glow_draw.ellipse((cx2 - r, cy2 - r, cx2 + r, cy2 + r), fill=(*COLOR_ROSE_GOLD, alpha))
    for r in range(int(H * 0.20), 0, -6):
        factor = (1.0 - (r / (H * 0.20))) ** 1.1
        alpha = int(50 * factor)
        glow_draw.ellipse((cx2 - r, cy2 - r, cx2 + r, cy2 + r), fill=(*COLOR_CHAMPAGNE, alpha))

    # Subtle Luminous Luxury Bokeh Circles
    bokeh_spots = [
        (int(W * 0.08), int(H * 0.18), int(80 * SCALE), COLOR_BLACK_CHERRY, 30),
        (int(W * 0.28), int(H * 0.85), int(110 * SCALE), COLOR_BLACK_CHERRY_DARK, 35),
        (int(W * 0.72), int(H * 0.15), int(95 * SCALE), COLOR_ROSE_GOLD, 25),
        (int(W * 0.82), int(H * 0.82), int(120 * SCALE), COLOR_BLACK_CHERRY_VIVID, 32),
        (int(W * 0.96), int(H * 0.65), int(75 * SCALE), COLOR_ROSE_GOLD_LIGHT, 24),
    ]
    for bx, by, br, bcol, balp in bokeh_spots:
        glow_draw.ellipse((bx - br, by - br, bx + br, by + br), fill=(*bcol, balp))

    glow = glow.filter(ImageFilter.GaussianBlur(radius=45 * SCALE))
    img = Image.alpha_composite(base, glow)
    draw = ImageDraw.Draw(img)

    # 3. Fine Technical Grid Dots (Delicate Champagne Starlight)
    dot_color = (*COLOR_CHAMPAGNE, 13)
    dot_step = 36 * SCALE
    for x in range(dot_step, W, dot_step):
        for y in range(dot_step, H, dot_step):
            draw.ellipse((x - 1 * SCALE, y - 1 * SCALE, x + 1 * SCALE, y + 1 * SCALE), fill=dot_color)

    # 4. Exponential Compounding Alpha Curve (Seamless Far Right Quadrant)
    curve_pts = []
    start_x = int(W * 0.78)
    end_x = int(W * 0.95)
    base_y = int(H * 0.80)
    peak_y = int(H * 0.22)

    for x in range(start_x, end_x, 4):
        t = (x - start_x) / (end_x - start_x)
        y = base_y - (base_y - peak_y) * (t ** 2.2) + math.sin(t * 8) * (3 * SCALE)
        curve_pts.append((x, int(y)))

    if len(curve_pts) > 2:
        # Seamless Area Fill without hard edge clipping
        area_mask = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        area_draw = ImageDraw.Draw(area_mask)
        # Vertical gradient slices under the curve for completely organic dissipation
        for idx in range(len(curve_pts) - 1):
            x1, y1 = curve_pts[idx]
            x2, y2 = curve_pts[idx + 1]
            t = (x1 - start_x) / (end_x - start_x)
            # Alpha increases smoothly towards peak
            alpha_col = int(32 * (t ** 1.5))
            area_draw.polygon([(x1, y1), (x2, y2), (x2, base_y), (x1, base_y)], fill=(*COLOR_BLACK_CHERRY_VIVID, alpha_col))

        area_mask = area_mask.filter(ImageFilter.GaussianBlur(radius=6 * SCALE))
        img = Image.alpha_composite(img, area_mask)
        draw = ImageDraw.Draw(img)

        # Baseline Sub-Axis
        draw.line([(start_x, base_y), (end_x + int(14 * SCALE), base_y)], fill=(*COLOR_ROSE_GOLD, 45), width=1 * SCALE)

        # Multi-pass Luminous Curve
        draw.line(curve_pts, fill=(*COLOR_BLACK_CHERRY_VIVID, 90), width=8 * SCALE)
        draw.line(curve_pts, fill=(*COLOR_ROSE_GOLD, 215), width=3 * SCALE)
        draw.line(curve_pts, fill=(*COLOR_CHAMPAGNE_BRIGHT, 255), width=1 * SCALE)

        # Target Apex Jewel Node
        px, py = curve_pts[-1]
        draw.ellipse((px - 14 * SCALE, py - 14 * SCALE, px + 14 * SCALE, py + 14 * SCALE), fill=(*COLOR_BLACK_CHERRY_VIVID, 110))
        draw.ellipse((px - 8 * SCALE, py - 8 * SCALE, px + 8 * SCALE, py + 8 * SCALE), fill=(*COLOR_ROSE_GOLD, 220))
        draw.ellipse((px - 3.5 * SCALE, py - 3.5 * SCALE, px + 3.5 * SCALE, py + 3.5 * SCALE), fill=(*COLOR_CHAMPAGNE_BRIGHT, 255))

    # 5. Fonts Resolution
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")

    def get_font(name: str, size: int):
        path = os.path.join(fonts_dir, name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size * SCALE)
            except Exception:
                pass
        return ImageFont.load_default()

    font_brand = get_font("bahnschrift.ttf", 72)       # Brand Mark
    font_title = get_font("segoeuib.ttf", 27)         # Headline
    font_sub = get_font("segoeui.ttf", 17)            # Subtitle
    font_badge = get_font("segoeuib.ttf", 12)         # Badges
    font_mono = get_font("consola.ttf", 12)           # Taxonomy

    # 6. Iconic Brand Logo Emblem (Left Side) - Metallic Medallion
    lx = int(W * 0.16)
    ly = int(H * 0.50)
    rad = int(126 * SCALE)

    # Base Hexagonal Shield Coordinates
    hex_outer = []
    hex_inner = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        hex_outer.append((lx + int(rad * math.cos(a)), ly + int(rad * math.sin(a))))
        hex_inner.append((lx + int((rad - 4 * SCALE) * math.cos(a)), ly + int((rad - 4 * SCALE) * math.sin(a))))

    # Hexagonal Shield Halo
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    halo_draw.polygon(hex_outer, fill=(*COLOR_BLACK_CHERRY_VIVID, 130))
    halo = halo.filter(ImageFilter.GaussianBlur(radius=12 * SCALE))
    img = Image.alpha_composite(img, halo)
    draw = ImageDraw.Draw(img)

    # Outer Shield Fill & Double Rose Gold Rim
    draw.polygon(hex_outer, fill=(*COLOR_BLACK_CHERRY_DARK, 255), outline=(*COLOR_ROSE_GOLD, 240), width=int(2.5 * SCALE))
    draw.polygon(hex_inner, outline=(*COLOR_ROSE_GOLD_LIGHT, 120), width=1 * SCALE)

    # Concentric Ring in Muted Rose Gold
    inner_ring_r = int(rad * 0.78)
    draw.ellipse((lx - inner_ring_r, ly - inner_ring_r, lx + inner_ring_r, ly + inner_ring_r), outline=(*COLOR_ROSE_GOLD, 90), width=1 * SCALE)

    # Precision Geometric Alpha Prism (Delta Facets)
    pt_top = (lx, ly - int(rad * 0.65))
    pt_br = (lx + int(rad * 0.60), ly + int(rad * 0.45))
    pt_bl = (lx - int(rad * 0.60), ly + int(rad * 0.45))
    pt_ctr = (lx, ly + int(rad * 0.05))

    # Facet 1 (Left Wing - Deep Black Cherry Velvet)
    draw.polygon([pt_top, pt_ctr, pt_bl], fill=(*COLOR_NEAR_BLACK, 255), outline=(*COLOR_BLACK_CHERRY, 255), width=2 * SCALE)
    # Facet 2 (Right Wing - Wine Velvet with Champagne Beam Edge)
    draw.polygon([pt_top, pt_br, pt_ctr], fill=(45, 14, 25, 255), outline=(*COLOR_CHAMPAGNE, 240), width=2 * SCALE)
    # Facet 3 (Base - Rose Gold Reflective Horizon)
    draw.polygon([pt_bl, pt_ctr, pt_br], fill=(58, 20, 30, 255), outline=(*COLOR_ROSE_GOLD, 255), width=2 * SCALE)

    # Central Core Diamond (Polished Champagne Jewel)
    cr = int(16 * SCALE)
    draw.polygon([(lx, ly - cr), (lx + cr, ly), (lx, ly + cr), (lx - cr, ly)], fill=(*COLOR_CHAMPAGNE_BRIGHT, 255))
    draw.ellipse((lx - int(25 * SCALE), ly - int(25 * SCALE), lx + int(25 * SCALE), ly + int(25 * SCALE)), outline=(*COLOR_ROSE_GOLD_LIGHT, 200), width=1 * SCALE)

    # 7. Typography & Hierarchy (Centered-Right Layout)
    tx = int(W * 0.33)

    # Line 1: Pre-Header Taxonomy with Geometric Diamond
    diamond_x = tx
    diamond_y = int(H * 0.22) + int(5 * SCALE)
    dr = int(4 * SCALE)
    draw.polygon([(diamond_x, diamond_y - dr), (diamond_x + dr, diamond_y), (diamond_x, diamond_y + dr), (diamond_x - dr, diamond_y)], fill=(*COLOR_ROSE_GOLD, 255))

    cat_str = "INSTITUTIONAL QUANTITATIVE SYSTEM // HIGH-BETA ALPHA"
    draw.text((tx + int(14 * SCALE), int(H * 0.22)), cat_str, font=font_mono, fill=(*COLOR_ROSE_GOLD_LIGHT, 240))

    # Line 2: Brand Title "AQTA" (Grand Champagne Presence)
    draw.text((tx, int(H * 0.29)), "AQTA", font=font_brand, fill=(*COLOR_CHAMPAGNE_BRIGHT, 255))

    # Line 3: System Headline
    draw.text((tx, int(H * 0.48)), "Autonomous Quantitative Trading Agent", font=font_title, fill=(*COLOR_CHAMPAGNE, 255))

    # Line 4: Value Proposition (Warm Taupe Cashmere)
    draw.text(
        (tx, int(H * 0.57)),
        "Compounding monthly capital into high-beta secular monopolies with mathematical anti-ruin guardrails.",
        font=font_sub,
        fill=(*COLOR_CASHMERE, 255)
    )

    # Line 5: Three Refined Architecture Badges (Sleek Rose Gold & Black Cherry)
    badges = [
        ("FIDUCIARY ANTI-RUIN", COLOR_ROSE_GOLD),
        ("SECULAR MONOPOLIES", COLOR_CHAMPAGNE),
        ("MULTI-AGENT DELIBERATION", COLOR_ROSE_GOLD_LIGHT)
    ]

    bx = tx
    by = int(H * 0.69)
    b_h = int(32 * SCALE)

    for label, border_col in badges:
        bbox = draw.textbbox((0, 0), label, font=font_badge)
        tw = bbox[2] - bbox[0]
        bw = tw + int(32 * SCALE)

        # Pill background
        draw.rounded_rectangle(
            [bx, by, bx + bw, by + b_h],
            radius=int(16 * SCALE),
            fill=(*COLOR_NEAR_BLACK, 245),
            outline=(*border_col, 195),
            width=int(1.5 * SCALE)
        )

        # Status Dot (Pulsing accent)
        dot_r = int(3.5 * SCALE)
        dot_x = bx + int(13 * SCALE)
        dot_y = by + int(b_h / 2)
        draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r], fill=(*border_col, 255))

        # Text
        draw.text((bx + int(24 * SCALE), by + int(7.5 * SCALE)), label, font=font_badge, fill=(*COLOR_CHAMPAGNE_BRIGHT, 255))

        bx += bw + int(14 * SCALE)

    # 8. Subtle Outer Border (Double Rose Gold & Black Cherry Rim)
    draw.rectangle([(0, 0), (W - 1, H - 1)], outline=(*COLOR_ROSE_GOLD, 85), width=int(1.5 * SCALE))
    draw.rectangle([(4 * SCALE, 4 * SCALE), (W - 1 - 4 * SCALE, H - 1 - 4 * SCALE)], outline=(*COLOR_BLACK_CHERRY, 60), width=int(1 * SCALE))

    # 9. Downsample with Lanczos Antialiasing
    final_img = img.resize((W_FINAL, H_FINAL), Image.Resampling.LANCZOS)
    rgb_img = Image.new("RGB", (W_FINAL, H_FINAL), COLOR_VELVET_NOIR)
    rgb_img.paste(final_img, mask=final_img.split()[3])

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    rgb_img.save(OUTPUT_PATH, "JPEG", quality=98, optimize=True)
    print(f"[*] Brand-Grade Social Preview Banner generated at:\n    {OUTPUT_PATH}")

if __name__ == "__main__":
    create_brand_banner()
