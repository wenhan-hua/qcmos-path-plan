"""Port-swappable version of the qCMOS/Basler beam-path diagram (new file; the original make_diagram.py is untouched).
usage: python3 -I make_diagram_flip.py <script_dir> <ComponentLibrary.svg> <inkscape> <out.svg> [flip]
  default : qCMOS on DM transmitted port, Basler on reflected port (shortpass DM: T 852 nm, R 1030 nm)
  flip    : qCMOS on DM reflected port,  Basler on transmitted port (longpass DM: R 852 nm, T 1030 nm)"""
import sys, math, re
sys.path.insert(0, sys.argv[1])
from cl_lib import *
import layout as LY
C_ = LY.CUR; F4, F5 = C_['f_L4'], C_['f_L5']
FLIP = len(sys.argv) > 5 and sys.argv[5] == 'flip'

L = Lib(sys.argv[2], sys.argv[3])
W = 1700
MIR = LY.MIRROR                                   # whole layout mirrored across the objective axis (M1 turns the other way)
H0 = 1490 if FLIP else 1060
H = H0 + (70 if MIR else 0)
PAN = []
doc = L.new_doc(W, H)
defs = L.docdefs
def E(parent, tag, **kw):
    return ET.SubElement(parent, '{%s}%s' % (SVG, tag), {k.replace('_', '-'): str(v) for k, v in kw.items()})
g = E(defs, 'linearGradient', id='barrel', x1=0, y1=0, x2=0, y2=1)
for o, c in [(0, '#2b2b2b'), (0.5, '#a9a9a9'), (1, '#2b2b2b')]: E(g, 'stop', offset=o, style=f'stop-color:{c}')
g = E(defs, 'linearGradient', id='fov', x1=0, y1=0, x2=1, y2=0)
for o, c in [(0, '#89A4B6'), (0.5, '#FFFFFF'), (1, '#89A4B6')]: E(g, 'stop', offset=o, style=f'stop-color:{c}')

FONT = 'Helvetica, Arial, sans-serif'; RED = '#ee0000'; S2, S1 = 2.3, 1.45
bg = E(doc, 'g'); beams = E(doc, 'g'); comps = E(doc, 'g'); txt = E(doc, 'g'); ubg = E(doc, 'g'); utxt = E(doc, 'g')   # u* = fixed UI, not mirrored
E(bg, 'rect', width=W, height=H, fill='white')

def text(x, y, lines, anchor='middle', size=15, color='#000'):
    t = E(txt, 'text', x=x, y=y, font_family=FONT, font_size=size, text_anchor=anchor, fill=color)
    for i, ln in enumerate(lines):
        s = E(t, 'tspan', x=x, dy=0 if i == 0 else size * 1.25)
        if i == 0: s.set('font-weight', 'bold')
        else: s.set('fill', '#444'); s.set('font-size', str(size * .85))
        s.text = ln
def unit(a, b):
    d = math.hypot(b[0] - a[0], b[1] - a[1]); return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
def strip_black(g):
    for par in list(g.iter()):
        for ch in list(par):
            if ch.tag in ('{%s}path' % SVG, '{%s}rect' % SVG) and 'fill' not in ch.get('style', '') and not ch.get('fill'):
                par.remove(ch)
def mirror(p, din, dout, s=S2):
    n = (dout[0] - din[0], dout[1] - din[1]); m = math.hypot(*n); n = (n[0] / m, n[1] / m)
    ang = math.degrees(math.atan2(n[1], n[0])) - 135
    E(comps, 'rect', x=-5.5 * s * .96, y=-14.5 * s * .96, width=11 * s * .96, height=29 * s * .96, fill='white',
      transform=f'translate({p[0]},{p[1]}) rotate({ang - 45})')
    L.place(comps, 'g7458', p[0], p[1], angle=ang, scale=s)
def lens(p, h, s=S2):
    L.place(comps, 'g3746', p[0], p[1], angle=0 if abs(h[0]) > .5 else 90, scale=s)
def filt(p, h):
    gg = L.place(comps, 'g3533', p[0], p[1], angle=0 if abs(h[0]) > .5 else 90, scale=S2 * .9); strip_black(gg)
def camera(p, h):
    L.place(comps, 'g90078', p[0], p[1], angle=math.degrees(math.atan2(h[1], h[0])), scale=2.0)
def beam(pts):
    E(beams, 'path', d='M ' + ' L '.join(f'{x},{y}' for x, y in pts), fill='none', stroke=RED, stroke_width=2.6)
    for a, b in zip(pts, pts[1:]):
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 110: continue
        ux, uy = unit(a, b); mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        P = [(mx + ux * 7, my + uy * 7), (mx - ux * 6 - uy * 6, my - uy * 6 + ux * 6), (mx - ux * 6 + uy * 6, my - uy * 6 - ux * 6)]
        E(beams, 'polygon', points=' '.join(f'{a_:.1f},{b_:.1f}' for a_, b_ in P), fill=RED)

# ---- common path (FoV -> obj -> M1 -> M2 -> L1 -> DM) ------------------------------------------
Y0 = 175; Y1 = 560 if FLIP else 365; DMx = 730; fx = 85; ox = 125
FWD, LEFT_ = (1, 0), (0, 1)
E(comps, 'rect', x=fx - 4, y=Y0 - 30, width=8, height=60, fill='url(#fov)', stroke='black', stroke_width=1.2)
obj = [(ox, Y0 - 9), (ox + 34, Y0 - 24), (ox + 100, Y0 - 24), (ox + 100, Y0 + 24), (ox + 34, Y0 + 24), (ox, Y0 + 9)]
E(comps, 'polygon', points=' '.join(f'{a},{b}' for a, b in obj), fill='url(#barrel)', stroke='black', stroke_width=1.2)
E(comps, 'rect', x=ox + 100, y=Y0 - 29, width=10, height=58, fill='#111')
E(comps, 'rect', x=ox + 34, y=Y0 - 27, width=5, height=54, fill='#111')
M1, M2, L1p, DM = (370, Y0), (370, Y1), (560, Y1), (DMx, Y1)
beam([(fx, Y0), M1, M2, DM])
mirror(M1, (1, 0), (0, 1)); mirror(M2, (0, 1), (1, 0)); lens(L1p, (1, 0))
gg = L.place(comps, 'g3568', DM[0], DM[1], angle=-45, scale=S2); strip_black(gg)
text(fx, Y0 - 52, ['FoV', '1 mm × 1 mm'])
text(ox + 50, Y0 + 50, ['Static objective', 'EFL = 10 mm'])
text(M1[0] + 20, Y0 - 50, ['M1', '1″ or 2″'], 'start')
text(M2[0] + 20, Y1 + 55, ['M2', '2″'], 'start')
text(L1p[0], Y1 + 60, ['L1  f = 150 mm', '2″ lens'])

# ---- branch chains, defined in a local frame: u = along port heading, v = to the left of heading ----
# element: (kind, u, v, din, dout | size, label lines)
CH_Q = dict(name='qCMOS', els=[
    ('M', 200, 0, (1, 0), (0, 1), 2, ['M3', '2″']), ('M', 200, 190, (0, 1), (1, 0), 2, ['M4', '2″']),
    ('L', 360, 190, 2, ['L2  f = 150 mm', '2″ lens']),
    ('M', 510, 190, (1, 0), (0, -1), 2, ['M5', '2″']), ('M', 510, 0, (0, -1), (1, 0), 1, ['M6', '1″']),
    ('F', 575, 0, ['852 nm line filters', '≥ 1, last one before L3']), ('F', 610, 0, None),
    ('L', 670, 0, 1, ['L3  f = 40 mm', '(or 50 mm)', '1″ lens']),
    ('C', 790, 0, ['qCMOS', 'C15550-22UP', '18.8 × 10.6 mm', '4.6 µm pixel'])], end=790 - 35)
CH_B = dict(name='Basler', els=[
    ('M', 165, 0, (1, 0), (0, 1), 2, ['M7', '2″']), ('M', 165, 140, (0, 1), (1, 0), 2, ['M8', '2″']),
    ('L', 260, 140, C_['L4_size'], ['L4  f = %g mm' % F4, '%d″ lens' % C_['L4_size']]),
    ('M', 360, 140, (1, 0), (0, 1), C_['M9_size'], ['M9', '%d″' % C_['M9_size']]), ('M', 360, 310, (0, 1), (1, 0), C_['M10_size'], ['M10', '%d″' % C_['M10_size']]),
    ('L', 445, 310, C_['L5_size'], ['L5  f = %g mm' % F5, '%d″ lens' % C_['L5_size']]),
    ('C', 540, 310, ['Basler acA4029-29um', '7.5 × 5.6 mm', '1.85 µm pixel'])], end=540 - 40)

SIDES = {('qCMOS', 'T'): dict(L2='r', F='l', L3='r', C='l'), ('qCMOS', 'R'): dict(L2='r', F='r', L3='r', C='l'),
         ('Basler', 'R'): dict(L4='r', L5='r', C='r'), ('Basler', 'T'): dict(L4='r', L5='l', C='r')}
MOFF = {('Basler', 'R', 'M8'): (48, 22)}
def run_chain(ch, port):
    heading = {'T': (1, 0), 'R': (0, 1)}[port]
    h = heading; l = (h[1], -h[0])             # left of heading in screen coords (y down)
    G = lambda u, v: (DM[0] + u * h[0] + v * l[0], DM[1] + u * h[1] + v * l[1])
    D = lambda d: (d[0] * h[0] + d[1] * l[0], d[0] * h[1] + d[1] * l[1])
    pts = [DM]; allp = []; boxes = []
    sd = SIDES[(ch['name'], port)]
    def label(p, lines, off, side=None, along=0):
        if side: v = l if side == 'l' else (-l[0], -l[1]); off = (v[0] * 62 + h[0] * along, v[1] * 62 + h[1] * along)
        x, y = p[0] + off[0], p[1] + off[1]
        wid = max(len(t) for t in lines) * 7.6; hei = 15 * 1.25 * len(lines)
        if abs(off[1]) >= abs(off[0]):
            yb = y + (14 if off[1] > 0 else -26 - 13 * (len(lines) - 1)); text(x, yb, lines)
            boxes.append((x - wid / 2, yb - 14, x + wid / 2, yb - 14 + hei + 8))
        else:
            anc = 'start' if off[0] > 0 else 'end'; text(x, y - 4, lines, anc)
            boxes.append((x if off[0] > 0 else x - wid, y - 18, x + wid if off[0] > 0 else x, y - 18 + hei + 8))
    for e in ch['els']:
        k = e[0]; p = G(e[1], e[2]); allp.append(p)
        if k == 'M':
            din, dout, size, lines = D(e[3]), D(e[4]), e[5], e[6]
            pts.append(p); mirror(p, din, dout, S2 if size == 2 else S1)
            n = (dout[0] - din[0], dout[1] - din[1]); m = math.hypot(*n)
            label(p, lines, MOFF.get((ch['name'], port, lines[0])) and tuple(map(float, (MOFF[(ch['name'], port, lines[0])][0] * 1, MOFF[(ch['name'], port, lines[0])][1]))) or (-n[0] / m * 50, -n[1] / m * 50))
        elif k == 'L':
            size, lines = e[3], e[4]; lens(p, h, S2 if size == 2 else S1); label(p, lines, None, sd[lines[0].split()[0]])
        elif k == 'F':
            filt(p, h)
            if e[3]: label(p, e[3], None, sd['F'], along=32)
        elif k == 'C':
            camera(p, h); label(p, e[3], None, sd['C'])
    last_v = ch['els'][-1][2]
    pts.append(G(ch['end'], last_v)); beam(pts)
    return allp, boxes

a = CH_B if FLIP else CH_Q; b = CH_Q if FLIP else CH_B       # a on T port, b on R port
pa, ba = run_chain(a, 'T'); pb, bb = run_chain(b, 'R')

def panel(pts, boxes, fill, title, pos):
    xs = [p[0] for p in pts] + [q for bx_ in boxes for q in (bx_[0], bx_[2])]
    ys = [p[1] for p in pts] + [q for bx_ in boxes for q in (bx_[1], bx_[3])]
    x0, x1, y0, y1 = min(xs) - 45, max(xs) + 45, min(ys) - 45, max(ys) + 25
    y0 = max(y0, 92)
    if pos == 'T': x0 = max(x0, DM[0] + 55); y0 = min(y0, DM[1] - 45); y1 = min(y1, DM[1] + 112)
    else: y0 = max(y0, DM[1] + 125); x0 = min(x0, DM[0] - 45)
    PAN.append((y0, y1))
    E(bg, 'rect', x=x0, y=y0, width=x1 - x0, height=y1 - y0, rx=22, fill=fill)
    t = E(txt, 'text', x=(x1 - 22) if pos == 'T' else (x0 + 22), y=(y0 + 30) if pos == 'T' else (y1 - 16), text_anchor='end' if pos == 'T' else 'start', font_family=FONT, font_size=17, font_weight='bold', fill='#555'); t.text = title
PT = 'Transmitted path  →  ' + a['name']; PR = 'Reflected path  →  ' + b['name']
panel(pa, ba, '#e6eef6', PT, 'T'); panel(pb, bb, '#f7eddc', PR, 'R')

if FLIP:
    text(DMx - 40, Y1 - 85, ['Longpass dichroic (2″), ports swapped', 'R: 852 nm  ·  T: 1030 nm', 'hypothetical: not the DMSP1000L'])
else:
    text(DMx - 40, Y1 - 85, ['Thorlabs DMSP1000L (2″ shortpass)', 'T: 852 nm  ·  R: 1030 nm (mostly)', '1000 nm cutoff'])

title = 'Single-atom tweezer imaging: beam-path plan  (' + ('ports swapped: qCMOS on R, Basler on T' if FLIP else 'qCMOS on T, Basler on R') + ')'
t = E(utxt, 'text', x=40, y=48, font_family=FONT, font_size=28, font_weight='bold'); t.text = title
t = E(utxt, 'text', x=40, y=72, font_family=FONT, font_size=14, fill='#555'); t.text = 'Rev. 2026-11-23 (compact), variant L4 = %g mm / L5 = %g mm.  Schematic (spacings: see box / 3D layout).  All beams at the static-objective height.  2″ optics drawn larger than 1″.' % (F4, F5)

rows = [('Magnification  M = (150 / 10) × f(last) / f(relay)', 'b', '#000'),
 ('L1 = 150 mm focuses; the relay lens collimates', 'n', '#555'), ('', 'n', 0),
 ('qCMOS  (18.8 × 10.6 mm, 4.6 µm px),  relay L2 = 150', 'b', '#000'),
 ('L3 = 40 mm:  M = 4.0×  (preferred)', 'n', '#000'), ('   1 µm waist → 4.0 µm = 0.87 px', 'n', '#555'),
 ('   FoV 1 mm → 4.0 mm: fits', 'n', '#2a7a2a'), ('L3 = 50 mm:  M = 5.0×', 'n', '#000'), ('   1 µm waist → 5.0 µm = 1.09 px', 'n', '#555'),
 ('   FoV 1 mm → 5.0 mm: fits', 'n', '#2a7a2a'), ('', 'n', 0)]
BASLER_ROWS = [('Basler  (7.5 × 5.6 mm, 1.85 µm px),  relay L4 = %g' % F4, 'b', '#000'),
 ('L5 = %g mm:  M = %.1f×  (%.2f µm / px)' % (F5, 15.0 * F5 / F4, 1.85 / (15.0 * F5 / F4)), 'n', '#000')]
_M = 15.0 * F5 / F4
if _M > 5.6:
    BASLER_ROWS += [('   FoV 1 mm → %.1f mm: %.0f%% over the 5.6 mm height' % (_M, (_M / 5.6 - 1) * 100), 'n', '#b06a00'),
                    ('   usable FoV %.2f × %.2f mm' % (7.5 / _M, 5.6 / _M), 'n', '#b06a00'),
                    ('   full 1 mm FoV needs f(L5) ≤ %.0f mm' % (5.6 / 15.0 * F4), 'n', '#555'),
                    ('   (%.1f mm → 5.25×, %.2f µm / px, fits)' % (5.25 / 15.0 * F4, 1.85 / 5.25), 'n', '#555')]
else:
    BASLER_ROWS += [('   FoV 1 mm → %.1f mm: fits 5.6 mm' % _M, 'n', '#2a7a2a')]
rows += BASLER_ROWS
YMIN = min(p[0] for p in PAN); YMAX = max(p[1] for p in PAN); CPIV = YMIN + YMAX + (70 if MIR else 0)   # mirror: y -> CPIV - y
bh = 25 * len(rows) + 22; bx, by = W - 470, H - bh - 36
if MIR: by = CPIV - (H0 - 36)
E(ubg, 'rect', x=bx, y=by, width=450, height=bh, rx=14, fill='#fff', stroke='#999', stroke_width=1.2)
yy = by + 34
for s_, w, c in rows:
    if s_:
        t = E(utxt, 'text', x=bx + 18, y=yy, font_family=FONT, font_size=14.5, fill=c, font_weight='bold' if w == 'b' else 'normal', xml_space='preserve'); t.text = s_
    yy += 25
import check_layout
kl = check_layout.summary_lines(FLIP)
kh = 25 * (len(kl) + 1) - 5; kx, ky = 40, H - kh - 40
if MIR: ky = CPIV - (H0 - 40)
E(ubg, 'rect', x=kx, y=ky, width=405, height=kh, rx=14, fill='#fff', stroke='#999', stroke_width=1.2)
t = E(utxt, 'text', x=kx + 16, y=ky + 26, font_family=FONT, font_size=14.5, font_weight='bold'); t.text = 'Key spacings (beam path, mm; from the 3D layout)'
for i, ln in enumerate(kl):
    t = E(utxt, 'text', x=kx + 16, y=ky + 52 + i * 22, font_family=FONT, font_size=12.5, fill='#1a6f1a' if ln.startswith('full') else '#222', xml_space='preserve'); t.text = ln
t = E(utxt, 'text', x=40, y=H - 18, font_family=FONT, font_size=11, fill='#777')
t.text = 'Component glyphs: ComponentLibrary by Alexander Franzen, CC BY-NC 3.0 (gwoptics.org/ComponentLibrary).'
if MIR:   # mirror the drawing layers across the objective axis (vertical flip); glyphs flip with the layout, text blocks are re-seated
    for g_ in (bg, beams, comps):
        if g_ is not bg: g_.set('transform', f'translate(0,{CPIV}) scale(1,-1)')
    # page background stays put; only the panels in bg flip
    for r_ in list(bg):
        if r_.get('fill') != 'white': r_.set('transform', f'translate(0,{CPIV}) scale(1,-1)')
    for t_ in txt:
        if t_.tag != '{%s}text' % SVG: continue
        size = float(t_.get('font-size')); n_ = max(1, len(t_.findall('{%s}tspan' % SVG))); y_last = float(t_.get('y')) + (n_ - 1) * size * 1.25
        t_.set('y', f'{CPIV - y_last + 0.75 * size:.1f}')
ET.ElementTree(doc).write(sys.argv[4], xml_declaration=True, encoding='utf-8')
