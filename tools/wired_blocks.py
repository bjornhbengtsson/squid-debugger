"""Hand-laid ('wired') layouts for every power block. Imported by gen_sheet2.py, which supplies
T (part templates), SPEC (designator -> (template, comment, pin->net)) and blocks (title -> parts).

Coordinates are 10-mil units relative to each block's origin; tools/wired.py renders them.
Style: rails are power-port symbols, sheet-crossing signals are ports, parts hang off the wires,
no wire crossings, junction dots where three or more connections meet.
"""
from wired import Block

def make(T, SPEC, blocks):
    def P(B, des, pin, at, rot=0):
        tk, cm, pm = SPEC[des]; return B.part(T[tk], des, cm, pm, pin, at, rot)

    def VG(B, des, at):
        """vertical 2-pin part: pin 1 up at `at`, GND symbol on pin 2 (works for any template orientation)."""
        tk = SPEC[des][0]; rot = (1 - T[tk].pins()['1'][2]) % 4
        pins = P(B, des, '1', at, rot); B.gnd(pins['2']); return pins

    def parts_of(title):
        return next(parts for tt, parts in blocks if tt == title)

    def mux(title):
        """TPS2121. Dual-input (3V3/5V): IN1 = PSU preferred over IN2 = USB. Single-input (5V RF/12V)."""
        ps = parts_of(title); d = [p[1] for p in ps]; pins = ps[0][3]
        in1, in2, out = pins['7'], pins['2'], pins['1']; dual = in2 != 'GND'
        if dual:
            U, CIN1, CIN2, RT, RB, RH, RPU, ZEN, RO2T, RO2B, BAT, RO1T, RO1B, RILM, CSS, CO1, CO2 = d
        else:
            U, CIN1, BAT, RO1T, RO1B, RILM, CSS, CO1, CO2 = d
        tag = SPEC[RILM][2]['1'].split('_', 1)[1]
        sense = SPEC[RO1T][2]['1']          # dividers watch the jack side (x_PSU); IN1 itself is the limited rail (x_LIM)
        B = Block(None)
        P(B, U, '7', (0, 0))
        xl = -360 if dual else -230; xc = xl + 40
        # IN1 enters above IN2; its input cap hangs off the line
        B.wire((0, 0), (-30, 0), (-30, 50), (xl, 50), (xl, 70)); B.pwr(in1, (xl, 70), 1)
        VG(B, CIN1, (xc, 50))
        if dual:
            B.wire((0, -10), (xl - 40, -10), (xl - 40, 10)); B.pwr(in2, (xl - 40, 10), 1)
            VG(B, CIN2, (xc, -10))
            B.wire((0, -70), (-30, -70)); B.pwr('XREF_2V5', (-30, -70), 2)
            # divider stacks: rail -> R -> node -> R -> GND; node wired back to its pin
            B.wire((0, -30), (-265, -30), (-265, -200), (-300, -200))
            P(B, RO1T, '2', (-300, -200), 1); B.pwr(sense, (-300, -160), 1)
            P(B, RO1B, '1', (-300, -200), 1); B.gnd((-300, -240))
            B.wire((0, -40), (-190, -40), (-190, -200), (-225, -200))
            P(B, RO2T, '2', (-225, -200), 1); B.pwr(in2, (-225, -160), 1)
            P(B, RO2B, '1', (-225, -200), 1); B.gnd((-225, -240))
            B.wire((0, -90), (-115, -90), (-115, -200), (-150, -200))
            P(B, RT, '2', (-150, -200), 1); B.pwr(sense, (-150, -160), 1)
            P(B, RB, '1', (-150, -200), 1); B.gnd((-150, -240))
            B.wire((-115, -200), (-85, -200)); P(B, ZEN, '3', (-85, -200), 3); B.gnd((-85, -240))
            B.wire((-115, -150), (-80, -150)); P(B, RH, '1', (-80, -150), 2)
            # disable diodes (two identical diodes): K1 = OV2, K2 = OV1
            B.wire((-265, -200), (-265, -280), (-40, -280))
            B.wire((-190, -200), (-190, -270), (-40, -270))
        else:
            for y in (-10, -40, -70, -90):                  # IN2, OV2, CP2, PR1 unused -> GND
                B.wire((0, y), (-20, y)); B.gnd((-20, y), 2)
            B.wire((0, -30), (-90, -30), (-90, -200), (-120, -200))
            P(B, RO1T, '2', (-120, -200), 1); B.pwr(sense, (-120, -160), 1)
            P(B, RO1B, '1', (-120, -200), 1); B.gnd((-120, -240))
            B.wire((-90, -200), (-90, -270), (-40, -270))
        P(B, BAT, '1', (-40, -270), 0); B.wire((70, -270), (100, -270)); B.port(f'DIS_{tag}', (100, -270), False)
        # right: OUT rail + output caps, ILM, SS, ST, GND
        xo, (c1, c2), xi, xs = (520, (400, 470), 320, 200) if dual else (430, (300, 380), 240, 190)
        B.wire((130, 0), (160, 0)); B.wire((130, -10), (160, -10), (160, 0))
        B.wire((160, 0), (xo - 10, 0), (xo - 10, 20)); B.pwr(out, (xo - 10, 20), 1)
        VG(B, CO1, (c1, 0)); VG(B, CO2, (c2, 0))
        B.wire((130, -30), (xi, -30)); P(B, RILM, '1', (xi, -30), 1); B.gnd((xi, -70))
        B.wire((130, -50), (xs, -50)); VG(B, CSS, (xs, -50))
        if dual:
            B.wire((130, -100), (150, -100)); B.gnd((150, -100))
            B.wire((130, -70), (170, -70), (170, -150), (300, -150)); B.wire((-40, -150), (170, -150))
            P(B, RPU, '1', (250, -150), 3); B.pwr('+3V3_AUX', (250, -110), 1)
            B.port(f'ST_{tag}', (300, -150), False)
            labels = [(f'OV1_{tag}', (-255, -30)), (f'OV2_{tag}', (-180, -40)), (f'PR1_{tag}', (-105, -90))]
        else:   # ST unused -> GND (tied to the GND pin)
            B.wire((130, -70), (150, -70), (150, -100)); B.wire((130, -100), (150, -100)); B.gnd((150, -100))
            labels = [(f'OV1_{tag}', (-80, -30))]
        for net, at in labels + [(f'ILM_{tag}', (180, -30)), (f'SS_{tag}', (165, -50))]:
            B.label(net, at)
        return B

    def inputs():
        B = Block(None)
        for i, (tk, des, cm, pm) in enumerate(parts_of('Bench Inputs')):
            x = i * 110; P(B, des, 'C', (x, 0), 3); B.pwr(pm['C'], (x, 0), 1); B.gnd((x, -40))
        return B

    def aux():
        B = Block(None)
        D8, D9, D10, C27, U9, C28, R13, U10, C29 = (p[1] for p in parts_of('AUX Supply & 2.5V Reference'))
        for dd, y in ((D8, 40), (D9, -10), (D10, -60)):     # VAUX = Schottky OR of every input
            P(B, dd, '1', (-300, y)); pm = SPEC[dd][2]
            if pm['1'] == pm['2']:
                B.wire((-300, y), (-320, y), (-320, y - 10), (-300, y - 10)); B.wire((-320, y), (-340, y))
                B.pwr(pm['1'], (-340, y), 2)
            else:
                B.wire((-300, y), (-330, y)); B.pwr(pm['1'], (-330, y), 2)
                B.wire((-300, y - 10), (-330, y - 10)); B.pwr(pm['2'], (-330, y - 10), 2)
            B.wire((-120, y), (-80, y))
        B.wire((-80, 60), (-80, -60)); B.pwr('VAUX', (-80, 60), 1)
        B.wire((-80, 0), (0, 0)); VG(B, C27, (-40, 0))
        P(B, U9, '2', (0, 0)); B.wire((100, -50), (120, -50)); B.gnd((120, -50))     # TLV70433 -> +3V3_AUX
        B.wire((100, 0), (300, 0), (300, 20)); B.pwr('+3V3_AUX', (300, 20), 1)
        VG(B, C28, (160, 0))
        P(B, R13, '1', (240, 0), 1); B.wire((240, -40), (240, -80), (290, -80))      # R13 + LM4040 -> XREF
        B.wire((265, -80), (265, -60)); B.pwr('XREF_2V5', (265, -60), 1)
        VG(B, C29, (240, -80))
        P(B, U10, '1', (290, -80)); B.wire((290, -90), (275, -90), (275, -120)); B.gnd((275, -120))
        B.wire((380, -80), (400, -80)); B.gnd((400, -80))
        return B

    def enable():
        B = Block(None); ps = parts_of('Rail Enable')
        for i in range(4):
            RPU, Q, RG, RGD = (p[1] for p in ps[4 * i: 4 * i + 4]); y = -i * 150
            en = SPEC[RG][2]['1']; dis = SPEC[RPU][2]['1']
            P(B, Q, '1', (0, y))
            B.wire((-90, y), (0, y)); P(B, RG, '2', (-90, y), 2); B.wire((-130, y), (-150, y)); B.port(en, (-150, y), True)
            P(B, RGD, '1', (-70, y), 1); B.gnd((-70, y - 40)); B.label(SPEC[RGD][2]['1'], (-55, y))
            B.wire((0, y - 20), (-10, y - 20), (-10, y - 50)); B.gnd((-10, y - 50))
            B.wire((140, y), (230, y)); B.port(dis, (230, y), False)
            P(B, RPU, '1', (180, y), 3); B.pwr('+3V3_AUX', (180, y + 40), 1)
        sw = ps[16][1]; pm = SPEC[sw][2]
        P(B, sw, '1', (440, -30))
        for k in range(4):
            y = -30 - 10 * k; B.wire((440, y), (420, y)); B.port(pm[str(k + 1)], (420, y), True)
        for k in range(4):
            y = -30 - 10 * k; B.wire((520, y), (540, y))
        B.wire((540, -30), (540, -80)); B.gnd((540, -80))
        return B

    def monitors():
        B = Block(None); ps = parts_of('Rail Monitors')
        for k in range(3):
            RT_, RB_, C_ = (p[1] for p in ps[3 * k: 3 * k + 3]); x = k * 230
            rail, adc = SPEC[RT_][2]['1'], SPEC[RT_][2]['2']
            B.pwr(rail, (x, 40), 1); P(B, RT_, '1', (x, 40), 1); P(B, RB_, '1', (x, 0), 1); B.gnd((x, -40))
            B.wire((x, 0), (x + 110, 0)); VG(B, C_, (x + 50, 0))
            B.port(adc, (x + 110, 0), False)
        for k, p in enumerate(ps[9:]):
            y = -110 - 40 * k; pm = SPEC[p[1]][2]
            P(B, p[1], '1', (0, y), 2); B.wire((0, y), (-20, y)); B.port(pm['1'], (-20, y), True)
            B.wire((40, y), (60, y)); B.port(pm['2'], (60, y), False)
        return B

    def limiters():
        """One TPS259621 per bench rail: jack rail in on the left, limited rail out on the right."""
        B = Block(None); ps = parts_of('PSU Current Limit')
        starts = [k for k, p in enumerate(ps) if p[0] == 'EFUSE'] + [len(ps)]
        for row, (a, b_) in enumerate(zip(starts, starts[1:])):
            grp = [p[1] for p in ps[a:b_]]; U, CIN, RENT, RENB, RILM = grp[:5]; ROVC = grp[5] if len(grp) > 5 else None
            pm = SPEC[U][2]; y = -row * 220
            P(B, U, '4', (0, y))
            B.wire((0, y), (-230, y), (-230, y + 20)); B.pwr(pm['4'], (-230, y + 20), 1)
            VG(B, CIN, (-180, y))
            B.wire((-110, y), (-110, y - 20)); P(B, RENT, '2', (-110, y - 60), 1); P(B, RENB, '1', (-110, y - 60), 1); B.gnd((-110, y - 100))
            B.wire((0, y - 20), (-60, y - 20), (-60, y - 60), (-110, y - 60)); B.label(pm['3'], (-55, y - 20))
            if pm.get('8') == 'GND': B.wire((0, y - 40), (-20, y - 40)); B.gnd((-20, y - 40), 2)
            elif ROVC:
                B.wire((0, y - 40), (-25, y - 40), (-25, y - 90)); P(B, ROVC, '1', (-25, y - 90), 1); B.gnd((-25, y - 130)); B.label(pm['8'], (-25, y - 80))
            else: B.noerc((0, y - 40))
            B.noerc((0, y - 60))                                   # dVdt open = fastest turn-on (the TPS2121 does the soft start)
            B.wire((130, y), (250, y), (250, y + 20)); B.pwr(pm['5'], (250, y + 20), 1)
            B.noerc((130, y - 10))                                 # FLT (open drain) not used
            B.wire((130, y - 40), (200, y - 40)); P(B, RILM, '1', (200, y - 40), 1); B.gnd((200, y - 80)); B.label(pm['7'], (140, y - 40))
            B.wire((130, y - 60), (150, y - 60), (150, y - 80)); B.gnd((150, y - 80))
        return B

    return {'PSU Current Limit': limiters, '3V3 Power Mux': lambda: mux('3V3 Power Mux'), '5V Power Mux': lambda: mux('5V Power Mux'),
            '5V RF Switch': lambda: mux('5V RF Switch'), '12V Switch': lambda: mux('12V Switch'),
            'Bench Inputs': inputs, 'AUX Supply & 2.5V Reference': aux,
            'Rail Enable': enable, 'Rail Monitors': monitors}
