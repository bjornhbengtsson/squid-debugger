"""Extract the zlib-compressed source SchLib/PcbLib streams from an Altium IntLib.
Usage: python tools/intlib_extract.py <file.IntLib> <outdir>"""
import sys, os, zlib
sys.path.insert(0, os.path.dirname(__file__))
from cfb import read_cfb
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
base = os.path.splitext(os.path.basename(src))[0]
for p, v in read_cfb(src).items():
    if v and (p.startswith('SchLib/') or p.startswith('PCBLib/')):
        for off in range(8):
            try: raw = zlib.decompress(v[off:]); break
            except Exception: raw = None
        if raw is None: print('FAIL', p); continue
        ext = '.SchLib' if p.startswith('SchLib/') else '.PcbLib'
        fn = os.path.join(out, base + ext); open(fn, 'wb').write(raw); print('wrote', fn, len(raw))
