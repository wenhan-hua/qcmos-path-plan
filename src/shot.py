"""Render layout3d.html in headless Chrome to a PNG (page exports its own canvas; Chrome's screenshot of WebGL is unreliable).
usage: python3 -I shot.py <layout3d.html> <hash-args> <out.png> [w h]"""
import subprocess, sys, re, base64, os
html, h, out = sys.argv[1:4]
w, ht = (sys.argv[4], sys.argv[5]) if len(sys.argv) > 5 else ('1800', '1100')
CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
cmd = [CH, '--headless=new', '--disable-gpu', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--hide-scrollbars',
       f'--window-size={w},{ht}', '--virtual-time-budget=20000', '--dump-dom', f'file://{html}#{h}&once=1&ui=0']
try:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
except subprocess.TimeoutExpired:
    print('timeout'); sys.exit(1)
m = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', r.stdout)
if not m: print('no image; dom head:', r.stdout[:300]); sys.exit(1)
open(out, 'wb').write(base64.b64decode(m.group(1))); print('ok', out, os.path.getsize(out))
