"""Check the real board (tools/altium/pcb_dump.txt written by DumpV1, plus the saved PcbDoc) against the plan.

  1. every part is at the position, rotation and side in pcb_place.py
  2. no two parts closer than pcb_place.GAP (real outline boxes)
  3. every designator: right size, inside the board, not on a pad or hole, not on another designator, near its part
  4. the layer stack saved in the PcbDoc
Usage: python tools/pcb_check.py     (run DumpV1 in Altium and save the board first)
"""
import os, re, sys, math, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcb_place as pp
from cfb import read_cfb, records
mm = lambda s: float(s) * 0.0254
C, N, PADS = {}, {}, []
for line in open(pp.DUMP_PATH, encoding='latin-1'):
    f = line.rstrip('\r\n').split('|')
    if f[0] == 'C' and len(f) >= 11: C[f[1]] = dict(side='B' if f[3].startswith('Bottom') else 'T', rot=float(f[4]) % 360, o=(mm(f[5]), mm(f[6])), box=tuple(mm(v) for v in f[7:11]))
    elif f[0] == 'N' and len(f) >= 9: N[f[1]] = dict(side='B' if f[2].startswith('Bottom') else 'T', h=mm(f[4]), box=tuple(mm(v) for v in f[5:9]))
    elif f[0] == 'P' and len(f) >= 11: PADS.append((f[1], 'M' if f[3].startswith('Multi') else 'B' if f[3].startswith('Bottom') else 'T', tuple(mm(v) for v in f[7:11])))
C.pop('G***', None); N.pop('G***', None)
bad = 0
# 1. positions
off = [d for d in pp.P if d not in C or abs(C[d]['o'][0] - pp.P[d][0]) > 0.02 or abs(C[d]['o'][1] - pp.P[d][1]) > 0.02
       or C[d]['rot'] != pp.P[d][2] % 360 or C[d]['side'] != pp.P[d][3]]
print(f'parts on board {len(C)} / table {len(pp.P)}; not at table position: {off or "none"}'); bad += len(off) + abs(len(C) - len(pp.P))
# 2. spacing, from the real boxes
def occupies(d, side):
    if C[d]['side'] == side: return [C[d]['box'] if d != 'U1' else pp.box('U1')]
    return [r for o, k, r in PADS if o == d and k == 'M']
close = []
for a, b in itertools.combinations(C, 2):
    for side in 'TB':
        if C[a]['side'] != side and C[b]['side'] != side: continue
        for ra in occupies(a, side):
            for rb in occupies(b, side):
                if pp.ROUND(a) and pp.ROUND(b): hit = False
                elif pp.ROUND(a): hit = pp.hit_round(ra, rb, pp.GAP - 0.01)
                elif pp.ROUND(b): hit = pp.hit_round(rb, ra, pp.GAP - 0.01)
                else: hit = pp.hit(ra, rb, pp.GAP - 0.01)
                if hit and (a, b) not in close: close.append((a, b))
print(f'pairs closer than {pp.GAP} mm: {close or "none"}'); bad += len(close)
# 3. designators
probs = []
for d, n in N.items():
    r = n['box']
    if abs(n['h'] - pp.TXT_H) > 0.01: probs.append((d, f'height {n["h"]:.2f}'))
    if not pp.inside_board(r, 0.3): probs.append((d, 'off board / at edge'))
    for o, k, pr in PADS:
        on = pp.hit_round(pr, r, 0.05) if pp.ROUND(o) else pp.hit(r, pr, 0.05)        # jack and hole pads are round
        if (k == 'M' or k == n['side']) and on: probs.append((d, f'on pad of {o}')); break
    if n['side'] == 'T' and d != 'U1' and pp.hit(r, pp.box('U1')): probs.append((d, 'under the Pico'))
    b = C[d]['box'] if d != 'U1' else pp.box('U1')
    gap = max(r[0] - b[2], b[0] - r[2], r[1] - b[3], b[1] - r[3], 0)
    if gap > 3.0: probs.append((d, f'{gap:.1f} mm from its part'))
for a, b in itertools.combinations(N, 2):
    if N[a]['side'] == N[b]['side'] and pp.hit(N[a]['box'], N[b]['box']): probs.append((a, f'overlaps designator {b}'))
print(f'designators {len(N)}: problems {probs or "none"}'); bad += len(probs)
w = sorted((n['box'][2] - n['box'][0], n['box'][3] - n['box'][1], d) for d, n in N.items())
print('  text box sizes (mm): smallest %.2fx%.2f %s, largest %.2fx%.2f %s' % (w[0] + w[-1]))
# 4. layer stack in the saved file
b = dict(x.split('=', 1) for x in records(read_cfb(pp.PCB_PATH)['Board6/Data'])[0].rstrip(b'\0').decode('latin-1').split('|') if '=' in x)
tot = 0.0
for i in range(3, 10):
    name = b.get(f'V9_STACK_LAYER{i}_NAME'); cu = b.get(f'V9_STACK_LAYER{i}_COPTHICK'); di = b.get(f'V9_STACK_LAYER{i}_DIELHEIGHT')
    t = float((cu or di)[:-3]) * 0.0254; tot += t
    print(f'  {name:14} {"copper" if cu else "dielectric"} {t:.4f} mm' + (f'  er {b.get(f"V9_STACK_LAYER{i}_DIELCONST")}' if di else ''))
print(f'  copper + dielectric total {tot:.3f} mm')
# 5. 3D models: seated on the board (not floating, not sunk) and signed off as the right way up
BODY, ZR = {}, {}
for line in open(pp.DUMP_PATH, encoding='latin-1'):
    f = line.rstrip('\r\n').split('|')
    if f[0] == 'B' and len(f) >= 3: BODY[f[1]] = int(f[2])
    elif f[0] == 'Z' and len(f) >= 5: ZR[(f[1], float(f[2]))] = (float(f[3]), float(f[4]))
m = []
for d in pp.P:
    if BODY.get(d, 1) == 0 and not d.startswith('MH') and d not in pp.NO_MODEL: m.append((d, 'no 3D model'))
    if BODY.get(d, 1) > 1: m.append((d, f'{BODY[d]} 3D bodies'))
for d, (f, rx, rz, dz) in sorted(pp.STEP.items()):
    z = ZR.get((f, float(rx % 360))) or ZR.get((f, float(rx)))
    if z is None: m.append((d, 'model height not in the dump: run DumpV1')); continue
    low = z[0] + dz
    if abs(low) > 0.15: m.append((d, f'lowest point {low:+.2f} mm from the board (model z {z[0]}..{z[1]}, lift {dz})'))
for f in pp.unverified_models(): m.append((f, 'not checked in a tilted 3D view: see VERIFIED in pcb_place.py'))
print(f'3D models: {len(pp.STEP)} seated by script; problems {m or "none"}'); bad += len(m)
print('errors =', bad)
