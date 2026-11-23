"""To-scale table layout (mm) for the FoV -> objective -> DM -> {qCMOS, Basler} imaging path.
Top view: x to the right, y 'south' (down the page).  Beam height above table is set in the 3D viewer.
Spacings obey the optics: obj collimates, L1 focuses, L1->(L2|L4) = 2*f = 300 mm (1:1 relay), last lens -> sensor = f."""
import json, math

D_L1_DM = 45
# Relay rule: the intermediate image sits f(L1)=150 mm after L1; the relay lens collimates it, so
#   L1 -> relay lens = 150 + f(relay).   T chain (qCMOS) relay L2 = 150 mm -> 300 mm ;  Basler chain relay L4 = 100 mm -> 250 mm.
RELAY_TOTAL = {'Q': 150 + 150, 'B': 150 + 100}
# (A, JOG, B) per (chain, port): DM->first fold mirror, jog length, second fold mirror -> relay lens.
# Chosen so that D + A + JOG + B = RELAY_TOTAL and the 2'' mounts of the two ports clear each other.
PARAMS = {('Q', 'T'): (120, 85, 50), ('B', 'R'): (70, 75, 60), ('B', 'T'): (90, 70, 45), ('Q', 'R'): (70, 130, 55)}
for (_c, _p), (_a, _j, _b) in PARAMS.items(): assert D_L1_DM + _a + _j + _b == RELAY_TOTAL[_c], (_c, _p)

def unit(v):
    m = math.hypot(*v); return (v[0] / m, v[1] / m)

def build(swapped):
    parts, beams = [], []
    def add(kind, p, d, **kw):
        parts.append(dict(kind=kind, x=round(p[0], 2), z=round(p[1], 2), dx=d[0], dz=d[1], **kw))
    # ---- common path --------------------------------------------------------------------------
    FOV = (0, 0); M1 = (230, 0); M2 = (230, 150); DM = (390, 150); L1 = (DM[0] - D_L1_DM, 150)
    add('fov', FOV, (1, 0), label='FoV 1×1 mm')
    add('objective', (8, 0), (1, 0), label='Static objective EFL 10 mm', length=62)
    add('mirror', M1, (1, 0), din=(1, 0), dout=(0, 1), size=2, label='M1 (1″/2″)')
    add('mirror', M2, (1, 0), din=(0, 1), dout=(1, 0), size=2, label='M2 2″')
    add('lens', L1, (1, 0), size=2, f=150, label='L1  f=150 mm')
    add('dm', DM, (1, 0), din=(1, 0), dout=(0, 1), size=2, label=('Longpass DM 2″ (hypothetical)' if swapped else 'DMSP1000L 2″'), kindDM='longpass' if swapped else 'shortpass')
    common = [FOV, M1, M2, DM]

    # chains in local frame (u along port heading from DM, v to the left of heading)
    def Q(A, JOG, B): return [('mirror', A, 0, (1, 0), (0, 1), 2, 'M3 2″'), ('mirror', A, JOG, (0, 1), (1, 0), 2, 'M4 2″'),
         ('lens', A + B, JOG, 2, 150, 'L2  f=150 mm'),
         ('mirror', A + B + 110, JOG, (1, 0), (0, -1), 2, 'M5 2″'), ('mirror', A + B + 110, 0, (0, -1), (1, 0), 1, 'M6 1″'),
         ('filter', A + B + 150, 0, 1, '852 nm line filter'), ('filter', A + B + 185, 0, 1, '852 nm line filter'),
         ('lens', A + B + 240, 0, 1, 40, 'L3  f=40 mm (or 50)'),
         ('camera', A + B + 280, 0, 'qcmos', 'qCMOS C15550-22UP')]
    def Bc(A, JOG, B): return [('mirror', A, 0, (1, 0), (0, 1), 2, 'M7 2″'), ('mirror', A, JOG, (0, 1), (1, 0), 2, 'M8 2″'),
          ('lens', A + B, JOG, 2, 100, 'L4  f=100 mm'),
          ('mirror', A + B + 110, JOG, (1, 0), (0, 1), 2, 'M9 2″'), ('mirror', A + B + 110, JOG + 100, (0, 1), (1, 0), 1, 'M10 1″'),
          ('lens', A + B + 200, JOG + 100, 1, 40, 'L5  f=40 mm'),
          ('camera', A + B + 250, JOG + 100, 'basler', 'Basler acA4029-29um')]
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
