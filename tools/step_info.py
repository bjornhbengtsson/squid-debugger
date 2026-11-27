"""Read a vendor STEP model's real geometry so it can be seated on its footprint.

Uses only the points that are model vertices (VERTEX_POINT), so stray reference points do not distort the box.
  vertices(path)            -> list of (x, y, z)
  turned(pts, rot_x, rot_z) -> the points after Altium's model rotation (about X, then about Z)
  box(pts)                  -> [(min, max)] per axis
Usage: python tools/step_info.py file.stp [...]     prints the box and, per axis, where the lead feet are
"""
import re, sys, os
def vertices(path):
    t = open(path, encoding='latin-1').read()
    t = re.sub(r'\s+', ' ', t)
    cp = {m.group(1): tuple(float(v) for v in m.group(2, 3, 4)) for m in
          re.finditer(r"#(\d+) ?= ?CARTESIAN_POINT ?\( ?'[^']*' ?, ?\( ?([-+0-9.eE]+) ?, ?([-+0-9.eE]+) ?, ?([-+0-9.eE]+) ?\) ?\)", t)}
    ids = re.findall(r"VERTEX_POINT ?\( ?'[^']*' ?, ?#(\d+) ?\)", t)
    return [cp[i] for i in ids if i in cp]
def rot_x(p, deg):
    x, y, z = p
    return {0: (x, y, z), 90: (x, -z, y), 180: (x, -y, -z), 270: (x, z, -y)}[deg % 360]
def rot_z(p, deg):
    x, y, z = p
    return {0: (x, y, z), 90: (-y, x, z), 180: (-x, -y, z), 270: (y, -x, z)}[deg % 360]
def turned(pts, rx, rz): return [rot_z(rot_x(p, rx), rz) for p in pts]
def box(pts): return [(min(p[i] for p in pts), max(p[i] for p in pts)) for i in range(3)]
def seat(path, rx, rz):
    """Model state for Altium: lift dz so the lowest point is on the board, and the XY centre of the turned model
    and of the unturned model (both relative to the model origin)."""
    v = vertices(path); b0 = box(v); b = box(turned(v, rx, rz))
    return dict(dz=-b[2][0], centre=((b[0][0] + b[0][1]) / 2, (b[1][0] + b[1][1]) / 2),
                centre0=((b0[0][0] + b0[0][1]) / 2, (b0[1][0] + b0[1][1]) / 2), size=tuple(hi - lo for lo, hi in b))
if __name__ == '__main__':
    for f in sys.argv[1:]:
        v = vertices(f); b = box(v)
        print(os.path.basename(f), len(v), 'vertices; box', [(round(lo, 2), round(hi, 2)) for lo, hi in b], 'size', [round(hi - lo, 2) for lo, hi in b])
        for ax in range(3):                  # the lowest and highest 12 % along each axis: outline of what is there
            lo, hi = b[ax]; o = [i for i in range(3) if i != ax]; out = []
            for name, a0, a1 in (('low', lo, lo + 0.12 * (hi - lo)), ('high', hi - 0.12 * (hi - lo), hi)):
                sl = [p for p in v if a0 - 1e-6 <= p[ax] <= a1 + 1e-6]
                out.append('%s %d pts, %s %.2f..%.2f, %s %.2f..%.2f' % (name, len(sl), 'xyz'[o[0]], min(p[o[0]] for p in sl), max(p[o[0]] for p in sl),
                                                                      'xyz'[o[1]], min(p[o[1]] for p in sl), max(p[o[1]] for p in sl)))
            print('   along', 'xyz'[ax], '|', ' | '.join(out))
