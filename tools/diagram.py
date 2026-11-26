"""Generate the Squid Debugger V1 power/debug block diagram as SVG."""
W, H = 1160, 985
o = []
def a(s): o.append(s)

def rect(x, y, w, h, cls="box", rx=4):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="{cls}"/>')
def text(x, y, s, cls="t", anchor="start"):
    a(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{s}</text>')
def wire(pts, cls):
    d = "M" + " L".join(f"{x} {y}" for x, y in pts)
    a(f'<path d="{d}" class="w {cls}"/>')
def dot(x, y, cls):
    a(f'<circle cx="{x}" cy="{y}" r="3.5" class="dot {cls}"/>')
def arrow(x, y, cls):  # right-pointing arrowhead ending at x,y
    a(f'<path d="M{x-8} {y-4.5} L{x} {y} L{x-8} {y+4.5} Z" class="ah {cls}"/>')

def tag(y, src, net):
    cls = {"STACK": "stk", "PSU": "psu", "USB": "usb"}[src]
    rect(20, y, 150, 30, f"tag {cls}", 3)
    text(30, y + 19.5, src, f"tl {cls}")
    text(162, y + 19.5, net, "net", "end")
    return (170, y + 15)

def mux(x, y, h, ref, name, trip, p1, p2, pout):
    rect(x, y, 130, h, "mux", 3)
    text(x + 65, y + 18, ref, "ref", "middle")
    text(x + 65, y + 34, "TPS2121", "part", "middle")
    text(x + 65, y + 51, name, "mname", "middle")
    text(x + 65, y + h - 9, trip, "small", "middle")
    text(x + 6, p1 + 4, "IN1", "pin")
    text(x + 6, p2 + 4, "IN2", "pin")
    text(x + 124, pout + 4, "OUT", "pin", "end")

a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="bdT bdD" class="bd">')
a('<title id="bdT">Squid Debugger V1 power and debug block diagram</title>')
a('<desc id="bdD">PSU and USB feed stage-A TPS2121 muxes for 3.3 V and 5 V; stage B then gives the flight stack priority over that result; 5 V RF and 12 V use one Stack-vs-PSU mux and single muxes for 5 V RF and 12 V; outputs go to the J1 debug port. A reference band and the Pico debug chain are shown below.</desc>')
rect(0, 0, W, H, "bg", 0)

# column headers
for x, s in [(20, "SOURCES"), (195, "USB CONDITIONING"), (390, "STAGE A · PSU vs USB"),
             (700, "STAGE B · STACK vs A"), (920, "OUTPUTS → DUT")]:
    text(x, 26, s, "hdr")

# lane bands
lanes = [("+3.3 V", 40, 200), ("+5 V", 208, 400), ("+5 V RF", 408, 530), ("+12 V", 538, 662)]
for i, (n, y0, y1) in enumerate(lanes):
    rect(10, y0, 900, y1 - y0, "lane" + (" alt" if i % 2 else ""), 6)
    text(20, y0 + 22, n, "lname")

# ---------- 3V3 lane ----------
s1 = tag(76, "STACK", "+3V3_STK")
s2 = tag(112, "PSU", "+3V3_PSU")
rect(195, 150, 130, 40, "box", 3)
text(260, 166, "U13 AP63203", "ref", "middle"); text(260, 182, "buck 5 V → 3.3 V", "small", "middle")
mux(390, 106, 84, "U3", "3V3-A", "PR1 trip 3.00 V", 127, 170, 150)
mux(700, 70, 96, "U5", "3V3-B", "PR1 trip 3.00 V", 91, 150, 120)
wire([s2, (390, 127)], "psu"); arrow(390, 127, "psu")
wire([(325, 170), (390, 170)], "usb"); arrow(390, 170, "usb"); text(358, 163, "+3V3_USB", "netsm", "middle")
wire([s1, (700, 91)], "stk"); arrow(700, 91, "stk")
wire([(520, 150), (700, 150)], "sp"); arrow(700, 150, "sp"); text(610, 143, "+3V3_PU", "net", "middle")
wire([(830, 120), (920, 120)], "out"); arrow(920, 120, "out")

# ---------- 5V lane ----------
s1 = tag(232, "STACK", "+5V_STK")
s2 = tag(272, "PSU", "+5V_PSU")
s3 = tag(312, "USB", "VBUS (Pico)")
rect(195, 307, 130, 40, "box", 3)
text(260, 323, "U4 MIC2544", "ref", "middle"); text(260, 339, "current limit 0.5 A", "small", "middle")
text(260, 362, "→ +VBUS_PROT", "netsm", "middle")
mux(390, 266, 84, "U7", "5V-A", "PR1 trip 4.52 V", 287, 327, 307)
mux(700, 228, 98, "U8", "5V-B", "PR1 trip 4.52 V", 247, 307, 275)
wire([s3, (195, 327)], "usb"); arrow(195, 327, "usb")
wire([(325, 327), (390, 327)], "usb"); arrow(390, 327, "usb")
wire([s2, (390, 287)], "psu"); arrow(390, 287, "psu")
wire([s1, (700, 247)], "stk"); arrow(700, 247, "stk")
wire([(520, 307), (700, 307)], "sp"); arrow(700, 307, "sp"); text(610, 300, "+5V_PU", "net", "middle")
wire([(830, 275), (920, 275)], "out"); arrow(920, 275, "out")
# VBUS_PROT branch up to the buck, hopping the PSU and STACK 5 V wires
dot(355, 327, "usb")
a('<path d="M355 327 L355 295 A8 8 0 0 0 355 279 L355 255 A8 8 0 0 0 355 239 L355 214 L260 214 L260 190" class="w usb"/>')
a('<path d="M255.5 198 L260 190 L264.5 198 Z" class="ah usb"/>')

# ---------- 5V RF lane ----------
s1 = tag(440, "STACK", "+5VRF_STK")
s2 = tag(480, "PSU", "+5VRF_PSU")
mux(700, 434, 84, "U9", "5VRF", "PR1 trip 4.52 V", 455, 495, 475)
wire([s1, (700, 455)], "stk"); arrow(700, 455, "stk")
wire([s2, (700, 495)], "psu"); arrow(700, 495, "psu")
wire([(830, 475), (920, 475)], "out"); arrow(920, 475, "out")
text(455, 479, "single stage · no USB source", "small", "middle")

# ---------- 12V lane ----------
s1 = tag(570, "STACK", "+12V_STK")
s2 = tag(610, "PSU", "+12V_PSU")
mux(700, 564, 84, "U10", "12V", "PR1 trip 11.1 V", 585, 625, 605)
wire([s1, (700, 585)], "stk"); arrow(700, 585, "stk")
wire([s2, (700, 625)], "psu"); arrow(700, 625, "psu")
wire([(830, 605), (920, 605)], "out"); arrow(920, 605, "out")
text(455, 609, "single stage · no USB source", "small", "middle")

# ---------- J1 power block ----------
rect(920, 40, 220, 622, "conn", 4)
text(934, 64, "J1 · Squid Debug Port", "ref")
text(934, 81, "JST-GH 12 · BM12B-GHS-TBT", "small")
text(934, 96, "+ P3 power breakout", "small")
for y, pin, net in [(120, 1, "+3V3_OUT"), (275, 2, "+5V_OUT"), (475, 4, "+5VRF_OUT"), (605, 3, "+12V_OUT")]:
    rect(924, y - 9, 18, 18, "pinbox", 2)
    text(933, y + 4, str(pin), "pinno", "middle")
    text(950, y + 5, net, "netb")
text(934, 640, "GND: pins 5, 6, 13, 14", "small")
text(934, 655, "≤ 1 A per GH contact", "small")

# ---------- reference band ----------
rect(10, 680, 1130, 88, "band", 6)
text(20, 700, "REFERENCE &amp; AUX · alive whenever any source is present", "hdr")
rect(30, 712, 240, 44, "box", 3)
text(150, 730, "D4–D8 BAT54C ×5", "ref", "middle"); text(150, 746, "Schottky OR of all 9 inputs → VAUX", "small", "middle")
rect(330, 712, 200, 44, "box", 3)
text(430, 730, "U14 TLV70433", "ref", "middle"); text(430, 746, "VAUX → +3V3_AUX", "small", "middle")
rect(590, 712, 200, 44, "box", 3)
text(690, 730, "U15 LM4040-2.5", "ref", "middle"); text(690, 746, "2.0 kΩ bias → XREF_2V5", "small", "middle")
wire([(270, 734), (330, 734)], "ref"); arrow(330, 734, "ref")
wire([(530, 734), (590, 734)], "ref"); arrow(590, 734, "ref")
wire([(790, 734), (840, 734)], "ref"); arrow(840, 734, "ref")
text(848, 730, "XREF → CP2 of all six muxes", "small")
text(848, 746, "+3V3_AUX → ST pull-ups (10 kΩ)", "small")

# ---------- debug / data band ----------
rect(20, 796, 200, 148, "box", 4)
text(120, 818, "U1 Raspberry Pi Pico", "ref", "middle")
text(120, 835, "RP2040 debug firmware", "small", "middle")
text(120, 851, "USB data to host PC", "small", "middle")
text(120, 867, "reads ST ×6 (active source)", "small", "middle")
text(120, 883, "own 3V3 → CAN chips", "small", "middle")
wire([(220, 820), (920, 820)], "data"); arrow(920, 820, "data")
text(560, 812, "SWDIO · SWCLK · SWO · MCU_RST", "netsm", "middle")
wire([(220, 862), (300, 862)], "data"); arrow(300, 862, "data")
rect(300, 846, 170, 32, "box", 3); text(385, 866, "P2 UART · D2/D3 LEDs", "small", "middle")
wire([(220, 914), (300, 914)], "data"); arrow(300, 914, "data"); text(260, 907, "SPI", "netsm", "middle")
rect(300, 898, 150, 32, "box", 3); text(375, 918, "U6 MCP2515 + Y1", "small", "middle")
wire([(450, 914), (500, 914)], "data"); arrow(500, 914, "data")
rect(500, 898, 150, 32, "box", 3); text(575, 918, "U2 TCAN330", "small", "middle")
wire([(650, 914), (920, 914)], "data"); arrow(920, 914, "data"); text(785, 907, "CAN_H · CAN_L", "netsm", "middle")
rect(920, 796, 220, 148, "conn", 4)
text(934, 818, "J1 signals · pins 7–12", "ref")
text(934, 840, "7 / 8   CAN_P / CAN_N", "netsm")
text(934, 858, "9 SWO · 10 SWCLK", "netsm")
text(934, 876, "11 SWDIO · 12 MCU_RST", "netsm")
text(934, 900, "+ P4 debug breakout", "small")

# legend
lx = 700
for i, (cls, s) in enumerate([("stk", "Stack"), ("psu", "Bench PSU"), ("usb", "USB"), ("sp", "PSU-or-USB node"), ("out", "Muxed output")]):
    x = 400 + i * 140
    wire([(x, 968), (x + 22, 968)], cls)
    text(x + 28, 972, s, "small")
a('</svg>')
svg = "\n".join(o)
if __name__ == "__main__":
    import sys
    open(sys.argv[1], "w").write(svg)
