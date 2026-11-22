"""Produce the site's web images from the strata-rs source assets.

    python tools/images.py [path-to-strata-rs]

Writes WebP screenshots, the social-card JPEG and the favicons into docs/.
Outputs are committed, so this only needs rerunning when the source shots are
recaptured (see steam/shots/README.md in strata-rs).
"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'docs', 'img')
DOCS = os.path.join(ROOT, 'docs')

# source relative to the strata-rs checkout -> published basename
SHOTS = {
    'steam/shots/graph.png': 'graph',
    'steam/shots/river.png': 'river',
    'steam/shots/layers.png': 'layers',
    'steam/shots/walk-river.png': 'walk-river',
    'steam/shots/guided.png': 'guided',
}
KEYART = 'itch/assets/key-art-1438x810.jpg'

MAX_W = 1400      # shown at ~640 CSS px; this covers 2x displays
QUALITY = 80
BG = (11, 14, 19)
GOLD = (255, 193, 97)


def find_repo():
    if len(sys.argv) > 1:
        return os.path.abspath(sys.argv[1])
    for c in (os.path.join(ROOT, '..', 'strata-rs'), os.path.join(ROOT, 'strata-rs')):
        if os.path.isdir(os.path.join(c, 'src')):
            return os.path.abspath(c)
    return None


def webp(src, name, max_w=MAX_W, quality=QUALITY):
    im = Image.open(src)
    im = im.convert('RGB')
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = os.path.join(IMG, name + '.webp')
    im.save(out, 'WEBP', quality=quality, method=6)
    return out, im.size


def social_card(src):
    """1200x630 JPEG for Open Graph: the one size every platform agrees on,
    in the one format all of them render without argument."""
    im = Image.open(src).convert('RGB')
    target = 1200 / 630
    if im.width / im.height > target:                   # too wide: crop sides
        w = round(im.height * target)
        im = im.crop(((im.width - w) // 2, 0, (im.width - w) // 2 + w, im.height))
    else:                                               # too tall: crop bottom
        h = round(im.width / target)
        top = round((im.height - h) * 0.25)             # keep the peaks, drop foreground
        im = im.crop((0, top, im.width, top + h))
    im = im.resize((1200, 630), Image.LANCZOS)
    out = os.path.join(DOCS, 'og.jpg')
    im.save(out, 'JPEG', quality=84, optimize=True, progressive=True)
    return out


def chevron(size, pad_ratio=0.22, stroke_ratio=0.115, radius_ratio=0.18):
    """The brand chevron, the same mark the header draws in CSS."""
    ss = 4                                              # supersample for clean edges
    s = size * ss
    im = Image.new('RGB', (s, s), BG)
    d = ImageDraw.Draw(im)
    r = round(s * radius_ratio)
    # rounded-corner mask so the icon reads as a tile, not a square
    mask = Image.new('L', (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=255)

    pad = s * pad_ratio
    w = round(s * stroke_ratio)
    mid = s * 0.5
    d.line([(pad, s - pad * 1.25), (mid, pad * 1.35), (s - pad, s - pad * 1.25)],
           fill=GOLD, width=w, joint='curve')
    # round the three ends/corner the way the CSS border does
    for pt in [(pad, s - pad * 1.25), (mid, pad * 1.35), (s - pad, s - pad * 1.25)]:
        d.ellipse([pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2], fill=GOLD)

    out = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)


FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="12" fill="#0b0e13"/>
  <path d="M14 42 L32 20 L50 42" fill="none" stroke="#ffc161" stroke-width="7"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def main():
    repo = find_repo()
    if not repo:
        sys.exit("could not find the strata-rs source.\n"
                 "usage: python tools/images.py [path-to-strata-rs]")
    os.makedirs(IMG, exist_ok=True)

    sizes, total = {}, 0
    for rel, name in SHOTS.items():
        src = os.path.join(repo, rel)
        if not os.path.exists(src):
            sys.exit(f"missing source image: {src}")
        out, wh = webp(src, name)
        sizes[name + '.webp'] = list(wh)
        n = os.path.getsize(out)
        total += n
        print(f"{n/1024:8.1f} KB  img/{name}.webp  {wh[0]}x{wh[1]}")

    key = os.path.join(repo, KEYART)
    out, wh = webp(key, 'keyart', max_w=1600, quality=78)
    sizes['keyart.webp'] = list(wh)
    total += os.path.getsize(out)
    print(f"{os.path.getsize(out)/1024:8.1f} KB  img/keyart.webp  {wh[0]}x{wh[1]}")

    card = social_card(key)
    print(f"{os.path.getsize(card)/1024:8.1f} KB  og.jpg  1200x630")

    with open(os.path.join(DOCS, 'favicon.svg'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(FAVICON_SVG)
    chevron(32).save(os.path.join(DOCS, 'favicon.png'))
    chevron(180, pad_ratio=0.24).save(os.path.join(DOCS, 'apple-touch-icon.png'))
    print("          favicon.svg, favicon.png, apple-touch-icon.png")

    with open(os.path.join(HERE, 'images.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(sizes, fh, indent=1, sort_keys=True)

    print(f"\n{total/1024:.1f} KB of images total")


if __name__ == '__main__':
    main()
