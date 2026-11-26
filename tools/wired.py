"""Hand-laid, wired schematic blocks: parts placed by pin position (with rotation), real wires, junctions,
power ports, GND symbols, ports and net labels. Used by gen_sheet2.py for blocks drawn in the
'connected' style (parts hang off the wires a reader follows), as opposed to label-per-pin blocks.

Coordinates are in 10-mil units (Altium's integer coordinate unit), relative to the block origin.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from schgen import *

U = FRAC
CH = 5.6          # label character width, 10-mil units (Times New Roman 10)
PAIRS = [('Location.X', 'Location.Y'), ('Corner.X', 'Corner.Y')] + [(f'X{i}', f'Y{i}') for i in range(1, 50)]

def rot_pt(x, y, q):
    for _ in range(q % 4): x, y = -y, x
    return x, y

class Block:
    def __init__(self, emit):
        self.emit = emit                # emit(list_of_records, own_indices_base) -> appends to sheet
        self.items = []                 # deferred draw ops (in local units)
        self.parts = []
        self.wires = []                 # list of polylines [(x,y),...]
        self.pins = []                  # absolute pin tips (x,y)

    # ---------------------------------------------------------------- parts
    def part(self, tpl, des, comment, pinmap, pin, at, rot=0, label=None):
        """label: None = legacy (labels moved right of the body only when rotated), 'keep' = template positions,
        'right' / 'left' / 'above' / 'below' / 'split' (designator above, value below) = always placed."""
        """place `tpl` rotated by rot quarter-turns (CCW) so that pin `pin` tip lands on `at`."""
        px, py, _ = tpl.pins()[pin]
        rx, ry = rot_pt(px / U, py / U, rot)
        ox, oy = at[0] - rx, at[1] - ry
        self.parts.append((tpl, des, comment, pinmap, ox, oy, rot, label))
        for p, (qx, qy, _) in tpl.pins().items():
            if p in pinmap:
                a, b = rot_pt(qx / U, qy / U, rot); self.pins.append((ox + a, oy + b))
        return {p: (ox + rot_pt(qx / U, qy / U, rot)[0], oy + rot_pt(qx / U, qy / U, rot)[1])
                for p, (qx, qy, _) in tpl.pins().items()}

    def wire(self, *pts): self.wires.append([tuple(p) for p in pts])
    def gnd(self, at, direction=3): self.items.append(('gnd', at, direction))
    def pwr(self, net, at, direction=1): self.items.append(('pwr', net, at, direction))
    def port(self, net, at, toward_left): self.items.append(('port', net, at, toward_left))
    def label(self, net, at): self.items.append(('label', net, at))
    def noerc(self, at): self.items.append(('noerc', at))

    # ---------------------------------------------------------------- render
    def render(self, ox, oy, put, out, instantiate_fn):
        """ox,oy = block origin on the sheet (10-mil units)."""
        T = lambda p: (round((p[0] + ox) * U), round((p[1] + oy) * U))
        for tpl, des, cm, pm, px, py, rot, label in self.parts:
            base = len(out)
            recs = instantiate(tpl, base, round((px + ox) * U), round((py + oy) * U), des, cm, {'Value': cm})
            cx, cy = round((px + ox) * U), round((py + oy) * U)
            if rot % 4:
                for r in recs:
                    for a, b in PAIRS:
                        if r.get(a) is not None or r.get(b) is not None:
                            if r.get(a) is None and r.get(b) is None: continue
                            x, y = getc(r, a) - cx, getc(r, b) - cy
                            x, y = rot_pt(x, y, rot)
                            setc(r, a, cx + x); setc(r, b, cy + y)
                    t = r.get('RECORD')
                    if t == '2':
                        c = int(r.get('PinConglomerate', 0)); r.set('PinConglomerate', (c & ~3) | (((c & 3) + rot) % 4))
                    elif t == '14' or t == '13' and False:
                        pass
                    if t == '14':   # rectangle: normalize corners
                        x1, y1, x2, y2 = getc(r, 'Location.X'), getc(r, 'Location.Y'), getc(r, 'Corner.X'), getc(r, 'Corner.Y')
                        setc(r, 'Location.X', min(x1, x2)); setc(r, 'Location.Y', min(y1, y2))
                        setc(r, 'Corner.X', max(x1, x2)); setc(r, 'Corner.Y', max(y1, y2))
                    elif t == '12':
                        for k in ('StartAngle', 'EndAngle'):
                            if r.get(k) is not None: r.set(k, round((float(r.get(k)) + 90 * rot) % 360, 3))
                    elif t == '1':
                        r.set('Orientation', rot % 4)
            mode = label if label is not None else ('right' if rot % 4 else 'keep')
            if mode != 'keep':
                # labels: horizontal, beside the body
                body = [(getc(r, a), getc(r, b)) for r in recs if r.get('RECORD') in ('6', '13', '14', '12', '7')
                        for a, b in PAIRS if r.get(a) is not None and r.get(b) is not None]
                for r in recs:          # arcs: add their radius (an inductor is mostly arcs)
                    if r.get('RECORD') == '12':
                        cx_, cy_, rr = getc(r, 'Location.X'), getc(r, 'Location.Y'), getc(r, 'Radius')
                        body += [(cx_ - rr, cy_ - rr), (cx_ + rr, cy_ + rr)]
                if body:
                    bx0 = min(x for x, _ in body); bx1 = max(x for x, _ in body)
                    by0 = min(y for _, y in body); by1 = max(y for _, y in body); by = (by0 + by1) // 2; bxc = (bx0 + bx1) // 2
                    vis = [r for r in recs if r.get('RECORD') in ('34', '41') and r.get('IsHidden') != 'T'
                           and (r.get('RECORD') == '34' or (r.get('Name') or '').lower() == 'comment')]
                    for r in recs:      # stray visible parameters (hashes etc.) would land far away: hide them
                        if r.get('RECORD') == '41' and r.get('IsHidden') != 'T' and r not in vis: r.set('IsHidden', 'T')
                    for r in vis:
                        r.delete('Orientation'); r.delete('Justification'); is_des = r.get('RECORD') == '34'
                        w = round(CH * len(r.get('Text') or '') * U)
                        if mode == 'right':
                            x, y = bx1 + 6 * U, by + (2 * U if is_des else -8 * U)
                        elif mode == 'left':
                            x, y = bx0 - 6 * U - w, by + (2 * U if is_des else -8 * U)
                        elif mode == 'above':
                            x, y = bxc - w // 2, by1 + (13 * U if is_des else 4 * U)
                        elif mode == 'below':
                            x, y = bxc - w // 2, by0 - (10 * U if is_des else 19 * U)
                        else:   # split
                            x, y = bxc - w // 2, (by1 + 3 * U) if is_des else (by0 - 10 * U)
                        setc(r, 'Location.X', x); setc(r, 'Location.Y', y)
            out.extend(recs)
        for pl in self.wires:
            for a, b in zip(pl, pl[1:]):
                w = put('wire'); (x1, y1), (x2, y2) = T(a), T(b)
                setc(w, 'X1', x1); setc(w, 'Y1', y1); setc(w, 'X2', x2); setc(w, 'Y2', y2)
        for it in self.items:
            if it[0] == 'gnd':
                p = put('gnd', Orientation=it[2]); x, y = T(it[1]); setc(p, 'Location.X', x); setc(p, 'Location.Y', y)
            elif it[0] == 'pwr':
                p = put('pwr', Orientation=it[3], Text=it[1]); x, y = T(it[2]); setc(p, 'Location.X', x); setc(p, 'Location.Y', y)
            elif it[0] == 'port':
                net, at, left = it[1:]; w = 5 * len(net) + 30
                p = put('port', Name=net, Width=w); x, y = T(at)
                setc(p, 'Location.X', x - w * U if left else x); setc(p, 'Location.Y', y)
            elif it[0] == 'label':
                p = put('label', Text=it[1]); x, y = T(it[2]); setc(p, 'Location.X', x); setc(p, 'Location.Y', y)
            elif it[0] == 'noerc':
                p = put('noerc'); x, y = T(it[1]); setc(p, 'Location.X', x); setc(p, 'Location.Y', y)
        for j in self.junctions():
            p = put('junction'); x, y = T(j); setc(p, 'Location.X', x); setc(p, 'Location.Y', y)

    def junctions(self):
        """points where 3+ connections meet (wire ends, pin tips, or a wire end landing mid-segment)."""
        segs = [(a, b) for pl in self.wires for a, b in zip(pl, pl[1:])]
        def on_mid(p, s):
            (x1, y1), (x2, y2) = s
            if p in s: return False
            return (x1 == x2 == p[0] and min(y1, y2) < p[1] < max(y1, y2)) or (y1 == y2 == p[1] and min(x1, x2) < p[0] < max(x1, x2))
        pts = {}
        for a, b in segs:
            for p in (a, b): pts[p] = pts.get(p, 0) + 1
        out = []
        for p, n in pts.items():
            n += sum(1 for q in self.pins if q == p)
            n += 2 * sum(1 for s in segs if on_mid(p, s))
            if n >= 3: out.append(p)
        return out

    def bbox(self):
        xs, ys = [], []
        for pl in self.wires:
            for x, y in pl: xs.append(x); ys.append(y)
        for tpl, des, cm, pm, px, py, rot, label in self.parts:
            x0, y0, x1, y1 = (v / U for v in (tpl.gbbox() if hasattr(tpl, 'gbbox') else tpl.bbox()))
            for cx, cy in ((x0, y0), (x1, y1), (x0, y1), (x1, y0)):
                a, b = rot_pt(cx, cy, rot); xs.append(px + a); ys.append(py + b)
            xs.append(px + 60)
        for it in self.items:                       # text of power ports / ports extends past their hotspot
            if it[0] == 'pwr':
                (x, y), d, n = it[2], it[3], len(it[1]) * 6 + 12
                xs.append(x + n if d == 0 else x - n if d == 2 else x); ys.append(y + 15 if d == 1 else y)
            elif it[0] == 'port':
                (x, y), w = it[2], 5 * len(it[1]) + 30
                xs.append(x - w if it[3] else x + w)
        return min(xs), min(ys), max(xs), max(ys)
