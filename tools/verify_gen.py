"""Check generated power sheets: every pin of every part on exactly its spec net (gen_sheet2.blocks)."""
import sys, io, contextlib, os
sys.path.insert(0, os.path.dirname(__file__))
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hardware')
argv = sys.argv; sys.argv = ['x', os.devnull, os.devnull]
with contextlib.redirect_stdout(io.StringIO()):
    import gen_sheet2 as G
sys.argv = argv
from schnet import extract
files = sys.argv[1:] or [os.path.join(D, 'DebugBoardMuxes.SchDoc'), os.path.join(D, 'DebugBoardPowerControl.SchDoc')]
expect = {des: (cm, pm) for _, parts in G.blocks for _, des, cm, pm in parts}
seen, bad = [], 0
for f in files:
    comps, nets = extract(f, 'x'); nm = lambda k: '/'.join(sorted(nets[k]['names']))
    for c in comps.values():
        d = c['des']; seen.append(d)
        if d not in expect: print('UNEXPECTED', d); bad += 1; continue
        for pin, k in c['net'].items():
            if nm(k) != expect[d][1].get(pin, ''): print(f'{d}.{pin}: got {nm(k)!r} want {expect[d][1].get(pin,"")!r}'); bad += 1
    for k, n in nets.items():
        if len(n['names']) > 1: print('MULTI-NAME', nm(k)); bad += 1
print(f'parts {len(seen)}/{len(expect)} dup={len(seen)-len(set(seen))} missing={set(expect)-set(seen)} errors={bad}')
