"""Draw the docs' block diagrams as plain SVG files (docs/img/*.svg).

The GitHub mobile app shows Mermaid blocks as raw code, so each Mermaid diagram in the docs has an SVG twin made here.
The Mermaid source stays in the doc (inside a collapsed <details>) as the editable description; when you change one,
change the matching diagram below and re-run:   python tools/doc_diagrams.py
"""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'img')
FILL = {'a': '#e8f0fe', 'p': '#fdf1d6', 'g': '#e6f4ea', 'x': '#f3e8fd', 'n': '#f1f3f4'}

class Diagram:
    def __init__(self, w, h, title):
        self.w, self.h, self.title, self.items, self.boxes, self.labels = w, h, title, [], {}, []
    def box(self, key, x, y, w, h, text, kind='a'):
        self.boxes[key] = (x, y, w, h)
        lines = text.split('\n'); y0 = y + h / 2 - (len(lines) - 1) * 8 + 4
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{FILL[kind]}" stroke="#3c4043" stroke-width="1.3"/>')
        for i, l in enumerate(lines):
            wt = ' font-weight="bold"' if i == 0 else ''
            self.items.append(f'<text x="{x + w / 2}" y="{y0 + i * 16}" text-anchor="middle" font-size="13"{wt}>{l}</text>')
    def edge(self, pts, label=None, at=None, anchor='middle'):
        """pts: list of (x, y); the arrow head is at the last point. Label goes at `at` or the middle of the first segment.
        Arrow heads and label backgrounds are drawn as plain shapes so every SVG viewer shows them."""
        import math
        d = 'M' + ' L'.join(f'{x},{y}' for x, y in pts)
        self.items.append(f'<path d="{d}" fill="none" stroke="#3c4043" stroke-width="1.4"/>')
        (x1, y1), (x2, y2) = pts[-2], pts[-1]; a = math.atan2(y2 - y1, x2 - x1)
        tri = [(x2, y2)] + [(x2 - 9 * math.cos(a + s), y2 - 9 * math.sin(a + s)) for s in (0.42, -0.42)]
        self.items.append('<polygon points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in tri) + '" fill="#3c4043"/>')
        if label:
            if at is None: at = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2 - 5)
            w = len(label) * 6.1 + 6
            x0 = at[0] - w / 2 if anchor == 'middle' else at[0] - 3
            self.labels.append(f'<rect x="{x0:.1f}" y="{at[1] - 11}" width="{w:.1f}" height="14" fill="#ffffff"/>'
                               f'<text x="{at[0]}" y="{at[1]}" text-anchor="{anchor}" font-size="11" fill="#1a73e8">{label}</text>')
    def L(self, k): x, y, w, h = self.boxes[k]; return x, y + h / 2
    def R(self, k): x, y, w, h = self.boxes[k]; return x + w, y + h / 2
    def T(self, k): x, y, w, h = self.boxes[k]; return x + w / 2, y
    def B(self, k): x, y, w, h = self.boxes[k]; return x + w / 2, y + h
    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
             f'font-family="Arial, Helvetica, sans-serif" role="img" aria-label="{self.title}">',
             f'<title>{self.title}</title>',
             f'<rect width="{self.w}" height="{self.h}" fill="#ffffff"/>'] + self.items + self.labels + ['</svg>']
        open(os.path.join(OUT, name), 'w', encoding='utf-8').write('\n'.join(s)); print('wrote', name)

def overview():
    d = Diagram(1040, 400, 'Squid Debugger block diagram')
    d.box('PC', 20, 150, 120, 50, 'PC / laptop', 'n'); d.box('PSU', 20, 300, 120, 60, 'Bench PSU\nbanana jacks\nTP1-TP5', 'p')
    d.box('PICO', 200, 60, 140, 70, 'Raspberry Pi Pico\nRP2040'); d.box('LIM', 200, 215, 140, 50, 'MIC2544\n0.4 A limit', 'p')
    d.box('P2', 410, 10, 130, 40, 'P2 UART header', 'x'); d.box('MCP', 410, 75, 130, 50, 'MCP2515\nCAN controller')
    d.box('TCAN', 590, 75, 120, 50, 'TCAN330\ntransceiver'); d.box('BUCK', 410, 215, 130, 50, 'AP63203\n3.3 V buck', 'p')
    d.box('PWR', 590, 290, 130, 70, 'Power path\n4x eFuse 0.9 A\n4x TPS2121', 'p')
    d.box('J1', 780, 140, 120, 80, 'J1\nSquid Standard\nDebug Port', 'x'); d.box('TGT', 940, 155, 85, 50, 'Target\nboard', 'g')
    d.edge([(140, 165), (170, 165), (170, 95), (200, 95)], 'USB', (170, 135), 'middle')
    d.edge([(140, 185), (170, 185), (170, 240), (200, 240)], 'VBUS 5 V', (164, 262), 'middle')
    d.edge([(340, 75), (375, 75), (375, 30), (410, 30)], 'UART', (375, 22))
    d.edge([(340, 100), (410, 100)], 'SPI'); d.edge([d.R('MCP'), d.L('TCAN')])
    d.edge([(710, 100), (745, 100), (745, 160), (780, 160)], 'CAN_H / CAN_L', (745, 92))
    d.edge([(340, 120), (375, 120), (375, 180), (780, 180)], 'SWD + reset', (560, 174))
    d.edge([(270, 130), (270, 200), (655, 200), (655, 290)], 'EN / ADC / status', (460, 194))
    d.edge([d.R('LIM'), d.L('BUCK')], '+VBUS_PROT'); d.edge([(540, 240), (620, 240), (620, 290)], '+3V3_USB', (585, 234))
    d.edge([(270, 265), (270, 310), (590, 310)], '+VBUS_PROT', (430, 304))
    d.edge([(140, 340), (590, 340)], '+3V3 / +5V / +5V_RF / +12V _PSU', (365, 334))
    d.edge([(720, 325), (840, 325), (840, 220)], '3V3 / 5V / 5V_RF / 12V', (790, 345))
    d.edge([d.R('J1'), d.L('TGT')])
    d.save('overview-block.svg')

def sources():
    d = Diagram(960, 400, 'Power sources and the four rail switches')
    d.box('TP', 20, 60, 150, 90, 'Banana jacks\n+3V3_PSU  +5V_PSU\n+5V_RF_PSU\n+12V_PSU', 'p'); d.box('TVS', 205, 80, 110, 50, 'TVS clamps\nD4-D7', 'p'); d.box('LIM', 365, 72, 150, 66, 'U14-U17 eFuses\nTPS259621\n0.9 A limit each', 'p')
    d.box('VBUS', 20, 300, 150, 45, 'USB VBUS', 'n'); d.box('U4', 220, 295, 130, 55, 'U4 MIC2544\n0.4 A limit', 'p')
    d.box('U13', 420, 295, 130, 55, 'U13 AP63203\nbuck', 'p')
    for i, (k, t) in enumerate((('M3', 'U3  3V3 mux'), ('M5', 'U5  5V mux'), ('M7', 'U7  5V_RF switch'), ('M8', 'U8  12V switch'))):
        d.box(k, 640, 20 + i * 70, 150, 50, t)
    d.box('J1', 870, 20, 70, 260, 'J1', 'x')
    d.edge([d.R('TP'), d.L('TVS')]); d.edge([d.R('TVS'), d.L('LIM')]); d.edge([d.R('VBUS'), d.L('U4')]); d.edge([d.R('U4'), d.L('U13')], '+VBUS_PROT')
    for i, k in enumerate(('M3', 'M5', 'M7', 'M8')):
        y = 35 + i * 70
        d.edge([(515, 105), (590, 105), (590, y), (640, y)], '+x_LIM' if i == 0 else None, (552, 99))
    d.edge([(550, 322), (610, 322), (610, 58), (640, 58)], '+3V3_USB', (580, 316))
    d.edge([(385, 322), (385, 375), (625, 375), (625, 128), (640, 128)], '+VBUS_PROT', (505, 369))
    for i, (k, n) in enumerate((('M3', '+3V3_TGT'), ('M5', '+5V_TGT'), ('M7', '+5V_RF_TGT'), ('M8', '+12V_TGT'))):
        y = 45 + i * 70
        d.edge([(790, y), (870, y)], n, (830, y - 6))
    d.save('power-sources.svg')

def onoff():
    d = Diagram(820, 300, 'Rail on/off control: DIS_x forces the TPS2121 OV pins high')
    d.box('AUX', 20, 30, 130, 45, '+3V3_AUX\nalways on', 'p'); d.box('DIS', 300, 30, 130, 45, 'DIS_x\nhigh = rail OFF', 'x')
    d.box('OV', 600, 30, 190, 45, 'OV1 / OV2 of the mux\nabove VREF = OFF')
    d.box('EN', 20, 140, 130, 45, 'Pico EN_x\nhigh = rail ON', 'a'); d.box('Q', 300, 140, 130, 55, '2N7002\ngate: 100k to GND\ndrain on DIS_x', 'n')
    d.box('SW', 20, 235, 130, 45, 'DIP switch SW1\nposition n', 'g')
    d.edge([d.R('AUX'), d.L('DIS')], '4.7k pull-up'); d.edge([d.R('DIS'), d.L('OV')], 'BAT54A')
    d.edge([d.R('EN'), d.L('Q')], '100R'); d.edge([(400, 140), (400, 77)], 'pulls DIS_x to GND', (408, 112), 'start')
    d.edge([(150, 257), (330, 257), (330, 77)], 'shorts DIS_x to GND (manual ON)', (240, 251))
    d.save('power-onoff.svg')

if __name__ == '__main__':
    overview(); sources(); onoff()
