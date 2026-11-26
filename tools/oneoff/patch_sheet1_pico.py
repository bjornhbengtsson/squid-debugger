"""Add stub wires + yellow ports on the Pico's spare pins in DebugBoard.SchDoc (sheet 1).
Usage: python tools/patch_sheet1_pico.py <in.SchDoc> <out.SchDoc>"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from schgen import *
PINS = {'GP14': 'PICO_ST_3V3', 'GP15': 'PICO_ST_5V', 'GP16': 'EN_3V3', 'GP17': 'EN_5V', 'GP18': 'EN_5VRF',
        'GP19': 'EN_12V', 'GP26_A0': 'ADC_3V3', 'GP27_A1': 'ADC_5V', 'GP28_A2': 'ADC_12V'}
fs, recs = load(sys.argv[1])
u1 = next(int(r.get('OwnerIndex')) + 1 for r in recs if r.get('RECORD') == '34' and r.get('Text') == 'U1')
wire_t = Rec(b'|RECORD=27|OwnerPartId=-1|LineWidth=1|Color=8388608|UniqueID=AAAAAAAA|LocationCount=2|X1=0|Y1=0|X2=0|Y2=0')
port_t = Rec(b'|RECORD=18|OwnerPartId=-1|IOType=0|Alignment=1|Width=50|Location.X=0|Location.Y=0|Color=128|FontID=1|AreaColor=8454143|TextColor=128|Name=X|UniqueID=AAAAAAAA|Height=10')
done = []
for r in list(recs):
    if r.get('RECORD') == '2' and r.get('OwnerIndex') == str(u1 - 1) and r.get('Name') in PINS:
        net = PINS[r.get('Name')]
        x, y = getc(r, 'Location.X'), getc(r, 'Location.Y'); L = getc(r, 'PinLength'); rot = int(r.get('PinConglomerate')) & 3
        dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][rot]
        ax, ay = x + dx * L, y + dy * L; bx, by = ax + dx * 20 * FRAC, ay
        w = wire_t.copy(); w.set('UniqueID', uid()); setc(w, 'X1', ax); setc(w, 'Y1', ay); setc(w, 'X2', bx); setc(w, 'Y2', by); recs.append(w)
        width = 5 * len(net) + 30
        p = port_t.copy(); p.set('UniqueID', uid()); p.set('Name', net); p.set('Width', width)
        setc(p, 'Location.X', bx - width * FRAC if rot == 2 else bx); setc(p, 'Location.Y', by); recs.append(p)
        done.append((r.get('Name'), net))
assert len(done) == len(PINS), done
write_cfb(sys.argv[2], {'FileHeader': stream_from(recs), 'Storage': fs['Storage'], 'Additional': fs['Additional']})
print('added', done)
