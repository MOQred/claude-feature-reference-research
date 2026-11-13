"""Check that every local link (img/, yt/, research/) in the research page points to an existing file; list unused images.
usage: python check_refs.py <path/to/page.html>
"""
import os
import re
import sys

page = os.path.abspath(sys.argv[1])
root = os.path.dirname(page)
html = open(page, encoding='utf-8').read()
refs = set(re.findall(r'(?:src|href)="((?:img|yt|research)/[^"]+)"', html))
missing = sorted(r for r in refs if not os.path.exists(os.path.join(root, r)))
used = {r.split('/', 1)[1] for r in refs if r.startswith('img/')}
img_dir = os.path.join(root, 'img')
unused = sorted(set(os.listdir(img_dir)) - used) if os.path.isdir(img_dir) else []
print('refs:', len(refs))
print('missing:', missing or 'none')
print('unused img:', unused or 'none')
print('page size KB:', os.path.getsize(page) // 1024)
sys.exit(1 if missing else 0)
