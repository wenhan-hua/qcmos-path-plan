"""Helpers to lift components out of Alexander Franzen's ComponentLibrary.svg (CC BY-NC 3.0)."""
import copy, re, subprocess, math
import xml.etree.ElementTree as ET

SVG = 'http://www.w3.org/2000/svg'
for p, u in [('', SVG), ('svg', SVG), ('inkscape', 'http://www.inkscape.org/namespaces/inkscape'),
             ('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'),
             ('xlink', 'http://www.w3.org/1999/xlink'), ('i', 'http://ns.adobe.com/AdobeIllustrator/10.0/'),
             ('a', 'http://ns.adobe.com/AdobeSVGViewerExtensions/3.0/')]:
    ET.register_namespace(p, u)
INK = 'http://www.inkscape.org/namespaces/inkscape'

class Lib:
    def __init__(self, svg_path, inkscape):
        self.tree = ET.parse(svg_path)
        self.root = self.tree.getroot()
        self.byid = {e.get('id'): e for e in self.root.iter() if e.get('id')}
        out = subprocess.run([inkscape, '--query-all', svg_path], capture_output=True, text=True).stdout
        self.bbox = {}
        for l in out.splitlines():
            p = l.split(',')
            if len(p) == 5:
                x, y, w, h = map(float, p[1:])
                self.bbox[p[0]] = (x, y, w, h)
        self.defs = self.root.find('{%s}defs' % SVG)

    def new_doc(self, w, h):
        r = ET.Element('{%s}svg' % SVG, {'width': str(w), 'height': str(h), 'viewBox': f'0 0 {w} {h}',
                                         'version': '1.1'})
        self.docdefs = copy.deepcopy(self.defs)
        r.append(self.docdefs)
        self.hoisted = {d.get('id') for d in self.docdefs.iter() if d.get('id')}
        return r

    def place(self, parent, cid, x, y, angle=0, scale=1.0, flip=False):
        """Copy component `cid`, put its bbox centre at (x,y), rotate by angle (deg, screen coords)."""
        e = self.byid[cid]
        bx, by, bw, bh = self.bbox[cid]
        cx, cy = bx + bw / 2, by + bh / 2
        c = copy.deepcopy(e)
        # hoist gradients/clips into the doc <defs> (once), strip other ids to avoid duplicates
        GR = {'{%s}%s' % (SVG, t) for t in ('linearGradient', 'radialGradient', 'pattern', 'clipPath', 'mask', 'filter')}
        ddefs = [d for d in parent.iter('{%s}defs' % SVG)][0] if False else self.docdefs
        for par in list(c.iter()):
            for ch in list(par):
                if ch.tag in GR:
                    par.remove(ch)
                    if ch.get('id') not in self.hoisted:
                        self.hoisted.add(ch.get('id')); ddefs.append(ch)
        for d in c.iter():
            if 'id' in d.attrib:
                del d.attrib['id']
        sx = -scale if flip else scale
        g = ET.SubElement(parent, '{%s}g' % SVG, {
            'transform': f'translate({x:.2f},{y:.2f}) rotate({angle:.3f}) scale({sx},{scale}) translate({-cx:.3f},{-cy:.3f})'})
        g.append(c)
        return g
