"""Contact sheets of all images in a folder, to eyeball downloaded screenshots and captured frames.
usage: python contact_sheet.py <folder> [out_prefix]  -> <out_prefix>0.jpg, <out_prefix>1.jpg ... (50 images per sheet)
"""
import glob
import os
import sys

from PIL import Image, ImageDraw

folder = sys.argv[1]
prefix = sys.argv[2] if len(sys.argv) > 2 else os.path.join(folder, '_sheet')
files = sorted(f for f in glob.glob(os.path.join(folder, '*.*')) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) and '_sheet' not in f)
COLS, W, H = 8, 240, 150
for part in range((len(files) + 49) // 50):
    sub = files[part * 50:(part + 1) * 50]
    sheet = Image.new('RGB', (COLS * W, ((len(sub) + COLS - 1) // COLS) * (H + 14)), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(sub):
        x, y = (i % COLS) * W, (i // COLS) * (H + 14)
        try:
            im = Image.open(f).convert('RGB')
            im.thumbnail((W - 4, H))
            sheet.paste(im, (x + 2, y + 14))
        except Exception:
            d.text((x + 4, y + 40), 'ERROR', fill=(255, 0, 0))
        d.text((x + 2, y + 1), os.path.basename(f)[:38], fill=(255, 255, 0))
    out = '%s%d.jpg' % (prefix, part)
    sheet.save(out, quality=75)
    print(out, len(sub))
