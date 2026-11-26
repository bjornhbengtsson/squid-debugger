"""List symbol pins and footprint names in Altium SchLib / IntLib files (read-only).
Usage: python tools/libpins.py <file.SchLib|file.IntLib> ...
"""
import sys, os, struct, zlib, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from cfb import read_cfb, records

ETYPE = ['Input', 'IO', 'Output', 'OpenCollector', 'Passive', 'HiZ', 'OpenEmitter', 'Power']

def pstr(b, i):
    n = b[i]; return b[i + 1:i + 1 + n].decode('latin-1'), i + 1 + n

def pins_from_data(data):
    pins, comp, fps = [], {}, []
    for r in records(data):
        if r[:4] == b'\x02\x00\x00\x00':          # binary pin record
            i = 4 + 1 + 2 + 1 + 4                  # unknown, ownerpart, displaymode, 4 symbol bytes
            desc, i = pstr(r, i)
            i += 1                                 # formal type
            et = r[i]; i += 1
            i += 1 + 2 + 2 + 2 + 4                 # conglomerate, length, x, y, colour
            name, i = pstr(r, i)
            des, i = pstr(r, i)
            pins.append((des, name.replace('\\', ''), ETYPE[et] if et < 8 else et))
        else:
            t = r.rstrip(b'\0').decode('latin-1', 'replace')
            d = dict(kv.split('=', 1) for kv in t.split('|') if '=' in kv)
            if d.get('RECORD') == '1': comp = d
            if d.get('RECORD') == '45' and d.get('ModelType', d.get('MODELTYPE')) in ('PCBLIB',):
                fps.append(d.get('ModelName', d.get('MODELNAME')))
    return comp, pins, fps

def schlib(fs):
    out = []
    for p, v in fs.items():
        if p.endswith('/Data') and v is not None:
            comp, pins, fps = pins_from_data(v)
            out.append((p[:-5], comp.get('LibReference', comp.get('LIBREFERENCE', '?')), pins, fps))
    return out

def open_lib(path):
    fs = read_cfb(path)
    if path.lower().endswith('.intlib'):
        res = []
        for p, v in fs.items():
            if p.startswith('SchLib/') and v:
                raw = None
                for off in range(0, 8):
                    try: raw = zlib.decompress(v[off:]); break
                    except Exception: pass
                if raw is None: res.append((p, 'decompress failed', [], [])); continue
                tf = tempfile.NamedTemporaryFile(delete=False, suffix='.schlib'); tf.write(raw); tf.close()
                res += schlib(read_cfb(tf.name)); os.unlink(tf.name)
        return res
    return schlib(fs)

if __name__ == '__main__':
    for f in sys.argv[1:]:
        print('==', os.path.basename(f))
        for st, ref, pins, fps in open_lib(f):
            print(f'  {ref}  footprints={fps}')
            for d, n, e in sorted(pins, key=lambda x: (len(x[0]), x[0])):
                print(f'     {d:>3} {n:<12} {e}')
