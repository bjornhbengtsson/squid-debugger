"""Check the generated sheet 1 against its source (tools/templates/sheet1_source.SchDoc).

Every multi-pin node of the source must exist in the output with exactly the same pins, and keep its name
(nodes listed in gen_sheet1.RENAME get their new name). Named single-pin nets (ports to other sheets) must keep
their name on that pin. Pins that were unconnected must still be unconnected.
Usage: python tools/verify_sheet1.py [generated.SchDoc]   (default hardware/DebugBoard.SchDoc)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schnet import extract
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'templates', 'sheet1_source.SchDoc')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'hardware', 'DebugBoard.SchDoc')
RENAME = {'R2.1': 'PICO_SWCLK', 'R4.1': 'PICO_SWDIO', 'R8.1': 'PICO_MCU_RESET', 'R9.1': 'PICO_SWO',
          'R11.1': 'PICO_UART_TX', 'R12.1': 'PICO_UART_RX'}

def nodes(f):
    """nets as Altium sees them: geometric islands merged by name (Global scope)."""
    comps, nets = extract(f, 'x'); named, res = {}, {}
    for k, n in nets.items():
        pins = frozenset(n['pins'])
        if not pins: continue
        if n['names']: named.setdefault('/'.join(sorted(n['names'])), set()).update(pins)
        else: res[pins] = ''
    for name, pins in named.items(): res[frozenset(pins)] = name
    return res, len(comps)

a, na = nodes(SRC); b, nb = nodes(OUT)
by_pin = {p: (pins, name) for pins, name in b.items() for p in pins}
bad = 0
for pins, name in a.items():
    want = next((RENAME[p] for p in pins if p in RENAME), name)
    if len(pins) == 1 and not name:                     # unconnected stub in the source
        p = next(iter(pins))
        if p in by_pin and (len(by_pin[p][0]) > 1 or by_pin[p][1]): print('NOW CONNECTED', p, by_pin[p]); bad += 1
        continue
    got = b.get(pins)
    if got is None: print('NODE CHANGED', sorted(pins), name, '->', by_pin.get(next(iter(pins)))); bad += 1
    elif want and got != want: print('NAME', sorted(pins), repr(want), '->', repr(got)); bad += 1
src_pins = {p for pins in a for p in pins}
for pins, name in b.items():
    extra = pins - src_pins
    if extra: print('EXTRA PINS', sorted(extra), name); bad += 1
# Altium joins a net label only to net labels and a port only to ports: one name used both ways splits the net
from schgen import load
_, recs = load(OUT)
lab = {r.get('Text') for r in recs if r.get('RECORD') == '25'}
prt = {r.get('Name') for r in recs if r.get('RECORD') == '18'}
for n in sorted(lab & prt): print('LABEL AND PORT', n); bad += 1
print(f'parts {nb}/{na} source nodes {len(a)} output nodes {len(b)} errors={bad}')
