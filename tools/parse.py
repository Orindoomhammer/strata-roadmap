"""Extract Strata's node definitions and in-app node reference text from source.

Reads src/node_types.rs (NODE_TYPES + EXTRA_NODE_TYPES, with OVERRIDES applied
the same way node_types::all() applies them) and src/tutorial.rs (LESSONS),
and writes one JSON file the site generator consumes.
"""
import json, re, sys, os

SRC = sys.argv[1]
BS = chr(92)   # backslash
ESC = {'n': '\n', 't': '\t', 'r': '', '"': '"', BS: BS, "'": "'"}

PIN = re.compile(
    r'Pin \{\s*key: "([^"]+)",\s*label: "([^"]*)",\s*kind: PinKind::(\w+)\s*\}', re.S)
FIELD = re.compile(
    r'FieldDef \{\s*key: "([^"]+)",\s*label: "([^"]*)",\s*kind: "(\w+)",\s*'
    r'default: Val::(\w)\(([^)]*)\),\s*min: (-?[\d.]+)(?:f32)?,\s*max: (-?[\d.]+)(?:f32)?,\s*'
    r'options: (?:&\[([^\]]*)\]|(BLEND_MODES))', re.S)


def rust_str(s, i):
    """Read a Rust string literal starting at s[i] == quote. Returns (text, next_index)."""
    assert s[i] == '"', s[i:i + 20]
    i += 1
    out = []
    while True:
        c = s[i]
        if c == BS:
            n = s[i + 1]
            if n == '\n':                      # line continuation: skip newline + indent
                i += 2
                while i < len(s) and s[i] in ' \t':
                    i += 1
                continue
            out.append(ESC.get(n, n))
            i += 2
            continue
        if c == '"':
            return ''.join(out), i + 1
        out.append(c)
        i += 1


def segment(ch, start_key, end_key):
    """The text of one struct field, from its key up to the next key."""
    try:
        a = ch.index(start_key)
    except ValueError:
        return ''
    b = ch.index(end_key, a) if end_key and end_key in ch[a:] else len(ch)
    return ch[a:b]


def pins(seg):
    return [{'key': k, 'label': l, 'kind': kd} for k, l, kd in PIN.findall(seg)]


def fields(seg, blend_modes):
    out = []
    for key, flab, kind, vt, val, mn, mx, opts, is_blend in FIELD.findall(seg):
        val = val.strip().replace('f32', '')
        if vt == 'S':
            val = val.strip('"')
        options = list(blend_modes) if is_blend else \
            [o.strip().strip('"') for o in opts.split(',') if o.strip()]
        out.append({'key': key, 'label': flab.strip(), 'kind': kind, 'default': val,
                    'min': mn, 'max': mx, 'options': options})
    return out


nt = open(os.path.join(SRC, 'node_types.rs'), encoding='utf-8').read()

blend_modes = [m for m in re.findall(
    r'"([a-z-]+)"', nt[nt.index('pub const BLEND_MODES'):nt.index('pub const OVERRIDES')])]
max_layers = int(re.search(r'pub const MAX_LAYERS: usize = (\d+)', nt).group(1))
default_layers = int(re.search(r'pub const DEFAULT_LAYERS: usize = (\d+)', nt).group(1))


def parse_array(text):
    found = []
    for ch in text.split('NodeTypeDef {')[1:]:
        m = re.search(r'id: "([^"]+)"', ch)
        if not m:
            continue
        nid = m.group(1)
        seg_f = segment(ch, 'fields:', None)
        n = {
            'id': nid,
            'label': re.search(r'label: "([^"]+)"', ch).group(1),
            'category': re.search(r'category: "([^"]+)"', ch).group(1),
            'terminal': re.search(r'terminal: (true|false)', ch).group(1) == 'true',
            'inputs': pins(segment(ch, 'inputs:', 'outputs:')),
            'outputs': pins(segment(ch, 'outputs:', 'fields:')),
            'fields': fields(seg_f, blend_modes),
        }
        # Layer Stack builds its pins and fields from macros, so they are not
        # literal in the source. Describe it from the constants instead.
        if 'layer_pins!' in ch:
            n['macro_pins'] = True
            n['inputs'] = ([{'key': 'base', 'label': 'Base', 'kind': 'Height'}] +
                           [p for i in range(1, max_layers + 1) for p in (
                               {'key': f'l{i}', 'label': f'Layer {i}', 'kind': 'Height'},
                               {'key': f'm{i}', 'label': f'Mask {i}', 'kind': 'Mask'})])
            n['outputs'] = [{'key': 'height', 'label': 'Height', 'kind': 'Height'}]
            n['fields'] = []
        found.append(n)
    return found


def array_body(name):
    """The literal entries of `pub const <name>`, cut at the array's closing `];`."""
    a = nt.index('pub const ' + name)
    return nt[a:nt.index('\n];', a)]


main = parse_array(array_body('NODE_TYPES'))
extra = parse_array(array_body('EXTRA_NODE_TYPES'))
overrides = {n['id']: n for n in parse_array(array_body('OVERRIDES'))}

nodes = [overrides.get(n['id'], n) for n in main + extra]

# ---------- tutorial.rs ----------
tu = open(os.path.join(SRC, 'tutorial.rs'), encoding='utf-8').read()
body = tu[tu.index('pub const LESSONS'):tu.index('pub struct Step')]

lessons = []
for m in re.finditer(r'\bl\(\s*(None|Some\("([^"]+)"\))\s*,', body):
    i = m.end()
    parts = []
    for _ in range(3):
        while body[i] != '"':
            i += 1
        txt, i = rust_str(body, i)
        parts.append(txt)
    lessons.append({'node': m.group(2), 'title': parts[0], 'body': parts[1], 'tip': parts[2]})

# ---------- presets.rs + export.rs ----------
pr = open(os.path.join(SRC, 'presets.rs'), encoding='utf-8').read()
FMT = {'R16': '16-bit R16 raw', 'Png16': '16-bit PNG'}
presets = []
for ch in pr[pr.index('pub const PRESETS'):].split('Preset {')[1:]:
    m = re.search(r'name: "([^"]+)"', ch)
    if not m:
        continue
    sizes = [int(w) for w in re.findall(r'Size \{ label: "[^"]*", w: (\d+)', ch)]
    presets.append({
        'name': m.group(1),
        'fmt': FMT[re.search(r'fmt: Fmt::(\w+)', ch).group(1)],
        'min': min(sizes), 'max': max(sizes), 'steps': len(sizes),
        'height_range_m': re.search(r'height_range_m: ([\d.]+)', ch).group(1).rstrip('.0') or '0',
        'hint': re.search(r'hint: "([^"]*)"', ch).group(1),
    })

ex = open(os.path.join(SRC, 'export.rs'), encoding='utf-8').read()
# The shipping build's layouts: the #[cfg(not(feature = "demo"))] arm.
lay = re.search(r'not\(feature = "demo"\)\)\]\s*pub const LAYOUTS: \[Layout; \d+\] = \[([^\]]*)\]', ex)
layouts = []
for tok in lay.group(1).split(','):
    tok = tok.strip()
    if tok == 'Layout::Single':
        layouts.append('1 x 1')
    elif tok.startswith('Layout::Grid'):
        n = re.search(r'Grid\((\d+)\)', tok).group(1)
        layouts.append(f'{n} x {n}')

data = {'nodes': nodes, 'lessons': lessons, 'blend_modes': blend_modes,
        'max_layers': max_layers, 'default_layers': default_layers,
        'presets': presets, 'layouts': layouts}
with open(sys.argv[2], 'w', encoding='utf-8') as fh:
    json.dump(data, fh, indent=1)

byid = {l['node'] for l in lessons if l['node']}
ids = {n['id'] for n in nodes}
print(f"nodes={len(nodes)}  main={len(main)} extra={len(extra)} overrides={len(overrides)}")
print(f"lessons={len(lessons)} (intro {sum(1 for l in lessons if not l['node'])})")
print(f"blend_modes={len(blend_modes)} max_layers={max_layers} default_layers={default_layers}")
print("no lesson:", sorted(ids - byid))
print("lesson with no node:", sorted(byid - ids))
print("fieldless:", [n['id'] for n in nodes if not n['fields'] and not n.get('macro_pins')])
print("layouts:", layouts)
for p in presets:
    print(f"  {p['name']:17} {p['min']:>5}-{p['max']:<5} {p['steps']} steps  {p['fmt']}")
