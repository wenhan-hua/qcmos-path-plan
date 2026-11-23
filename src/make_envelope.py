"""To-scale top view with the beam envelope and a clear-aperture check per element.
usage: python3 -I make_envelope.py <src_dir> <ComponentLibrary.svg> <inkscape> <out.svg> [default|swapped] [NA]
Dark red band = beam of an on-axis atom (radius f_obj*NA); light red band = union over the field (+-0.5 mm in-plane);
dashed lines = chief rays of the field edges.  Grey bar at an element = its clear aperture (90 % of the diameter,
x cos45 for 45-deg mirrors/DM); red/green bar = beam footprint (field edge) there."""
import sys, math
sys.path.insert(0, sys.argv[1])
from cl_lib import *
import optics_trace as O

variant = sys.argv[5] if len(sys.argv) > 5 else 'default'
NA = float(sys.argv[6]) if len(sys.argv) > 6 else O.DEFAULT_NA
swapped = variant == 'swapped'
res, a, LAY = O.full(swapped, NA)
PPM = 1.35
FONT = 'Helvetica, Arial, sans-serif'
Lb = Lib(sys.argv[2], sys.argv[3])

# ---- extents ---------------------------------------------------------------------------------------
pts = [(n['x'], n['z']) for k in res for n in res[k]]
for k in 'TR':                                   # camera bodies extend ~170 mm behind the sensor plane
    rr = res[k]; s_ = rr[-1]; p_ = rr[-2]; d_ = math.hypot(s_['x'] - p_['x'], s_['z'] - p_['z']) or 1
    body = 170 if s_.get('model') == 'qcmos' else 60
    pts.append((s_['x'] + body * (s_['x'] - p_['x']) / d_, s_['z'] + body * (s_['z'] - p_['z']) / d_))
X0, X1 = min(p[0] for p in pts) - 90, max(p[0] for p in pts) + 60
Z0, Z1 = min(p[1] for p in pts) - 110, max(p[1] for p in pts) + 40
LW, LH = (X1 - X0) * PPM, (Z1 - Z0) * PPM
TABLE_H = 400
W, H = int(max(LW + 40, 1560)), int(LH + TABLE_H)
px = lambda x: (x - X0) * PPM + 20
pz = lambda z: (z - Z0) * PPM + 10

doc = Lb.new_doc(W, H); defs = Lb.docdefs
def E(parent, tag, **kw): return ET.SubElement(parent, '{%s}%s' % (SVG, tag), {k.replace('_', '-'): str(v) for k, v in kw.items()})
for gid, cols in (('barrel', ['#2b2b2b', '#a9a9a9', '#2b2b2b']), ('body', ['#25282d', '#555b64', '#25282d']), ('silver', ['#8e949c', '#e4e7ea', '#8e949c'])):
    g = E(defs, 'linearGradient', id=gid, x1=0, y1=0, x2=0, y2=1)
    for o, c in zip((0, .5, 1), cols): E(g, 'stop', offset=o, style=f'stop-color:{c}')
bg = E(doc, 'g'); env = E(doc, 'g'); comps = E(doc, 'g'); bars = E(doc, 'g'); txt = E(doc, 'g')
E(bg, 'rect', width=W, height=H, fill='white')
E(bg, 'rect', x=10, y=10, width=LW + 20, height=LH, rx=14, fill='#f4f6f9', stroke='#cfd5dd')
# 100 mm grid ticks
for gx in range((int(X0) // 100 + 1) * 100, int(X1), 100):
    E(bg, 'line', x1=px(gx), y1=pz(Z0 + 100), x2=px(gx), y2=pz(Z1) - 4, stroke='#e2e6ec', stroke_width=1)
for gz in range((int(Z0) // 100 + 1) * 100, int(Z1), 100):
    E(bg, 'line', x1=px(X0) + 10, y1=pz(gz), x2=px(X1) - 4, y2=pz(gz), stroke='#e2e6ec', stroke_width=1)
def text(x, y, s, size=13, anchor='middle', color='#111', bold=False):
    t = E(txt, 'text', x=x, y=y, font_family=FONT, font_size=size, text_anchor=anchor, fill=color, font_weight='bold' if bold else 'normal'); t.text = s; return t

# ---- sequences of nodes per branch (common path + T chain, common + R chain) ---------------------------------
def seq(branch):
    rows = res['common'] + res[branch]; seen = False
    for r in rows:
        if r['kind'] == 'filter':
            r['_second'] = seen; seen = True
    return rows
def unit(a_, b_):
    d = math.hypot(b_[0] - a_[0], b_[1] - a_[1]) or 1; return ((b_[0] - a_[0]) / d, (b_[1] - a_[1]) / d)

# ---- beam envelope ------------------------------------------------------------------------------------
def envelope(nodes):
    for n0, n1 in zip(nodes, nodes[1:]):
        if n0['kind'] == 'fov': continue            # object space: not drawn
        p0, p1 = (n0['x'], n0['z']), (n1['x'], n1['z']); d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if d < 1e-6: continue
        ux, uz = unit(p0, p1); nx, nz = -uz, ux
        N = max(2, int(d / 4)); L1_, R1_, L2_, R2_, c1, c2 = [], [], [], [], [], []
        for i in range(N + 1):
            t = d * i / N
            al = n0['alpha'] + n0['alpha_u'] * t; be = n0['beta'] + n0['beta_u'] * t
            cx, cz = p0[0] + ux * t, p0[1] + uz * t
            w1, w2 = abs(al) * a, abs(al) * a + abs(be) * O.H_EDGE
            L1_.append((cx + nx * w1, cz + nz * w1)); R1_.append((cx - nx * w1, cz - nz * w1))
            L2_.append((cx + nx * w2, cz + nz * w2)); R2_.append((cx - nx * w2, cz - nz * w2))
            c1.append((cx + nx * be * O.H_EDGE, cz + nz * be * O.H_EDGE)); c2.append((cx - nx * be * O.H_EDGE, cz - nz * be * O.H_EDGE))
        poly = lambda A, B: ' '.join(f'{px(x):.1f},{pz(z):.1f}' for x, z in A + B[::-1])
        E(env, 'polygon', points=poly(L2_, R2_), fill='#ff5a4d', fill_opacity=.22)
        E(env, 'polygon', points=poly(L1_, R1_), fill='#d40000', fill_opacity=.45)
        for c in (c1, c2):
            E(env, 'polyline', points=' '.join(f'{px(x):.1f},{pz(z):.1f}' for x, z in c), fill='none', stroke='#8a0000', stroke_width=1, stroke_dasharray='5 3')
        E(env, 'line', x1=px(p0[0]), y1=pz(p0[1]), x2=px(p1[0]), y2=pz(p1[1]), stroke='#ee0000', stroke_width=1.2)
for br in 'TR': envelope(seq(br))

# ---- components, to scale -----------------------------------------------------------------------------
def dir_at(nodes, i):
    a_ = nodes[i - 1] if i > 0 else nodes[i]; b_ = nodes[i + 1] if i + 1 < len(nodes) and i == 0 else nodes[i]
    return unit((a_['x'], a_['z']), (b_['x'], b_['z']))
def strip_black(g):
    for par in list(g.iter()):
        for ch in list(par):
            if ch.tag in ('{%s}path' % SVG, '{%s}rect' % SVG) and 'fill' not in ch.get('style', '') and not ch.get('fill'): par.remove(ch)
def mirror_glyph(n, din, dout, dm=False):
    if n.get('din') and n.get('dout'): din, dout = n['din'], n['dout']      # layout's own reflection geometry (DM is straight on the T branch)
    nrm = (dout[0] - din[0], dout[1] - din[1]); m = math.hypot(*nrm); nrm = (nrm[0] / m, nrm[1] / m)
    mm = 25.4 * (n.get('size') or 1); s = mm * PPM / 29
    X, Y = px(n['x']), pz(n['z']); ang = math.degrees(math.atan2(nrm[1], nrm[0]))
    if dm:
        g = Lb.place(comps, 'g3568', X, Y, angle=ang - 180, scale=s); strip_black(g)
    else:
        E(comps, 'rect', x=-5.5 * s * .96, y=-14.5 * s * .96, width=11 * s * .96, height=29 * s * .96, fill='white', transform=f'translate({X},{Y}) rotate({ang - 135 - 45})')
        Lb.place(comps, 'g7458', X, Y, angle=ang - 135, scale=s)
def draw_cam(n, h):
    q = n['model'] == 'qcmos'; Lm, Wd = (160, 100) if q else (42, 29)
    g = E(comps, 'g', transform=f"translate({px(n['x']):.1f},{pz(n['z']):.1f}) rotate({math.degrees(math.atan2(h[1], h[0])):.2f}) scale({PPM})")
    E(g, 'rect', x=-17.5, y=-7.5 if not q else -12, width=17.5, height=15 if not q else 24, fill='url(#silver)', stroke='black', stroke_width=.6)
    E(g, 'rect', x=-17.5 + 17.5, y=-Wd / 2, width=Lm, height=Wd, fill='url(#body)', stroke='black', stroke_width=.8)
    if q:
        for k in range(-4, 5): E(g, 'rect', x=10, y=-Wd / 2 + 12 + (k + 4) * 9, width=120, height=3, fill='#aab0b8')
    else: E(g, 'rect', x=0, y=-Wd / 2, width=3, height=Wd, fill='#1f6fb5')
def draw_all():
    done = set()
    for br in 'TR':
        nodes = seq(br)
        for i, n in enumerate(nodes):
            key = (n['name'], round(n['x']), round(n['z']))
            if key in done: continue
            done.add(key); X, Y = px(n['x']), pz(n['z'])
            prev = nodes[i - 1] if i > 0 else n; nxt = nodes[i + 1] if i + 1 < len(nodes) else n
            din = unit((prev['x'], prev['z']), (n['x'], n['z'])) if i > 0 else unit((n['x'], n['z']), (nxt['x'], nxt['z']))
            dout = unit((n['x'], n['z']), (nxt['x'], nxt['z'])) if nxt is not n else din
            k = n['kind']
            if k == 'mirror': mirror_glyph(n, din, dout)
            elif k == 'dm': mirror_glyph(n, din, dout, dm=True)
            elif k == 'lens':
                mm = 25.4 * n['size']; Lb.place(comps, 'g3746', X, Y, angle=0 if abs(din[0]) > .5 else 90, scale=mm * PPM / 23.05)
            elif k == 'filter':
                g = Lb.place(comps, 'g3533', X, Y, angle=0 if abs(din[0]) > .5 else 90, scale=25.4 * PPM / 29); strip_black(g)
            elif k == 'camera': draw_cam(n, din)
    # FoV + objective
    E(comps, 'circle', cx=px(0), cy=pz(0), r=3.2, fill='#ffd23f', stroke='#7a5d00', stroke_width=1)
    prof = [(8, 3.5), (30, 8), (44, 14.5), (66, 14.5), (66, 17), (70, 17)]
    g = E(comps, 'g', transform=f'translate({px(0)},{pz(0)}) scale({PPM})')
    E(g, 'polygon', points=' '.join(f'{x},{y}' for x, y in prof + [(x, -y) for x, y in prof[::-1]]), fill='url(#barrel)', stroke='black', stroke_width=.6)
    E(comps, 'line', x1=px(70), y1=pz(-20), x2=px(70), y2=pz(20), stroke='#0a58ca', stroke_width=2.2)
draw_all()

# ---- aperture bars + labels ---------------------------------------------------------------------------------
def aperture_bars():
    done = set()
    for br in 'TR':
        nodes = seq(br)
        for i, n in enumerate(nodes):
            key = (n['name'], round(n['x']), round(n['z']))
            if key in done or 'r_allow' not in n: continue
            done.add(key)
            prev = nodes[i - 1]; ux, uz = unit((prev['x'], prev['z']), (n['x'], n['z'])); nx, nz = -uz, ux
            X, Z = n['x'], n['z']
            ra, rf = n['r_allow'], n['r_edge']; bad = rf > ra + 1e-9
            def bar(r, col, w):
                E(bars, 'line', x1=px(X - nx * r), y1=pz(Z - nz * r), x2=px(X + nx * r), y2=pz(Z + nz * r), stroke=col, stroke_width=w, stroke_linecap='round')
            bar(ra, '#444', 5.5); bar(rf, '#e00000' if bad else '#1a8f1a', 2.4)
def labels():
    done = set()
    for br in 'TR':
        nodes = seq(br)
        for i, n in enumerate(nodes):
            key = (n['name'], round(n['x']), round(n['z']))
            if key in done: continue
            done.add(key); k = n['kind']
            if k in ('fov', 'pupil'): continue
            prev = nodes[i - 1]; ux, uz = unit((prev['x'], prev['z']), (n['x'], n['z']))
            side = LABSIDE.get((n['name'], br), 1)
            nx, nz = -uz * side, ux * side
            R = max(n.get('r_edge', 0), n.get('r_allow', 0), 20) + 22
            if k in ('mirror', 'dm'):                    # outside the fold
                if n.get('din') and n.get('dout'): ux, uz = n['din']; dout = n['dout']
                else: dout = unit((n['x'], n['z']), (nodes[i + 1]['x'], nodes[i + 1]['z'])) if i + 1 < len(nodes) else (ux, uz)
                nx, nz = -(dout[0] - ux), -(dout[1] - uz); m = math.hypot(nx, nz) or 1.0; nx, nz = nx / m, nz / m; R = 46
                if m == 1.0 and nx == 0 and nz == 0: nx, nz = -uz, ux
            if k == 'camera': R = 70
            X, Z = px(n['x'] + nx * R), pz(n['z'] + nz * R)
            anc = 'start' if nx > .5 else 'end' if nx < -.5 else 'middle'
            if (n['name'], br) in LABOFF:
                ox, oz, anc = LABOFF[(n['name'], br)]; X, Z = px(n['x'] + ox), pz(n['z'] + oz)
            if k == 'filter':
                if n.get('_second'): continue
                fl = [m for m in nodes if m['kind'] == 'filter']; hmin = min(m['h_ok'] for m in fl)
                n = dict(n, name='Filters ×%d' % len(fl), h_ok=hmin)
            title = n['name'] + (f"  f={n['f']:g}" if k == 'lens' else '')
            if k == 'camera': title = 'qCMOS' if n.get('model') == 'qcmos' else 'Basler'
            if k == 'dm': title = 'DM'
            text(X, Z, title, 13, anc, bold=True)
            if 'h_ok' in n:
                ok = n['h_ok'] >= O.H_CORNER; edge = n['h_ok'] >= O.H_EDGE
                col = '#1a8f1a' if ok else ('#b06a00' if edge else '#d00000')
                s_ = ('passes full FoV' if ok else f"max field ±{n['h_ok']:.2f} mm") if n['h_ok'] < 99 else 'passes full FoV'
                text(X, Z + 14, s_, 11.5, anc, color=col)
LABSIDE = {('L2', 'T'): -1, ('L2', 'R'): -1, ('Filter', 'T'): -1, ('Filter', 'R'): -1, ('L1', 'T'): -1, ('L1', 'R'): -1, ('L4', 'T'): -1, ('L5', 'T'): -1}
LABOFF = {('M6', 'T'): (-34, 0, 'end'), ('M8', 'T'): (-40, 44, 'end'), ('M3', 'T'): (50, 6, 'start'), ('Filter', 'T'): (20, 78, 'middle'), ('M6', 'R'): (-34, 0, 'end'), ('Filter', 'R'): (46, 0, 'start'), ('M8', 'T'): (-45, -34, 'end'), ('M7', 'T'): (34, -44, 'start'),
          ('M10', 'R'): (45, -10, 'start'), ('M10', 'T'): (40, -26, 'start'), ('M5', 'R'): (46, 10, 'start'), ('M4', 'T'): (-34, -34, 'end')}
bars_done = aperture_bars(); labels()

# ---- title / legend -------------------------------------------------------------------------------------------
import layout as _LY
text(30, 36, f"Beam envelope check ({'ports swapped' if swapped else 'qCMOS on T, Basler on R'}) – to scale   ·   variant L4 = {_LY.CUR['f_L4']:g} mm / L5 = {_LY.CUR['f_L5']:g} mm", 24, 'start', bold=True)
text(30, 58, f"Assumes objective NA {NA:g} (EFL 10 mm → beam Ø{2 * a:g} mm), exit pupil at the objective back end (blue bar), FoV 1×1 mm, thin lenses, geometric rays. Grid = 100 mm.", 13, 'start', color='#444')
lx, ly = 30, 84
E(txt, 'rect', x=lx, y=ly - 9, width=26, height=9, fill='#d40000', fill_opacity=.45); text(lx + 34, ly, 'beam of an on-axis atom', 12, 'start')
E(txt, 'rect', x=lx + 190, y=ly - 9, width=26, height=9, fill='#ff5a4d', fill_opacity=.22); text(lx + 224, ly, 'union over the field (±0.5 mm)', 12, 'start')
E(txt, 'line', x1=lx + 430, y1=ly - 4, x2=lx + 456, y2=ly - 4, stroke='#8a0000', stroke_dasharray='5 3'); text(lx + 464, ly, 'chief rays of field edge', 12, 'start')
E(txt, 'line', x1=lx + 620, y1=ly - 4, x2=lx + 646, y2=ly - 4, stroke='#444', stroke_width=5.5, stroke_linecap='round'); text(lx + 654, ly, 'clear aperture', 12, 'start')
E(txt, 'line', x1=lx + 760, y1=ly - 4, x2=lx + 786, y2=ly - 4, stroke='#e00000', stroke_width=2.4); text(lx + 794, ly, 'footprint too big', 12, 'start')

# ---- table ------------------------------------------------------------------------------------------------------
ty = LH + 50
text(30, ty, 'Clear-aperture check (field edge in-plane, ±0.5 mm; "max field" = largest field radius that passes the element without clipping)', 14, 'start', bold=True)
cols = {'T': 30, 'R': 30 + (W - 60) / 2}
for br in 'TR':
    x = cols[br]; y = ty + 28
    port = ('qCMOS' if (br == 'T') != swapped else 'Basler')
    text(x, y, f"{'Transmitted' if br == 'T' else 'Reflected'} port → {port}   (path incl. common part)", 13, 'start', bold=True); y += 18
    text(x, y, 'element', 11.5, 'start', color='#666'); text(x + 150, y, 'footprint r', 11.5, 'start', color='#666'); text(x + 235, y, 'allowed r', 11.5, 'start', color='#666'); text(x + 315, y, 'max field', 11.5, 'start', color='#666'); y += 15
    for n in seq(br):
        if 'h_ok' not in n: continue
        h = n['h_ok']; col = '#1a8f1a' if h >= O.H_CORNER else ('#b06a00' if h >= O.H_EDGE else '#d00000')
        nm = n['name'] + (f" ({25.4 * n['size']:.0f} mm)" if n['kind'] in ('mirror', 'dm', 'lens', 'filter') else '')
        text(x, y, nm, 12, 'start'); text(x + 150, y, f"{n['r_edge']:.1f} mm", 12, 'start'); text(x + 235, y, f"{n['r_allow']:.1f} mm", 12, 'start')
        text(x + 315, y, 'OK' if h >= O.H_CORNER else f"±{h:.2f} mm", 12, 'start', color=col, bold=True); y += 16
    lim = min((n for n in seq(br) if 'h_ok' in n), key=lambda n: n['h_ok'])
    text(x, y + 8, f"limiting: {lim['name']} → only ±{lim['h_ok']:.2f} mm of the ±0.50 mm field is unvignetted" if lim['h_ok'] < O.H_EDGE else f"limiting: {lim['name']} (±{lim['h_ok']:.2f} mm) – full FoV passes", 12.5, 'start', color='#d00000' if lim['h_ok'] < O.H_EDGE else '#1a8f1a', bold=True)
text(30, H - 14, 'Allowed r = 0.9 × radius of the optic; ×0.707 for 45° mirrors/DM (in-plane). Green ≥ corner (0.71 mm) · orange ≥ edge (0.50 mm) · red < edge.   Glyphs: ComponentLibrary, A. Franzen, CC BY-NC 3.0.', 11, 'start', color='#777')
ET.ElementTree(doc).write(sys.argv[4], xml_declaration=True, encoding='utf-8')
