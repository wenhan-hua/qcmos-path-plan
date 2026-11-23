import json, sys, subprocess, os
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import layout
data = dict(default=layout.build(False), swapped=layout.build(True))
t = open(os.path.join(here, 'template.html')).read()
three = open(os.path.join(here, 'vendor/three.min.js')).read()
orbit = open(os.path.join(here, 'vendor/OrbitControls.js')).read()
assert '</script' not in three.lower() and '</script' not in orbit.lower()
c = layout.CUR
rev = (f"<b>Rev. 2026-11-23, variant L4 = {c['f_L4']} mm / L5 = {c['f_L5']} mm.</b> Back aperture → L1 = 170 mm of beam path (≥ 150). "
       f"T port: L2 = 150, L3 = 40 mm (M = 4×). R port: L4 = {c['f_L4']} mm (2″), L5 = {c['f_L5']} mm (M = {15 * c['f_L5'] / c['f_L4']:.1f}×). "
       "Beam-size check at NA 0.55: full 1×1 mm field clears every optic.")
t = t.replace('/*REVTEXT*/', rev)
t = t.replace('/*THREE*/', three).replace('/*ORBIT*/', orbit).replace('/*LAYOUTS*/', json.dumps(data))
open(sys.argv[1], 'w').write(t); print('wrote', sys.argv[1], len(t))
