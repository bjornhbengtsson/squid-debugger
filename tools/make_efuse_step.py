"""Write a simplified STEP model of the TPS259621 package (TI DDA, HSOIC-8 with thermal pad).

No vendor model is in the repo, so this draws the package from its datasheet dimensions as plain boxes: body
4.9 x 3.9 x 1.65 mm, eight gull-wing leads on 1.27 mm pitch (6.0 mm tip to tip), thermal pad 2.4 x 3.1 mm and a
pin-1 dot. Z is up, the board surface is z = 0, pins run along Y with pin 1 at -X / +Y, matching the footprint
SOIC127P600X170-9N. Run:   python tools/make_efuse_step.py
"""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hardware', 'Libraries', 'SquidDebugger_V1', '3D',
                   'TPS259621DDAR_simplified.step')
BLACK, METAL, WHITE = (0.12, 0.12, 0.12), (0.80, 0.80, 0.82), (0.92, 0.92, 0.92)

boxes = [((-1.95, -2.45, 0.05), (1.95, 2.45, 1.70), BLACK),          # body
         ((-1.20, -1.55, 0.00), (1.20, 1.55, 0.05), METAL),          # thermal pad
         ((-1.55, 1.55, 1.70), (-1.15, 1.95, 1.72), WHITE)]          # pin-1 dot
for i in range(4):
    y = 1.905 - 1.27 * i
    for s in (-1, 1):
        for x1, x2, z1, z2 in ((2.45, 3.00, 0.00, 0.20), (2.25, 2.45, 0.00, 0.95), (1.95, 2.25, 0.75, 0.95)):   # foot, riser, shoulder
            xa, xb = sorted((s * x1, s * x2))
            boxes.append(((xa, y - 0.21, z1), (xb, y + 0.21, z2), METAL))

E = []
def add(s): E.append(s); return f'#{len(E)}'
def f(v): return ('%.6f' % v).rstrip('0').rstrip('.') if abs(v) > 1e-9 else '0.'
def pt(p): return add(f"CARTESIAN_POINT('',({f(p[0])},{f(p[1])},{f(p[2])}))")
def dr(d): return add(f"DIRECTION('',({f(d[0])},{f(d[1])},{f(d[2])}))")

ctx_app = add("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,{ctx_app})")
pc = add(f"PRODUCT_CONTEXT('',{ctx_app},'mechanical')")
prod = add(f"PRODUCT('TPS259621DDAR','TPS259621DDAR simplified','',({pc}))")
pdf = add(f"PRODUCT_DEFINITION_FORMATION('','',{prod})")
pdc = add(f"PRODUCT_DEFINITION_CONTEXT('part definition',{ctx_app},'design')")
pd = add(f"PRODUCT_DEFINITION('design','',{pdf},{pdc})")
pds = add(f"PRODUCT_DEFINITION_SHAPE('','',{pd})")
lu = add("(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))")
au = add("(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))")
su = add("(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())")
unc = add(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-6),{lu},'distance_accuracy_value','')")
ctx = add(f"(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT(({unc}))"
          f"GLOBAL_UNIT_ASSIGNED_CONTEXT(({lu},{au},{su}))REPRESENTATION_CONTEXT('',''))")
origin = add(f"AXIS2_PLACEMENT_3D('',{pt((0, 0, 0))},{dr((0, 0, 1))},{dr((1, 0, 0))})")

FACES = [((0, 0, -1), (1, 0, 0), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)]),
         ((0, 0, 1), (1, 0, 0), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
         ((-1, 0, 0), (0, 1, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
         ((1, 0, 0), (0, 1, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
         ((0, -1, 0), (0, 0, 1), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
         ((0, 1, 0), (0, 0, 1), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)])]

def box(lo, hi):
    P = lambda k: tuple(hi[a] if k[a] else lo[a] for a in range(3))
    keys = [(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    cp = {k: pt(P(k)) for k in keys}
    vx = {k: add(f"VERTEX_POINT('',{cp[k]})") for k in keys}
    edge = {}
    for a in keys:
        for b in keys:
            if a < b and sum(x != y for x, y in zip(a, b)) == 1:
                pa, pb = P(a), P(b); d = [pb[n] - pa[n] for n in range(3)]; L = sum(abs(x) for x in d)
                vec = add(f"VECTOR('',{dr([x / L for x in d])},{f(L)})")
                ln = add(f"LINE('',{cp[a]},{vec})")
                edge[(a, b)] = add(f"EDGE_CURVE('',{vx[a]},{vx[b]},{ln},.T.)")
    faces = []
    for n, ref, cyc in FACES:
        oe = []
        for m in range(4):
            a, b = cyc[m], cyc[(m + 1) % 4]
            oe.append(add(f"ORIENTED_EDGE('',*,*,{edge[(a, b)] if a < b else edge[(b, a)]},{'.T.' if a < b else '.F.'})"))
        loop = add(f"EDGE_LOOP('',({','.join(oe)}))")
        bound = add(f"FACE_OUTER_BOUND('',{loop},.T.)")
        plane = add(f"PLANE('',{add(f'AXIS2_PLACEMENT_3D({chr(39)}{chr(39)},{cp[cyc[0]]},{dr(n)},{dr(ref)})')})")
        faces.append(add(f"ADVANCED_FACE('',({bound}),{plane},.T.)"))
    shell = add(f"CLOSED_SHELL('',({','.join(faces)}))")
    return add(f"MANIFOLD_SOLID_BREP('',{shell})")

solids, styled, colours = [], [], {}
for lo, hi, col in boxes:
    s = box(lo, hi); solids.append(s)
    if col not in colours:
        c = add(f"COLOUR_RGB('',{f(col[0])},{f(col[1])},{f(col[2])})")
        fa = add(f"FILL_AREA_STYLE('',({add(f'FILL_AREA_STYLE_COLOUR({chr(39)}{chr(39)},{c})')}))")
        ss = add(f"SURFACE_SIDE_STYLE('',({add(f'SURFACE_STYLE_FILL_AREA({fa})')}))")
        colours[col] = add(f"PRESENTATION_STYLE_ASSIGNMENT(({add(f'SURFACE_STYLE_USAGE(.BOTH.,{ss})')}))")
    styled.append(add(f"STYLED_ITEM('',({colours[col]}),{s})"))
rep = add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('',({origin},{','.join(solids)}),{ctx})")
add(f"SHAPE_DEFINITION_REPRESENTATION({pds},{rep})")
add(f"MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({','.join(styled)}),{ctx})")

head = ["ISO-10303-21;", "HEADER;", "FILE_DESCRIPTION(('simplified HSOIC-8 (TI DDA) package model, boxes only'),'2;1');",
        "FILE_NAME('TPS259621DDAR_simplified.step','2026-11-27T00:00:00',(''),(''),'tools/make_efuse_step.py','','');",
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));", "ENDSEC;", "DATA;"]
with open(OUT, 'w', encoding='ascii', newline='\n') as fh:
    fh.write('\n'.join(head + [f'#{i + 1}={e};' for i, e in enumerate(E)] + ['ENDSEC;', 'END-ISO-10303-21;', '']))
print('wrote', os.path.normpath(OUT), len(boxes), 'solids', len(E), 'entities')
