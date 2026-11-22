"""Generate the Strata site from parsed source data + CHANGELOG.md."""
import html, json, os, re, sys

DATA, REPO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(DATA, encoding='utf-8'))
NODES, LESSONS = d['nodes'], d['lessons']
LESSON = {l['node']: l for l in LESSONS if l['node']}
VERSION = re.search(r'^version = "([^"]+)"',
                    open(os.path.join(REPO, 'Cargo.toml'), encoding='utf-8').read(),
                    re.M).group(1)

ITCH = 'https://orindoomhammer.itch.io/strata'
STEAM = 'https://store.steampowered.com/app/4791200/'
STEAM_DEMO = 'https://store.steampowered.com/app/4865260/'
ROADMAP = 'https://github.com/Orindoomhammer/strata-roadmap'

CAT_ORDER = ['Generators', 'Filters', 'Analysis', 'Composite', 'Math', 'Values', 'Output']
PIN_CLASS = {'Height': 'height', 'Mask': 'mask', 'Scalar': 'scalar'}

e = html.escape


def inline(t):
    """Bold, code spans and links inside already-escaped text."""
    def link(m):
        text, href = m.group(1), m.group(2)
        rel = ' rel="noopener"' if href.startswith('http') else ''
        return f'<a href="{href}"{rel}>{text}</a>'

    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t, flags=re.S)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def paras(text):
    """Lesson bodies: blank-line separated paragraphs."""
    return '\n'.join(f'<p>{inline(e(p.strip()))}</p>'
                     for p in re.split(r'\n\s*\n', text.strip()) if p.strip())


# ---------------------------------------------------------------- shell
def page(title, desc, body, active, extra_head='', extra_js=''):
    nav = ''.join(
        f'<a href="{href}"{" class=on" if key == active else ""}>{label}</a>'
        for key, href, label in [('home', 'index.html', 'Overview'),
                                 ('nodes', 'nodes.html', 'Node reference'),
                                 ('changelog', 'changelog.html', 'Changelog')])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="img/keyart.jpg">
<meta property="og:type" content="website">
<link rel="stylesheet" href="css/site.css">
{extra_head}
</head>
<body>
<header class="top">
  <div class="wrap topbar">
    <a class="brand" href="index.html"><span class="chev"></span>STRATA</a>
    <nav>{nav}</nav>
    <a class="btn small" href="{ITCH}" rel="noopener">Get it</a>
  </div>
</header>
{body}
<footer class="foot">
  <div class="wrap footgrid">
    <div>
      <p class="brand small"><span class="chev"></span>STRATA</p>
      <p class="dim">Node-based terrain editor for game developers.<br>
      Version {e(VERSION)}. Windows and Linux, native.</p>
    </div>
    <div>
      <h4>Get it</h4>
      <p><a href="{ITCH}" rel="noopener">itch.io</a></p>
      <p><a href="{STEAM}" rel="noopener">Steam</a></p>
      <p><a href="{STEAM_DEMO}" rel="noopener">Free demo</a></p>
    </div>
    <div>
      <h4>More</h4>
      <p><a href="nodes.html">Node reference</a></p>
      <p><a href="changelog.html">Changelog</a></p>
      <p><a href="{ROADMAP}" rel="noopener">Public roadmap</a></p>
    </div>
  </div>
</footer>
{extra_js}
</body>
</html>
"""


# ---------------------------------------------------------------- landing
def shot(src, alt, cap):
    return (f'<figure class="shot"><img src="img/{src}" alt="{e(alt)}" loading="lazy">'
            f'<figcaption>{inline(e(cap))}</figcaption></figure>')


def feature_rows():
    rows = [
        ('graph.png', 'The Strata node graph with noise, mix and terrace nodes wired to a height output',
         'A node graph built for terrain',
         'Every element of the landscape is a node. Chain them, adjust them with live '
         'sliders, watch the result update. Nothing is destructive — change any step at '
         'any time without starting over.',
         ['**Generators** — Perlin, Simplex, Voronoi and Gradient noise, plus Island Cluster '
          'for archipelagos and Mountain Ridge for ranges you draw yourself',
          '**Hydraulic and thermal erosion** — water and slope-driven wear, for terrain that '
          'looks like it got that way for a reason',
          '**Masks from the terrain itself** — shoreline, slope, curvature and height '
          'selection, so material masks come out of the landscape rather than being painted on',
          '**A full maths and filter library** — Warp, Terrace, Smooth, Sharpen, Remap, '
          'Clamp, Power, Invert, Mix and more'],
         'A graph that mixes two noise generators, terraces the result and sends it to the height output.'),
        ('river.png', 'The River node selected, its spline drawn over the 2D preview, inspector open',
         'Rivers you draw, roads that obey a grade',
         'Draw a route over the preview and get a channel with banks, meander and '
         'tributaries — plus a water mask for your material stack. The Road / Path node '
         'works the same way, cutting into hills and filling across dips so the surface '
         'never exceeds the grade you set.',
         ['**River** — width, depth and bank in metres; tributaries with their own reach',
          '**Road / Path** — width and shoulder in metres, maximum grade in percent, with '
          'road and shoulder masks',
          '**Flatten Pin** — a level building pad anywhere on the map, placeable while you walk'],
         'River: spline points on the 2D preview, parameters in metres on the right.'),
        ('layers.png', 'The Layer Stack node showing blend modes and per-layer controls',
         f"Photoshop's compositing model, rethought for heightfields",
         f"Layer Stack composites up to {d['max_layers']} layers with {len(d['blend_modes'])} "
         'blend modes, per-layer opacity, masks and visibility — so landforms stack the way '
         'image layers do, with the mask deciding where each one lands.',
         [], 'Layer Stack with per-layer blend mode, amount and mask controls.'),
        ('walk-river.png', 'Ground-level view of a riverbed with gravel and rock, walking HUD visible',
         'Look at it from the ground',
         'Orbit it, or drop down and walk. The walk and follow cameras put you at eye level '
         'with the terrain you are building, because "is this hill the right size?" is a '
         'question best answered standing at the bottom of it.',
         ['The 3D viewport textures from the same splat channels your engine will get — '
          'grass, rock, dirt, snow and riverbed — and renders water at the level the graph '
          'sets. The preview is the export, not an impression of it.'],
         'Walk mode at 4 km scale. The minimap tracks where you are on the heightmap.'),
        ('guided.png', 'The guided start panel open beside the node graph',
         'Learn it while you build',
         f'Thirty-odd nodes is a lot to face on an empty graph, so Strata ships two guides, '
         'both reachable from the Help menu at any time. Neither blocks anything — the '
         'application stays fully usable underneath.',
         ['**A guided start**, which reads your graph and advances when you have actually '
          'done the step rather than when you click Next',
          '**A node reference**, one entry per node, with an explanation and a practical '
          'note — the same text is [on this site](nodes.html)'],
         'The guided start reads the graph and moves on when the step is actually done.'),
    ]
    out = []
    for i, (img, alt, title, lead, bullets, cap) in enumerate(rows):
        lis = ''.join(f'<li>{inline(e(b))}</li>' for b in bullets)
        out.append(f"""
<section class="split{' flip' if i % 2 else ''}">
  <div class="split-text">
    <h2>{e(title)}</h2>
    <p class="lead">{inline(e(lead))}</p>
    {f'<ul class="ticks">{lis}</ul>' if lis else ''}
  </div>
  {shot(img, alt, cap)}
</section>""")
    return '\n'.join(out)


def export_table():
    rows = ''.join(
        f'<tr><th scope="row">{e(p["name"])}</th>'
        f'<td>{p["min"]} – {p["max"]}</td>'
        f'<td>{e(p["fmt"])}</td></tr>'
        for p in d['presets'])
    tiles = ' or '.join(t.replace(' x ', ' × ') for t in d['layouts'])
    return f"""
<section class="band" id="export">
  <div class="wrap narrow">
    <h2>Export for your engine</h2>
    <p class="lead">Strata writes the formats and resolutions your engine actually expects —
    not a generic image you have to convert.</p>
    <table class="data">
      <thead><tr><th scope="col">Engine</th><th scope="col">Resolutions</th><th scope="col">Format</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <p class="note">Export a single map or a {tiles.split(' or ')[-1]} tile grid — each tile is evaluated in its own
    world coordinates, so the seams line up. Splat masks are written alongside the heightmap
    as RGBA PNG. Projects are plain JSON: diffable, readable, and portable.</p>
  </div>
</section>"""


LIMITS = [
    ('Evaluation can briefly pause the interface', ' on a complex rebuild at Fine detail. '
     'Moving it off-thread is next.'),
    ('Higher preview detail does not resolve small features at large scale', ' — a 64 km world '
     'at 2048 samples still has ~31 m between samples. The editor tells you the spacing rather '
     'than letting you guess.'),
    ('The Road tool shapes terrain', '. It does not generate road meshes, bridges or tunnels.'),
    ('Rivers can still disagree across a tiled export', '. The equivalent problem in Road is fixed; '
     'River is known and not yet done.'),
    ('The interface is English only', '.'),
]

REQS = [
    ('Windows', 'Windows 10 64-bit', 'Intel Core i5-4000 / AMD equivalent', '4 GB',
     'DirectX 12 or Vulkan GPU, 2 GB VRAM', '150 MB'),
    ('Linux', 'Ubuntu 22.04 / SteamOS 3 or newer', 'Intel Core i5-4000 / AMD equivalent', '4 GB',
     'Vulkan GPU, 2 GB VRAM', '150 MB'),
]


def landing():
    limits = ''.join(f'<li><strong>{e(a)}</strong>{inline(e(b))}</li>' for a, b in LIMITS)
    reqrows = ''.join(
        f'<tr><th scope="row">{e(os_)}</th><td>{e(osv)}</td><td>{e(cpu)}</td>'
        f'<td>{e(ram)}</td><td>{e(gpu)}</td><td>{e(disk)}</td></tr>'
        for os_, osv, cpu, ram, gpu, disk in REQS)
    ncount = len(NODES)
    return page(
        'Strata — node-based terrain editor',
        'Build landscapes from a node graph, erode them, carve rivers and roads, then walk the '
        'result at player scale before exporting to Unreal Engine 5, Unity, Godot, O3DE or Leadwerks.',
        f"""
<section class="hero">
  <div class="hero-bg" role="presentation"></div>
  <div class="wrap hero-in">
    <p class="kicker">Node-based terrain editor · Windows &amp; Linux</p>
    <h1>Build worlds,<br>not formulas.</h1>
    <p class="lead big">Connect generators, filters and masks in a node graph. Watch the terrain
    take shape in a live 2D preview and a textured 3D viewport — then walk it on foot, at player
    scale, to find out what it actually feels like to cross. Then export a heightmap your engine
    reads directly.</p>
    <p class="cta">
      <a class="btn" href="{ITCH}" rel="noopener">Buy on itch.io</a>
      <a class="btn ghost" href="{STEAM}" rel="noopener">Buy on Steam</a>
      <a class="btn ghost" href="{STEAM_DEMO}" rel="noopener">Try the free demo</a>
    </p>
    <p class="dim small">No launcher, no account, no DRM. Native on Windows and Linux, including Steam Deck.</p>
  </div>
</section>

<section class="wrap stats">
  <div><b>{ncount}</b><span>nodes</span></div>
  <div><b>{d['max_layers']}</b><span>layers, {len(d['blend_modes'])} blend modes</span></div>
  <div><b>{len(d['presets'])}</b><span>engine export presets</span></div>
  <div><b>8129</b><span>max heightmap px</span></div>
</section>

<div class="wrap">
{feature_rows()}
</div>

{export_table()}

<section class="wrap narrow" id="units">
  <h2>Real units, chosen detail</h2>
  <p class="lead">Preview sampling is independent of physical size. Pick Draft (512), Balanced
  (1024) or Fine (2048); the editor tells you the real sample spacing in metres and the memory
  cost before you commit.</p>
  <p>Terrain is authored in units that mean something — map width in kilometres, height range in
  metres, river widths in metres, road grades in percent. The landscape comes out the size you meant.</p>
</section>

<section class="band" id="honest">
  <div class="wrap narrow">
    <h2>What it does not do yet</h2>
    <p class="lead">Worth knowing before you buy rather than after.</p>
    <ul class="plain">{limits}</ul>
    <p class="note">The full roadmap, including what is being worked on now, is public:
    <a href="{ROADMAP}" rel="noopener">github.com/Orindoomhammer/strata-roadmap</a>.</p>
  </div>
</section>

<section class="wrap narrow" id="requirements">
  <h2>Requirements</h2>
  <p class="lead">Terrain is evaluated with GPU compute shaders, so a Vulkan or DX12 capable GPU is
  required — roughly NVIDIA GTX 600, AMD HD 7000 or Intel HD 520 and newer.</p>
  <div class="scroll">
  <table class="data">
    <thead><tr><th scope="col">Minimum</th><th scope="col">OS</th><th scope="col">Processor</th>
    <th scope="col">Memory</th><th scope="col">Graphics</th><th scope="col">Storage</th></tr></thead>
    <tbody>{reqrows}</tbody>
  </table>
  </div>
  <p class="note">Recommended for either: a GTX 1060 / RX 580 or better with 4 GB VRAM, and 8 GB RAM.
  The Linux build is native — Proton is not required, and it runs on Steam Deck.</p>
</section>

<section class="closer">
  <div class="wrap narrow">
    <h2>Build the landscape you meant.</h2>
    <p class="cta">
      <a class="btn" href="{ITCH}" rel="noopener">Buy on itch.io</a>
      <a class="btn ghost" href="{STEAM_DEMO}" rel="noopener">Try the free demo</a>
    </p>
  </div>
</section>
""", 'home')


# ---------------------------------------------------------------- nodes
# Nodes with no entry in the in-app tour yet. Written from the source and the
# changelog so the reference is complete; drop one once a lesson ships for it.
SUPPLEMENT = {
    'Road': {
        'body': 'Draw a route over the 2D preview and get a grade-limited carriageway. It cuts '
                'into hills and fills across dips so the finished surface never exceeds the '
                'maximum grade you set.\n\n'
                'Width and shoulder are authored in metres, grade in percent. Alongside the '
                'terrain it outputs a road mask and a shoulder mask for your material stack.\n\n'
                'It shapes terrain only — it does not generate road meshes, bridges or tunnels.',
        'tip': 'The elevation profile is solved once over the whole route, so a tiled export '
               'resolves the same surface on both sides of a seam.',
    },
    'WaterOutput': {
        'body': 'Terminal, like Height Output and Splat Output: it marks which mask in the graph '
                'is standing water, so the 3D viewport can put a surface on it and an export can '
                'hand your engine a water map.\n\n'
                'Sea level lives here rather than in the view settings, because it is part of the '
                'terrain rather than a display preference.',
        'tip': 'Wire a water mask here — the River node\'s mask output is the usual source.',
    },
}


def node_card(n):
    les = LESSON.get(n['id']) or SUPPLEMENT.get(n['id'])
    body = paras(les['body']) if les else \
        '<p class="dim">No reference entry ships for this node yet.</p>'
    tip = ''
    if les and les['tip'] and not les['tip'].startswith('Category:'):
        tip = f'<p class="tip">{inline(e(les["tip"]))}</p>'

    def pinlist(pins, label):
        if not pins:
            return ''
        items = ''.join(
            f'<span class="pin {PIN_CLASS.get(p["kind"], "")}">{e(p["label"])}</span>'
            for p in pins)
        return f'<div class="pins"><span class="pinlab">{label}</span>{items}</div>'

    pins_html = pinlist(n['inputs'], 'In') + pinlist(n['outputs'], 'Out')
    if n.get('macro_pins'):
        pins_html = (f'<div class="pins"><span class="pinlab">In</span>'
                     f'<span class="pin height">Base</span>'
                     f'<span class="pin height">Layer 1 – {d["max_layers"]}</span>'
                     f'<span class="pin mask">Mask 1 – {d["max_layers"]}</span></div>'
                     f'<div class="pins"><span class="pinlab">Out</span>'
                     f'<span class="pin height">Height</span></div>')

    params = ''
    if n['fields']:
        rows = ''
        for f in n['fields']:
            if f['options']:
                rng = ', '.join(e(o) for o in f['options'][:6])
                if len(f['options']) > 6:
                    rng += f' … ({len(f["options"])} total)'
            elif f['kind'] == 'bool':
                rng = 'on / off'
            else:
                rng = f'{f["min"]} – {f["max"]}'
            dflt = f['default']
            if f['kind'] == 'bool':
                dflt = 'off' if dflt in ('0', '0.0') else 'on'
            rows += (f'<tr><th scope="row">{e(f["label"])}</th><td><code>{e(f["key"])}</code></td>'
                     f'<td>{e(dflt)}</td><td>{rng}</td></tr>')
        params = (f'<div class="scroll"><table class="data params">'
                  f'<thead><tr><th scope="col">Parameter</th>'
                  f'<th scope="col">Key</th><th scope="col">Default</th>'
                  f'<th scope="col">Range</th></tr></thead><tbody>{rows}</tbody></table></div>')
    elif n.get('macro_pins'):
        modes = ', '.join(e(m) for m in d['blend_modes'])
        params = (f'<p class="note">Five controls per layer — blend mode, amount, '
                  f'"only where layer has height" and "invert mask" — for up to '
                  f'{d["max_layers"]} layers (a new stack starts with {d["default_layers"]}).<br>'
                  f'<strong>Blend modes:</strong> {modes}.<br>'
                  f'<span class="dim">{len(d["blend_modes"])} entries in the menu; '
                  f'<code>max</code> and <code>min</code> are terrain-friendly names for '
                  f'<code>lighten</code> and <code>darken</code>, so there are 19 distinct '
                  f'operations.</span></p>')

    return f"""
<article class="node" id="{e(n['id'])}" data-cat="{e(n['category'])}" data-name="{e((n['label'] + ' ' + n['id']).lower())}">
  <div class="node-head">
    <h3>{e(n['label'])}</h3>
    <span class="tag">{e(n['category'])}</span>
    {'<span class="tag term">terminal</span>' if n['terminal'] else ''}
    <code class="nid">{e(n['id'])}</code>
  </div>
  {pins_html}
  <div class="node-body">{body}{tip}</div>
  {params}
</article>"""


NODES_JS = """
<script>
(function () {
  var q = document.getElementById('q');
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.node'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.catgroup'));
  var cat = 'All';
  function apply() {
    var term = (q.value || '').trim().toLowerCase();
    cards.forEach(function (c) {
      var okCat = cat === 'All' || c.dataset.cat === cat;
      var okTerm = !term || c.dataset.name.indexOf(term) > -1 ||
                   c.textContent.toLowerCase().indexOf(term) > -1;
      c.hidden = !(okCat && okTerm);
    });
    groups.forEach(function (g) {
      g.hidden = !g.querySelector('.node:not([hidden])');
    });
    var n = cards.filter(function (c) { return !c.hidden; }).length;
    document.getElementById('count').textContent =
      n + (n === 1 ? ' node' : ' nodes');
  }
  chips.forEach(function (ch) {
    ch.addEventListener('click', function () {
      chips.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
      ch.setAttribute('aria-pressed', 'true');
      cat = ch.dataset.cat;
      apply();
    });
  });
  q.addEventListener('input', apply);
  apply();
})();
</script>
"""


def nodes_page():
    cats = [c for c in CAT_ORDER if any(n['category'] == c for n in NODES)]
    cats += sorted({n['category'] for n in NODES} - set(cats))
    chips = ''.join(
        f'<button class="chip" data-cat="{e(c)}" aria-pressed="{"true" if c == "All" else "false"}">{e(c)}</button>'
        for c in ['All'] + cats)
    groups = ''
    for c in cats:
        inner = ''.join(node_card(n) for n in NODES if n['category'] == c)
        groups += f'<section class="catgroup"><h2 class="cathead">{e(c)}</h2>{inner}</section>'
    return page(
        'Node reference — Strata',
        f'Every one of Strata\'s {len(NODES)} nodes: what it does, its pins, and every '
        'parameter with its default and range.',
        f"""
<section class="pagehead">
  <div class="wrap narrow">
    <h1>Node reference</h1>
    <p class="lead">All {len(NODES)} nodes — what each one does, its pins, and every parameter with
    its default and range. This is the same reference that ships in the application under
    <em>Help</em>, generated from the source of version {e(VERSION)}, so it cannot drift from the build.</p>
  </div>
</section>
<div class="wrap">
  <div class="filters">
    <label class="srch"><span class="vh">Search nodes</span>
      <input id="q" type="search" placeholder="Search nodes, parameters…" autocomplete="off"></label>
    <div class="chips">{chips}</div>
    <p id="count" class="dim small" aria-live="polite"></p>
  </div>
  <div class="nodegrid">{groups}</div>
</div>
""", 'nodes', extra_js=NODES_JS)


# ---------------------------------------------------------------- changelog
def changelog_page():
    src = open(os.path.join(REPO, 'CHANGELOG.md'), encoding='utf-8').read()
    src = re.sub(r'<!--.*?-->', '', src, flags=re.S)          # drop maintenance notes
    src = re.sub(r'^\[[^\]]+\]:\s*\S+\s*$', '', src, flags=re.M)  # drop link definitions

    out, buf, item = [], [], []

    def flush_para():
        if buf:
            out.append(f'<p>{inline(e(" ".join(buf).strip()))}</p>')
            buf.clear()

    def flush_item(stack):
        if item:
            stack.append(f'<li>{inline(e(" ".join(item).strip()))}</li>')
            item.clear()

    lis = []

    def flush_list():
        flush_item(lis)
        if lis:
            out.append('<ul class="plain">' + ''.join(lis) + '</ul>')
            lis.clear()

    sections = []
    for raw in src.split('\n'):
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush_item(lis)
            flush_para()
            continue
        if s == '---':
            continue
        if s.startswith('# '):
            continue
        if s.startswith('## '):
            flush_list(); flush_para()
            title = s[3:].strip()
            m = re.match(r'\[([^\]]+)\]\s*(?:—|-)?\s*(.*)', title)
            ver, date = (m.group(1), m.group(2)) if m else (title, '')
            sections.append(ver)
            if ver.lower() == 'unreleased':
                sections[-1] = None
                continue
            out.append(f'<h2 id="v{e(ver)}">{e(ver)}'
                       f'{f"<span>{e(date)}</span>" if date else ""}</h2>')
            continue
        if s.startswith('### '):
            flush_list(); flush_para()
            out.append(f'<h3>{e(s[4:].strip())}</h3>')
            continue
        if s.startswith('- '):
            flush_para()
            flush_item(lis)
            item.append(s[2:].strip())
            continue
        if item and raw.startswith(('  ', '\t')):
            item.append(s)
            continue
        flush_list()
        buf.append(s)
    flush_list(); flush_para()

    # Drop an Unreleased heading that had no entries under it.
    body = '\n'.join(out)
    shipped = [v for v in sections if v]
    return page(
        'Changelog — Strata',
        f'What changed in each release of Strata, newest first. Current version {VERSION}.',
        f"""
<section class="pagehead">
  <div class="wrap narrow">
    <h1>Changelog</h1>
    <p class="lead">What changed in each release, newest first. Written from the point of view of
    someone using Strata rather than someone reading its source. Current version {e(VERSION)}.</p>
    <p class="dim small">Releases: {" · ".join(f'<a href="#v{e(v)}">{e(v)}</a>' for v in shipped)}</p>
  </div>
</section>
<div class="wrap narrow prose changelog">
{body}
</div>
""", 'changelog')


# ---------------------------------------------------------------- css
CSS = """
:root{
  --bg:#0b0e13; --bg2:#10141b; --surface:#151a23; --surface2:#1b212c;
  --line:#242c39; --ink:#e9edf3; --ink2:#9aa6b8; --ink3:#6f7c90;
  --gold:#ffc161; --gold-dim:#c99340; --blue:#4a8af4; --green:#60c060;
  --radius:14px; --maxw:1160px;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
  color-scheme:dark;
}
@media (prefers-color-scheme:light){
  :root{
    --bg:#f7f8fa; --bg2:#eef1f5; --surface:#ffffff; --surface2:#f2f5f9;
    --line:#dde3ec; --ink:#161b22; --ink2:#55606f; --ink3:#788393;
    --gold:#9a6b12; --gold-dim:#b8842a; --blue:#1f5fd0; --green:#2f7d32;
    color-scheme:light;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--sans); font-size:17px; line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
img{max-width:100%; height:auto; display:block}
a{color:var(--ink); text-decoration-color:color-mix(in oklab,var(--gold) 60%,transparent);
  text-underline-offset:3px}
a:hover{color:var(--gold)}
code{font-family:var(--mono); font-size:.86em;
  background:var(--surface2); padding:.12em .4em; border-radius:5px; color:var(--ink2)}
h1,h2,h3,h4{line-height:1.15; letter-spacing:-.02em; margin:0 0 .5em}
h1{font-size:clamp(2.1rem,5.5vw,3.9rem); font-weight:700}
h2{font-size:clamp(1.5rem,2.6vw,2.1rem); font-weight:650}
h3{font-size:1.14rem; font-weight:650}
p{margin:0 0 1em}
.wrap{max-width:var(--maxw); margin:0 auto; padding:0 24px}
.narrow{max-width:760px}
.dim{color:var(--ink2)}
.small{font-size:.9rem}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

/* header */
.top{position:sticky; top:0; z-index:20; backdrop-filter:blur(10px);
  background:color-mix(in oklab,var(--bg) 82%,transparent); border-bottom:1px solid var(--line)}
.topbar{display:flex; align-items:center; gap:20px; height:60px}
.brand{display:flex; align-items:center; gap:9px; font-weight:300; letter-spacing:.34em;
  font-size:1.02rem; text-decoration:none; color:var(--ink)}
.brand.small{font-size:.92rem; margin-bottom:.6em}
.chev{width:15px; height:15px; border-top:2.5px solid var(--gold);
  border-right:2.5px solid var(--gold); transform:rotate(-45deg) translate(1px,2px); display:inline-block}
.top nav{display:flex; gap:20px; margin-left:auto; flex-wrap:wrap}
.top nav a{font-size:.95rem; color:var(--ink2); text-decoration:none}
.top nav a:hover,.top nav a.on{color:var(--ink)}
.top nav a.on{box-shadow:inset 0 -2px 0 var(--gold)}

/* buttons */
.btn{display:inline-block; background:var(--gold); color:#14100a; font-weight:620;
  padding:.72em 1.25em; border-radius:10px; text-decoration:none; border:1px solid transparent;
  font-size:.97rem; transition:transform .12s ease, filter .12s ease}
.btn:hover{filter:brightness(1.07); color:#14100a; transform:translateY(-1px)}
.btn.ghost{background:transparent; color:var(--ink); border-color:var(--line)}
.btn.ghost:hover{border-color:var(--gold); color:var(--gold)}
.btn.small{padding:.45em .9em; font-size:.88rem; margin-left:4px}
.cta{display:flex; flex-wrap:wrap; gap:12px; margin:1.6em 0 1em}

/* hero */
.hero{position:relative; overflow:hidden; border-bottom:1px solid var(--line)}
.hero-bg{position:absolute; inset:0; background:url(../img/keyart.jpg) center 38%/cover no-repeat;
  opacity:.5}
.hero-bg::after{content:""; position:absolute; inset:0;
  background:linear-gradient(180deg,
    color-mix(in oklab,var(--bg) 55%,transparent) 0%,
    color-mix(in oklab,var(--bg) 72%,transparent) 55%,
    var(--bg) 100%)}
.hero-in{position:relative; padding:104px 24px 86px; max-width:900px}
.kicker{text-transform:uppercase; letter-spacing:.17em; font-size:.76rem; color:var(--gold);
  margin-bottom:1.1em; font-weight:600}
.lead{font-size:1.1rem; color:var(--ink2)}
.lead.big{font-size:1.22rem; max-width:40em; color:var(--ink2)}

/* stats */
.stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px;
  margin:-34px auto 72px; position:relative; z-index:2}
.stats>div{background:var(--surface); border:1px solid var(--line); border-radius:var(--radius);
  padding:18px 20px}
.stats b{display:block; font-size:1.85rem; font-weight:680; letter-spacing:-.03em; color:var(--gold)}
.stats span{font-size:.9rem; color:var(--ink2)}

/* split sections */
.split{display:grid; grid-template-columns:1fr 1.18fr; gap:52px; align-items:center;
  padding:66px 0; border-top:1px solid var(--line)}
.split.flip .split-text{order:2}
.split h2{margin-bottom:.45em}
.ticks{list-style:none; padding:0; margin:1.2em 0 0}
.ticks li{position:relative; padding-left:26px; margin-bottom:.75em; color:var(--ink2)}
.ticks li::before{content:""; position:absolute; left:4px; top:.62em; width:7px; height:7px;
  background:var(--gold); border-radius:2px; transform:rotate(45deg)}
.ticks strong{color:var(--ink); font-weight:620}
.shot{margin:0}
.shot img{border:1px solid var(--line); border-radius:var(--radius); background:var(--surface)}
.shot figcaption{font-size:.86rem; color:var(--ink3); margin-top:.7em}

/* bands */
.band{background:var(--bg2); border-top:1px solid var(--line); border-bottom:1px solid var(--line);
  padding:70px 0; margin-top:66px}
.wrap.narrow>h2,.band h2{margin-top:0}
section.wrap.narrow{padding-top:66px; padding-bottom:0}
.note{font-size:.95rem; color:var(--ink2); margin-top:1.4em}
.plain{list-style:none; padding:0; margin:1.2em 0}
.plain li{padding-left:22px; position:relative; margin-bottom:.85em; color:var(--ink2)}
.plain li::before{content:""; position:absolute; left:2px; top:.68em; width:9px; height:2px;
  background:var(--gold-dim)}
.plain strong{color:var(--ink); font-weight:620}

/* tables */
.scroll{overflow-x:auto}
.data{width:100%; border-collapse:collapse; margin:1.4em 0; font-size:.95rem}
.data th,.data td{text-align:left; padding:.72em .9em; border-bottom:1px solid var(--line);
  vertical-align:top}
.data thead th{font-size:.78rem; text-transform:uppercase; letter-spacing:.09em;
  color:var(--ink3); font-weight:600; border-bottom-color:var(--line)}
.data tbody th{font-weight:620; color:var(--ink)}
.data td{color:var(--ink2)}

/* closer */
.closer{text-align:center; padding:84px 0 96px; border-top:1px solid var(--line)}
.closer .cta{justify-content:center}

/* page head */
.pagehead{padding:70px 0 10px; border-bottom:1px solid var(--line); background:var(--bg2)}
.pagehead h1{font-size:clamp(1.9rem,4vw,2.9rem)}

/* nodes */
.filters{position:sticky; top:60px; z-index:10; background:var(--bg);
  padding:20px 0 14px; border-bottom:1px solid var(--line); margin-bottom:28px}
.srch{display:block; margin-bottom:12px}
.srch input{width:100%; max-width:420px; font:inherit; font-size:.97rem; color:var(--ink);
  background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:.6em .9em}
.srch input:focus{outline:2px solid var(--gold); outline-offset:1px}
.chips{display:flex; flex-wrap:wrap; gap:8px}
.chip{font:inherit; font-size:.86rem; color:var(--ink2); background:var(--surface);
  border:1px solid var(--line); border-radius:999px; padding:.34em .85em; cursor:pointer}
.chip:hover{color:var(--ink)}
.chip[aria-pressed=true]{background:var(--gold); color:#14100a; border-color:var(--gold);
  font-weight:600}
.cathead{font-size:.8rem; text-transform:uppercase; letter-spacing:.13em; color:var(--ink3);
  margin:34px 0 14px; font-weight:600}
.catgroup:first-child .cathead{margin-top:6px}
.nodegrid{padding-bottom:70px}
.node{background:var(--surface); border:1px solid var(--line); border-radius:var(--radius);
  padding:22px 24px; margin-bottom:14px}
.node-head{display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:12px}
.node-head h3{margin:0}
.tag{font-size:.72rem; text-transform:uppercase; letter-spacing:.09em; color:var(--ink3);
  border:1px solid var(--line); border-radius:999px; padding:.18em .6em}
.tag.term{border-color:var(--gold-dim); color:var(--gold)}
.nid{margin-left:auto; font-size:.78rem; color:var(--ink3); background:none; padding:0}
.pins{display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin-bottom:8px}
.pinlab{font-size:.72rem; text-transform:uppercase; letter-spacing:.09em; color:var(--ink3);
  width:28px}
.pin{font-size:.8rem; color:var(--ink2); background:var(--surface2); border:1px solid var(--line);
  border-radius:7px; padding:.1em .55em; display:inline-flex; align-items:center; gap:6px}
.pin::before{content:""; width:8px; height:8px; border-radius:50%; background:var(--ink3)}
.pin.height::before{background:var(--blue)}
.pin.mask::before{background:#d0a040}
.pin.scalar::before{background:var(--green)}
.node-body{margin-top:14px}
.node-body p{color:var(--ink2); margin-bottom:.75em}
.tip{font-size:.92rem; color:var(--ink3); border-left:2px solid var(--gold-dim);
  padding-left:12px; margin-top:1em!important}
.params{margin:1.2em 0 0; font-size:.9rem; min-width:440px}
.node .scroll{margin-top:1.2em}
.params code{font-size:.84em}

/* changelog */
.prose{padding-top:52px; padding-bottom:80px}
.changelog h2{margin-top:2.2em; padding-top:1.2em; border-top:1px solid var(--line);
  display:flex; align-items:baseline; gap:14px; flex-wrap:wrap}
.changelog h2:first-of-type{border-top:0; margin-top:1em; padding-top:0}
.changelog h2 span{font-size:.86rem; font-weight:400; color:var(--ink3); letter-spacing:0}
.changelog h3{margin-top:1.8em; font-size:.8rem; text-transform:uppercase; letter-spacing:.13em;
  color:var(--gold)}

/* footer */
.foot{border-top:1px solid var(--line); background:var(--bg2); padding:52px 0 64px}
.footgrid{display:grid; grid-template-columns:2fr 1fr 1fr; gap:34px}
.foot h4{font-size:.78rem; text-transform:uppercase; letter-spacing:.11em; color:var(--ink3);
  margin-bottom:.9em}
.foot p{margin:0 0 .45em; font-size:.94rem}
.foot a{color:var(--ink2); text-decoration:none}
.foot a:hover{color:var(--gold)}

@media (max-width:880px){
  .split{grid-template-columns:1fr; gap:28px; padding:48px 0}
  .split.flip .split-text{order:0}
  .footgrid{grid-template-columns:1fr 1fr}
  .hero-in{padding:72px 24px 60px}
  .stats{margin-bottom:48px}
}
@media (max-width:560px){
  body{font-size:16px}
  /* two rows: brand + buy on top, nav beneath, so nothing collides */
  .topbar{height:auto; flex-wrap:wrap; padding:10px 0 0; gap:10px}
  .brand{letter-spacing:.26em; font-size:.95rem}
  .top nav{order:3; width:100%; margin-left:0; gap:18px;
    border-top:1px solid var(--line); padding:8px 0; margin-top:2px}
  .top nav a{font-size:.9rem}
  .btn.small{margin-left:auto}
  .btn{width:100%; text-align:center}
  .btn.small{width:auto}
  .cta{flex-direction:column}
  .footgrid{grid-template-columns:1fr}
  .filters{position:static}
}
@media (prefers-reduced-motion:reduce){
  *{transition:none!important}
}
"""

os.makedirs(os.path.join(OUT, 'css'), exist_ok=True)
w = lambda p, s: open(os.path.join(OUT, p), 'w', encoding='utf-8', newline='\n').write(s)
w('index.html', landing())
w('nodes.html', nodes_page())
w('changelog.html', changelog_page())
w('css/site.css', CSS.lstrip())
print('wrote index.html, nodes.html, changelog.html, css/site.css')
print(f'version {VERSION}, {len(NODES)} nodes, {len(d["presets"])} presets')
