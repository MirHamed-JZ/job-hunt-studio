"""Visual readability check for resume PDFs (what a human sees, not ATS).

For each PDF: renders page 1, writes a blurred "squint test" image (if roles,
sections and dates still stand out when nothing is legible, the page is
scannable), and measures density:
  ink        share of dark pixels on the page (higher = denser)
  blocks     text blocks separated by a visible vertical gap (more = easier to scan)
  longest    height of the tallest uninterrupted text block, as % of page height
  gap_avg    average height of the gaps between blocks (px at 100 dpi)
With several PDFs it also writes a side-by-side contact sheet (normal and
squint rows) so layouts and fonts can be compared directly.

Usage (workspace Python): python visual_check.py OUT_DIR a.pdf [b.pdf ...]
The plugin ships a reference, tools/assets/reference_jakes_resume.pdf (the original Jake's Resume, MIT).
Needs: pdftoppm (Poppler; MiKTeX and TeX Live ship it) and Pillow.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageOps

DPI = 100
GAP_PX = 7  # a blank band at least this tall (about 1.8 mm) counts as a visual break

out_dir, pdfs = sys.argv[1], sys.argv[2:]
os.makedirs(out_dir, exist_ok=True)
rows = []
for pdf in pdfs:
    name = os.path.splitext(os.path.basename(pdf))[0]
    stem = os.path.join(out_dir, name)
    subprocess.run(["pdftoppm", "-r", str(DPI), "-png", "-singlefile", "-f", "1", "-l", "1", pdf, stem],
                   check=True, capture_output=True)
    page = Image.open(stem + ".png").convert("L")
    squint = page.filter(ImageFilter.GaussianBlur(radius=4))
    squint = ImageOps.autocontrast(squint)
    squint.save(stem + "_squint.png")

    w, h = page.size
    px = page.load()
    dark_rows = []
    ink = 0
    for y in range(h):
        row_dark = 0
        for x in range(0, w, 2):
            if px[x, y] < 160:
                row_dark += 1
        ink += row_dark
        dark_rows.append(row_dark > 0)
    blocks, gaps, run, gap = [], [], 0, 0
    for d in dark_rows:
        if d:
            if gap >= GAP_PX and run:
                blocks.append(run)
                gaps.append(gap)
                run = 0
            run += 1 + (gap if gap < GAP_PX else 0)
            gap = 0
        else:
            gap += 1
    if run:
        blocks.append(run)
    metrics = {
        "ink": 100.0 * ink / ((w // 2) * h),
        "blocks": len(blocks),
        "longest": 100.0 * max(blocks) / h if blocks else 0,
        "gap_avg": sum(gaps) / len(gaps) if gaps else 0,
    }
    rows.append((name, page, squint, metrics))
    print(f"{name:42} ink {metrics['ink']:5.1f}%  blocks {metrics['blocks']:3d}  "
          f"longest {metrics['longest']:4.1f}%  gap_avg {metrics['gap_avg']:4.1f}px")

if len(rows) > 1:
    tw = 420
    th = int(rows[0][1].size[1] * tw / rows[0][1].size[0])
    sheet = Image.new("L", (tw * len(rows) + 10 * (len(rows) + 1), 2 * th + 60), 255)
    draw = ImageDraw.Draw(sheet)
    for i, (name, page, squint, m) in enumerate(rows):
        x = 10 + i * (tw + 10)
        draw.text((x, 5), f"{name}  ink {m['ink']:.0f}%  blocks {m['blocks']}", fill=0)
        sheet.paste(page.resize((tw, th)), (x, 25))
        sheet.paste(squint.resize((tw, th)), (x, 35 + th))
    sheet.save(os.path.join(out_dir, "comparison.png"))
    print("contact sheet:", os.path.join(out_dir, "comparison.png"))
