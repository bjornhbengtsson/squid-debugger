"""Usage: python tools/schnet.py <file.SchDoc>...  Geometric netlist extraction from Altium binary SchDoc (approximate, single sheet + global labels)."""
import sys, collections
sys.path.insert(0, __import__('os').path.dirname(__file__))
from cfb import read_cfb, records

def parse(path):
    recs = []
    for r in records(read_cfb(path)['FileHeader'])[1:]:
        t = r.rstrip(b'\0').decode('latin-1')
        d = {}
        for kv in t.split('|'):
            if '=' in kv:
                k, v = kv.split('=', 1); d[k.upper()] = v
        recs.append(d)
    return recs

def coord(d, k):
    v = int(d.get(k, 0)); f = int(d.get(k + '_FRAC', 0))
    return round(v * 10 + f / 10000)  # mils*... units of 1 mil (10 mil base)

def extract(path, sheet):
    recs = parse(path)
    comps = {}
    for i, d in enumerate(recs):
        if d.get('RECORD') == '1':
            comps[i] = dict(lib=d.get('LIBREFERENCE', '?'), des='?', val='', comment='', part=d.get('CURRENTPARTID', '1'), disp=d.get('DISPLAYMODE', '0'), pins=[])
    for d in recs:
        o = d.get('OWNERINDEX')
        if o is None: continue
        o = int(o)
        if o not in comps: continue
        c = comps[o]
        if d.get('RECORD') == '34': c['des'] = d.get('TEXT', '?')
        if d.get('RECORD') == '41':
            n = d.get('NAME', '').lower()
            if n in ('value', 'comment'): c[n if n == 'comment' else 'val'] = d.get('TEXT', '')
        if d.get('RECORD') == '2':
            if d.get('OWNERPARTID', '1') not in (c['part'], '-1', '0'): continue
            if d.get('OWNERPARTDISPLAYMODE', '0') != c['disp']: continue
            x, y = coord(d, 'LOCATION.X'), coord(d, 'LOCATION.Y')
            L = coord(d, 'PINLENGTH'); rot = int(d.get('PINCONGLOMERATE', 0)) & 3
            dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][rot]
            c['pins'].append((d.get('DESIGNATOR', '?'), d.get('NAME', ''), (x + dx * L, y + dy * L)))
    segs = []; labels = []
    for d in recs:
        r = d.get('RECORD')
        if r == '27':  # wire
            n = int(d.get('LOCATIONCOUNT', 0))
            pts = [(coord(d, 'X%d' % k), coord(d, 'Y%d' % k)) for k in range(1, n + 1)]
            segs += list(zip(pts, pts[1:]))
        elif r in ('25', '17'):  # net label, power port
            labels.append((d.get('TEXT', '?'), (coord(d, 'LOCATION.X'), coord(d, 'LOCATION.Y'))))
        elif r == '18':  # port: both ends
            x, y, w = coord(d, 'LOCATION.X'), coord(d, 'LOCATION.Y'), coord(d, 'WIDTH')
            st = int(d.get('STYLE', 0))
            ends = [(x, y), (x + w, y)] if st < 4 else [(x, y), (x, y + w)]
            for e in ends: labels.append((d.get('NAME', '?'), e))
    # union-find over points
    par = {}
    def f(p):
        par.setdefault(p, p)
        while par[p] != p: par[p] = par[par[p]]; p = par[p]
        return p
    def u(a, b): par[f(a)] = f(b)
    def on(p, s):
        (x1, y1), (x2, y2) = s
        return min(x1, x2) <= p[0] <= max(x1, x2) and min(y1, y2) <= p[1] <= max(y1, y2) and (x2 - x1) * (p[1] - y1) == (y2 - y1) * (p[0] - x1)
    pts = [p for s in segs for p in s] + [p for c in comps.values() for *_, p in c['pins']] + [p for _, p in labels]
    for a, b in segs: u(a, b)
    for p in pts:
        for s in segs:
            if on(p, s): u(p, s[0])
    # also pins touching pins directly
    nets = collections.defaultdict(lambda: dict(names=set(), pins=[]))
    for t, p in labels: nets[f(p)]['names'].add(t)
    for c in comps.values():
        for pd, pn, p in c['pins']:
            nets[f(p)]['pins'].append(f"{c['des']}.{pd}({pn})")
    for c in comps.values():
        c['net'] = {pd: f(p) for pd, pn, p in c['pins']}
    return comps, nets

if __name__ == '__main__':
    for path in sys.argv[1:]:
        comps, nets = extract(path, path)
        print('#####', path)
        print('--- components')
        for c in sorted(comps.values(), key=lambda c: c['des']):
            print(f"{c['des']:6s} {c['lib']:28s} {c['comment'] or c['val']}")
        print('--- nets')
        merged = collections.defaultdict(list)
        for k, n in nets.items():
            name = '/'.join(sorted(n['names'])) or ('?' + str(k))
            merged[name] += n['pins']
        for name in sorted(merged):
            if merged[name] or not name.startswith('?'):
                print(f"{name:28s} {' '.join(sorted(merged[name]))}")
