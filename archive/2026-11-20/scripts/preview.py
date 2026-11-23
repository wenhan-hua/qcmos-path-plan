import sys
sys.path.insert(0, sys.argv[1])
from cl_lib import *
L = Lib(sys.argv[2], sys.argv[3])
doc = L.new_doc(1100, 260)
ET.SubElement(doc, '{%s}rect' % SVG, {'width': '1100', 'height': '260', 'fill': 'white'})
ids = ['g3693','g3746','g3775','g7458','g3815','g3419','g3533','g3568','g90078','g14171','g3850']
for k, i in enumerate(ids):
    L.place(doc, i, 50 + k * 95, 100, scale=2.5)
    t = ET.SubElement(doc, '{%s}text' % SVG, {'x': str(50 + k * 95), 'y': '200', 'font-size': '12', 'text-anchor': 'middle'}); t.text = i
ET.ElementTree(doc).write(sys.argv[4])
