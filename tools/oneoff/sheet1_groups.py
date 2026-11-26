"""Shared: classify sheet-1 top-level objects into layout groups by anchor position."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from schgen import *
# current regions (10-mil units): name -> (x0, y0, x1, y1)
REGIONS = {
    'debug':  (940, 615, 1288, 1085),
    'banana': (1288, 690, 1475, 1085),
    'holes':  (1475, 760, 1690, 1085),
    'caps':   (1100, 420, 1260, 660),
    'uart':   (1340, 280, 1690, 530),
    'header': (686, 21, 1064, 209),
}
def anchor(r):
    for a, b in (('Location.X', 'Location.Y'), ('X1', 'Y1')):
        if r.get(a) is not None or r.get(b) is not None:
            if r.get(a) is None and r.get(b) is None: continue
            return getc(r, a) / FRAC, getc(r, b) / FRAC
    return None
def classify(recs, first):
    groups = {k: [] for k in REGIONS}
    for i, r in enumerate(recs):
        if i < first or r.get('OwnerIndex') is not None or r.get('RECORD') in ('6',): continue
        if r.get('RECORD') == '27':
            pts = [(getc(r, f'X{n}') / FRAC, getc(r, f'Y{n}') / FRAC) for n in range(1, int(r.get('LocationCount')) + 1)]
        else:
            a = anchor(r)
            if a is None: continue
            pts = [a]
        for k, (x0, y0, x1, y1) in REGIONS.items():
            if any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts): groups[k].append(i); break
    return groups
def coords(recs, idxs):
    xs, ys = [], []
    for i in idxs:
        for j in subtree(recs, i) if recs[i].get('RECORD') == '1' else [i]:
            r = recs[j]
            for k, v in r.kv:
                if v is not None and COORD.match(k):
                    (xs if 'X' in k.upper() else ys).append(getc(r, k) / FRAC)
            if r.get('RECORD') == '18':   # port extends by Width
                xs.append(getc(r, 'Location.X') / FRAC + int(r.get('Width', 0)))
    return min(xs), min(ys), max(xs), max(ys)
