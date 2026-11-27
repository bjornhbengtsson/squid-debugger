"""Turn Altium's Smart PDF of the project into the repo's schematic pictures.

In Altium: File > Smart PDF > Current Project > Finish (writes "hardware/Debugging Board V1.pdf"). Then:
    python tools/sch_images.py
Writes screenshots/V1_sheetN_<name>.png for each schematic sheet (250 dpi, white border trimmed) and
screenshots/V1_schematic.pdf with the schematic pages only, in sheet order. PCB pages in the PDF are skipped.
"""
import os, sys
import pymupdf
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'hardware', 'Debugging Board V1.pdf')
OUT = os.path.join(ROOT, 'screenshots')
SHEETS = ['DebugBoard', 'DebugBoardMuxes', 'DebugBoardPowerControl', 'DebugBoard3V3Mux', 'DebugBoard5VMux', 'DebugBoardLimiters']

doc = pymupdf.open(SRC); found = {}
for i, page in enumerate(doc):
    text = page.get_text()
    for name in sorted(SHEETS, key=len, reverse=True):          # longest first: "DebugBoard" is a prefix of the others
        if name + '.SchDoc' in text:
            found.setdefault(name, i); break
missing = [s for s in SHEETS if s not in found]
if missing: sys.exit('sheets not found in the PDF: %s' % missing)
out = pymupdf.open()
for n, name in enumerate(SHEETS, 1):
    page = doc[found[name]]
    pix = page.get_pixmap(dpi=250, alpha=False)
    import numpy as np
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    ink = (a < 245).any(axis=2); ys, xs = np.nonzero(ink)
    x0, y0, x1, y1 = max(xs.min() - 12, 0), max(ys.min() - 12, 0), min(xs.max() + 12, pix.width), min(ys.max() + 12, pix.height)
    k = 72 / 250.0
    clip = pymupdf.Rect(page.rect.x0 + x0 * k, page.rect.y0 + y0 * k, page.rect.x0 + x1 * k, page.rect.y0 + y1 * k)
    path = os.path.join(OUT, 'V1_sheet%d_%s.png' % (n, name))
    page.get_pixmap(dpi=250, clip=clip, alpha=False).save(path)
    out.insert_pdf(doc, from_page=found[name], to_page=found[name])
    print('sheet', n, name, 'page', found[name] + 1, '->', os.path.basename(path))
out.save(os.path.join(OUT, 'V1_schematic.pdf'), garbage=3, deflate=True)
print('wrote V1_schematic.pdf with', len(SHEETS), 'pages')
