"""To-scale table layout (mm) for the FoV -> objective -> DM -> {qCMOS, Basler} imaging path.  REV 2026-11-23 "compact".
Top view: x to the right, y 'south' (down the page).  Beam height above table is set in the 3D viewer.
Spacings obey the optics: obj collimates, L1 focuses, L1 -> relay lens = f(L1) + f(relay), last lens -> sensor = f.
Compact front end + short post-relay legs keep the 1x1 mm field unvignetted (see optics_trace.py / check_layout.py).
The objective back aperture (exit pupil) is at x = 70 mm; obj back -> L1 must be >= 150 mm (here 170 mm of beam path)."""
import json, math, os

D_L1_DM = 45
OBJ_BACK = 70                                   # objective body spans x = 8 .. 70 mm (FoV at x = 0)
OBJ_TO_M1, M1_TO_M2, M2_TO_L1 = 55, 60, 55      # beam path after the back aperture: 55 + 60 + 55 = 170 mm  (>= 150 mm required)
# legs after the relay lens (beam path, mm) -- kept short so the field-angle walk-off stays inside the 1'' parts
Q_TAIL = dict(L2_M5=45, JOG2=60, M6_F1=30, F1_F2=20, F2_L3=25, L3_SENSOR=40)      # qCMOS branch  (L2 -> L3 = 180)
# Relay rule: the intermediate image sits f(L1)=150 mm after L1; the relay lens collimates it, so
#   L1 -> relay lens = 150 + f(relay).
# ---- variants: only the Basler branch differs (relay lens L4 and last lens L5) ------------------------------------------
VARIANTS = {
    # current plan: M = 150/10 * 40/100 = 6x ; L4 -> L5 = 155 mm
    'L4-100_L5-40': dict(f_L4=100, f_L5=40, L4_size=2, L5_size=1, M9_size=2, M10_size=1,
                         B_PARAMS={'R': (70, 75, 60), 'T': (80, 75, 50)},
                         B_TAIL=dict(L4_M9=45, JOG2=75, M10_L5=35, L5_SENSOR=40)),
    # trial: M = 150/10 * 100/250 = 6x again; relay L1 -> L4 = 400 mm and a wider collimated beam (Ø18 mm) after L4 -> M9/M10 must be 2'' (1'' M10 clips); L5 can stay 1''
    'L4-250_L5-100': dict(f_L4=250, f_L5=100, L4_size=2, L5_size=1, M9_size=2, M10_size=2,
                          B_PARAMS={'R': (70, 75, 210), 'T': (80, 75, 200)},
                          B_TAIL=dict(L4_M9=60, JOG2=80, M10_L5=60, L5_SENSOR=100)),
}
DEFAULT_VARIANT = 'L4-100_L5-40'
VARIANT = os.environ.get('QVARIANT', DEFAULT_VARIANT)
CUR = VARIANTS[VARIANT]
RELAY_TOTAL = {'Q': 150 + 150, 'B': 150 + CUR['f_L4']}
# (A, JOG, B) per (chain, port): DM->first fold mirror, jog length, second fold mirror -> relay lens.
# Chosen so that D + A + JOG + B = RELAY_TOTAL and the 2'' mounts of the two ports clear each other.
PARAMS = {('Q', 'T'): (120, 85, 50), ('Q', 'R'): (80, 130, 45),
          ('B', 'T'): CUR['B_PARAMS']['T'], ('B', 'R'): CUR['B_PARAMS']['R']}
for (_c, _p), (_a, _j, _b) in PARAMS.items(): assert D_L1_DM + _a + _j + _b == RELAY_TOTAL[_c], (_c, _p, VARIANT)
B_TAIL = CUR['B_TAIL']

def unit(v):
    m = math.hypot(*v); return (v[0] / m, v[1] / m)

def build(swapped):
    parts, beams = [], []
    def add(kind, p, d, **kw):
        parts.append(dict(kind=kind, x=round(p[0], 2), z=round(p[1], 2), dx=d[0], dz=d[1], **kw))
    # ---- common path --------------------------------------------------------------------------
    FOV = (0, 0); M1 = (OBJ_BACK + OBJ_TO_M1, 0); M2 = (M1[0], M1_TO_M2); L1 = (M2[0] + M2_TO_L1, M2[1]); DM = (L1[0] + D_L1_DM, M2[1])
    add('fov', FOV, (1, 0), label='FoV 1×1 mm')
    add('objective', (8, 0), (1, 0), label='Static objective EFL 10 mm', length=62)
    add('mirror', M1, (1, 0), din=(1, 0), dout=(0, 1), size=2, label='M1 (1″/2″)')
    add('mirror', M2, (1, 0), din=(0, 1), dout=(1, 0), size=2, label='M2 2″')
    add('lens', L1, (1, 0), size=2, f=150, label='L1  f=150 mm')
    add('dm', DM, (1, 0), din=(1, 0), dout=(0, 1), size=2, label=('Longpass DM 2″ (hypothetical)' if swapped else 'DMSP1000L 2″'), kindDM='longpass' if swapped else 'shortpass')
    common = [FOV, M1, M2, DM]

    # chains in local frame (u along port heading from DM, v to the left of heading)
    def Q(A, JOG, B):
        t = Q_TAIL; u5 = A + B + t['L2_M5']; v6 = JOG - t['JOG2']; u_f1 = u5 + t['M6_F1']; u_f2 = u_f1 + t['F1_F2']; u_l3 = u_f2 + t['F2_L3']
        return [('mirror', A, 0, (1, 0), (0, 1), 2, 'M3 2″'), ('mirror', A, JOG, (0, 1), (1, 0), 2, 'M4 2″'),
                ('lens', A + B, JOG, 2, 150, 'L2  f=150 mm'),
                ('mirror', u5, JOG, (1, 0), (0, -1), 2, 'M5 2″'), ('mirror', u5, v6, (0, -1), (1, 0), 1, 'M6 1″'),
                ('filter', u_f1, v6, 1, '852 nm line filter'), ('filter', u_f2, v6, 1, '852 nm line filter'),
                ('lens', u_l3, v6, 1, 40, 'L3  f=40 mm (or 50)'),
                ('camera', u_l3 + t['L3_SENSOR'], v6, 'qcmos', 'qCMOS C15550-22UP')]
    def Bc(A, JOG, B):
        t = B_TAIL; c = CUR; u9 = A + B + t['L4_M9']; v10 = JOG + t['JOG2']; u_l5 = u9 + t['M10_L5']
        return [('mirror', A, 0, (1, 0), (0, 1), 2, 'M7 2″'), ('mirror', A, JOG, (0, 1), (1, 0), 2, 'M8 2″'),
                ('lens', A + B, JOG, c['L4_size'], c['f_L4'], 'L4  f=%g mm' % c['f_L4']),
                ('mirror', u9, JOG, (1, 0), (0, 1), c['M9_size'], 'M9 %d″' % c['M9_size']),
                ('mirror', u9, v10, (0, 1), (1, 0), c['M10_size'], 'M10 %d″' % c['M10_size']),
                ('lens', u_l5, v10, c['L5_size'], c['f_L5'], 'L5  f=%g mm' % c['f_L5']),
                ('camera', u_l5 + t['L5_SENSOR'], v10, 'basler', 'Basler acA4029-29um')]
    def chain(spec, heading, tag):
        h = heading; l = (h[1], -h[0])
        G = lambda u, v: (DM[0] + u * h[0] + v * l[0], DM[1] + u * h[1] + v * l[1])
        Dd = lambda d: (d[0] * h[0] + d[1] * l[0], d[0] * h[1] + d[1] * l[1])
        pts = [DM]
        for e in spec:
            k = e[0]; p = G(e[1], e[2])
            if k == 'mirror':
                add('mirror', p, h, din=Dd(e[3]), dout=Dd(e[4]), size=e[5], label=e[6], chain=tag); pts.append(p)
            elif k == 'lens': add('lens', p, h, size=e[3], f=e[4], label=e[5], chain=tag)
            elif k == 'filter': add('filter', p, h, size=e[3], label=e[4], chain=tag)
            elif k == 'camera': add('camera', p, h, model=e[3], label=e[4], chain=tag); pts.append(p)
        return pts
    right, down = (1, 0), (0, 1)
    f_T, f_R = (Bc, Q) if swapped else (Q, Bc)
    cT, cR = ('B', 'Q') if swapped else ('Q', 'B')
    pt = chain(f_T(*PARAMS[(cT, 'T')]), right, 'T'); pr = chain(f_R(*PARAMS[(cR, 'R')]), down, 'R')
    # which wavelength travels on each port: 852 nm -> qCMOS, 1030 nm -> Basler
    wl = lambda f: 852 if f is Q else 1030
    beams.append(dict(pts=common, wl='both'))
    beams.append(dict(pts=pt, wl=wl(f_T))); beams.append(dict(pts=pr, wl=wl(f_R)))
    xs = [p['x'] for p in parts]; zs = [p['z'] for p in parts]
    ext = dict(minx=min(xs), maxx=max(xs) + 160, minz=min(zs), maxz=max(zs) + 160)
    return dict(parts=parts, beams=beams, ext=ext, swapped=swapped)

if __name__ == '__main__':
    import sys
    out = dict(default=build(False), swapped=build(True))
    json.dump(out, open(sys.argv[1], 'w'))
    for k, v in out.items(): print(k, v['ext'])
