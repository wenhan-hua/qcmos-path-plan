"""Build the qCMOS / Basler imaging beam-path diagram from ComponentLibrary parts.
usage: python3 -I make_diagram.py <script_dir> <ComponentLibrary.svg> <inkscape> <out.svg>"""
import sys, math
sys.path.insert(0, sys.argv[1])
from cl_lib import *

L = Lib(sys.argv[2], sys.argv[3])
W, H = 1640, 1000
doc = L.new_doc(W, H)
defs = L.docdefs
def E(parent, tag, **kw):
    return ET.SubElement(parent, '{%s}%s' % (SVG, tag), {k.replace('_', '-'): str(v) for k, v in kw.items()})

# ---- own gradients (objective barrel, sensor-plane) -------------------------------------------
g = E(defs, 'linearGradient', id='barrel', x1=0, y1=0, x2=0, y2=1)
for o, c in [(0, '#2b2b2b'), (0.5, '#a9a9a9'), (1, '#2b2b2b')]:
    E(g, 'stop', offset=o, style=f'stop-color:{c}')
g = E(defs, 'linearGradient', id='fov', x1=0, y1=0, x2=1, y2=0)
for o, c in [(0, '#89A4B6'), (0.5, '#FFFFFF'), (1, '#89A4B6')]:
    E(g, 'stop', offset=o, style=f'stop-color:{c}')

FONT = 'Helvetica, Arial, sans-serif'
RED = '#ee0000'
S2, S1 = 2.3, 1.45            # 2" and 1" optics scale
bg = E(doc, 'g', id='backgrounds'); beams = E(doc, 'g', id='beams'); comps = E(doc, 'g', id='components')
txt = E(doc, 'g', id='labels')
E(bg, 'rect', width=W, height=H, fill='white')

def text(x, y, lines, anchor='middle', size=15, bold_first=True, color='#000'):
    t = E(txt, 'text', x=x, y=y, font_family=FONT, font_size=size, text_anchor=anchor, fill=color)
    for i, ln in enumerate(lines):
        s = E(t, 'tspan', x=x, dy=0 if i == 0 else size * 1.25)
        if i == 0 and bold_first:
            s.set('font-weight', 'bold')
        elif i > 0:
            s.set('fill', '#444'); s.set('font-size', str(size * 0.85))
        s.text = ln
    return t

# ---- components -------------------------------------------------------------------------------
def unit(a, b):
    d = math.hypot(b[0] - a[0], b[1] - a[1]); return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
def mirror(x, y, din, dout, s=S2):
    n = (dout[0] - din[0], dout[1] - din[1]); m = math.hypot(*n); n = (n[0] / m, n[1] / m)
    ang = math.degrees(math.atan2(n[1], n[0])) - 135
    E(comps, 'rect', x=-5.5 * s * .96, y=-14.5 * s * .96, width=11 * s * .96, height=29 * s * .96, fill='white',
      transform=f'translate({x},{y}) rotate({ang - 45})')       # opaque substrate: beam ends on the mirror
    L.place(comps, 'g7458', x, y, angle=ang, scale=s)
R_, D_, U_, Lf = (1, 0), (0, 1), (0, -1), (-1, 0)
def lens(x, y, vertical=False, s=S2):
    L.place(comps, 'g3746', x, y, angle=90 if vertical else 0, scale=s)
def strip_black(g):
    for par in list(g.iter()):
        for ch in list(par):
            if ch.tag in ('{%s}path' % SVG, '{%s}rect' % SVG) and 'fill' not in ch.get('style', '') and not ch.get('fill'):
                par.remove(ch)
import re
def plate(cid, x, y, angle, s, strip=True):
    gg = L.place(comps, cid, x, y, angle=angle, scale=s)
    if strip: strip_black(gg)
def camera(x, y, d):
    L.place(comps, 'g90078', x, y, angle={R_: 0, D_: 90}[d], scale=2.0)

def beam(pts, arrows=True):
    d = 'M ' + ' L '.join(f'{x},{y}' for x, y in pts)
    E(beams, 'path', d=d, fill='none', stroke=RED, stroke_width=2.6, stroke_linejoin='miter')
    if arrows:
        for a, b in zip(pts, pts[1:]):
            ln = math.hypot(b[0] - a[0], b[1] - a[1])
            if ln < 110: continue
            ux, uy = unit(a, b); mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            p = [(mx + ux * 7, my + uy * 7), (mx - ux * 6 - uy * 6, my - uy * 6 + ux * 6), (mx - ux * 6 + uy * 6, my - uy * 6 - ux * 6)]
            E(beams, 'polygon', points=' '.join(f'{px:.1f},{py:.1f}' for px, py in p), fill=RED)

Y0, Y1, Y2 = 175, 365, 530
# region panels (like the grey "Cavity" box in the library)
def panel(x, y, w, h, fill, title, tx):
    E(bg, 'rect', x=x, y=y, width=w, height=h, rx=22, fill=fill)
    t = E(txt, 'text', x=tx, y=y + (h - 16 if title.startswith('Reflected') else 28), font_family=FONT, font_size=17, font_weight='bold', fill='#555', text_anchor='start'); t.text = title
panel(800, 70, 810, 410, '#e6eef6', 'Transmitted path  →  qCMOS', 822)
panel(630, 500, 540, 470, '#f7eddc', 'Reflected path  →  Basler', 652)
PANEL_R_TITLE = True

# ---- FoV + objective (custom drawings, library style) ----------------------------------------
fx = 85
E(comps, 'rect', x=fx - 4, y=Y0 - 30, width=8, height=60, fill='url(#fov)', stroke='black', stroke_width=1.2)
ox = 125  # objective: tip at ox, body to ox+95
obj = [(ox, Y0 - 9), (ox + 34, Y0 - 24), (ox + 34, Y0 - 24), (ox + 100, Y0 - 24), (ox + 100, Y0 + 24), (ox + 34, Y0 + 24), (ox, Y0 + 9)]
E(comps, 'polygon', points=' '.join(f'{a},{b}' for a, b in obj), fill='url(#barrel)', stroke='black', stroke_width=1.2)
E(comps, 'rect', x=ox + 100, y=Y0 - 29, width=10, height=58, fill='#111')
E(comps, 'rect', x=ox + 34, y=Y0 - 27, width=5, height=54, fill='#111')

# ---- beam path --------------------------------------------------------------------------------
M1, M2 = (370, Y0), (370, Y1)
L1x, DMx = 560, 730
M3, M4 = (930, Y1), (930, Y0)
L2x = 1090
M5, M6 = (1240, Y0), (1240, Y1)
F1x, F2x, L3x, CAMx = 1305, 1340, 1400, 1520
Ma, Mb = (DMx, Y2), (870, Y2)
L4y = 625
Mc, Md = (870, 725), (1040, 725)
L5y, CAMy = 810, 905

beam([(fx, Y0), M1, M2, (DMx, Y1)])
beam([(DMx, Y1), M3, M4, M5, M6, (CAMx - 35, Y1)])
beam([(DMx, Y1), Ma, Mb, Mc, Md, (Md[0], CAMy - 40)])

mirror(*M1, R_, D_);  mirror(*M2, D_, R_)
lens(L1x, Y1)
plate('g3568', DMx, Y1, -45, S2)                       # dichroic plate, reflect right->down
mirror(*M3, R_, U_);  mirror(*M4, U_, R_)
lens(L2x, Y0)
mirror(*M5, R_, D_);  mirror(*M6, D_, R_, S1)
plate('g3533', F1x, Y1, 0, S2 * 0.9); plate('g3533', F2x, Y1, 0, S2 * 0.9)
lens(L3x, Y1, s=S1 * 1.0)
camera(CAMx, Y1, R_)
mirror(*Ma, D_, R_);  mirror(*Mb, R_, D_)
lens(Mb[0], L4y, vertical=True)
mirror(*Mc, D_, R_);  mirror(*Md, R_, D_, S1)
lens(Md[0], L5y, vertical=True, s=S1)
camera(Md[0], CAMy, D_)

# ---- labels -----------------------------------------------------------------------------------
text(fx, Y0 - 52, ['FoV', '1 mm × 1 mm'])
text(ox + 50, Y0 + 50, ['Static objective', 'EFL = 10 mm'])
text(M1[0] + 20, Y0 - 50, ['M1', '1″ or 2″'], anchor='start')
text(M2[0] + 20, Y1 + 55, ['M2', '2″'], anchor='start')
text(L1x, Y1 + 60, ['L1  f = 150 mm', '2″ lens'])
text(DMx - 40, 280, ['Shortpass dichroic (2″)', 'T: 852 nm  ·  R: 1030 nm', 'Thorlabs DMSP-series, P/N to confirm'])
text(M3[0] + 20, Y1 + 55, ['M3', '2″'], anchor='start')
text(M4[0] + 20, Y0 - 50, ['M4', '2″'], anchor='start')
text(L2x, Y0 + 60, ['L2  f = 150 mm', '2″ lens'])
text(M5[0] + 20, Y0 - 50, ['M5', '2″'], anchor='start')
text(M6[0] - 22, Y1 + 40, ['M6', '1″'], anchor='end')
text((F1x + F2x) / 2, Y1 - 62, ['852 nm line filters', '≥ 1, last one before L3'])
text(L3x, Y1 + 50, ['L3  f = 40 mm', '(or 50 mm)', '1″ lens'])
text(CAMx, Y1 - 112, ['qCMOS', 'C15550-22UP', '18.8 × 10.6 mm', '4.6 µm pixel'])
text(Ma[0] - 55, Y2 - 22, ['M7', '2″'], anchor='end')
text(Mb[0] + 20, Y2 - 22, ['M8', '2″'], anchor='start')
text(Mb[0] + 38, L4y + 5, ['L4  f = 150 mm', '2″ lens'], anchor='start')
text(Mc[0] - 40, Mc[1] + 6, ['M9', '2″'], anchor='end')
text(Md[0] + 20, Md[1] - 22, ['M10', '1″'], anchor='start')
text(Md[0] - 26, L5y - 4, ['L5  f = 50 mm', '(or 60 mm)', '1″ lens'], anchor='end')
text(Md[0] - 62, CAMy - 8, ['Basler acA4029-29um', '7.5 × 5.6 mm', '1.85 µm pixel'], anchor='end')

# title
t = E(txt, 'text', x=40, y=48, font_family=FONT, font_size=28, font_weight='bold'); t.text = 'Single-atom tweezer imaging: beam-path plan'
t = E(txt, 'text', x=40, y=72, font_family=FONT, font_size=14, fill='#555'); t.text = 'Schematic, not to scale.  All beam heights match the static-objective axis. 2″ optics drawn larger than 1″.'

# spec table
bx, by = 1200, 520
E(bg, 'rect', x=bx, y=by, width=410, height=450, rx=14, fill='#ffffff', stroke='#999', stroke_width=1.2)
rows = [
 ('Magnification  M = f(last lens) / f(obj, 10 mm)', 'b', '#000'),
 ('(objective → L1/L2 is a 1:1 relay)', 'n', '#555'),
 ('', 'n', '#000'),
 ('qCMOS  (18.8 × 10.6 mm, 4.6 µm px)', 'b', '#000'),
 ('L3 = 40 mm:  M = 4.0×', 'n', '#000'),
 ('   1 µm waist → 4.0 µm = 0.87 px', 'n', '#555'),
 ('   FoV 1 mm → 4.0 mm: fits', 'n', '#2a7a2a'),
 ('L3 = 50 mm:  M = 5.0×', 'n', '#000'),
 ('   1 µm waist → 5.0 µm = 1.09 px', 'n', '#555'),
 ('   FoV 1 mm → 5.0 mm: fits', 'n', '#2a7a2a'),
 ('', 'n', '#000'),
 ('Basler  (7.5 × 5.6 mm, 1.85 µm px)', 'b', '#000'),
 ('L5 = 50 mm:  M = 5.0×  (0.37 µm / px)', 'n', '#000'),
 ('   FoV 1 mm → 5.0 mm: fits 5.6 mm', 'n', '#2a7a2a'),
 ('L5 = 60 mm:  M = 6.0×  (0.31 µm / px)', 'n', '#000'),
 ('   FoV 1 mm → 6.0 mm: clips 5.6 mm', 'n', '#b02020'),
 ('   f(L5) ≤ 56 mm keeps the full FoV', 'n', '#555'),
]
yy = by + 34
for s, w, c in rows:
    if s:
        t = E(txt, 'text', x=bx + 18, y=yy, font_family=FONT, font_size=14.5, fill=c, font_weight='bold' if w == 'b' else 'normal', xml_space='preserve'); t.text = s
    yy += 25

t = E(txt, 'text', x=40, y=H - 18, font_family=FONT, font_size=11, fill='#777')
t.text = 'Component glyphs: ComponentLibrary by Alexander Franzen, CC BY-NC 3.0 (gwoptics.org/ComponentLibrary).'
ET.ElementTree(doc).write(sys.argv[4], xml_declaration=True, encoding='utf-8')
