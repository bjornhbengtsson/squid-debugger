"""Compare connectivity of two SchDocs (named nets + unnamed pin groups). Usage: compare_nets.py a b"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from schnet import extract
def sig(f):
    c, n = extract(f, 'x'); named = {}; anon = set()
    for v in n.values():
        pins = frozenset(v['pins'])
        if not pins: continue
        if v['names']: named.setdefault('/'.join(sorted(v['names'])), set()).update(pins)
        else: anon.add(pins)
    return {k: frozenset(v) for k, v in named.items()}, anon, len(c)
a, b = sig(sys.argv[1]), sig(sys.argv[2])
bad = 0
for k in set(a[0]) | set(b[0]):
    if a[0].get(k) != b[0].get(k): print('DIFF', k, a[0].get(k), b[0].get(k)); bad += 1
for s in a[1] ^ b[1]: print('ANON DIFF', sorted(s)); bad += 1
print(f'parts {a[2]}/{b[2]} named nets {len(a[0])} unnamed {len(a[1])} differences {bad}')
