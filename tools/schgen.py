"""Generate an Altium SchDoc from a parts+nets spec, using components already placed in existing SchDocs
as templates. Output style: every pin gets a short wire stub ending in a net label (or GND power port).

Library-free: reads/writes the CFB container and the |KEY=VALUE| record stream directly.
"""
import struct, random, string, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from cfb import read_cfb, records

FRAC = 100000  # Altium coordinate fraction units per 10-mil unit

# ---------------------------------------------------------------- records (order-preserving)
class Rec:
    def __init__(self, raw):
        t = raw.rstrip(b'\0').decode('latin-1')
        segs = t.split('|')[1:] if t.startswith('|') else t.split('|')
        self.kv = [s.split('=', 1) if '=' in s else [s, None] for s in segs]
    def get(self, k, d=None):
        for kk, v in self.kv:
            if v is not None and kk.upper() == k.upper(): return v
        return d
    def set(self, k, v, after=None):
        for p in self.kv:
            if p[1] is not None and p[0].upper() == k.upper(): p[1] = str(v); return
        if after is not None:
            for i, p in enumerate(self.kv):
                if p[1] is not None and p[0].upper() == after.upper(): self.kv.insert(i + 1, [k, str(v)]); return
        self.kv.append([k, str(v)])
    def delete(self, k):
        self.kv = [p for p in self.kv if not (p[1] is not None and p[0].upper() == k.upper())]
    def copy(self):
        r = Rec(b''); r.kv = [list(p) for p in self.kv]; return r
    def bytes(self):
        return ('|' + '|'.join(k if v is None else f'{k}={v}' for k, v in self.kv)).encode('latin-1') + b'\0'

def load(path):
    fs = read_cfb(path)
    raws = records(fs['FileHeader'])
    return fs, [Rec(r) for r in raws]   # index 0 = HEADER, OWNERINDEX counts from 1 == list index here

def uid():
    return ''.join(random.choice(string.ascii_uppercase) for _ in range(8))

# coordinate helpers (total units = int*FRAC + frac)
COORD = re.compile(r'^(LOCATION\.X|LOCATION\.Y|CORNER\.X|CORNER\.Y|X\d+|Y\d+)$', re.I)
def getc(r, k):
    return int(r.get(k, 0)) * FRAC + int(r.get(k + '_FRAC', 0))
def setc(r, k, tot):
    i, f = divmod(tot, FRAC)
    r.set(k, i)
    if f: r.set(k + '_FRAC', f, after=k)
    else: r.delete(k + '_FRAC')

# ---------------------------------------------------------------- CFB writer
def write_cfb(path, streams):
    """streams: dict name->bytes (flat, no storages)."""
    SS, MSS, CUT = 512, 64, 4096
    END, FREE, FATS = 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFD
    names = sorted(streams, key=lambda n: (len(n), n.upper()))
    small = [n for n in names if len(streams[n]) < CUT]
    big = [n for n in names if len(streams[n]) >= CUT]
    # mini stream
    mini, minifat, mstart = b'', [], {}
    for n in small:
        d = streams[n]; k = (len(d) + MSS - 1) // MSS
        mstart[n] = len(minifat) if d else END
        for j in range(k): minifat.append(len(minifat) + 1 if j < k - 1 else END)
        mini += d + b'\0' * (k * MSS - len(d))
    nsec = lambda b: (b + SS - 1) // SS
    ndir = nsec(128 * (1 + len(names)))
    nminifat = nsec(4 * len(minifat)) if minifat else 0
    nmini = nsec(len(mini))
    nbig = {n: nsec(len(streams[n])) for n in big}
    body = ndir + nminifat + nmini + sum(nbig.values())
    nfat = 1
    while nfat * 128 < body + nfat: nfat += 1
    assert nfat <= 109
    fat = [FATS] * nfat
    def chain(k):
        s = len(fat)
        for j in range(k): fat.append(len(fat) + 1 if j < k - 1 else END)
        return s if k else END
    dir_s = chain(ndir); mf_s = chain(nminifat); ms_s = chain(nmini)
    big_s = {n: chain(nbig[n]) for n in big}
    fat += [FREE] * (nfat * 128 - len(fat))
    # directory: root + binary tree (all black) over sorted names
    ents = [None] * (1 + len(names))
    idx = {n: i + 1 for i, n in enumerate(names)}
    left = {}; right = {}
    def build(lo, hi):
        if lo > hi: return 0xFFFFFFFF
        m = (lo + hi) // 2
        left[m] = build(lo, m - 1); right[m] = build(m + 1, hi)
        return m + 1
    root_child = build(0, len(names) - 1)
    def entry(name, typ, l, r, c, start, size):
        nm = name.encode('utf-16-le') + b'\0\0'
        e = nm + b'\0' * (64 - len(nm))
        e += struct.pack('<HBBIII', len(nm), typ, 1, l, r, c)
        e += b'\0' * 16 + b'\0' * 4 + b'\0' * 16 + struct.pack('<IQ', start, size)
        return e
    d = entry('Root Entry', 5, 0xFFFFFFFF, 0xFFFFFFFF, root_child, ms_s if mini else END, len(mini))
    for i, n in enumerate(names):
        st = mstart[n] if n in mstart else big_s[n]
        d += entry(n, 2, left[i], right[i], 0xFFFFFFFF, st, len(streams[n]))
    d += b'\0' * (ndir * SS - len(d))
    hdr = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' + b'\0' * 16 + struct.pack('<HHHHH', 0x3E, 3, 0xFFFE, 9, 6)
    hdr += b'\0' * 6 + struct.pack('<IIIIIIIII', 0, nfat, dir_s, 0, CUT, mf_s if nminifat else END, nminifat, END, 0)
    difat = list(range(nfat)) + [FREE] * (109 - nfat)
    hdr += struct.pack('<109I', *difat)
    out = hdr
    out += struct.pack('<%dI' % len(fat), *fat)
    out += d
    if nminifat:
        mf = struct.pack('<%dI' % len(minifat), *minifat); out += mf + b'\xff' * (nminifat * SS - len(mf))
    out += mini + b'\0' * (nmini * SS - len(mini))
    for n in big:
        b = streams[n]; out += b + b'\0' * (nbig[n] * SS - len(b))
    open(path, 'wb').write(out)

def stream_from(recs):
    # HEADER 'Weight' = number of records after the header; Altium reads exactly that many
    if recs and recs[0].get('HEADER'): recs[0].set('Weight', len(recs) - 1)
    out = b''
    for r in recs:
        b = r.bytes(); out += struct.pack('<I', len(b)) + b
    return out

# ---------------------------------------------------------------- component cloning
def subtree(recs, ci):
    """indices of records owned (transitively) by component record ci, in file order."""
    own = {ci}; changed = True
    while changed:
        changed = False
        for i, r in enumerate(recs):
            o = r.get('OwnerIndex')
            if o is not None and int(o) + 1 in own and i not in own: own.add(i); changed = True
    return sorted(own)

def find_comp(recs, libref):
    for i, r in enumerate(recs):
        if r.get('RECORD') == '1' and r.get('LibReference') == libref: return i
    raise KeyError(libref)

class Template:
    def __init__(self, recs, ci, fontmap=None):
        self.recs = [recs[i].copy() for i in subtree(recs, ci)]
        old = subtree(recs, ci); self.local = {o: k for k, o in enumerate(old)}
        for r in self.recs:
            if fontmap and r.get('FontID') in fontmap: r.set('FontID', fontmap[r.get('FontID')])
        c = self.recs[0]
        self.x0, self.y0 = getc(c, 'Location.X'), getc(c, 'Location.Y')
    def pins(self):
        out = {}
        for r in self.recs:
            if r.get('RECORD') == '2':
                x, y = getc(r, 'Location.X'), getc(r, 'Location.Y')
                L = getc(r, 'PinLength'); rot = int(r.get('PinConglomerate', 0)) & 3
                dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][rot]
                out[r.get('Designator')] = (x + dx * L - self.x0, y + dy * L - self.y0, rot)
        return out
    def bbox(self):
        xs, ys = [], []
        for r in self.recs:
            for k, v in r.kv:
                if v is not None and COORD.match(k):
                    (xs if 'X' in k.upper() else ys).append(getc(r, k) - (self.x0 if 'X' in k.upper() else self.y0))
        for _, (x, y, _) in self.pins().items(): xs.append(x); ys.append(y)
        return min(xs), min(ys), max(xs), max(ys)

def instantiate(tpl, base_index, x, y, des, comment=None, params=None):
    """returns records for one instance placed with origin at (x,y) [total units]."""
    dx, dy = x - tpl.x0, y - tpl.y0
    out = []
    for k, r in enumerate(tpl.recs):
        r = r.copy()
        for kk, vv in list(r.kv):
            if vv is not None and COORD.match(kk): setc(r, kk, getc(r, kk) + (dx if 'X' in kk.upper() else dy))
        o = r.get('OwnerIndex')
        if o is not None and k > 0:
            # owners inside template: remap via local positions
            r.set('OwnerIndex', base_index + tpl.local[int(o) + 1] - 1)
        if r.get('UniqueID'): r.set('UniqueID', uid())
        if r.get('RECORD') == '34': r.set('Text', des)
        if r.get('RECORD') == '41' and (r.get('Name', '').lower() == 'comment') and comment is not None: r.set('Text', comment)
        if r.get('RECORD') == '41' and params and r.get('Name') in params: r.set('Text', params[r.get('Name')])
        out.append(r)
    out[0].delete('IndexInSheet')
    return out
