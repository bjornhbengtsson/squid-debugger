"""Block-level sketches of the three V1 layout options -> design/V1_layout_options.svg (+ .png if PyMuPDF is installed)."""
import os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); S = 4.2
COL = {'pico': '#f6c9c9', 'pwr': '#cfe3f7', 'jack': '#f3d9a4', 'can': '#d5efd0', 'conn': '#e2d6f3', 'misc': '#e8e8e8'}
# option: (title, width, height, [(label, kind, x0, y0, x1, y1)], [circle jacks (label, x, y)], note)
A = ('A  V0 classic, two-sided  (61 x 100)', 61, 100, [
    ('Pico', 'pico', 20, 48, 41, 99), ('USB buck', 'pwr', 2, 84, 19, 99), ('VBUS limit', 'pwr', 42, 84, 59, 99),
    ('UART', 'misc', 2, 57, 19, 71), ('3V3 mux', 'pwr', 2, 41, 19, 56), ('5V mux', 'pwr', 42, 53, 59, 71),
    ('AUX/ref', 'pwr', 42, 40, 59, 52), ('CAN', 'can', 19, 35, 42, 47), ('12V sw', 'pwr', 2, 15, 18, 27),
    ('5V RF sw', 'pwr', 43, 15, 59, 27), ('DIP', 'misc', 24, 14, 37, 24), ('P4', 'conn', 12, 10, 26, 13),
    ('P3', 'conn', 35, 10, 49, 13), ('J1', 'conn', 21, 1, 40, 7)],
     [('3V3', 7.5, 77.5), ('5V', 53.5, 77.5), ('12V', 7.5, 34), ('5VRF', 53.5, 34), ('GND', 30.5, 29.5)],
     'dividers + rail enables on the bottom')
B = ('B  Power spine, two-sided  (61 x 100)', 61, 100, [
    ('Pico', 'pico', 38, 47, 59, 98), ('3V3 mux', 'pwr', 14, 80, 36, 97), ('5V mux', 'pwr', 14, 61, 36, 78),
    ('5V RF sw', 'pwr', 14, 44, 36, 59), ('12V sw', 'pwr', 14, 27, 36, 42), ('buck + VBUS limit', 'pwr', 14, 15, 36, 25),
    ('CAN', 'can', 38, 27, 59, 45), ('UART / DIP / AUX', 'misc', 38, 15, 59, 25), ('P4', 'conn', 12, 10, 26, 13),
    ('P3', 'conn', 35, 10, 49, 13), ('J1', 'conn', 21, 1, 40, 7)],
     [('3V3', 7, 88.5), ('5V', 7, 69.5), ('5VRF', 7, 50.5), ('12V', 7, 31.5), ('GND', 7, 16)],
     'jacks in one column at 19 mm pitch')
C = ('C  Wide, single-sided  (96 x 100)', 96, 100, [
    ('Pico', 'pico', 20, 48, 41, 99), ('USB buck', 'pwr', 2, 84, 19, 99), ('VBUS limit', 'pwr', 42, 84, 59, 99),
    ('UART', 'misc', 2, 57, 19, 71), ('CAN', 'can', 19, 30, 42, 47), ('DIP', 'misc', 24, 14, 37, 24),
    ('3V3 mux + dividers', 'pwr', 62, 78, 94, 98), ('5V mux + dividers', 'pwr', 62, 56, 94, 76),
    ('5V RF sw', 'pwr', 62, 40, 77, 54), ('12V sw', 'pwr', 79, 40, 94, 54), ('AUX/ref', 'pwr', 62, 26, 77, 38),
    ('rail enables', 'misc', 79, 14, 94, 38), ('P4', 'conn', 12, 10, 26, 13), ('P3', 'conn', 35, 10, 49, 13),
    ('J1', 'conn', 21, 1, 40, 7)],
     [('3V3', 9, 46), ('5V', 52, 68), ('12V', 9, 30), ('5VRF', 52, 46), ('GND', 52, 28)],
     'everything on top; 35 mm wing outside the card outline')
def draw(opt, ox):
    t, w, h, blocks, jacks, note = opt
    o = [f'<g transform="translate({ox},34)">', f'<text x="0" y="-12" font-size="14" font-weight="bold">{t}</text>',
         f'<rect width="{w*S}" height="{h*S}" rx="{5*S}" fill="#fbfaf4" stroke="#222" stroke-width="2"/>']
    for hx, hy in ((5, 5), (56, 5), (5, 95), (56, 95)):
        o.append(f'<circle cx="{hx*S}" cy="{(h-hy)*S}" r="{1.6*S}" fill="#fff" stroke="#222"/>')
    for l, k, x0, y0, x1, y1 in blocks:
        o.append(f'<rect x="{x0*S}" y="{(h-y1)*S}" width="{(x1-x0)*S}" height="{(y1-y0)*S}" fill="{COL[k]}" stroke="#555"/>')
        o.append(f'<text x="{(x0+x1)/2*S}" y="{(h-(y0+y1)/2)*S+4}" text-anchor="middle" font-size="10">{l}</text>')
    for l, x, y in jacks:
        o.append(f'<circle cx="{x*S}" cy="{(h-y)*S}" r="{5.3*S}" fill="{COL["jack"]}" stroke="#a60"/>')
        o.append(f'<text x="{x*S}" y="{(h-y)*S+4}" text-anchor="middle" font-size="10">{l}</text>')
    o.append(f'<text x="0" y="{h*S+16}" font-size="11" fill="#444">{note}</text></g>'); return o
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{(61+61+96)*S+80}" height="{100*S+62}" font-family="Arial">',
       '<rect width="100%" height="100%" fill="#fff"/>']
out += draw(A, 16) + draw(B, 61 * S + 40) + draw(C, 122 * S + 64) + ['</svg>']
p = os.path.join(ROOT, 'design', 'V1_layout_options.svg'); open(p, 'w').write('\n'.join(out))
try:
    import pymupdf; pymupdf.open(p)[0].get_pixmap(dpi=120).save(p[:-3] + 'png')
except ImportError: pass
print('wrote', p)
