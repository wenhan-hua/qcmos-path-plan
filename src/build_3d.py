import json, sys, subprocess, os
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import layout
data = dict(default=layout.build(False), swapped=layout.build(True))
t = open(os.path.join(here, 'template.html')).read()
three = open(os.path.join(here, 'vendor/three.min.js')).read()
orbit = open(os.path.join(here, 'vendor/OrbitControls.js')).read()
assert '</script' not in three.lower() and '</script' not in orbit.lower()
t = t.replace('/*THREE*/', three).replace('/*ORBIT*/', orbit).replace('/*LAYOUTS*/', json.dumps(data))
open(sys.argv[1], 'w').write(t); print('wrote', sys.argv[1], len(t))
