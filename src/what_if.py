"""What-if: re-run the beam-footprint trace for alternative distances on collinear (unfolded) distances.
The APPLIED scenario below is the one now in layout.py (check_layout.py checks the real layout).
Folding mirrors do not change the footprints, only the path lengths matter.   usage: python3 -I what_if.py [NA]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optics_trace as O

NA = float(sys.argv[1]) if len(sys.argv) > 1 else O.DEFAULT_NA
a = O.F_OBJ * NA

def run(title, seq):
    nodes = [dict(name=n, kind=k, size=sz, f=f, x=s, z=0) for n, k, sz, f, s in seq]
    rows, _, _, _ = O.walk(nodes, [[1.0, 0.0], [0.0, -1.0 / O.F_OBJ]], O.PUPIL_X, (O.PUPIL_X, 0), a)
    print('\n' + title)
    worst = ('', 9)
    for r in rows:
        h = r.get('h_ok')
        if h is not None and h < worst[1]: worst = (r['name'], h)
        print(f"  {r['name']:7s} s={r['s']:5.0f}  r_corner={r['r_corner']:5.1f}" + (f"  allowed={r['r_allow']:5.1f}  max field ±{h:5.2f} mm" if h is not None else ''))
    print(f"  limiting: {worst[0]} (max field ±{worst[1]:.2f} mm; need ≥ 0.50 edge / 0.71 corner)")

def chain(pupil_to_L1, m1, m2, tail, f_relay=150):
    L1 = O.PUPIL_X + pupil_to_L1
    seq = [('M1', 'mirror', 2, 0, O.PUPIL_X + m1), ('M2', 'mirror', 2, 0, O.PUPIL_X + m2), ('L1', 'lens', 2, 150, L1), ('DM', 'dm', 2, 0, L1 + 45),
           ('Ma', 'mirror', 2, 0, L1 + 125), ('Mb', 'mirror', 2, 0, L1 + 210), ('Relay', 'lens', 2, f_relay, L1 + 150 + f_relay)]
    s = L1 + 150 + f_relay
    for n, k, sz, f, d in tail: s += d; seq.append((n, k, sz, f, s))
    return seq

# current plan, unfolded distances (obj back aperture -> L1 = 425 mm; relay -> last lens = 325 mm)
run('PREVIOUS layout (qCMOS branch): back aperture→L1 = 425 mm, L2→L3 = 325 mm, M6 and filters 1"',
    chain(425, 160, 310, [('M5', 'mirror', 2, 0, 110), ('M6', 'mirror', 1, 0, 85), ('F1', 'filter', 1, 0, 40), ('F2', 'filter', 1, 0, 35), ('L3', 'lens', 1, 40, 55), ('Sensor', 'sensor', 1, 0, 40)]))
# compact: back aperture -> L1 = 200 mm, last lens 170 mm after L2
run('APPLIED (qCMOS branch): back aperture→L1 = 170 mm (M1 +55, M2 +115), L2→L3 = 180 mm',
    chain(170, 55, 115, [('M5', 'mirror', 2, 0, 45), ('M6', 'mirror', 1, 0, 60), ('F1', 'filter', 1, 0, 30), ('F2', 'filter', 1, 0, 20), ('L3', 'lens', 1, 40, 25), ('Sensor', 'sensor', 1, 0, 40)]))
run('APPLIED (Basler branch, relay L4 = 100 mm): back aperture→L1 = 170 mm, L4→L5 = 155 mm',
    chain(170, 55, 115, [('M9', 'mirror', 2, 0, 45), ('M10', 'mirror', 1, 0, 75), ('L5', 'lens', 1, 40, 35), ('Sensor', 'sensor', 1, 0, 40)], f_relay=100))
