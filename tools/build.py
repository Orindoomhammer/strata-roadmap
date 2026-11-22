"""Build the Strata site into docs/.

    python tools/build.py [path-to-strata-rs]

Looks for the strata-rs checkout next to this repository by default. Parses the
node definitions, export presets and node-reference text out of the Rust
source, then writes docs/index.html, docs/nodes.html, docs/changelog.html and
docs/css/site.css.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, 'docs')
DATA = os.path.join(HERE, 'data.json')

CANDIDATES = [
    os.path.join(ROOT, '..', 'strata-rs'),   # side by side with this repo
    os.path.join(ROOT, 'strata-rs'),         # checked out inside it
]


def find_repo():
    if len(sys.argv) > 1:
        return os.path.abspath(sys.argv[1])
    for c in CANDIDATES:
        if os.path.isdir(os.path.join(c, 'src')):
            return os.path.abspath(c)
    return None


REPO = find_repo()
if not REPO or not os.path.isdir(os.path.join(REPO, 'src')):
    sys.exit("could not find the strata-rs source.\n"
             "looked in:\n  " + "\n  ".join(os.path.abspath(c) for c in CANDIDATES) +
             "\nusage: python tools/build.py [path-to-strata-rs]")

print(f"source: {REPO}")
for step in ([sys.executable, '-I', os.path.join(HERE, 'parse.py'),
              os.path.join(REPO, 'src'), DATA],
             [sys.executable, '-I', os.path.join(HERE, 'gen.py'), DATA, REPO, SITE]):
    r = subprocess.run(step)
    if r.returncode:
        sys.exit(r.returncode)

print(f"\nbuilt into {SITE}")
print("preview with:  python -m http.server 8099 --bind 127.0.0.1 --directory docs")
