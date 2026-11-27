"""V1 PCB placement and silkscreen designators: one table -> preview + Altium DelphiScript.

Real footprint geometry (outline box and pads of every part) comes from tools/altium/pcb_dump.txt, which the
DumpV1 script writes from the open PcbDoc. All positions are mm from the board's lower-left corner.

  python tools/pcb_place.py     -> design/V1_placement.svg/.png, tools/altium/place_v1.pas
  Altium: File > Run Script > SquidPcbTools.PrjScr > PlaceV1   (then DumpV1, then python tools/pcb_check.py)

The script places parts, positions and sizes every designator, moves the jack labels and sets the layer stack.
It does not route anything.
"""
import os, math, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
UP = 10.0                                    # the board is 10 mm longer than V0: everything from the Pico up moved by this
W, H, CORNER = 61.0, 100.0 + UP, 5.0
ORIGIN_MIL = (11558.4886, 3895.504)          # board lower-left corner in the PcbDoc (absolute mils)
PCB_PATH = r'C:\Users\Public\Documents\Altium\Squid-Debugger\Squid-Debugger\hardware\DebugBoard.PcbDoc'
DUMP_PATH = os.path.join(HERE, 'altium', 'pcb_dump.txt')
V0_PATH = os.path.abspath(os.path.join(ROOT, '_backup', 'DebugBoard_V0.PcbDoc'))   # git show 009cc9b:hardware/DebugBoard.PcbDoc
GAP = 0.25                                   # minimum space between two parts' outline boxes
TXT_H, TXT_W = 0.8, 0.15                     # designator height and stroke width (fab minimum for legible silk)
LBL_H = 1.5                                  # jack label height

# ------------------------------------------------------------------ geometry from the Altium dump
def rot(p, a):
    a = int(round(a)) % 360
    x, y = p
    return {0: (x, y), 90: (-y, x), 180: (-x, -y), 270: (y, -x)}[a]
def norm(r): return (min(r[0], r[2]), min(r[1], r[3]), max(r[0], r[2]), max(r[1], r[3]))

GEO, FREE_TEXT = {}, []
def load_dump():
    mm = lambda s: float(s) * 0.0254
    comps = {}
    for line in open(DUMP_PATH, encoding='latin-1'):
        f = line.rstrip('\r\n').split('|')
        if f[0] == 'C' and len(f) >= 11:
            comps[f[1]] = dict(pattern=f[2], side='B' if f[3].startswith('Bottom') else 'T', rot=float(f[4]),
                               o=(mm(f[5]), mm(f[6])), box=tuple(mm(v) for v in f[7:11]), pads=[])
        elif f[0] == 'P' and f[1] in comps and len(f) >= 12:
            comps[f[1]]['pads'].append((f[2], f[3], tuple(mm(v) for v in f[7:11]), f[11], mm(f[6])))
        elif f[0] == 'T' and len(f) >= 9:
            if f[1].startswith(('Squid Debugger', '"Any', 'TX RX')): continue
            try: FREE_TEXT.append((f[1], 'B' if f[2].startswith('Bottom') else 'T', float(f[3]) % 180, tuple(mm(v) for v in f[5:9])))
            except ValueError: pass
    for d, c in comps.items():
        def loc(r, c=c):
            pts = []
            for px, py in ((r[0], r[1]), (r[2], r[3])):
                x, y = rot((px - c['o'][0], py - c['o'][1]), -c['rot'])
                pts += [-x if c['side'] == 'B' else x, y]
            return norm(pts)
        box = (-10.5, -25.5, 10.5, 25.5) if d == 'U1' else loc(c['box'])     # Pico: body only (its box includes drawing extras)
        GEO[d] = dict(pattern=c['pattern'], box=box, nets={p[0]: p[3] for p in c['pads']},
                      pads=[(p[0], 'M' if p[1].startswith('Multi') else 'S', loc(p[2]), p[4]) for p in c['pads']])
load_dump()
def net(des, pin): return GEO[des]['nets'].get(str(pin), '')
def signal_net(des): return next(n for n in GEO[des]['nets'].values() if n and n != 'GND')

P = {}                                       # des -> (origin x, origin y, rotation, side)
def world(des, r):
    ox, oy, a, side = P[des]; pts = []
    for px, py in ((r[0], r[1]), (r[2], r[3])):
        x, y = rot((-px if side == 'B' else px, py), a); pts += [ox + x, oy + y]
    return norm(pts)
def box(des): return world(des, GEO[des]['box'])
def put(des, cx, cy, a=0, side='T', origin=False):
    """Place a part by the centre of its outline box (or by its footprint origin when origin=True)."""
    if origin: P[des] = (cx, cy, a, side); return
    b = GEO[des]['box']; lx, ly = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    x, y = rot((-lx if side == 'B' else lx, ly), a)
    P[des] = (cx - x, cy - y, a, side)

# ------------------------------------------------------------------ the placement table
for d, x, y in (('MH1', 56, 5), ('MH2', 56, 95 + UP), ('MH3', 5, 95 + UP), ('MH4', 5, 5)): put(d, x, y, origin=True)
put('U1', 30.5, 73.65 + UP, origin=True)                                       # Pico, as V0
put('J1', 30.5, 4.03, origin=True); put('P4', 19.07, 11.42, origin=True); put('P3', 41.93, 11.42, 180, origin=True)
# bench jacks, each with its TVS beside it
put('TP3', 7.2, 77.5 + UP); put('D4', 15.4, 77.5 + UP, 90)                          # +3V3_PSU
put('TP1', 53.8, 77.5 + UP); put('D5', 45.6, 77.5 + UP, 90)                         # +5V_PSU
put('TP2', 7.2, 34.2); put('D7', 15.4, 34.2, 90)                          # +12V_PSU
put('TP4', 53.8, 34.2); put('D6', 45.6, 34.2, 90)                         # +5V_RF_PSU
put('TP5', 30.5, 38.3)                                                    # GND, on the centre line as in V0
# VBUS current limit (top right, at Pico pin 40)
put('U4', 49.7, 93.3 + UP, 270); put('C4', 45.0, 95.6 + UP, 90); put('R5', 45.0, 90.6 + UP, 270); put('C23', 49.7, 87.6 + UP)
put('R3', 57.8, 89.9 + UP, 90); put('D1', 54.6, 87.0 + UP, 90)
# USB buck (top left)
put('L1', 14.3, 88.0 + UP); put('U13', 16.3, 94.0 + UP); put('C18', 15.6, 97.85 + UP); put('C21', 10.9, 93.5 + UP); put('C22', 10.6, 96.3 + UP)
put('C19', 2.9, 87.2 + UP, 90); put('C20', 6.3, 87.2 + UP, 90)
# UART header and LEDs
put('P2', 13.74, 68.29, origin=True); put('R6', 13.35, 63.7, 90); put('R7', 16.75, 63.7, 90)
put('D2', 13.35, 57.7, 90); put('D3', 16.75, 57.7, 90); put('R11', 4.6, 67.3); put('R12', 4.6, 64.2)

def mux(u, ux, uy, parts, bottom):
    """A TPS2121 with its parts. At 0 deg the IC has IN2 (2) lower left, IN1 (7) lower right, OUT (1, 8) upper
    left/right, SS and ILM in the top row. Each part goes next to the pin it serves; dividers go underneath."""
    put(u, ux, uy)
    outs = []
    for d in parts:
        n = signal_net(d)
        if n == net(u, 7) and net(u, 2) == 'GND': put(d, ux + 1.2, uy - 3.2)   # IN1 bypass, single-input switch
        elif n == net(u, 7): put(d, ux + 3.2, uy - 2.2, 90)               # IN1 bypass
        elif n == net(u, 2): put(d, ux - 3.2, uy - 2.2, 90)               # IN2 bypass
        elif n == net(u, 1): outs.append(d)                               # output caps
        elif n == net(u, 11): put(d, ux - 1.85, uy + 4.5)                 # soft-start cap
        elif n == net(u, 10): put(d, ux + 2.05, uy + 4.5)                 # current-limit resistor
        else: raise SystemExit(f'{d}: net {n} is not on {u}')
    for d, sx in zip(outs, (-1, 1)): put(d, ux + sx * 4.7, uy + 1.7)
    res = [d for d in bottom if d[0] == 'R']; dio = [d for d in bottom if d[0] == 'D']
    cols = (ux - 4.6, ux + 3.3)
    for i, d in enumerate(res): put(d, cols[i // 4] if len(res) > 4 else cols[0], uy - 4.2 + 2.9 * (i % 4), 0, 'B')
    for i, d in enumerate(dio): put(d, cols[i] if len(res) > 4 else cols[1], uy + (8.2 if len(res) > 4 else -2.5), 0, 'B')
mux('U3', 10.2, 45.3, ['C6', 'C26', 'C30', 'C31', 'C32', 'R22'], ['R14', 'R15', 'R16', 'R17', 'R18', 'R19', 'R20', 'R21', 'D11', 'D12'])
mux('U5', 50.8, 61.5, ['C2', 'C3', 'C33', 'C34', 'C35', 'R31'], ['R23', 'R24', 'R25', 'R26', 'R27', 'R28', 'R29', 'R30', 'D13', 'D14'])
mux('U8', 8.7, 18.9, ['C25', 'C39', 'C40', 'C41', 'R37'], ['R35', 'R36', 'D16'])
mux('U7', 52.0, 18.9, ['C24', 'C36', 'C37', 'C38', 'R34'], ['R32', 'R33', 'D15'])
# AUX supply and 2.5 V reference (right, above the 5 V RF jack)
put('D8', 45.25, 42.5); put('D9', 50.55, 42.5); put('D10', 55.85, 42.5)
put('C27', 44.0, 48.4, 90); put('U9', 48.4, 48.4); put('C28', 52.4, 48.4, 90); put('R13', 55.4, 48.4, 90)
put('C29', 50.2, 53.0); put('U10', 55.8, 53.1)
# CAN: controller on the centre line under the Pico's SPI1 pins, crystal to its lower right, transceiver by SW1
put('U6', 30.5, 50.6, 90); put('Y1', 39.85, 42.0, 180); put('C7', 39.85, 38.3); put('C8', 39.85, 45.7)
put('C9', 22.3, 54.4, 90); put('R10', 22.3, 49.9, 90)
put('U2', 20.8, 20.3, 90); put('R1', 19.2, 26.1, 90); put('C1', 22.25, 26.1, 90)
# force-on DIP switch and SWD series resistors (bottom side, on the way to J1 pins 9-12)
put('SW1', 30.5, 23.4)
for i, d in enumerate(('R8', 'R4', 'R2', 'R9')): put(d, 15.6 + 3.0 * i, 17.6, 90, 'B')
# rail enables and ADC dividers: bottom side, between the Pico's two pin rows
for i in range(4):
    y0 = 51.0 + UP + 6.4 * i
    put(f'Q{i+1}', 25.0, y0, 0, 'B'); put(f'R{38+3*i}', 32.0, y0, 0, 'B')
    put(f'R{39+3*i}', 25.0, y0 + 3.1, 0, 'B'); put(f'R{40+3*i}', 32.0, y0 + 3.1, 0, 'B')
for i, d in enumerate(('C42', 'C43', 'C44')): put(d, 25.0 if i != 1 else 32.0, 77.0 + UP + (2.9 if i == 2 else 0), 0, 'B')
for i in range(8): put(f'R{50+i}', 25.0 if i < 4 else 32.0, 83.2 + UP + 2.9 * (i % 4), 0, 'B')
put('R57', 32.0, 79.9 + UP, 0, 'B')

LOGO = (30.5, 49.3, 0); LOGO_BOX = (23.7, 44.0, 37.3, 54.6)                       # SDSL logo: bottom side, centre
LABELS = {'+3.3V': (1.5, 76.6), '+5V': (49.6, 76.6), '+12V': (2.0, 26.3), '+5V RF': (47.6, 26.3), 'GND': (28.2, 30.25)}       # GND sits directly under its jack
TITLE = (30.5, 22.6, 1.0)                   # "Squid Debugger V1 / By: Bjorn Bengtsson and Alex Jaber", bottom side
TITLE_BOX = (TITLE[0] - 20.0, TITLE[1] - 2.2, TITLE[0] + 20.0, TITLE[1] + 2.2)
FRAME = (11.2, 51.4, 19.0, 72.15)            # V0 silk frame around the UART parts (free tracks on the top overlay)
FRAME_LINES = [(FRAME[0] - 0.1, FRAME[1] - 0.1, FRAME[2] + 0.1, FRAME[1] + 0.1), (FRAME[0] - 0.1, FRAME[3] - 0.1, FRAME[2] + 0.1, FRAME[3] + 0.1),
               (FRAME[0] - 0.1, FRAME[1] - 0.1, FRAME[0] + 0.1, FRAME[3] + 0.1), (FRAME[2] - 0.1, FRAME[1] - 0.1, FRAME[2] + 0.1, FRAME[3] + 0.1)]
TXRX = (15.1, 70.75, 1.3)                    # "TX RX" label: centred in the frame above P2, 1.3 mm so it clears the frame lines
# parts whose footprint has no 3D body: STEP file (in hardware/Libraries/SquidDebugger_V1/3D) per designator
STEP_DIR = os.path.join(os.path.dirname(PCB_PATH), 'Libraries', 'SquidDebugger_V1', '3D')
STEP = {'SW1': ('219-4MST.stp', 90, 0, 0.25),                       # height is the model's Y axis; feet at y = -0.25
        'U10': ('LM4040BIM3-2.5_NOPB.stp', 0, 0, 0.0)}              # TI SOT-23: already flat, leads along X
STEP.update({d: ('GCM31CR71A226KE02K.stp', 0, 0, 0.0) for d in ('C31', 'C32', 'C34', 'C35', 'C37', 'C38')})
STEP.update({d: ('BAT54C,215.stp', 90, 180, -1.16) for d in ('D8', 'D9', 'D10')})           # Nexperia SOT-23: height along Y
STEP.update({d: ('BAT54A,215.stp', 90, 90, -1.16) for d in ('D12', 'D14', 'D15', 'D16')})  # footprint has pads 1, 2 on +X
STEP.update({d: ('BZX84-C4V7,215.stp', 90, 90, -1.16) for d in ('D11', 'D13')})
THT = {d for d in GEO if any(p[1] == 'M' for p in GEO[d]['pads'])}
ROUND = lambda d: d.startswith(('TP', 'MH'))

# ------------------------------------------------------------------ checks
def hit(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap
def hit_round(c, q, gap=0.0):
    cx, cy, r = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2, (c[2] - c[0]) / 2 + gap
    dx, dy = max(q[0] - cx, 0, cx - q[2]), max(q[1] - cy, 0, cy - q[3])
    return dx * dx + dy * dy < r * r
def inside_board(r, inset):
    if r[0] < inset or r[1] < inset or r[2] > W - inset or r[3] > H - inset: return False
    for x, y in ((r[0], r[1]), (r[0], r[3]), (r[2], r[1]), (r[2], r[3])):
        cx = CORNER if x < CORNER else W - CORNER if x > W - CORNER else None
        cy = CORNER if y < CORNER else H - CORNER if y > H - CORNER else None
        if cx is not None and cy is not None and math.hypot(x - cx, y - cy) > CORNER - inset: return False
    return True
def pads_of(des, side):
    """world boxes of the pads of `des` that are copper on `side` (through pads count on both sides)."""
    return [world(des, r) for n, kind, r, hole in GEO[des]['pads'] if kind == 'M' or P[des][3] == side]
def outline(des, side):
    """what `des` occupies on `side`: its outline box on its own side, only its through pads on the other."""
    if P[des][3] == side: return [box(des)]
    return pads_of(des, side) if des in THT else []
def check():
    bad = []
    for a, b in itertools.combinations(P, 2):
        for side in 'TB':
            if P[a][3] != side and P[b][3] != side: continue
            A, B = outline(a, side), outline(b, side)
            clash = False
            for ra in A:
                for rb in B:
                    if ROUND(a) and ROUND(b): clash |= math.hypot((ra[0] + ra[2] - rb[0] - rb[2]) / 2, (ra[1] + ra[3] - rb[1] - rb[3]) / 2) < (ra[2] - ra[0] + rb[2] - rb[0]) / 2 + GAP
                    elif ROUND(a): clash |= hit_round(ra, rb, GAP)
                    elif ROUND(b): clash |= hit_round(rb, ra, GAP)
                    else: clash |= hit(ra, rb, GAP)
            if clash: bad.append((a, b, side))
    for d in P:
        if d not in ('U1', 'J1') and not inside_board(box(d), 0.5): bad.append((d, 'EDGE'))
        texts = [(txt, r) for txt, side, a, r in FREE_TEXT if side == P[d][3] and not (txt in LABELS and a == 0) and txt != 'TX RX']
        if P[d][3] == 'B': texts += [('title', TITLE_BOX), ('logo', LOGO_BOX)]
        else: texts += [('UART frame', r) for r in FRAME_LINES]
        for txt, r in texts:
            if any(hit(r, q, 0.1) for q in [box(d)] if not ROUND(d)): bad.append((d, 'ON TEXT ' + txt))
    return bad

# ------------------------------------------------------------------ designators
def text_size(s, h=TXT_H, w=TXT_W): return (len(s) * h * 0.88 + w, h + w + 0.1)
DES = {}                                     # des -> (cx, cy, rotation)
def solve_designators():
    obstacles = {'T': [], 'B': []}           # (rect, owner)
    for d in P:
        for side in 'TB':
            for r in pads_of(d, side): obstacles[side].append((r, d, 0.2, True))
            if P[d][3] == side and d != 'U1': obstacles[side].append((box(d), d, 0.05, False))
    for txt, side, a, r in FREE_TEXT:
        if txt in LABELS and a == 0: continue                              # moved below
        obstacles[side].append((r, None, 0.15, True))
    for txt, (x, y) in LABELS.items():
        w, h = text_size(txt, LBL_H, 0.25); obstacles['T'].append(((x, y, x + w, y + h), None, 0.15, True))
    for r in (TITLE_BOX, LOGO_BOX): obstacles['B'].append((r, None, 0.15, True))
    for r in FRAME_LINES + [(TXRX[0] - 3.4, TXRX[1] - 0.9, TXRX[0] + 3.4, TXRX[1] + 0.9)]: obstacles['T'].append((r, None, 0.15, True))
    def candidates(d):
        b = box(d); cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        w, h = text_size(d)
        for dist in (0.15, 0.5, 0.9, 1.4, 2.0, 2.8):
            for a, (tw, th) in ((0, (w, h)), (90, (h, w))):
                for px, py in ((cx, b[3] + dist + th / 2), (cx, b[1] - dist - th / 2), (b[2] + dist + tw / 2, cy), (b[0] - dist - tw / 2, cy),
                               (b[0] + tw / 2, b[3] + dist + th / 2), (b[2] - tw / 2, b[3] + dist + th / 2),
                               (b[0] + tw / 2, b[1] - dist - th / 2), (b[2] - tw / 2, b[1] - dist - th / 2),
                               (b[2] + dist + tw / 2, b[3] - th / 2), (b[2] + dist + tw / 2, b[1] + th / 2),
                               (b[0] - dist - tw / 2, b[3] - th / 2), (b[0] - dist - tw / 2, b[1] + th / 2)):
                    yield (px, py, a, (px - tw / 2, py - th / 2, px + tw / 2, py + th / 2), False)
        for a, (tw, th) in ((0, (w, h)), (90, (h, w))):                    # last resort: on the part's own body, off its pads
            for fx in (0.5, 0.3, 0.7, 0.15, 0.85):
                for fy in (0.5, 0.3, 0.7, 0.15, 0.85):
                    px, py = b[0] + (b[2] - b[0]) * fx, b[1] + (b[3] - b[1]) * fy
                    yield (px, py, a, (px - tw / 2, py - th / 2, px + tw / 2, py + th / 2), True)
    def free(d, r, own_body):
        side = P[d][3]
        if not inside_board(r, 0.6): return False
        if side == 'T' and hit(r, box('U1'), 0.1) and d != 'U1': return False   # hidden under the Pico
        for o, owner, gap, is_pad in obstacles[side]:
            if owner == d and not is_pad:
                if not own_body and hit(r, o, 0.0): return False
                continue
            if own_body and owner != d and not is_pad and owner is not None and hit(r, o, gap): return False
            if owner is not None and ROUND(owner) and not is_pad:
                if hit_round(o, r, gap): return False
            elif hit(r, o, gap): return False
        return True
    order = sorted(P, key=lambda d: (sum(1 for c in itertools.islice(candidates(d), 48) if free(d, c[3], c[4])), d))
    failed = []
    for d in order:
        for px, py, a, r, own in candidates(d):
            if free(d, r, own):
                DES[d] = (px, py, a); obstacles[P[d][3]].append((r, None, 0.15, True)); break
        else: failed.append(d)
    return failed

# ------------------------------------------------------------------ outputs
def svg(path):
    S, pad = 9.0, 12
    def board(ox, side, title):
        fx = (lambda x: (W - x) * S) if side == 'B' else (lambda x: x * S)
        fy = lambda y: (H - y) * S
        def R(r, **kw):
            st = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
            return f'<rect x="{min(fx(r[0]), fx(r[2])):.1f}" y="{fy(r[3]):.1f}" width="{abs(r[2]-r[0])*S:.1f}" height="{(r[3]-r[1])*S:.1f}" {st}/>'
        o = [f'<g transform="translate({ox},{pad + 16})">',
             f'<text x="{W*S/2}" y="-8" text-anchor="middle" font-size="16" font-weight="bold">{title}</text>',
             f'<rect x="0" y="0" width="{W*S}" height="{H*S}" rx="{CORNER*S}" fill="#f4f1e6" stroke="#222" stroke-width="2"/>']
        for d in sorted(P):
            mine = P[d][3] == side
            if mine:
                b = box(d)
                if ROUND(d): o.append(f'<circle cx="{fx((b[0]+b[2])/2):.1f}" cy="{fy((b[1]+b[3])/2):.1f}" r="{(b[2]-b[0])/2*S:.1f}" fill="#fff" stroke="#a60"/>')
                else: o.append(R(b, fill='#fff', stroke='#c33' if d[0] == 'U' else '#888'))
            for r in pads_of(d, side): o.append(R(r, fill='#c9a227' if mine else '#bbb', stroke='none'))
        for d, (px, py, a) in DES.items():
            if P[d][3] != side: continue
            tr = f' transform="rotate(-90 {fx(px):.1f} {fy(py):.1f})"' if a else ''
            o.append(f'<text x="{fx(px):.1f}" y="{fy(py)+TXT_H*S*0.38:.1f}" text-anchor="middle" font-size="{TXT_H*S*1.15:.1f}" fill="#036"{tr}>{d}</text>')
        if side == 'T':
            for txt, (x, y) in LABELS.items():
                o.append(f'<text x="{fx(x):.1f}" y="{fy(y):.1f}" font-size="{LBL_H*S*1.2:.1f}" fill="#070">{txt}</text>')
        o.append('</g>'); return o
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{2*W*S+3*pad}" height="{H*S+2*pad+16}" font-family="Arial">',
           '<rect width="100%" height="100%" fill="#fff"/>']
    out += board(pad, 'T', f'TOP ({W:.0f} x {H:.0f} mm)') + board(W * S + 2 * pad, 'B', 'BOTTOM (seen from below)') + ['</svg>']
    open(path, 'w').write('\n'.join(out))
    try:
        import pymupdf; pymupdf.open(path)[0].get_pixmap(dpi=100).save(path[:-3] + 'png')
    except ImportError: pass

def pas(path):
    X = lambda v: f'MilsToCoord(X0 + {v:.3f} / 0.0254)'
    Y = lambda v: f'MilsToCoord(Y0 + {v:.3f} / 0.0254)'
    get_board = [f"  Board := PCBServer.GetPCBBoardByPath('{PCB_PATH}');",
                 '  If Board = Nil Then Board := PCBServer.GetCurrentPCBBoard;',
                 "  If Board = Nil Then Begin ShowMessage('Open DebugBoard.PcbDoc first'); Exit; End;",
                 f'  X0 := {ORIGIN_MIL[0]}; Y0 := {ORIGIN_MIL[1]};']
    L = ['{ Generated by tools/pcb_place.py - do not edit. PlaceV1 places parts and silkscreen; it routes nothing. }',
         'Var Board : IPCB_Board; Missing : String; X0, Y0 : Double; Wiped, Added : Integer; Sizes : String;', '',
         'Procedure Put(Des : String; X, Y, Rot : Double; Bottom : Boolean);', 'Var C : IPCB_Component;', 'Begin',
         '  C := Board.GetPcbComponentByRefDes(Des);',
         "  If C = Nil Then Begin Missing := Missing + Des + ' '; Exit; End;",
         '  C.BeginModify;',
         '  If Bottom Then C.Layer := eBottomLayer Else C.Layer := eTopLayer;',
         '  C.Rotation := Rot;',
         '  C.MoveToXY(MilsToCoord(X0 + X / 0.0254), MilsToCoord(Y0 + Y / 0.0254));',
         '  C.NameOn := True; C.CommentOn := False; C.NameAutoPosition := eAutoPos_Manual;',
         '  C.EndModify; C.GraphicallyInvalidate;', 'End;', '',
         'Procedure Des(D : String; X, Y, Rot : Double);', 'Var C : IPCB_Component; T : IPCB_Text; Rc : TCoordRect;', 'Begin',
         '  C := Board.GetPcbComponentByRefDes(D);', '  If C = Nil Then Exit;',
         '  T := C.Name;', '  T.BeginModify;',
         f'  T.Size := MilsToCoord({TXT_H} / 0.0254); T.Width := MilsToCoord({TXT_W} / 0.0254); T.Rotation := Rot;',
         '  T.EndModify;', '  T.BeginModify;',
         '  Rc := T.BoundingRectangleForSelection;',
         '  T.MoveByXY(MilsToCoord(X0 + X / 0.0254) - (Rc.Left + Rc.Right) Div 2, MilsToCoord(Y0 + Y / 0.0254) - (Rc.Bottom + Rc.Top) Div 2);',
         '  T.EndModify; T.GraphicallyInvalidate;', 'End;', '',
         'Procedure PutLogo(X, Y, Rot : Double; Bottom : Boolean);', 'Var It : IPCB_BoardIterator; C : IPCB_Component;', 'Begin',
         '  It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject));',
         '  It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  C := It.FirstPCBObject;',
         '  While C <> Nil Do Begin',
         "    If C.Pattern = 'SDSLLOGO' Then Begin",
         '      C.BeginModify;',
         '      If Bottom Then C.Layer := eBottomLayer Else C.Layer := eTopLayer;',
         '      C.Rotation := Rot; C.MoveToXY(MilsToCoord(X0 + X / 0.0254), MilsToCoord(Y0 + Y / 0.0254));',
         '      C.NameOn := False; C.CommentOn := False;',
         '      C.EndModify; C.GraphicallyInvalidate;',
         '    End;',
         '    C := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);', 'End;', '',
         'Procedure Art(T : IPCB_Text; X, Y, Hgt, FrameW, FrameH : Double);   { V0 artwork text frame: resize, lay flat, centre at X, Y }', 'Var Rc : TCoordRect;', 'Begin',
         '  T.BeginModify; T.Size := MilsToCoord(Hgt / 0.0254); T.Width := MilsToCoord(Hgt * 0.16 / 0.0254); T.Rotation := 0;',
         '  T.MultilineTextWidth := MilsToCoord(FrameW / 0.0254); T.MultilineTextHeight := MilsToCoord(FrameH / 0.0254); T.EndModify;',
         '  T.BeginModify; Rc := T.BoundingRectangleForSelection;',
         '  T.MoveByXY(MilsToCoord(X0 + X / 0.0254) - (Rc.Left + Rc.Right) Div 2, MilsToCoord(Y0 + Y / 0.0254) - (Rc.Bottom + Rc.Top) Div 2);',
         '  T.EndModify; T.GraphicallyInvalidate;', 'End;', '',
         'Procedure Wipe(Kind : Integer; Lay : TLayer; X1, Y1, X2, Y2 : Double);   { remove free silk primitives touching a box }',
         'Var SI : IPCB_SpatialIterator; O : IPCB_Primitive; Lst : TInterfaceList; I : Integer;', 'Begin',
         '  Lst := TInterfaceList.Create; SI := Board.SpatialIterator_Create;',
         '  SI.AddFilter_ObjectSet(MkSet(Kind)); SI.AddFilter_LayerSet(MkSet(Lay));',
         '  SI.AddFilter_Area(MilsToCoord(X0 + X1 / 0.0254), MilsToCoord(Y0 + Y1 / 0.0254), MilsToCoord(X0 + X2 / 0.0254), MilsToCoord(Y0 + Y2 / 0.0254));',
         '  O := SI.FirstPCBObject;',
         '  While O <> Nil Do Begin',
         '    If Not O.InComponent Then Lst.Add(O);',
         '    O := SI.NextPCBObject;', '  End;',
         '  Board.SpatialIterator_Destroy(SI);',
         '  For I := 0 To Lst.Count - 1 Do Board.RemovePCBObject(Lst.Items[I]);',
         '  Lst.Free;', 'End;', '',
         'Procedure WipeTracks(X1, Y1, X2, Y2 : Double);   { remove free top-silk tracks that lie inside a box }',
         'Var It : IPCB_BoardIterator; O : IPCB_Track; Lst : TInterfaceList; I : Integer; A, B, C, D : Integer;', 'Begin',
         '  A := MilsToCoord(X0 + X1 / 0.0254); B := MilsToCoord(Y0 + Y1 / 0.0254); C := MilsToCoord(X0 + X2 / 0.0254); D := MilsToCoord(Y0 + Y2 / 0.0254);',
         '  Lst := TInterfaceList.Create; It := Board.BoardIterator_Create;',
         '  It.AddFilter_ObjectSet(MkSet(eTrackObject)); It.AddFilter_LayerSet(MkSet(eTopOverlay)); It.AddFilter_Method(eProcessAll);',
         '  O := It.FirstPCBObject;',
         '  While O <> Nil Do Begin',
         '    If (Not O.InComponent) And (O.x1 >= A) And (O.x1 <= C) And (O.x2 >= A) And (O.x2 <= C) And (O.y1 >= B) And (O.y1 <= D) And (O.y2 >= B) And (O.y2 <= D) Then Lst.Add(O);',
         '    O := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         "  Missing := Missing + '';",
         '  Wiped := Lst.Count;',
         '  For I := 0 To Lst.Count - 1 Do Board.RemovePCBObject(Lst.Items[I]);',
         '  Lst.Free;', 'End;', '',
         'Procedure Vias(Des : String);   { TPS2121 via-in-pad stubs: 0.2 / 0.4 mm in the vendor footprint -> 0.25 / 0.52 mm }',
         'Var C : IPCB_Component; G : IPCB_GroupIterator; Vi : IPCB_Via;', 'Begin',
         '  C := Board.GetPcbComponentByRefDes(Des);', '  If C = Nil Then Exit;',
         '  G := C.GroupIterator_Create; G.AddFilter_ObjectSet(MkSet(eViaObject));',
         '  Vi := G.FirstPCBObject;',
         '  While Vi <> Nil Do Begin',
         '    Vi.BeginModify; Vi.HoleSize := MilsToCoord(0.25 / 0.0254); Vi.Size := MilsToCoord(0.52 / 0.0254); Vi.EndModify; Vi.GraphicallyInvalidate;',
         '    Vi := G.NextPCBObject;', '  End;',
         '  C.GroupIterator_Destroy(G);', 'End;', '',
         'Procedure StretchV1;   { make the board UP mm longer: move the top edge, and any free mechanical drawing above mid-board }',
         'Var BO : IPCB_BoardOutline; I : Integer; S : TPolySegment; Lim, D : Integer; It : IPCB_BoardIterator; T : IPCB_Track; A : IPCB_Arc; N : Integer;', 'Begin'] + get_board + [
         '  Lim := MilsToCoord(Y0 + 50 / 0.0254); N := 0;',
         '  BO := Board.BoardOutline;',
         f'  D := MilsToCoord(Y0 + {H} / 0.0254) - BO.BoundingRectangle.Top;',
         "  If Abs(D) < MilsToCoord(1) Then Begin ShowMessage('Board already has this length'); Exit; End;",
         '  PCBServer.PreProcess;',
         '  BO.BeginModify;',
         '  For I := 0 To BO.PointCount Do Begin',
         '    S := BO.Segments[I];',
         '    If S.vy > Lim Then Begin S.vy := S.vy + D; S.cy := S.cy + D; BO.Segments[I] := S; End;',
         '  End;',
         '  BO.EndModify; BO.Rebuild; BO.Validate; BO.GraphicallyInvalidate;',
         '  It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTrackObject));',
         '  It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  T := It.FirstPCBObject;',
         '  While T <> Nil Do Begin',
         '    If (Not T.InComponent) And (T.Layer <> eTopOverlay) And (T.Layer <> eBottomOverlay) Then Begin',
         '      T.BeginModify;',
         '      If T.y1 > Lim Then Begin T.y1 := T.y1 + D; N := N + 1; End;',
         '      If T.y2 > Lim Then T.y2 := T.y2 + D;',
         '      T.EndModify; T.GraphicallyInvalidate;',
         '    End;',
         '    T := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         '  It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eArcObject));',
         '  It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  A := It.FirstPCBObject;',
         '  While A <> Nil Do Begin',
         '    If (Not A.InComponent) And (A.Layer <> eTopOverlay) And (A.Layer <> eBottomOverlay) And (A.YCenter > Lim) Then Begin',
         '      A.BeginModify; A.YCenter := A.YCenter + D; A.EndModify; A.GraphicallyInvalidate; N := N + 1;',
         '    End;',
         '    A := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         '  PCBServer.PostProcess; Board.ViewManager_FullUpdate;',
         '  Board.RebuildSplitBoardRegions(True); Board.ViewManager_FullUpdate;',
         "  ShowMessage('Outline and board region stretched; free mechanical tracks/arcs moved: ' + IntToStr(N));", 'End;', '',
         'Procedure ArtV1;   { put V0''s full bottom-side artwork back: copy its silk regions from the V0 board file }',
         'Var Old : IPCB_Board; It : IPCB_BoardIterator; O : IPCB_Primitive; Lst : TInterfaceList; I, N : Integer;', 'Begin'] + get_board + [
         f"  Client.OpenDocument('PCB', '{V0_PATH}');",
         f"  Old := PCBServer.GetPCBBoardByPath('{V0_PATH}');",
         "  If Old = Nil Then Begin ShowMessage('Could not load the V0 board'); Exit; End;",
         '  PCBServer.PreProcess;',
         '  Lst := TInterfaceList.Create; It := Board.BoardIterator_Create;',
         '  It.AddFilter_ObjectSet(MkSet(eRegionObject)); It.AddFilter_LayerSet(MkSet(eBottomOverlay)); It.AddFilter_Method(eProcessAll);',
         '  O := It.FirstPCBObject;',
         '  While O <> Nil Do Begin If Not O.InComponent Then Lst.Add(O); O := It.NextPCBObject; End;',
         '  Board.BoardIterator_Destroy(It);',
         '  For I := 0 To Lst.Count - 1 Do Board.RemovePCBObject(Lst.Items[I]);',
         '  Lst.Free; N := 0;',
         '  It := Old.BoardIterator_Create;',
         '  It.AddFilter_ObjectSet(MkSet(eRegionObject)); It.AddFilter_LayerSet(MkSet(eBottomOverlay)); It.AddFilter_Method(eProcessAll);',
         '  O := It.FirstPCBObject;',
         '  While O <> Nil Do Begin',
         '    If Not O.InComponent Then Begin Board.AddPCBObject(O.Replicate); N := N + 1; End;',
         '    O := It.NextPCBObject;', '  End;',
         '  Old.BoardIterator_Destroy(It);',
         '  PCBServer.PostProcess; Board.ViewManager_FullUpdate;',
         "  ShowMessage('V0 artwork restored: ' + IntToStr(N) + ' silk regions');", 'End;', '',
         'Procedure WipeRound(X, Y, R : Double);   { remove bottom-silk artwork dots whose centre is inside a circle (round pads) }',
         'Var SI : IPCB_SpatialIterator; O : IPCB_Primitive; Lst : TInterfaceList; I : Integer; Rc : TCoordRect; Cx, Cy, Dx, Dy, Rr : Double;', 'Begin',
         '  Cx := X0 + X / 0.0254; Cy := Y0 + Y / 0.0254; Rr := R / 0.0254;',
         '  Lst := TInterfaceList.Create; SI := Board.SpatialIterator_Create;',
         '  SI.AddFilter_ObjectSet(MkSet(eRegionObject)); SI.AddFilter_LayerSet(MkSet(eBottomOverlay));',
         '  SI.AddFilter_Area(MilsToCoord(Cx - Rr), MilsToCoord(Cy - Rr), MilsToCoord(Cx + Rr), MilsToCoord(Cy + Rr));',
         '  O := SI.FirstPCBObject;',
         '  While O <> Nil Do Begin',
         '    If Not O.InComponent Then Begin',
         '      Rc := O.BoundingRectangle;',
         '      Dx := CoordToMils((Rc.Left + Rc.Right) Div 2) - Cx; Dy := CoordToMils((Rc.Bottom + Rc.Top) Div 2) - Cy;',
         '      If Dx * Dx + Dy * Dy < Rr * Rr Then Lst.Add(O);',
         '    End;',
         '    O := SI.NextPCBObject;', '  End;',
         '  Board.SpatialIterator_Destroy(SI);',
         '  For I := 0 To Lst.Count - 1 Do Board.RemovePCBObject(Lst.Items[I]);',
         '  Lst.Free;', 'End;', '',
         'Function ProbeOne(F : String; Rx, Ry, Rz : Double) : String;   { projected size of a STEP model for one rotation }',
         'Var B : IPCB_ComponentBody; Mdl : IPCB_Model; Rb : TCoordRect;', 'Begin',
         '  B := PCBServer.PCBObjectFactory(eComponentBodyObject, eNoDimension, eCreate_Default);',
         '  Mdl := B.ModelFactory_FromFilename(F, False);',
         '  Mdl.SetState(Rx, Ry, Rz, 0); B.Model := Mdl; B.SetState_FromModel;',
         '  Board.AddPCBObject(B);',
         '  Rb := B.BoundingRectangle;',
         "  Result := FloatToStr(Rx) + ',' + FloatToStr(Ry) + ',' + FloatToStr(Rz) + ': x ' + FloatToStr(Round(CoordToMils(Rb.Left) * 2.54) / 100) + '..' + FloatToStr(Round(CoordToMils(Rb.Right) * 2.54) / 100) + ' y ' + FloatToStr(Round(CoordToMils(Rb.Bottom) * 2.54) / 100) + '..' + FloatToStr(Round(CoordToMils(Rb.Top) * 2.54) / 100) + ' | ';",
         '  Board.RemovePCBObject(B);', 'End;', '',
         'Procedure ProbeV1;   { how do the TI and Nexperia SOT-23 STEP models project for each rotation? (model origin lands at absolute 0,0) }',
         'Var S, F : String;', 'Begin'] + get_board + [
         f"  F := '{os.path.join(STEP_DIR, 'LM4040BIM3-2.5_NOPB.stp')}';",
         "  S := 'TI: ' + ProbeOne(F, 0, 0, 0) + ProbeOne(F, 90, 0, 0) + ProbeOne(F, 0, 90, 0) + ProbeOne(F, 0, 0, 90) + ProbeOne(F, 90, 0, 90) + ProbeOne(F, 90, 90, 0);",
         f"  F := '{os.path.join(STEP_DIR, 'BAT54C,215.stp')}';",
         "  S := S + '   NXP: ' + ProbeOne(F, 0, 0, 0) + ProbeOne(F, 90, 0, 0) + ProbeOne(F, 90, 0, 90) + ProbeOne(F, 90, 0, 180) + ProbeOne(F, 90, 0, 270);",
         '  ShowMessage(S);', 'End;', '',
         'Procedure SideView(ShowTop, ShowBottom : Boolean);   { show or hide everything that belongs to one side of the board }',
         'Var I : Integer; L : TLayer; MO : IPCB_MechanicalLayer; N : String;', 'Begin'] + get_board + [
         '  Board.LayerIsDisplayed[eTopLayer] := ShowTop; Board.LayerIsDisplayed[eTopOverlay] := ShowTop;',
         '  Board.LayerIsDisplayed[eTopPaste] := ShowTop; Board.LayerIsDisplayed[eTopSolder] := ShowTop;',
         '  Board.LayerIsDisplayed[eBottomLayer] := ShowBottom; Board.LayerIsDisplayed[eBottomOverlay] := ShowBottom;',
         '  Board.LayerIsDisplayed[eBottomPaste] := ShowBottom; Board.LayerIsDisplayed[eBottomSolder] := ShowBottom;',
         '  For I := 1 To 32 Do Begin',
         '    L := LayerUtils.MechanicalLayer(I);',
         '    MO := Board.LayerStack_V7.LayerObject_V7[L];',
         '    If MO <> Nil Then If MO.MechanicalLayerEnabled Then Begin',
         '      N := UpperCase(MO.Name);',
         "      If Pos('TOP', N) = 1 Then Board.LayerIsDisplayed[L] := ShowTop;",
         "      If Pos('BOTTOM', N) = 1 Then Board.LayerIsDisplayed[L] := ShowBottom;",
         '    End;',
         '  End;',
         '  Board.ViewManager_UpdateLayerTabs; Board.ViewManager_FullUpdate;',
         "  Client.SendMessage('PCB:Zoom', 'Action=Redraw', 255, Client.CurrentView);", 'End;', '',
         'Procedure ViewFront;   { front view: hide bottom-side parts, pads and silk }', 'Begin', '  SideView(True, False);', 'End;', '',
         'Procedure ViewBack;    { back view (then View > Flip Board): hide top-side parts, pads and silk }', 'Begin', '  SideView(False, True);', 'End;', '',
         'Procedure ViewBoth;', 'Begin', '  SideView(True, True);', 'End;', '',
         'Procedure RegionV1;   { after StretchV1: make the board region (the solid board shape) follow the outline }', 'Begin'] + get_board + [
         '  Board.RebuildSplitBoardRegions(True);',
         '  Board.ViewManager_FullUpdate;',
         "  ShowMessage('Board region rebuilt');", 'End;', '',
         'Procedure Body3D(Des, FileName : String; RotX, RotZ, Dz : Double);',
         '{ Seat a STEP model on a part. The part is laid flat on top first (PlaceV1 puts it back afterwards). A new body',
         '  lands with the model origin at absolute 0,0; with the rotation set before it is added, its box is the turned',
         '  model, so centring that box on the pads seats it. Any body the part already has is replaced. }',
         'Var C : IPCB_Component; G : IPCB_GroupIterator; B, Old : IPCB_ComponentBody; Pd : IPCB_Pad; Mdl : IPCB_Model; Rb, Rp : TCoordRect;',
         '    L, Bt, R, Tp : Integer; First : Boolean; Lst : TInterfaceList; I : Integer;', 'Begin',
         '  C := Board.GetPcbComponentByRefDes(Des);', '  If C = Nil Then Exit;',
         '  Lst := TInterfaceList.Create;',
         '  G := C.GroupIterator_Create; G.AddFilter_ObjectSet(MkSet(eComponentBodyObject));',
         '  Old := G.FirstPCBObject;',
         '  While Old <> Nil Do Begin Lst.Add(Old); Old := G.NextPCBObject; End;',
         '  C.GroupIterator_Destroy(G);',
         '  For I := 0 To Lst.Count - 1 Do Begin C.RemovePCBObject(Lst.Items[I]); Board.RemovePCBObject(Lst.Items[I]); End;',
         '  Lst.Free;',
         '  C.BeginModify; C.Layer := eTopLayer; C.Rotation := 0; C.EndModify;',
         '  First := True;',
         '  G := C.GroupIterator_Create; G.AddFilter_ObjectSet(MkSet(ePadObject));',
         '  Pd := G.FirstPCBObject;',
         '  While Pd <> Nil Do Begin',
         '    Rp := Pd.BoundingRectangle;',
         '    If First Then Begin L := Rp.Left; Bt := Rp.Bottom; R := Rp.Right; Tp := Rp.Top; First := False; End',
         '    Else Begin',
         '      If Rp.Left < L Then L := Rp.Left; If Rp.Bottom < Bt Then Bt := Rp.Bottom;',
         '      If Rp.Right > R Then R := Rp.Right; If Rp.Top > Tp Then Tp := Rp.Top;',
         '    End;',
         '    Pd := G.NextPCBObject;', '  End;',
         '  C.GroupIterator_Destroy(G);',
         '  B := PCBServer.PCBObjectFactory(eComponentBodyObject, eNoDimension, eCreate_Default);',
         '  Mdl := B.ModelFactory_FromFilename(FileName, False);',
         "  If Mdl = Nil Then Begin Missing := Missing + Des + '(no model) '; Exit; End;",
         '  Mdl.SetState(RotX, 0, RotZ, MilsToCoord(Dz / 0.0254));',
         '  B.Model := Mdl;',
         '  B.SetState_FromModel;',
         '  Board.AddPCBObject(B);',
         '  Rb := B.BoundingRectangle;',
         '  B.MoveByXY((L + R) Div 2 - (Rb.Left + Rb.Right) Div 2, (Bt + Tp) Div 2 - (Rb.Bottom + Rb.Top) Div 2);',
         '  C.AddPCBObject(B);',
         "  Sizes := Sizes + Des + ' ' + FloatToStr(Round(CoordToMils(Rb.Right - Rb.Left) * 2.54) / 100) + 'x' + FloatToStr(Round(CoordToMils(Rb.Top - Rb.Bottom) * 2.54) / 100) + '  ';",
         '  Added := Added + 1;', 'End;', '',
         'Procedure NoRooms;   { the ECO adds a placement room off the board; nothing is meant to be confined to it }',
         'Var It : IPCB_BoardIterator; O : IPCB_Rule; Lst : TInterfaceList; I : Integer;', 'Begin',
         '  Lst := TInterfaceList.Create; It := Board.BoardIterator_Create;',
         '  It.AddFilter_ObjectSet(MkSet(eRuleObject)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  O := It.FirstPCBObject;',
         '  While O <> Nil Do Begin',
         '    If O.RuleKind = eRule_ConfinementConstraint Then Lst.Add(O);',
         '    O := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         '  For I := 0 To Lst.Count - 1 Do Board.RemovePCBObject(Lst.Items[I]);',
         '  Lst.Free;', 'End;', '',
         'Procedure Labels;', 'Var It : IPCB_BoardIterator; T : IPCB_Text; X, Y : Double; Lst : TInterfaceList; I : Integer; Flat : Boolean;', 'Begin',
         '  Lst := TInterfaceList.Create;',
         '  It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTextObject));',
         '  It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  T := It.FirstPCBObject;',
         '  While T <> Nil Do Begin',
         '    X := -1;',
         '    If Not T.InComponent Then Begin',
         '      Flat := (Round(T.Rotation) Mod 180) = 0;',
         "      If Flat And (T.Size < MilsToCoord(40)) And ((T.Text = '5V') Or (T.Text = '5V RF')) Then Lst.Add(T);   { labels of the deleted V0 jumper P1 }",
         "      If Pos('Squid Debugger V0', T.Text) > 0 Then Begin T.BeginModify; T.Text := StringReplace(T.Text, 'Squid Debugger V0', 'Squid Debugger V1', 0); T.EndModify; End;",
         "      If (Pos('By: Alex Jaber', T.Text) > 0) Then Begin T.BeginModify; T.Text := StringReplace(T.Text, 'By: Alex Jaber', 'By: Bjorn Bengtsson and Alex Jaber', 0); T.EndModify; End;",
         f"      If Pos('Squid Debugger', T.Text) > 0 Then Art(T, {TITLE[0]}, {TITLE[1]}, {TITLE[2]}, {TITLE_BOX[2]-TITLE_BOX[0]}, {TITLE_BOX[3]-TITLE_BOX[1]});",
         "      If Pos('sufficiently advanced', T.Text) > 0 Then Lst.Add(T);   { the Clarke quote: removed on request }",
         "      If T.Text = 'TX RX' Then Begin",
         f'        T.BeginModify; T.Size := MilsToCoord({TXRX[2]} / 0.0254); T.Width := MilsToCoord(0.2 / 0.0254); T.EndModify;',
         '        T.BeginModify;',
         f'        T.MoveByXY(MilsToCoord(X0 + {TXRX[0]} / 0.0254) - (T.BoundingRectangleForSelection.Left + T.BoundingRectangleForSelection.Right) Div 2, MilsToCoord(Y0 + {TXRX[1]} / 0.0254) - (T.BoundingRectangleForSelection.Bottom + T.BoundingRectangleForSelection.Top) Div 2);',
         '        T.EndModify; T.GraphicallyInvalidate;',
         '      End;',
         '      If Flat Then Begin',
     ] + [f"        If T.Text = '{txt}' Then Begin X := {x}; Y := {y}; End;" for txt, (x, y) in LABELS.items()] + [
         '      End;',
         '    End;',
         '    If X >= 0 Then Begin',
         f'      T.BeginModify; T.Size := MilsToCoord({LBL_H} / 0.0254); T.Width := MilsToCoord(0.25 / 0.0254); T.EndModify;',
         '      T.BeginModify;',
         '      T.MoveByXY(MilsToCoord(X0 + X / 0.0254) - T.BoundingRectangleForSelection.Left, MilsToCoord(Y0 + Y / 0.0254) - T.BoundingRectangleForSelection.Bottom);',
         '      T.EndModify; T.GraphicallyInvalidate;',
         '    End;',
         '    T := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         '  For I := 0 To Lst.Count - 1 Do Board.RemovePCBObject(Lst.Items[I]);',
         '  Lst.Free;', 'End;', '',
         'Function M(V : Integer; Ref : Double) : String;', 'Begin', '  Result := FloatToStr(Round((CoordToMils(V) - Ref) * 100) / 100);', 'End;', '',
         'Function R2S(Rc : TCoordRect) : String;', 'Begin',
         "  Result := M(Rc.Left, X0) + '|' + M(Rc.Bottom, Y0) + '|' + M(Rc.Right, X0) + '|' + M(Rc.Top, Y0);", 'End;', '',
         'Procedure DumpV1;',
         'Var It : IPCB_BoardIterator; C : IPCB_Component; G : IPCB_GroupIterator; Pd : IPCB_Pad; Vi : IPCB_Via; T : IPCB_Text; S : TStringList; N : String; Nb : Integer; Bd : IPCB_Primitive;',
         'Begin'] + get_board + [
         '  S := TStringList.Create;',
         '  It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eComponentObject));',
         '  It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  C := It.FirstPCBObject;',
         '  While C <> Nil Do Begin',
         "    S.Add('C|' + C.Name.Text + '|' + C.Pattern + '|' + Layer2String(C.Layer) + '|' + FloatToStr(C.Rotation) + '|' + M(C.x, X0) + '|' + M(C.y, Y0) + '|' + R2S(C.BoundingRectangleNoNameComment));",
         "    S.Add('N|' + C.Name.Text + '|' + Layer2String(C.Name.Layer) + '|' + FloatToStr(C.Name.Rotation) + '|' + M(C.Name.Size, 0) + '|' + R2S(C.Name.BoundingRectangleForSelection));",
         '    G := C.GroupIterator_Create; G.AddFilter_ObjectSet(MkSet(ePadObject));',
         '    Pd := G.FirstPCBObject;',
         '    While Pd <> Nil Do Begin',
         "      N := ''; If Pd.Net <> Nil Then N := Pd.Net.Name;",
         "      S.Add('P|' + C.Name.Text + '|' + Pd.Name + '|' + Layer2String(Pd.Layer) + '|' + M(Pd.x, X0) + '|' + M(Pd.y, Y0) + '|' + M(Pd.HoleSize, 0) + '|' + R2S(Pd.BoundingRectangle) + '|' + N);",
         '      Pd := G.NextPCBObject;', '    End;',
         '    C.GroupIterator_Destroy(G);',
         '    G := C.GroupIterator_Create; G.AddFilter_ObjectSet(MkSet(eComponentBodyObject));',
         '    Nb := 0; Bd := G.FirstPCBObject;',
         '    While Bd <> Nil Do Begin Nb := Nb + 1; Bd := G.NextPCBObject; End;',
         '    C.GroupIterator_Destroy(G);',
         "    S.Add('B|' + C.Name.Text + '|' + IntToStr(Nb) + '|' + C.SourceLibReference + '|' + C.Comment.Text);",
         '    G := C.GroupIterator_Create; G.AddFilter_ObjectSet(MkSet(eViaObject));',
         '    Vi := G.FirstPCBObject;',
         '    While Vi <> Nil Do Begin',
         "      N := ''; If Vi.Net <> Nil Then N := Vi.Net.Name;",
         "      S.Add('P|' + C.Name.Text + '|via|Multi Layer|' + M(Vi.x, X0) + '|' + M(Vi.y, Y0) + '|' + M(Vi.HoleSize, 0) + '|' + R2S(Vi.BoundingRectangle) + '|' + N);",
         '      Vi := G.NextPCBObject;', '    End;',
         '    C.GroupIterator_Destroy(G);',
         '    C := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         '  It := Board.BoardIterator_Create; It.AddFilter_ObjectSet(MkSet(eTextObject));',
         '  It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  T := It.FirstPCBObject;',
         '  While T <> Nil Do Begin',
         "    If Not T.InComponent Then S.Add('T|' + Copy(StringReplace(StringReplace(T.Text, #13, ' ', 1), #10, ' ', 1), 1, 22) + '|' + Layer2String(T.Layer) + '|' + FloatToStr(T.Rotation) + '|' + M(T.Size, 0) + '|' + R2S(T.BoundingRectangleForSelection));",
         '    T := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         f"  S.SaveToFile('{DUMP_PATH}'); S.Free;",
         "  ShowMessage('Dump written');", 'End;', '',
         'Procedure Clear(Kind : Integer);', 'Var It : IPCB_BoardIterator; O : IPCB_Primitive; Lst : TInterfaceList; I : Integer;', 'Begin',
         '  Lst := TInterfaceList.Create; It := Board.BoardIterator_Create;',
         '  It.AddFilter_ObjectSet(MkSet(Kind)); It.AddFilter_LayerSet(AllLayers); It.AddFilter_Method(eProcessAll);',
         '  O := It.FirstPCBObject;',
         '  While O <> Nil Do Begin',
         '    If (Not O.InComponent) And ((Kind = ePolyObject) Or (Kind = eViaObject) Or',
         '       (O.Layer = eTopLayer) Or (O.Layer = eBottomLayer) Or (O.Layer = eMidLayer1) Or (O.Layer = eMidLayer2)) Then Lst.Add(O);',
         '    O := It.NextPCBObject;', '  End;',
         '  Board.BoardIterator_Destroy(It);',
         '  For I := 0 To Lst.Count - 1 Do Board.RemovePCBObject(Lst.Items[I]);',
         '  Lst.Free;', 'End;', '',
         'Procedure StackV1;   { SIG / GND / GND / SIG, 1.6 mm, 7628 prepreg: see design/V1_LAYOUT.md }',
         'Var Stack : IPCB_LayerStack_V7; L : IPCB_LayerObject_V7;', 'Begin'] + get_board + [
         '  Stack := Board.LayerStack_V7;',
         '  L := Stack.FirstLayer;',
         '  While L <> Nil Do Begin',
         '    If (L.LayerID = eTopLayer) Or (L.LayerID = eBottomLayer) Then L.CopperThickness := MilsToCoord(1.378);',
         '    If (L.LayerID = eMidLayer1) Or (L.LayerID = eMidLayer2) Then L.CopperThickness := MilsToCoord(0.689);',
         '    If (L.LayerID = eTopLayer) Or (L.LayerID = eMidLayer2) Then Begin',
         "      L.Dielectric.DielectricHeight := MilsToCoord(8.268); L.Dielectric.DielectricConstant := 4.4; L.Dielectric.DielectricMaterial := '7628';",
         '    End;',
         '    If L.LayerID = eMidLayer1 Then Begin',
         "      L.Dielectric.DielectricHeight := MilsToCoord(41.93); L.Dielectric.DielectricConstant := 4.6; L.Dielectric.DielectricMaterial := 'FR-4';",
         '    End;',
         '    L := Stack.NextLayer(L);', '  End;',
         "  ShowMessage('Layer stack set');", 'End;', '',
         'Procedure PlaceV1;', 'Begin'] + get_board + [
         "  Missing := ''; Added := 0; Sizes := '';",
         '  PCBServer.PreProcess;',
     ] + [f"  Body3D('{d}', '{os.path.join(STEP_DIR, f)}', {rx}, {rz}, {dz});" for d, (f, rx, rz, dz) in sorted(STEP.items())] + [
         '  Clear(ePolyObject); Clear(eTrackObject); Clear(eArcObject); Clear(eViaObject); Clear(eFillObject); Clear(eRegionObject);']
    for d, (x, y, a, side) in sorted(P.items()):
        L.append(f"  Put('{d}', {x:.3f}, {y:.3f}, {a}, {'True' if side == 'B' else 'False'});")
    L.append(f"  PutLogo({LOGO[0]}, {LOGO[1]}, {LOGO[2]}, True); Labels;")
    for _ in range(2):                       # second pass settles text whose box changed with its new size
        for d, (x, y, a) in sorted(DES.items()): L.append(f"  Des('{d}', {x:.3f}, {y:.3f}, {a});")
    L.append('  NoRooms;')
    L.append("  Vias('U3'); Vias('U5'); Vias('U7'); Vias('U8');")
    keep_clear = []
    for d in P:
        for n, kind, r, hole in GEO[d]['pads']:
            w = world(d, r)
            if kind == 'M':
                L.append(f'  WipeRound({(w[0]+w[2])/2:.2f}, {(w[1]+w[3])/2:.2f}, {(w[2]-w[0])/2 + 0.15:.2f});')
            elif P[d][3] == 'B': keep_clear.append((w, 0.15))
    keep_clear += [((x - (text_size(d)[0] if not a else text_size(d)[1]) / 2, y - (text_size(d)[1] if not a else text_size(d)[0]) / 2,
                     x + (text_size(d)[0] if not a else text_size(d)[1]) / 2, y + (text_size(d)[1] if not a else text_size(d)[0]) / 2), 0.25)
                   for d, (x, y, a) in DES.items() if P[d][3] == 'B']
    keep_clear += [((TITLE[0] - 18.5, TITLE[1] - 2.0, TITLE[0] + 18.5, TITLE[1] + 2.0), 0.0)]
    for r, m in keep_clear:                  # V0 halftone artwork on the bottom silk: open a window under pads and text
        L.append(f'  Wipe(eRegionObject, eBottomOverlay, {r[0]-m:.2f}, {r[1]-m:.2f}, {r[2]+m:.2f}, {r[3]+m:.2f});')
    L += ['  PCBServer.PostProcess;', '  Board.ViewManager_FullUpdate;',
          "  If Missing <> '' Then ShowMessage('Not on board: ' + Missing) Else ShowMessage('V1 placement done: %d parts, %d designators. 3D models seated: ' + IntToStr(Added) + ' (' + Sizes + ')');" % (len(P), len(DES)),
          'End;']
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, 'w').write('\r\n'.join(L) + '\r\n')

if __name__ == '__main__':
    missing = sorted(set(GEO) - set(P) - {'G***'}); bad = check()
    failed = solve_designators()
    svg(os.path.join(ROOT, 'design', 'V1_placement.svg')); pas(os.path.join(HERE, 'altium', 'place_v1.pas'))
    print(len(P), 'parts placed; not in table:', missing or 'none')
    print('too close (<%.2f mm):' % GAP, bad or 'none')
    print('designators placed:', len(DES), ' no room for:', failed or 'none',
          ' on own body:', sorted(d for d, (x, y, a) in DES.items() if hit((x, y, x, y), box(d))) or 'none')
