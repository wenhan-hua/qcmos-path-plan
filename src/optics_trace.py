"""Paraxial (ABCD) trace of the imaging path through the to-scale layout in layout.py.

Every ray is y(s) = alpha(s)*y0 + beta(s)*h   (y0 = height at the objective pupil, h = object height in mm).
Footprint half-size at an element = |alpha|*a + |beta|*h_field,  a = f_obj*NA (pupil radius).
Model: infinity-corrected objective, EFL 10 mm; its exit pupil / back aperture sits at the rear of the objective body,
PUPIL_X mm from the FoV (70 mm in the 3D model), and emits a collimated bundle of radius a = f*NA per field point whose
chief ray crosses the axis there.  All other lenses are thin; mirrors/filters only fold or pass the rays.  Geometric optics only."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout

F_OBJ = 10.0
PUPIL_X = 70.0                                   # back aperture of the objective, mm from the FoV (matches layout.py's objective)
H_EDGE, H_CORNER = 0.5, 0.5 * math.sqrt(2)      # 1 x 1 mm FoV: half-side, half-diagonal
CA_FRAC = 0.9                                    # Thorlabs: clear aperture >= 90 % of diameter
COS45 = math.sqrt(0.5)

def allowed_radius(p):
    """Largest footprint radius an element passes (mm). 45-degree mirrors/DM lose cos45 in the plane of incidence."""
    ca2 = CA_FRAC * 25.4 * (p.get('size') or 1) / 2
    return ca2 * COS45 if p['kind'] in ('mirror', 'dm') else ca2

def nodes(swapped):
    L = layout.build(swapped); P = L['parts']
    by = {p['label'].split()[0]: p for p in P}
    def nm(p):
        return {'camera': 'Sensor', 'filter': 'Filter'}.get(p['kind']) or p['label'].split()[0]
    common = [dict(kind='fov', name='FoV', x=0, z=0), dict(kind='pupil', name='Obj. back aperture', x=PUPIL_X, z=0)]
    common += [dict(by[k], name=k) for k in ('M1', 'M2', 'L1')]
    common.append(dict(by['DMSP1000L'] if 'DMSP1000L' in by else [p for p in P if p['kind'] == 'dm'][0], name='DM'))
    ch = {c: [dict(p, name=nm(p)) for p in P if p.get('chain') == c] for c in 'TR'}
    return L, common, ch

def walk(seq, st, s, pos, a):
    rows = []
    for n in seq:
        d = math.hypot(n['x'] - pos[0], n['z'] - pos[1]); s += d; pos = (n['x'], n['z'])
        for b in st: b[0] += b[1] * d
        r = dict(n, s=s, alpha=st[0][0], beta=st[1][0])
        r['r_edge'] = abs(st[0][0]) * a + abs(st[1][0]) * H_EDGE
        r['r_corner'] = abs(st[0][0]) * a + abs(st[1][0]) * H_CORNER
        if n['kind'] in ('mirror', 'dm', 'lens', 'filter'):
            r['r_allow'] = allowed_radius(n)
            r['h_ok'] = (r['r_allow'] - abs(st[0][0]) * a) / abs(st[1][0]) if abs(st[1][0]) > 1e-9 else float('inf')
        if n['kind'] in ('lens', 'obj'):
            for b in st: b[1] -= b[0] / n['f']
        r['alpha_u'], r['beta_u'] = st[0][1], st[1][1]      # slopes just after the element
        rows.append(r)
    return rows, st, s, pos

def full(swapped, NA=0.4):
    L, common, ch = nodes(swapped)
    a = F_OBJ * NA
    # state at the exit pupil: marginal basis y=1, u=0 (collimated); field basis y=0 (chief through pupil centre), u=-1/f
    st = [[1.0, 0.0], [0.0, -1.0 / F_OBJ]]
    rows_c, st, s, pos = walk(common[1:], st, PUPIL_X, (PUPIL_X, 0), a)
    res = {'common': [dict(kind='fov', name='FoV', x=0, z=0, s=0, alpha=0, beta=1, r_edge=0, r_corner=0)] + rows_c}
    for c in 'TR':
        rows, _, _, _ = walk(ch[c], [list(b) for b in st], s, pos, a)
        res[c] = rows
    return res, a, L

def summary(res):
    """(limiting element, its max passable field radius) over all checked elements, per branch incl. the common path."""
    out = {}
    for c in 'TR':
        rr = [r for r in res['common'] + res[c] if 'h_ok' in r]
        w = min(rr, key=lambda r: r['h_ok']); out[c] = (w['name'], w['h_ok'])
    return out

if __name__ == '__main__':
    NA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4
    for sw in (False, True):
        res, a, _ = full(sw, NA)
        print(f"\n=== {'swapped' if sw else 'default'}  NA={NA}  pupil radius a={a:.1f} mm ===")
        for k in ('common', 'T', 'R'):
            for n in res[k]:
                ok = n.get('h_ok')
                print(f"{k:6s} {n['name']:9s} s={n['s']:6.0f} alpha={n['alpha']:7.3f} beta={n['beta']:7.2f}  r_edge={n['r_edge']:5.1f} r_corner={n['r_corner']:5.1f}"
                      + (f"  allow={n['r_allow']:5.1f}  h_ok={ok:5.2f}" if ok is not None else ''))
        print('limiting:', summary(res))
