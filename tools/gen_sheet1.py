"""Generate sheet 1 (DebugBoard.SchDoc) in the wired style used by sheets 2-5.

Source of truth for parts, values and connectivity: tools/templates/sheet1_source.SchDoc (sheet 1 as captured by
hand before this redraw). Every placed part is reused as its own template, so symbols, footprints, parameters and
designators are unchanged. Only the drawing changes (wires instead of per-pin labels) plus:
  - the Pico-side nodes of the six series resistors get names (PICO_SWCLK ...), because the resistors now sit
    next to the connector they protect instead of at the Pico pins;
  - unused pins get No-ERC markers.

Usage: python tools/gen_sheet1.py hardware/DebugBoard.SchDoc     (then python tools/verify_sheet1.py)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schgen import *
from schnet import extract
from wired import Block, CH

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'templates', 'sheet1_source.SchDoc')
fs, S = load(SRC)
U = FRAC

# ------------------------------------------------------------------ parts and nets from the source sheet
GRAPHIC = ('6', '7', '8', '11', '12', '13', '14')
class Part(Template):
    def gbbox(self):
        """body graphics + pins + designator/comment only (hidden parameters can sit inches away)."""
        xs, ys = [], []
        for r in self.recs:
            t = r.get('RECORD')
            if t in GRAPHIC:
                for k, v in r.kv:
                    if v is not None and COORD.match(k):
                        (xs if 'X' in k.upper() else ys).append(getc(r, k) - (self.x0 if 'X' in k.upper() else self.y0))
        for x, y, _ in self.pins().values(): xs.append(x); ys.append(y)
        return min(xs), min(ys), max(xs), max(ys)

T, CM = {}, {}
for i, r in enumerate(S):
    if r.get('RECORD') == '1':
        p = Part(S, i); des = next(q.get('Text') for q in p.recs if q.get('RECORD') == '34')
        T[des] = p
        CM[des] = next((q.get('Text') for q in p.recs if q.get('RECORD') == '41' and q.get('Name') == 'Comment'), '')

comps, nets = extract(SRC, 'x')
RENAME = {   # unnamed source nodes that get a name (keyed by one pin on the node)
    'R2.1': 'PICO_SWCLK', 'R4.1': 'PICO_SWDIO', 'R8.1': 'PICO_MCU_RESET', 'R9.1': 'PICO_SWO',
    'R11.1': 'PICO_UART_TX', 'R12.1': 'PICO_UART_RX',
}
PM = {}
for c in comps.values():
    PM[c['des']] = {}
    for pin, k in c['net'].items():
        names = sorted(nets[k]['names']); PM[c['des']][pin] = names[0] if names else None
for key, name in RENAME.items():
    d, p = key.split('.'); k = next(c for c in comps.values() if c['des'] == d)['net'][p]
    for c in comps.values():
        for pin, kk in c['net'].items():
            if kk == k: PM[c['des']][pin] = name
IOTYPE = {r.get('Name'): r.get('IOType', '0') for r in S if r.get('RECORD') == '18'}

def net(des, pin): return PM[des].get(pin)
def pdir(des, pin): return T[des].pins()[pin][2]
def P(B, des, pin, at, rot=0, label=None):
    return B.part(T[des], des, CM[des], {p: (net(des, p) or '?') for p in T[des].pins()}, pin, at, rot, label)
def hang(B, des, top, at, gnd=True, label='right'):
    """2-pin part hanging down from `at`: pin `top` up, the other pin down (GND symbol on it if gnd)."""
    pins = P(B, des, top, at, (1 - pdir(des, top)) % 4, label)
    other = next(p for p in pins if p != top)
    if gnd: B.gnd(pins[other])
    return pins
def inline(B, des, left, at, label='split'):
    """2-pin part lying horizontally, pin `left` on the left at `at`."""
    return P(B, des, left, at, (2 - pdir(des, left)) % 4, label)
def side(B, des, pin, at, length=20):
    """stub from a side pin to a GND symbol, power port, port or No-ERC marker, by the pin's net."""
    n = net(des, pin); d = pdir(des, pin); x, y = at
    if n is None: B.noerc(at); return
    dx = {0: 1, 2: -1}[d]
    if n == 'GND':
        e = (x + dx * 10, y); B.wire(at, e); B.gnd(e, d); return
    e = (x + dx * length, y); B.wire(at, e)
    if n.startswith('+'): B.pwr(n, e, d)
    else: B.port(n, e, d == 2)

# ------------------------------------------------------------------ blocks (10-mil units, part origin at 0,0)
def pico():
    B = Block(None); pins = P(B, 'U1', 'VBUS', (60, 80))
    for p, at in pins.items(): side(B, 'U1', p, at)
    return B

def vbus_limit():
    B = Block(None); P(B, 'U4', '7', (0, 0))
    B.wire((0, 0), (-170, 0), (-170, 20)); B.pwr('+VBUS', (-170, 20), 1)
    hang(B, 'C23', '1', (-150, 0))
    B.wire((0, -20), (-30, -20), (-30, 0))                                 # EN tied to IN: always on
    P(B, 'R3', '2', (-110, 0), (1 - pdir('R3', '2')) % 4, 'right')          # FLG LED: +VBUS -> R3 -> D1 -> FLG
    P(B, 'D1', 'A', (-110, -40), 0, 'below'); B.wire((-70, -40), (0, -40))
    B.wire((0, -60), (-50, -60)); hang(B, 'R5', '1', (-50, -60))           # ILIM resistor
    B.wire((130, -10), (150, -10), (150, 0))
    B.wire((130, 0), (250, 0), (250, 20)); B.pwr('+VBUS_PROT', (250, 20), 1)
    hang(B, 'C4', '2', (200, 0))
    B.noerc((130, -40))
    B.wire((130, -60), (150, -60)); B.gnd((150, -60))
    return B

def buck():
    B = Block(None); P(B, 'U13', '3', (0, 0))
    B.wire((0, 0), (-140, 0), (-140, 20)); B.pwr('+VBUS_PROT', (-140, 20), 1)
    hang(B, 'C22', '1', (-60, 0)); hang(B, 'C18', '1', (-110, 0))
    B.wire((0, -50), (-20, -50), (-20, 0))                                 # EN tied to VIN
    B.wire((110, 0), (150, 0)); hang(B, 'C21', '1', (150, 0), gnd=False)   # bootstrap cap BST -> SW
    B.wire((150, -20), (150, -30))
    B.wire((110, -30), (200, -30)); inline(B, 'L1', '1', (200, -30), 'above')
    B.wire((110, -50), (280, -50), (280, -30))                             # FB senses the output
    B.wire((260, -30), (400, -30), (400, -10)); B.pwr('+3V3_USB', (400, -10), 1)
    hang(B, 'C19', '1', (320, -30)); hang(B, 'C20', '1', (370, -30))
    B.wire((110, -70), (130, -70)); B.gnd((130, -70))
    return B

def debug_port():
    B = Block(None); pins = P(B, 'J1', '1', (0, 0))
    for p in ('1', '2', '3', '4', '7', '8'): side(B, 'J1', p, pins[p], 30)
    for a, b in (('5', '6'), ('13', '14')):
        (x, ya), (_, yb) = pins[a], pins[b]
        B.wire((x, ya), (x + 20, ya), (x + 20, yb)); B.wire((x, yb), (x + 30, yb)); B.gnd((x + 30, yb), 0)
    # SWD / reset: series resistors at the connector (100 R out, 1 k on SWO), staggered so labels never touch
    for k, (p, r) in enumerate((('9', 'R9'), ('10', 'R2'), ('11', 'R4'), ('12', 'R8'))):
        x, y = pins[p]; xr = 70 if k % 2 == 0 else 140
        B.wire((x, y), (xr, y)); inline(B, r, '2', (xr, y)); B.wire((xr + 40, y), (220, y))
        B.port(net(r, '1'), (220, y), False); B.label(net('J1', p), (x + 5, y))
    return B

LABELLED = {'SWO', 'SWCLK', 'SWDIO', 'MCU_RESET'}      # named by net labels on the J1 wires

def headers():
    B = Block(None); pins = P(B, 'P3', '2', (0, 0))
    for k, p in enumerate(('2', '1', '3', '4')):                           # rails fan out to power ports on top
        x, y = pins[p]; xk = x - 40 - 70 * k
        B.wire((x, y), (xk, y), (xk, 30)); B.pwr(net('P3', p), (xk, 30), 1)
    (x, y5), (_, y6) = pins['5'], pins['6']
    B.wire((x, y5), (x - 20, y5), (x - 20, y6)); B.wire((x, y6), (x - 20, y6)); B.gnd((x - 20, y6))
    q = P(B, 'P4', '1', (110, -50))
    for p, at in q.items():
        n = net('P4', p)
        if n in LABELLED:                       # J1 side carries a net label: Altium joins label to label, not to a port
            e = (at[0] + 70, at[1]); B.wire(at, e); B.label(n, (at[0] + 10, at[1]))
        else: side(B, 'P4', p, at)
    return B

def uart():
    B = Block(None); pins = P(B, 'P2', '2', (0, 0))
    (x, yrx), (_, ytx) = pins['2'], pins['1']
    # RX: P2.2 -> LED tap (R7, D3) -> R12 -> Pico
    B.wire((x, yrx), (x - 180, yrx)); B.label('UART_RX', (x - 90, yrx))
    hang(B, 'R7', '2', (x - 110, yrx), gnd=False); hang(B, 'D3', 'A', (x - 110, yrx - 40))
    inline(B, 'R12', '1', (x - 220, yrx)); B.wire((x - 220, yrx), (x - 240, yrx)); B.port('PICO_UART_RX', (x - 240, yrx), True)
    # TX drops below the RX tap first so the two LED taps never cross
    yt = yrx - 120
    B.wire((x, ytx), (x - 10, ytx), (x - 10, yt), (x - 180, yt)); B.label('UART_TX', (x - 150, yt))
    hang(B, 'R6', '2', (x - 60, yt), gnd=False); hang(B, 'D2', 'A', (x - 60, yt - 40))
    inline(B, 'R11', '1', (x - 220, yt)); B.wire((x - 220, yt), (x - 240, yt)); B.port('PICO_UART_TX', (x - 240, yt), True)
    return B

def can_xcvr():
    B = Block(None); pins = P(B, 'U2', '3', (0, 0))
    B.wire((0, 0), (-20, 0), (-20, 40), (-100, 40), (-100, 60)); B.pwr('+3V3_RPI', (-100, 60), 1)
    hang(B, 'C1', '2', (-60, 40))
    for p in ('1', '4', '5'): side(B, 'U2', p, pins[p])
    x, y = pins['8']; B.wire((x, y), (x - 70, y)); hang(B, 'R1', '2', (x - 40, y)); B.port('CAN_S', (x - 70, y), True)
    for p in ('7', '6', '2'): side(B, 'U2', p, pins[p])
    return B

def can_ctrl():
    B = Block(None); pins = P(B, 'U6', '17', (-20, -10))
    x, y = pins['17']; B.wire((x, y), (x - 60, y)); B.port('CAN_RST', (x - 60, y), True)
    P(B, 'R10', '1', (x - 30, y), (3 - pdir('R10', '1')) % 4, 'right'); B.pwr('+3V3_RPI', (x - 30, y + 40), 1)  # RESET pull-up
    for p in ('2', '16', '13', '14', '15', '4', '5', '6', '12', '1', '3', '11', '10'): side(B, 'U6', p, pins[p])
    # crystal below-left, turned 180 deg: OSC1 (upper pin) takes the outer path to Y1's left terminal, OSC2 the
    # inner path to its right terminal, so the two never cross; each load cap hangs from its corner.
    (xo, yo1), (_, yo2) = pins['8'], pins['7']
    xi, xL = xo - 90, xo - 180; xa, yc = xL - 40, yo1 - 80
    y1 = P(B, 'Y1', '1', (xL + 70, yc), 2, 'below')
    B.wire((xo, yo2), (xi, yo2), (xi, yc), y1['1']); B.label('CAN_OSC_2', (xi + 5, yo2))
    hang(B, 'C7', '2', (xi, yc))
    B.wire((xo, yo1), (xa, yo1), (xa, yc), y1['3']); B.label('CAN_OSC_1', (xa + 5, yo1))
    hang(B, 'C8', '2', (xa, yc))
    (gx, g2), (_, g4) = y1['2'], y1['4']                                      # case pins to GND
    B.wire((gx, g4), (gx - 10, g4), (gx - 10, g2)); B.wire((gx, g2), (gx - 10, g2)); B.gnd((gx - 10, g4), 2)
    # supply: VDD to +3V3_RPI, VSS to GND; C9 decouples VDD
    x, y = pins['18']; B.wire((x, y), (x - 20, y)); B.pwr('+3V3_RPI', (x - 20, y), 2)
    x, y = pins['9']; B.wire((x, y), (x - 10, y), (x - 10, y - 20)); B.gnd((x - 10, y - 20))
    B.pwr('+3V3_RPI', (190, -150), 1); hang(B, 'C9', '2', (190, -150))
    return B

def banana():
    B = Block(None)
    for k, d in enumerate(('TP1', 'TP2', 'TP3', 'TP4', 'TP5')):
        pins = P(B, d, '1', (10, -60 * k)); side(B, d, '1', pins['1'])
    return B

def holes():
    B = Block(None); n = 4
    for k in range(n):
        y = -50 * k; P(B, f'MH{k + 1}', 'MH1', (20, y)); B.wire((20, y), (40, y))
    B.wire((40, 0), (40, -50 * (n - 1) - 20)); B.gnd((40, -50 * (n - 1) - 20))
    return B

BLOCKS = {'Raspberry Pi Pico': pico, 'VBUS Current Limit': vbus_limit, 'USB 5V to 3.3V Buck Converter': buck,
          'Squid Standard Debug Port': debug_port, '2.54mm Header Breakout': headers, 'UART LEDs and Headers': uart,
          'CAN Transceiver': can_xcvr, 'CAN Controller': can_ctrl, 'Banana Jacks': banana, 'Mounting Holes': holes}

if __name__ == '__main__' and len(sys.argv) == 1:
    for t, f in BLOCKS.items():
        x0, y0, x1, y1 = f().bbox(); print(f'{t:32s} w={x1 - x0:5.0f} h={y1 - y0:5.0f}  ({x0:.0f},{y0:.0f})..({x1:.0f},{y1:.0f})')

# ------------------------------------------------------------------ sheet assembly
# frame boxes (x0, y0, x1, y1) in 10-mil units on the 1700 x 1100 (ANSI B) sheet; title block is x > 1180, y < 160
BOXES = {
    'Raspberry Pi Pico':             (20, 760, 620, 1080),
    'CAN Transceiver':               (20, 470, 620, 760),
    'CAN Controller':                (20, 20, 620, 470),
    'Squid Standard Debug Port':     (620, 700, 1100, 1080),
    'Banana Jacks':                  (1100, 700, 1340, 1080),
    'Mounting Holes':                (1340, 700, 1680, 1080),
    'VBUS Current Limit':            (620, 410, 1150, 700),
    'UART LEDs and Headers':         (1150, 410, 1680, 700),
    'USB 5V to 3.3V Buck Converter': (620, 200, 1680, 410),
    '2.54mm Header Breakout':        (620, 20, 1180, 200),
}
# headings clear of the template's disclaimer (top left) and revision table (top right): (left edge, drop)
HEAD = {'Raspberry Pi Pico': (300, 0), 'Banana Jacks': (1100, 25), 'Mounting Holes': (1340, 25)}
CONTENT_X = {'Raspberry Pi Pico': (100, 620)}           # keep U1's designator off the disclaimer
NOTES = {'VBUS Current Limit': 'ILIM = 230/R_SET (+/-20%); 230/576 = 0.40 A typ, 0.32-0.48 A (USB 2.0 <= 0.5 A)'}

def build(path):
    base = [r for i, r in enumerate(S) if i < 3 or r.get('OwnerIndex') == '1'
            or (r.get('RECORD') == '41' and r.get('OwnerIndex') is None)]
    out = list(base)
    proto = {}
    for r in S:
        t = r.get('RECORD')
        if t == '27': proto.setdefault('wire', r)
        if t == '29': proto.setdefault('junction', r)
        if t == '25': proto.setdefault('label', r)
        if t == '22': proto.setdefault('noerc', r)
        if t == '6' and r.get('OwnerIndex') is None: proto.setdefault('line', r)
        if t == '4' and r.get('FontID') == '17': proto.setdefault('head', r)
        if t == '4' and r.get('FontID') == '1' and r.get('OwnerIndex') is None: proto.setdefault('note', r)
        if t == '18': proto.setdefault('port', r)
        if t == '17' and r.get('Style') == '4': proto.setdefault('gnd', r)
        if t == '17' and r.get('Style') == '2': proto.setdefault('pwr', r)
    def put(kind, **kv):
        r = proto[kind].copy(); r.delete('IndexInSheet')
        if r.get('UniqueID'): r.set('UniqueID', uid())
        if kind == 'port':
            r.delete('AutoSize'); r.set('IOType', IOTYPE.get(kv.get('Name'), '0'))
        if kind in ('wire', 'line'):
            for k in [k for k, _ in r.kv if k[:1] in 'XY' and k[1:].isdigit()]: r.delete(k)
            r.set('LocationCount', 2)
            for k in ('X1', 'Y1', 'X2', 'Y2'): r.set(k, 0)
        for k, v in kv.items(): r.set(k, v)
        out.append(r); return r
    def line(pts):
        l = put('line'); l.set('LocationCount', len(pts))
        for k in ('X1', 'Y1', 'X2', 'Y2'): l.delete(k)
        for n, (x, y) in enumerate(pts, 1): setc(l, f'X{n}', int(x * U)); setc(l, f'Y{n}', int(y * U))
    def text(kind, s, x, y):
        t = put(kind, Text=s); setc(t, 'Location.X', int(x * U)); setc(t, 'Location.Y', int(y * U))

    placed = []
    for title, (x0, y0, x1, y1) in BOXES.items():
        B = BLOCKS[title](); bx0, by0, bx1, by1 = B.bbox()
        cx0, cx1 = CONTENT_X.get(title, (x0, x1))
        ox = round(((cx0 + cx1) / 2 - (bx0 + bx1) / 2) / 10) * 10
        oy = (y1 - 60 - HEAD.get(title, (0, 0))[1] - by1) // 10 * 10
        assert ox + bx0 >= x0 + 10 and ox + bx1 <= x1 - 10 and oy + by0 >= y0 + 10, (title, ox + bx0, ox + bx1, oy + by0)
        B.render(ox, oy, put, out, instantiate)
        placed += [p[1] for p in B.parts]
        hx0, hdy = HEAD.get(title, (x0, 0))
        text('head', title, (hx0 + x1) / 2 - len(title) * 6.5, y1 - 38 - hdy)
        if title in NOTES: text('note', NOTES[title], x0 + 20, y0 + 15)
    # frames: shared edges drawn once
    edges = set()
    for x0, y0, x1, y1 in BOXES.values():
        for e in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
            edges.add(e)
    for (a, b) in sorted(edges):
        on_border = (a[0] == b[0] and a[0] in (20, 1680)) or (a[1] == b[1] and a[1] in (20, 1080))
        if not on_border: line([a, b])
    line([(1180, 20), (1180, 160), (1680, 160)])           # title block frame
    missing = set(T) - set(placed); dup = len(placed) - len(set(placed))
    assert not missing and not dup, (missing, dup)
    write_cfb(path, {'FileHeader': stream_from(out), 'Storage': fs['Storage'], 'Additional': fs['Additional']})
    print(os.path.basename(path), 'parts', len(placed), 'records', len(out))

if __name__ == '__main__' and len(sys.argv) > 1:
    build(sys.argv[1])
