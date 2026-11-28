"""Build Squid Debugger V1 sheets 2-6 (power path) from V1_PLAN section 3.
Usage: python tools/gen_sheet2.py hardware/DebugBoardMuxes.SchDoc hardware/DebugBoardPowerControl.SchDoc hardware/DebugBoard3V3Mux.SchDoc hardware/DebugBoard5VMux.SchDoc hardware/DebugBoardLimiters.SchDoc
Templates: parts placed on DebugBoardMuxes.SchDoc + generic R / 100 nF from DebugBoard.SchDoc."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from schgen import *

TPL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
fs2, S2 = load(os.path.join(TPL, 'sheet2_part_templates.SchDoc'))   # one placed instance of each V1 part
fs1, S1 = load(os.path.join(TPL, 'sheet1_rc_templates.SchDoc'))     # generic R (R2) and 100 nF (C22)

def by_des(recs, des):
    for r in recs:
        if r.get('RECORD') == '34' and r.get('Text') == des: return int(r.get('OwnerIndex')) + 1
    raise KeyError(des)

FM1 = {'2': '12'}   # sheet-1 font 2 (underlined Times) -> sheet-2 font 12

def efuse_template():
    """TPS259621DDAR symbol. There is no library part for it yet, so the symbol is built from the placed MIC2544
    (U4, same 8-pin box): pins renamed and renumbered, the MIC2544's supplier data and footprints removed, and the
    footprint set to SOIC127P600X170-9N (tools/altium: MakeDDA8 creates that footprint in the project library)."""
    fsS, SS = load(os.path.join(TPL, 'sheet1_source.SchDoc'))
    ci = by_des(SS, 'U4'); sub = sorted(subtree(SS, ci))
    pin = {'7': ('IN', '4'), '1': ('EN/UVLO', '3'), '2': ('OVCSEL', '8'), '5': ('dVdt', '2'),
           '8': ('OUT', '5'), '6': ('F\\L\\T\\', '6'), '4': ('ILM', '7'), '3': ('GND', '1')}
    keep_param = {'Comment': 'TPS259621DDAR', 'Value': 'TPS259621', 'Case/Package': 'HSOIC-8 (DDA)', 'Height': '1.7mm', 'Pins': '8',
                  'Max Supply Voltage': '19V', 'Min Supply Voltage': '2.7V', 'On-State Resistance': '89mOhm', 'Current Rating': '2A'}
    rename = {'Schedule B': ('Manufacturer', 'Texas Instruments'), 'Part Series': ('Manufacturer Part Number', 'TPS259621DDAR'),
              'Projected EOL Date': ('Datasheet', 'https://www.ti.com/lit/ds/symlink/tps2596.pdf')}
    kept, seen_model, dropped = [], False, set()
    for i in sub:
        r = SS[i].copy(); rec = r.get('RECORD'); owner = r.get('OwnerIndex')
        if owner is not None and int(owner) + 1 in dropped: dropped.add(i); continue
        if rec == '1':
            for k in ('VaultGUID', 'ItemGUID', 'RevisionGUID', 'SymbolVaultGUID', 'SymbolItemGUID', 'SymbolRevisionGUID'): r.delete(k)
            for k, v in (('LibReference', 'TPS259621DDAR'), ('DesignItemId', 'TPS259621DDAR'), ('SourceLibraryName', '*'),
                         ('ComponentDescription', 'eFuse, 2.7-19 V, 0.125-2 A adjustable current limit, 89 mOhm, OV clamp, auto-retry, HSOIC-8')): r.set(k, v)
        elif rec == '2':
            n, d = pin[r.get('Designator')]; r.set('Name', n); r.set('Designator', d); r.set('Electrical', 4)
        elif rec == '41' and r.get('Name') != 'PinUniqueId':
            nm = r.get('Name')
            if nm in rename: r.set('Name', rename[nm][0]); r.set('Text', rename[nm][1])
            elif nm in keep_param: r.set('Text', keep_param[nm])
            else: dropped.add(i); continue
        elif rec == '45':
            if seen_model: dropped.add(i); continue
            seen_model = True
            for k in ('ModelVaultGUID', 'ModelItemGUID', 'ModelRevisionGUID', 'UseComponentLibrary', 'DatalinksLocked', 'DatabaseDatalinksLocked'): r.delete(k)
            r.set('ModelName', 'SOIC127P600X170-9N'); r.set('ModelDatafileEntity0', 'SOIC127P600X170-9N')
        kept.append((i, r))
    new_index = {i: n + 1 for n, (i, r) in enumerate(kept)}
    out_ = [SS[0].copy()]
    for i, r in kept:
        if r.get('OwnerIndex') is not None and int(r.get('OwnerIndex')) + 1 in new_index:
            r.set('OwnerIndex', new_index[int(r.get('OwnerIndex')) + 1] - 1)
        out_.append(r)
    return Template(out_, 1, FM1)
T = {
    'TPS': Template(S2, find_comp(S2, '7e2eec2e55e3eba557c36dfb5d176d9')),
    'TLV': Template(S2, find_comp(S2, 'TLV70433DBVR')),
    'REF': Template(S2, find_comp(S2, 'LM4040BIM3-2.5_NOPB')),
    'BAT54A': Template(S2, find_comp(S2, 'BAT54A_215')),
    'BAT54C': Template(S2, find_comp(S2, 'BAT54C_215')),
    'ZEN': Template(S2, find_comp(S2, 'BZX84-C4V7,215')),
    'FET': Template(S2, find_comp(S2, '2N7002-7-F')),
    'DIP': Template(S2, find_comp(S2, '219-4MST')),
    'TVS': Template(S2, find_comp(S2, 'SMBJ13A')),
    'C22U': Template(S2, find_comp(S2, 'GCM31CR71A226KE02K')),
    'C10U35': Template(S2, find_comp(S2, 'CGA5L1X7R1V106K160AE')),
    'C1U25': Template(S2, find_comp(S2, 'CL21B105KAFNNNE')),
    'C1U50': Template(S2, find_comp(S2, 'GRM21BR71H105KA12L')),
    'R': Template(S1, by_des(S1, 'R2'), FM1),
    'C100N': Template(S1, by_des(S1, 'C22'), FM1),
    'EFUSE': efuse_template(),
}

# ------------------------------------------------------------------ design
blocks = []   # (title, [(tpl, des, comment, {pin: net})])
cnt = {'R': 13, 'C': 24, 'D': 4, 'Q': 1, 'U': None, 'SW': 1}
def nx(p):
    v = cnt[p]; cnt[p] += 1; return f'{p}{v}'
def R(val, a, b): return ('R', nx('R'), val, {'1': a, '2': b})
def C(tpl, val, a, b='GND'): return (tpl, nx('C'), val, {'1': a, '2': b})

def tvs5_template():
    """SMBJ5.0A for the 3V3 / 5V / 5V RF jacks. There is no separate library symbol for it, so it is the SMBJ13A symbol
    (same SMB / DO-214AA footprint) with the part identity changed: before Nov 27 D4-D6 only had "SMBJ5.0A" as their
    comment while the part number, description and links still said SMBJ13A, so a BOM would have ordered 13 V diodes."""
    import copy
    tpl = copy.copy(T['TVS']); tpl.recs = [r.copy() for r in T['TVS'].recs]
    par = {'MP': 'SMBJ5.0A', 'MF': 'Littelfuse', 'Value': 'SMBJ5.0A', 'Package': 'SMB (DO-214AA)',
           'SnapEDA_Link': 'https://www.littelfuse.com/assetdocs/littelfuse-tvs-diode-smbj-datasheet',
           'Check_prices': 'https://www.digikey.com/en/products/result?keywords=SMBJ5.0A%20Littelfuse'}
    for r in tpl.recs:
        rec = r.get('RECORD')
        if rec == '1':
            for k, v in (('LibReference', 'SMBJ5.0A'), ('DesignItemId', 'SMBJ5.0A'), ('SourceLibraryName', '*'),
                         ('ComponentDescription', 'TVS, 600 W, 5.0 V stand-off, 6.40-7.00 V breakdown, 9.2 V clamp, unidirectional, SMB')): r.set(k, v)
        elif rec == '41' and r.get('Name') in par: r.set('Text', par[r.get('Name')])
    return tpl
T['TVS5'] = tvs5_template()

# Inputs: TVS at the banana jacks. Mux input caps (1 uF, one per TPS2121 IN pin) live in each mux box.
blk = []
for rail, tvs in (('+3V3_PSU', 'SMBJ5.0A'), ('+5V_PSU', 'SMBJ5.0A'), ('+5V_RF_PSU', 'SMBJ5.0A'), ('+12V_PSU', 'SMBJ13A')):
    blk.append(('TVS' if tvs == 'SMBJ13A' else 'TVS5', nx('D'), tvs, {'C': rail, 'A': 'GND'}))
CIN = {   # rail -> input cap (designators kept stable; C2/C3/C6 moved here from sheet 1)
    '+5V_RF_LIM': C('C1U25', '1uF 25V', '+5V_RF_LIM'),
    '+12V_LIM':   C('C1U50', '1uF 50V', '+12V_LIM'),
    '+3V3_USB':   C('C1U25', '1uF 25V', '+3V3_USB'),
    '+5V_LIM':    ('C1U25', 'C2', '1uF 25V', {'1': '+5V_LIM', '2': 'GND'}),
    '+VBUS_PROT': ('C1U25', 'C3', '1uF 25V', {'1': '+VBUS_PROT', '2': 'GND'}),
    '+3V3_LIM':   ('C1U25', 'C6', '1uF 25V', {'1': '+3V3_LIM', '2': 'GND'}),
}
# Each bench-supply rail passes through a <= 1 A limiter (sheet 6) before its TPS2121: `x_PSU` (jack) -> eFuse -> `x_LIM`
# (mux IN1). The PR1 and OV1 dividers still sense the jack side, so limiting never changes the source decision.
LIM = {'+3V3_PSU': '+3V3_LIM', '+5V_PSU': '+5V_LIM', '+5V_RF_PSU': '+5V_RF_LIM', '+12V_PSU': '+12V_LIM'}
blocks.append(('Bench Inputs', blk))

# VAUX / +3V3_AUX / XREF
blk = [
    ('BAT54C', nx('D'), 'BAT54C', {'1': '+3V3_PSU', '2': '+5V_PSU', '3': 'VAUX'}),
    ('BAT54C', nx('D'), 'BAT54C', {'1': '+5V_RF_PSU', '2': '+12V_PSU', '3': 'VAUX'}),
    ('BAT54C', nx('D'), 'BAT54C', {'1': '+VBUS', '2': '+VBUS', '3': 'VAUX'}),
    C('C1U50', '1uF 50V', 'VAUX'),
    ('TLV', 'U9', 'TLV70433DBVR', {'2': 'VAUX', '1': 'GND', '3': '+3V3_AUX'}),
    C('C1U25', '1uF 25V', '+3V3_AUX'),
    R('2.00k', '+3V3_AUX', 'XREF_2V5'),
    ('REF', 'U10', 'LM4040BIM3-2.5', {'1': 'XREF_2V5', '2': 'GND', '3': 'GND'}),
    C('C1U25', '1uF 25V', 'XREF_2V5'),
]
blocks.append(('AUX Supply & 2.5V Reference', blk))

def mux(tag, u, psu, in2, out, rt_ov, prio, cout):
    """prio = (R_T, R_H) for dual-input rails, None for single-input. IN1 is the limited rail; dividers sense `psu`."""
    in1 = LIM[psu]
    pr, ov1, ov2, st, ilm, ss, dis = (f'{x}_{tag}' for x in ('PR1', 'OV1', 'OV2', 'ST', 'ILM', 'SS', 'DIS'))
    pins = {'7': in1, '1': out, '8': out, '5': ov1, '10': ilm, '11': ss, '12': 'GND'}
    blk = [('TPS', u, 'TPS2121RUXR', pins), CIN[in1]] + ([CIN[in2]] if in2 else [])
    if prio:
        pins.update({'2': in2, '6': pr, '3': 'XREF_2V5', '4': ov2, '9': st})
        blk += [R(prio[0], psu, pr), R('10.0k', pr, 'GND'), R(prio[1], pr, st), R('10.0k', st, '+3V3_AUX'),
                ('ZEN', nx('D'), 'BZX84-C4V7', {'3': pr, '1': 'GND'}),
                R(rt_ov, in2, ov2), R('10.0k', ov2, 'GND'),
                ('BAT54A', nx('D'), 'BAT54A', {'3': dis, '1': ov2, '2': ov1})]
    else:
        pins.update({'2': 'GND', '6': 'GND', '3': 'GND', '4': 'GND', '9': 'GND'})
        blk += [('BAT54A', nx('D'), 'BAT54A', {'3': dis, '1': ov1})]
    blk += [R(rt_ov, psu, ov1), R('10.0k', ov1, 'GND'), R('100k', ilm, 'GND'), C('C100N', '100nF', ss),
            C(cout[0], cout[1], out), C(cout[0], cout[1], out)]
    return blk

blocks.append(('3V3 Power Mux', mux('3V3', 'U3', '+3V3_PSU', '+3V3_USB', '+3V3_TGT', '26.1k', ('2.10k', '54.9k'), ('C22U', '22uF 10V'))))
blocks.append(('5V Power Mux', mux('5V', 'U5', '+5V_PSU', '+VBUS_PROT', '+5V_TGT', '44.2k', ('8.25k', '150k'), ('C22U', '22uF 10V'))))
blocks.append(('5V RF Switch', mux('5VRF', 'U7', '+5V_RF_PSU', None, '+5V_RF_TGT', '44.2k', None, ('C22U', '22uF 10V'))))
blocks.append(('12V Switch', mux('12V', 'U8', '+12V_PSU', None, '+12V_TGT', '118k', None, ('C10U35', '10uF 35V'))))

blk = []
for tag in ('3V3', '5V', '5VRF', '12V'):
    blk += [R('4.7k', f'DIS_{tag}', '+3V3_AUX'),
            ('FET', nx('Q'), '2N7002-7-F', {'1': f'G_{tag}', '2': 'GND', '3': f'DIS_{tag}'}),
            R('100R', f'EN_{tag}', f'G_{tag}'), R('100k', f'G_{tag}', 'GND')]
blk.append(('DIP', 'SW1', '219-4MST', {'1': 'DIS_3V3', '2': 'DIS_5V', '3': 'DIS_5VRF', '4': 'DIS_12V',
                                      '8': 'GND', '7': 'GND', '6': 'GND', '5': 'GND'}))
blocks.append(('Rail Enable', blk))

blk = []
for net, tag, rt in (('+3V3_TGT', '3V3', '49.9k'), ('+5V_TGT', '5V', '100k'), ('+12V_TGT', '12V', '470k')):
    blk += [R(rt, net, f'ADC_{tag}'), R('100k', f'ADC_{tag}', 'GND'), C('C100N', '100nF', f'ADC_{tag}')]
# mux status (ST high = IN1/PSU in use) to Pico; 100k limits back-feed into an unpowered Pico (<= 27 uA)
blk += [R('100k', 'ST_3V3', 'PICO_ST_3V3'), R('100k', 'ST_5V', 'PICO_ST_5V')]
blocks.append(('Rail Monitors', blk))

# PSU current limit: TPS259621 eFuse per bench rail. I_LIM = 903 / R_ILM + 0.0112 A  ->  1.02 k = 0.90 A typical,
# <= 0.97 A with part and resistor tolerance, so a J1 contact (1 A) is never overloaded. OVCSEL straps the output
# clamp: GND = 3.8 V, 402 k = 5.7 V, open = 13.8 V. EN/UVLO needs a divider (abs max 7 V): on above ~2.4 V / ~6.8 V.
blk = []
cnt['U'] = 14
for tag, psu, en_top, ovc in (('3V3', '+3V3_PSU', '100k', 'GND'), ('5V', '+5V_PSU', '100k', '402k'),
                              ('5VRF', '+5V_RF_PSU', '100k', '402k'), ('12V', '+12V_PSU', '470k', None)):
    en, ilm, ovn = f'EN_LIM_{tag}', f'ILM_LIM_{tag}', f'OVC_{tag}'
    pins = {'4': psu, '5': LIM[psu], '1': 'GND', '3': en, '7': ilm}
    if ovc == 'GND': pins['8'] = 'GND'
    elif ovc: pins['8'] = ovn
    blk += [('EFUSE', nx('U'), 'TPS259621DDAR', pins), C('C100N', '100nF', psu),
            R(en_top, psu, en), R('100k', en, 'GND'), R('1.02k', ilm, 'GND')]
    if ovc and ovc != 'GND': blk.append(R(ovc, ovn, 'GND'))
blocks.append(('PSU Current Limit', blk))

# ------------------------------------------------------------------ wired (hand-laid) blocks
from wired import Block
SPEC = {des: (tk, cm, pm) for _, parts in blocks for tk, des, cm, pm in parts}
def P(B, des, pin, at, rot=0):
    tk, cm, pm = SPEC[des]; return B.part(T[tk], des, cm, pm, pin, at, rot)

import wired_blocks
WIRED = wired_blocks.make(T, SPEC, blocks)

# ------------------------------------------------------------------ layout + emit
U = FRAC          # one 10-mil unit
STUB = 20 * U     # 0.2 in
CH = 5.6          # label char width (10-mil units)
keep = []
comp_idx = {i for i, r in enumerate(S2) if r.get('RECORD') == '1'}
drop = set()
for ci in comp_idx: drop.update(subtree(S2, ci))
out = [r for i, r in enumerate(S2) if i not in drop]
assert all(i < min(drop) for i in range(len(out))) or True
lbl_t = Rec(b'|RECORD=25|OwnerPartId=-1|Location.X=0|Location.Y=0|Color=128|FontID=1|Text=X|UniqueID=AAAAAAAA')
gnd_t = Rec(b'|RECORD=17|OwnerPartId=-1|Style=4|ShowNetName=T|Location.X=0|Location.Y=0|Orientation=3|Color=128|FontID=1|Text=GND|UniqueID=AAAAAAAA')
pwr_t = Rec(b'|RECORD=17|OwnerPartId=-1|Style=2|ShowNetName=T|Location.X=0|Location.Y=0|Orientation=1|Color=128|FontID=1|Text=X|UniqueID=AAAAAAAA')
port_t = Rec(b'|RECORD=18|OwnerPartId=-1|IOType=0|Alignment=1|Width=50|Location.X=0|Location.Y=0|Color=128|FontID=1|AreaColor=8454143|TextColor=128|Name=X|UniqueID=AAAAAAAA|Height=10')
wire_t = Rec(b'|RECORD=27|OwnerPartId=-1|LineWidth=1|Color=8388608|UniqueID=AAAAAAAA|LocationCount=2|X1=0|Y1=0|X2=0|Y2=0')
head_t = Rec(b'|RECORD=4|OwnerPartId=-1|Location.X=0|Location.Y=0|Color=8388608|FontID=17|Text=X|UniqueID=AAAAAAAA')
line_t = Rec(b'|RECORD=6|OwnerPartId=-1|LineWidth=2|LocationCount=2|X1=0|Y1=0|X2=0|Y2=0|UniqueID=AAAAAAAA')

jct_t = Rec(b'|RECORD=29|OwnerPartId=-1|Location.X=0|Location.Y=0|Color=128')
noerc_t = Rec(b'|RECORD=22|OwnerPartId=-1|Location.X=0|Location.Y=0|Color=255|Orientation=1|Symbol=Thin Cross|IsActive=T|SuppressAll=T|UniqueID=AAAAAAAA')
KIND = {'wire': None, 'gnd': None, 'pwr': None, 'port': None, 'label': None, 'junction': None}
def put_kind(kind, **kv):
    tpl = {'wire': wire_t, 'gnd': gnd_t, 'pwr': pwr_t, 'port': port_t, 'label': lbl_t, 'junction': jct_t, 'noerc': noerc_t}[kind]
    return put(tpl, **kv)

def is_rail(net): return net.startswith('+') or net in ('VAUX', 'XREF_2V5')
def port_w(net): return 5 * len(net) + 30

def put(t, **kv):
    r = t.copy(); r.set('UniqueID', uid())
    for k, v in kv.items(): r.set(k, v)
    out.append(r); return r

def wire(x1, y1, x2, y2):
    w = put(wire_t); setc(w, 'X1', x1); setc(w, 'Y1', y1); setc(w, 'X2', x2); setc(w, 'Y2', y2)

def line(x1, y1, x2, y2):
    l = put(line_t); setc(l, 'X1', int(x1 * U)); setc(l, 'Y1', int(y1 * U)); setc(l, 'X2', int(x2 * U)); setc(l, 'Y2', int(y2 * U))

def port(net, x, y, toward_left):
    w = port_w(net); p = put(port_t, Name=net, Width=w)
    setc(p, 'Location.X', x - w * U if toward_left else x); setc(p, 'Location.Y', y)

def place(tpl, des, comment, pinmap, x, y):
    base = len(out)
    out.extend(instantiate(tpl, base, x, y, des, comment, {'Value': comment}))
    for pin, (px, py, rot) in tpl.pins().items():
        net = pinmap.get(pin)
        if not net: continue
        ax, ay = x + px, y + py
        dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][rot]
        L = 20 * U
        bx, by = ax + dx * L, ay + dy * L
        if net == 'GND' or is_rail(net):
            wire(ax, ay, bx, by)
            p = put(gnd_t if net == 'GND' else pwr_t, Orientation=rot)
            if net != 'GND': p.set('Text', net)
            setc(p, 'Location.X', bx); setc(p, 'Location.Y', by)
        elif rot in (0, 2):
            wire(ax, ay, bx, by); port(net, bx, by, rot == 2)
        else:   # vertical pin with a signal: short riser then out to the right into a port
            wire(ax, ay, bx, by); cx = bx + 15 * U; wire(bx, by, cx, by); port(net, cx, by, False)

def margins(tpl, pinmap):
    l = r = t = b = 0
    for pin, (px, py, rot) in tpl.pins().items():
        net = pinmap.get(pin)
        if not net: continue
        if net == 'GND': need = 34
        elif is_rail(net): need = 26 + CH * len(net)
        else: need = 22 + port_w(net)
        if rot == 2: l = max(l, need)
        elif rot == 0: r = max(r, need)
        elif rot == 1:
            if is_rail(net) or net == 'GND': t = max(t, 34)
            else: t = max(t, 28); r = max(r, 17 + port_w(net))
        else: b = max(b, 34)
    return l, r, t, b

SHEET_L, SHEET_R, TOP, FLOOR = 20, 1633, 1100, 22
TB_X, TB_Y = 1100, 285            # title block keep-out: x > TB_X and y < TB_Y
import itertools

def block_cols(parts, maxh, title=''):
    if title in WIRED:
        B = WIRED[title](); x0, y0, x1, y1 = B.bbox(); h = (y1 - y0) + 20; w = (x1 - x0) + 40
        return [([('WIRED', B, None, None, x0, y0, x1, y1, 0, 0, h)], w)], max(w + 50, len(title) * 14 + 60), h + 75
    cols, col, colh, colw = [], [], 0, 0
    for tplk, des, cm, pm in parts:
        tpl = T[tplk]; x0, y0, x1, y1 = (v / U for v in tpl.bbox()); l, r, t, b = margins(tpl, pm)
        w = (x1 - x0) + l + r + 30; h = (y1 - y0) + t + b + 14
        if col and colh + h > maxh:
            cols.append((col, colw)); col, colh, colw = [], 0, 0
        col.append((tplk, des, cm, pm, x0, y0, x1, y1, l, t, h)); colh += h; colw = max(colw, w)
    if col: cols.append((col, colw))
    bw = max(sum(w for _, w in cols) + 50, len(title) * 14 + 60)   # heading is Times 24
    bh = max(sum(it[-1] for it in c) for c, _ in cols) + 75
    return cols, bw, bh

def pack(order, maxh):
    """greedy shelf packing; returns list of (block, x, ytop, cols) or None"""
    res, bx, by, bandh = [], SHEET_L, TOP, 0
    for bi in order:
        cols, bw, bh = sized[(bi, maxh[bi])]
        def fits(x, y, band):
            right = x + bw; depth = max(band, bh)          # the whole row gets as deep as its deepest block
            if y - depth < FLOOR: return False
            limit = TB_X if y - depth < TB_Y else SHEET_R
            return right <= limit
        if not fits(bx, by, bandh):
            bx, by, bandh = SHEET_L, by - bandh, 0
            if not fits(bx, by, 0): return None
        res.append((bi, bx, by, cols)); bx += bw; bandh = max(bandh, bh)
    return res, by - bandh

H = [200, 240, 280, 320, 360, 400, 440]
sized = {(bi, h): block_cols(blocks[bi][1], h, blocks[bi][0]) for bi in range(len(blocks)) for h in H}
base_out = list(out)

def build_sheet(bset, path):
    global out
    out = list(base_out)
    best = None
    for perm in itertools.permutations(bset):
        order = list(perm)
        for hm in H:
            for ho in H:
                maxh = {bi: (hm if ('Mux' in blocks[bi][0] or 'Switch' in blocks[bi][0]) else ho) for bi in bset}
                r = pack(order, maxh)
                if r and (best is None or r[1] > best[1]): best = r
    assert best, f'no layout fits A3 for {path}'
    # sheet font 17 = Times New Roman 24 (sheet-1 heading font); 100-mil snap/visible grid like sheet 1
    sh = out[1]; n = int(sh.get('FontIdCount'))
    for k, v in (('SnapGridSize', 5), ('VisibleGridSize', 10)):     # same as sheet 1: 50-mil snap, 100-mil grid, mils
        sh.set(k, v); sh.delete(k + '_Frac')
    sh.set('Display_Unit', 0)
    if n < 17:
        for k in range(n + 1, 18):
            sh.set(f'Size{k}', 24 if k == 17 else 10, after=f'FontName{k-1}'); sh.set(f'FontName{k}', 'Times New Roman', after=f'Size{k}')
        sh.set('FontIdCount', 17)
    # group into bands (same top), stretch boxes to tile the drawing area
    bands = {}
    for bi, bx, by_top, cols in best[0]: bands.setdefault(by_top, []).append((bi, bx, cols))
    tops = sorted(bands, reverse=True)
    log = []; rects = []
    line(SHEET_L, TOP, SHEET_R, TOP)
    for n_b, top in enumerate(tops):
        row = sorted(bands[top], key=lambda z: z[1])
        bottom = tops[n_b + 1] if n_b + 1 < len(tops) else FLOOR
        content_bottom = top - max(max(sum(it[-1] for it in c) for c, _ in cols) + 75 for _, _, cols in row)
        right = TB_X if content_bottom < TB_Y else SHEET_R
        widths = [sized[(bi, 0)][1] if False else None for bi, _, _ in row]
        natural = [sum(w for _, w in cols) for _, _, cols in row]
        boxw = [max(n_ + 50, len(blocks[bi][0]) * 14 + 60) for n_, (bi, _, _) in zip(natural, row)]
        extra = (right - SHEET_L - sum(boxw)) / len(row)
        x = SHEET_L
        if n_b + 1 < len(tops): line(SHEET_L, bottom, SHEET_R, bottom)
        for k, ((bi, _, cols), bw_) in enumerate(zip(row, boxw)):
            w_box = bw_ + extra
            if k: line(x, top, x, bottom)
            title = blocks[bi][0]
            hx = x + (w_box - len(title) * 13) / 2
            put(head_t, Text=title); setc(out[-1], 'Location.X', int(hx * U)); setc(out[-1], 'Location.Y', int((top - 38) * U))
            cx = x + max(25, (w_box - natural[k]) / 2)
            for c, w in cols:
                cy = top - 60
                for tplk, des, cm, pm, x0, y0, x1, y1, l, t_, h in c:
                    if tplk == 'WIRED':
                        B = des; bo_x = round((cx + 20 - x0) / 10) * 10; bo_y = round((cy - 10 - y1) / 10) * 10   # on the 100-mil grid
                        B.render(bo_x, bo_y, put_kind, out, instantiate)
                        log.extend((p[1], p[2], title) for p in B.parts)
                        continue
                    ox = round(cx + l - x0); oy = round(cy - t_ - y1)
                    ox += (-ox) % 10; oy -= oy % 10          # snap right (into own column), down
                    place(T[tplk], des, cm, pm, ox * U, oy * U)
                    lm, rm, tm, bm = margins(T[tplk], pm)
                    rects.append((des, ox + x0 - lm, oy + y0 - bm, ox + x1 + rm, oy + y1 + tm))
                    log.append((des, cm, title))
                    cy -= h
                cx += w
            x += w_box
    for i_ in range(len(rects)):
        for j_ in range(i_ + 1, len(rects)):
            a, b = rects[i_], rects[j_]
            if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
                print('  OVERLAP', a[0], b[0], [round(v) for v in a[1:]], [round(v) for v in b[1:]])
    # frame the title block like sheet 1
    if tops and FLOOR < TB_Y:
        line(TB_X, FLOOR, TB_X, TB_Y); line(TB_X, TB_Y, SHEET_R, TB_Y)
    write_cfb(path, {'FileHeader': stream_from(out), 'Storage': fs2['Storage'], 'Additional': fs2['Additional']})
    print(path.split('/')[-1], 'parts', len(log), 'bottom', round(best[1]))
    return log

build_sheet([0, 1, 4, 5], sys.argv[1])             # sheet 2: Power Inputs, AUX + reference, 5V RF + 12V switches
build_sheet([6, 7], sys.argv[2])                   # sheet 3: Power Control
if len(sys.argv) > 3: build_sheet([2], sys.argv[3])  # sheet 4: 3V3 Power Mux
if len(sys.argv) > 4: build_sheet([3], sys.argv[4])  # sheet 5: 5V Power Mux
if len(sys.argv) > 5: build_sheet([8], sys.argv[5])  # sheet 6: PSU current limit (eFuses)
