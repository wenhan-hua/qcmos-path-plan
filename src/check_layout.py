"""Spacing + collision check of the to-scale layout (plan view).  usage: python3 -I check_layout.py"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout, optics_trace as O

def rect(p):
    """(cx, cz, ax, az, half_len_along_axis_a, half_len_along_axis_b): oriented plan-view footprint of an element."""
    k = p['kind']; dx, dz = p['dx'], p['dz']; sz = p.get('size') or 1
    if k in ('mirror', 'dm'):
        nx, nz = p['dout'][0] - p['din'][0], p['dout'][1] - p['din'][1]; m = math.hypot(nx, nz)
        n = (nx / m, nz / m); t = (-n[1], n[0])           # face normal from the reflection geometry
        w, back = (78, 47) if sz == 2 else (43, 33)      # ring width, mount depth behind the face
        c = (p['x'] - n[0] * (back / 2 - 2), p['z'] - n[1] * (back / 2 - 2))
        return (c[0], c[1], n, t, back / 2, w / 2)
    t = (-dz, dx); n = (dx, dz)
    if k == 'lens':   a_, b_, off = (17, 66, 0) if sz == 2 else (12, 38, 0)
    elif k == 'filter': a_, b_, off = 12, 38, 0
    elif k == 'objective': a_, b_, off = 62, 34, 31
    elif k == 'camera':
        a_, b_, off = (187, 104, 66) if p['model'] == 'qcmos' else (62, 29, 4)
    else: return None
    if k in ('lens', 'filter'): off = 0
    return (p['x'] + n[0] * off, p['z'] + n[1] * off, n, t, a_ / 2, b_ / 2)

def corners(r):
    cx, cz, n, t, ha, hb = r
    return [(cx + n[0] * sa * ha + t[0] * sb * hb, cz + n[1] * sa * ha + t[1] * sb * hb) for sa, sb in ((1, 1), (1, -1), (-1, -1), (-1, 1))]

def overlap(r1, r2, margin=0.0):
    for r in (r1, r2):
        for ax in (r[2], r[3]):
            pr = lambda R: [c[0] * ax[0] + c[1] * ax[1] for c in corners(R)]
            a, b = pr(r1), pr(r2)
            if max(a) + margin < min(b) or max(b) + margin < min(a): return False
    return True

def inside(r, x, z):
    cx, cz, n, t, ha, hb = r
    return abs((x - cx) * n[0] + (z - cz) * n[1]) <= ha and abs((x - cx) * t[0] + (z - cz) * t[1]) <= hb

def check(swapped, verbose=True):
    L = layout.build(swapped); P = [p for p in L['parts'] if rect(p)]
    R = {i: rect(p) for i, p in enumerate(P)}
    bad = []
    for i in R:
        for j in R:
            if j <= i: continue
            if overlap(R[i], R[j], margin=-3.0): bad.append(f"mounts overlap (<3 mm clearance): {P[i]['label']}  x  {P[j]['label']}")
    for b in L['beams']:
        pts = b['pts']
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            d = math.hypot(x1 - x0, z1 - z0); N = int(d / 2)
            for i, p in enumerate(P):
                if p['kind'] == 'fov': continue
                # skip elements sitting on this segment (its own optics)
                ux, uz = (x1 - x0) / d, (z1 - z0) / d; tt = (p['x'] - x0) * ux + (p['z'] - z0) * uz
                if -1 <= tt <= d + 1 and abs(-(p['x'] - x0) * uz + (p['z'] - z0) * ux) < 1.0: continue
                if any(inside(R[i], x0 + (x1 - x0) * k / N, z0 + (z1 - z0) * k / N) for k in range(N + 1)):
                    bad.append(f"beam passes through the mount of {p['label']}")
    return bad

def spacings(swapped):
    res, a, L = O.full(swapped, O.DEFAULT_NA)
    def s_of(rows, nm): return [r['s'] for r in rows if r['name'] == nm][0]
    out = {}
    c = res['common']; s_pupil = [r['s'] for r in c if r['kind'] == 'pupil'][0]
    out['back aperture -> L1 (beam path)'] = s_of(c, 'L1') - s_pupil
    for br in 'TR':
        rows = res[br]; lenses = [r for r in rows if r['kind'] == 'lens']; sens = rows[-1]
        relay, last = lenses[0], lenses[-1]
        out[f"{br}: L1 -> {relay['name']} (relay f={relay['f']:g})"] = relay['s'] - s_of(c, 'L1')
        out[f"{br}: {relay['name']} -> {last['name']} (last lens)"] = last['s'] - relay['s']
        out[f"{br}: {last['name']} -> sensor (f={last['f']:g})"] = sens['s'] - last['s']
        out[f"{br}: sensor focus  alpha / magnification"] = (round(sens['alpha'], 3), round(abs(sens['beta']), 2))
    return out, res

def summary_lines(swapped):
    """Text lines for the key-spacing box in the 2D schematic (computed from the layout, never typed by hand)."""
    sp, res = spacings(swapped)
    L = []
    pupil_l1 = sp['back aperture -> L1 (beam path)']
    L.append(f"obj back aperture → L1:  {pupil_l1:.0f}  (must be ≥ 150)")
    for br in 'TR':
        rows = res[br]; lenses = [r for r in rows if r['kind'] == 'lens']; relay, last = lenses[0], lenses[-1]
        cam = 'qCMOS' if rows[-1].get('model') == 'qcmos' else 'Basler'
        l1 = [r['s'] for r in res['common'] if r['name'] == 'L1'][0]
        L.append(f"{cam}:  L1 → relay {relay['f']:g} mm: {relay['s'] - l1:.0f}  (= 150 + {relay['f']:g})")
        L.append(f"          relay → last lens f={last['f']:g}: {last['s'] - relay['s']:.0f}   ·   last lens → sensor: {rows[-1]['s'] - last['s']:.0f}")
    lim = min((r for k in ('common', 'T', 'R') for r in res[k] if 'h_ok' in r), key=lambda r: r['h_ok'])
    if lim['h_ok'] >= O.H_CORNER: L.append(f"full 1×1 mm field passes all optics (NA {O.DEFAULT_NA:g}); tightest: {lim['name']} ±{lim['h_ok']:.2f} mm")
    else: L.append(f"field edge ±0.5 mm passes everywhere (NA {O.DEFAULT_NA:g}); {lim['name']}: corners marginal (±{lim['h_ok']:.2f} vs 0.71)")
    return L

if __name__ == '__main__':
    for sw in (False, True):
        print('\n== ' + ('swapped' if sw else 'default') + ' ==')
        sp, res = spacings(sw)
        for k, v in sp.items(): print(f"  {k:50s} {v if isinstance(v, tuple) else round(v, 1)}")
        lim = {c: min((r for r in res['common'] + res[c] if 'h_ok' in r), key=lambda r: r['h_ok']) for c in 'TR'}
        print('  limiting element for the 1x1 mm field:', {c: (r['name'], round(r['h_ok'], 2)) for c, r in lim.items()}, '(need >= 0.50 edge / 0.71 corner)')
        bad = check(sw)
        print('  collisions:', 'none' if not bad else '')
        for b in bad: print('   -', b)
