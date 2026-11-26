"""Minimal read-only Compound File Binary reader + Altium SchDoc record dumper."""
import struct, sys

def read_cfb(path):
    d = open(path, 'rb').read()
    ss = 1 << struct.unpack_from('<H', d, 30)[0]
    mss = 1 << struct.unpack_from('<H', d, 32)[0]
    nfat, dirstart, _, mincut, ministart, nmini, difstart, ndif = struct.unpack_from('<IIIIIIII', d, 44)
    sec = lambda i: d[(i + 1) * ss:(i + 2) * ss]
    difat = list(struct.unpack_from('<109I', d, 76))
    s = difstart
    for _ in range(ndif):
        b = sec(s); difat += list(struct.unpack_from('<%dI' % (ss // 4 - 1), b)); s = struct.unpack_from('<I', b, ss - 4)[0]
    fat = []
    for f in difat[:nfat]:
        fat += list(struct.unpack_from('<%dI' % (ss // 4), sec(f)))
    def chain(s):
        out = []
        while s < 0xFFFFFFFA: out.append(sec(s)); s = fat[s]
        return b''.join(out)
    dr = chain(dirstart)
    ents = []
    for i in range(len(dr) // 128):
        e = dr[i * 128:(i + 1) * 128]
        nl = struct.unpack_from('<H', e, 64)[0]
        name = e[:max(nl - 2, 0)].decode('utf-16le')
        typ = e[66]; l, r, c = struct.unpack_from('<III', e, 68)
        st, size = struct.unpack_from('<II', e, 116)
        ents.append(dict(name=name, typ=typ, l=l, r=r, c=c, st=st, size=size))
    root = ents[0]; ministream = chain(root['st'])
    minifat = list(struct.unpack_from('<%dI' % (len(chain(ministart)) // 4), chain(ministart))) if nmini else []
    def data(e):
        if e['size'] < mincut:
            out = []; s = e['st']
            while s < 0xFFFFFFFA: out.append(ministream[s * mss:(s + 1) * mss]); s = minifat[s]
            return b''.join(out)[:e['size']]
        return chain(e['st'])[:e['size']]
    # build paths
    paths = {}
    def walk(i, prefix):
        if i == 0xFFFFFFFF: return
        e = ents[i]; walk(e['l'], prefix); walk(e['r'], prefix)
        p = prefix + e['name']; paths[p] = e
        if e['typ'] == 1: walk(e['c'], p + '/')
    walk(root['c'], '')
    return {p: (data(e) if e['typ'] == 2 else None) for p, e in paths.items()}

def records(b):
    i = 0; out = []
    while i + 4 <= len(b):
        n = struct.unpack_from('<I', b, i)[0]; ln = n & 0xFFFFFF; i += 4
        out.append(b[i:i + ln]); i += ln
    return out

if __name__ == '__main__':
    fs = read_cfb(sys.argv[1])
    if len(sys.argv) == 2:
        for p, v in fs.items(): print(p, None if v is None else len(v))
    else:
        for k, r in enumerate(records(fs[sys.argv[2]])):
            print(k, r.rstrip(b'\0').decode('latin-1'))
