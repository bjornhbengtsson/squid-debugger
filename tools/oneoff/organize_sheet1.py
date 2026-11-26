"""Reorganize DebugBoard.SchDoc (sheet 1): box loose sections, remove the net-suffix note.
Usage: python tools/organize_sheet1.py <in.SchDoc> <out.SchDoc>"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sheet1_groups import *
fs, recs = load(sys.argv[1])
first = next(i for i, r in enumerate(recs) if r.get('RECORD') == '1')
G = classify(recs, first)
U = FRAC

def shift(idxs, dx, dy):
    dx, dy = round(dx / 10) * 10, round(dy / 10) * 10      # keep everything on the 100-mil grid
    for i in idxs:
        for j in (subtree(recs, i) if recs[i].get('RECORD') == '1' else [i]):
            r = recs[j]
            for k, v in list(r.kv):
                if v is not None and COORD.match(k):
                    setc(r, k, getc(r, k) + round((dx if 'X' in k.upper() else dy) * U))
def head_y(idxs):
    return next(getc(recs[i], 'Location.Y') / U for i in idxs if recs[i].get('RECORD') == '4' and recs[i].get('FontID') == '17')
def cx(idxs):
    x0, _, x1, _ = coords(recs, idxs); return (x0 + x1) / 2

# top row: headings at y=1040, centred in their boxes
for g, (bx0, bx1) in (('debug', (948, 1290)), ('banana', (1290, 1480)), ('holes', (1480, 1680))):
    idx = G[g]; x0, y0, x1, y1 = coords(recs, idx)
    hx = next(i for i in idx if recs[i].get('RECORD') == '4' and recs[i].get('FontID') == '17')
    hw = len(recs[hx].get('Text')) * 12.5
    lo = min(x0, getc(recs[hx], 'Location.X') / U); hi = max(x1, getc(recs[hx], 'Location.X') / U + hw)
    shift(idx, (bx0 + bx1) / 2 - (lo + hi) / 2, 1040 - head_y(idx))
# UART: centred in 1180..1680 x 160..600
idx = G['uart']; x0, y0, x1, y1 = coords(recs, idx)
shift(idx, 1430 - (x0 + max(x1, 1385 + 21 * 12.5)) / 2, 560 - head_y(idx))
# header breakout: centred in 682..1180 x 20..367
idx = G['header']; x0, y0, x1, y1 = coords(recs, idx)
shift(idx, 931 - (x0 + x1) / 2, 325 - head_y(idx))
# caps: two rows -> one row of four, under a new heading, box 485..948 x 367..579
idx = G['caps']
upper = [i for i in idx if anchor(recs[i])[1] > 540]; lower = [i for i in idx if anchor(recs[i])[1] <= 540]
ux0, uy0, ux1, uy1 = coords(recs, upper); lx0, ly0, lx1, ly1 = coords(recs, lower)
gap = 60; total = (ux1 - ux0) + gap + (lx1 - lx0); start = 716 - total / 2
shift(upper, start - ux0, 515 - uy1)
shift(lower, start + (ux1 - ux0) + gap - lx0, 515 - ly1)

# remove the net-suffix note and the old header-breakout/note box lines
drop = set(i for i, r in enumerate(recs) if r.get('RECORD') == '28' and 'NET SUFFIX' in (r.get('Text') or ''))
for i, r in enumerate(recs):
    if r.get('RECORD') == '6' and r.get('OwnerIndex') is None and i >= first:
        pts = [(int(r.get(f'X{k}', 0)), int(r.get(f'Y{k}', 0))) for k in range(1, int(r.get('LocationCount')) + 1)]
        if any(x >= 1060 for x, _ in pts) or pts == [(682, 367), (1065, 367)]: drop.add(i)
assert len(drop) == 4, drop
# new heading + frame lines (sheet-1 style: LineWidth=2 polylines, Times 24 headings)
head = Rec(b'|RECORD=4|OwnerPartId=-1|Location.X=0|Location.Y=0|Color=8388608|FontID=17|Text=Supply Decoupling|UniqueID=AAAAAAAA')
head.set('UniqueID', uid()); setc(head, 'Location.X', round((716 - 17 * 12.5 / 2) * U)); setc(head, 'Location.Y', 541 * U)
lines = [((682, 367), (1180, 367)), ((1180, 367), (1180, 160)), ((1180, 160), (1680, 160)),
         ((948, 367), (948, 600)), ((948, 600), (1680, 600)), ((1290, 600), (1290, 1080)), ((1480, 600), (1480, 1080))]
new = [head]
for (x1, y1), (x2, y2) in lines:
    l = Rec(b'|RECORD=6|OwnerPartId=-1|LineWidth=2|LocationCount=2|X1=0|Y1=0|X2=0|Y2=0|UniqueID=AAAAAAAA')
    l.set('UniqueID', uid()); l.set('X1', x1); l.set('Y1', y1); l.set('X2', x2); l.set('Y2', y2); new.append(l)
# rebuild record list: removing records shifts OwnerIndex of later children -> remap
keep = [i for i in range(len(recs)) if i not in drop]
newpos = {old: n for n, old in enumerate(keep)}
out = []
for i in keep:
    r = recs[i]
    o = r.get('OwnerIndex')
    if o is not None: r.set('OwnerIndex', newpos[int(o) + 1] - 1)
    out.append(r)
out += new
write_cfb(sys.argv[2], {'FileHeader': stream_from(out), 'Storage': fs['Storage'], 'Additional': fs['Additional']})
print('moved groups', {k: len(v) for k, v in G.items()}, 'dropped', len(drop), 'added', len(new))
