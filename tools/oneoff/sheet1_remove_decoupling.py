"""Sheet 1: delete C2/C3/C5/C6 + their power ports + 'Supply Decoupling' heading; merge that cell into the buck box.
Usage: python tools/sheet1_remove_decoupling.py <in.SchDoc> <out.SchDoc>"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sheet1_groups import *
fs, recs = load(sys.argv[1]); U = FRAC
first = next(i for i, r in enumerate(recs) if r.get('RECORD') == '1')
def inside(i, x0, y0, x1, y1):
    r = recs[i]
    if r.get('RECORD') == '27':
        pts = [(getc(r, f'X{n}') / U, getc(r, f'Y{n}') / U) for n in range(1, int(r.get('LocationCount')) + 1)]
    else:
        a = anchor(r); pts = [a] if a else []
    return pts and all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)
top = [i for i, r in enumerate(recs) if i >= first and r.get('OwnerIndex') is None and r.get('RECORD') not in ('6', '44', '45', '46', '48')]
# 1) the decoupling cell: 485..948 x 367..579
cell = [i for i in top if inside(i, 486, 368, 947, 578)]
kinds = sorted((recs[i].get('RECORD'), recs[i].get('Text') or '') for i in cell)
print('removing', kinds)
assert all(k in ('1', '17', '4') for k, _ in kinds) and sum(k == '1' for k, _ in kinds) == 4
drop = set()
for i in cell: drop.update(subtree(recs, i) if recs[i].get('RECORD') == '1' else [i])
# 2) old buck/decoupling separator polyline (485,579)->(947,579)->(947,869)->(948,869)
for i, r in enumerate(recs):
    if r.get('RECORD') == '6' and r.get('OwnerIndex') is None and r.get('X1') == '485' and r.get('Y1') == '579': drop.add(i)
# 3) recentre buck content (not its heading) in the taller box 485..948 x 367..870
buck = [i for i in top if inside(i, 486, 580, 947, 869) and not (recs[i].get('RECORD') == '4' and recs[i].get('FontID') == '17')]
x0, y0, x1, y1 = coords(recs, buck)
dy = round((((367 + 810) / 2) - (y0 + y1) / 2) / 10) * 10
for i in buck:
    for j in (subtree(recs, i) if recs[i].get('RECORD') == '1' else [i]):
        r = recs[j]
        for k, v in list(r.kv):
            if v is not None and COORD.match(k) and 'Y' in k.upper(): setc(r, k, getc(r, k) + dy * U)
print('buck moved', len(buck), 'objects by dy', dy)
l = Rec(b'|RECORD=6|OwnerPartId=-1|LineWidth=2|LocationCount=2|X1=948|Y1=600|X2=948|Y2=870|UniqueID=AAAAAAAA'); l.set('UniqueID', uid())
keep = [i for i in range(len(recs)) if i not in drop]; pos = {o: n for n, o in enumerate(keep)}
out = []
for i in keep:
    r = recs[i]; o = r.get('OwnerIndex')
    if o is not None: r.set('OwnerIndex', pos[int(o) + 1] - 1)
    out.append(r)
out.append(l)
write_cfb(sys.argv[2], {'FileHeader': stream_from(out), 'Storage': fs['Storage'], 'Additional': fs['Additional']})
print('dropped records', len(drop))
