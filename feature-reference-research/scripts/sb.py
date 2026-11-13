"""Build a labelled contact sheet from YouTube storyboard sprites to pick UI moments.
usage: python -I sb.py <name> <url_template_with_{m}> <pages> <cols> <rows> <w> <h> <interval_ms> [start_s end_s]
-> <name>_sb.jpg in the current directory (frames 192x108, time label in the corner)
"""
import io
import os
import sys
import urllib.request

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
name, tpl, pages, cols, rows, w, h, interval = sys.argv[1:9]
pages, cols, rows, w, h, interval = map(int, (pages, cols, rows, w, h, interval))
start, end = (int(sys.argv[9]), int(sys.argv[10])) if len(sys.argv) > 10 else (0, 10 ** 9)

frames = []
for m in range(pages):
    data = urllib.request.urlopen(tpl.replace('{m}', str(m)), timeout=30).read()
    sheet = Image.open(io.BytesIO(data)).convert('RGB')
    for r in range(rows):
        for c in range(cols):
            idx = m * cols * rows + r * cols + c
            t = idx * interval // 1000
            if start <= t <= end and (c + 1) * w <= sheet.width and (r + 1) * h <= sheet.height:
                frames.append((t, sheet.crop((c * w, r * h, (c + 1) * w, (r + 1) * h)).resize((192, 108))))

per_row = 10
out = Image.new('RGB', (per_row * 192, ((len(frames) + per_row - 1) // per_row) * 108), (20, 20, 20))
d = ImageDraw.Draw(out)
for i, (t, im) in enumerate(frames):
    x, y = (i % per_row) * 192, (i // per_row) * 108
    out.paste(im, (x, y))
    d.rectangle((x, y, x + 44, y + 14), fill=(0, 0, 0))
    d.text((x + 2, y + 1), '%d:%02d' % (t // 60, t % 60), fill=(255, 255, 0))
out.save(os.path.abspath(name + '_sb.jpg'), quality=80)
print(len(frames), 'frames', out.size)
