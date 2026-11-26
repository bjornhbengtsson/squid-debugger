"""Squid Debugger V1 power-path math. Run: python tools/calc_v1.py  (prints markdown tables)

Architecture: one TPS2121 per rail = source select + current limit + reverse block + on/off switch.
  3V3: IN1 +3V3_PSU, IN2 +3V3_USB      5V: IN1 +5V_PSU, IN2 +VBUS_PROT
  5V_RF / 12V: IN1 PSU, IN2 = GND (single input)
Enable: DIS_x pulled up to +3V3_AUX (R_DIS); BAT54A diodes from DIS_x into OV1/OV2 force both channels off.
Pico GPIO -> 2N7002 pulls DIS_x low -> rail ON.  DIP switch to GND = manual force ON.
"""
VREF = (1.01, 1.06, 1.10)            # TPS2121 OVx / comparator ref, min/typ/max
XREF = 2.5                           # LM4040-2.5 on CP2
VAUX = (2.9, 3.3)                    # +3V3_AUX min (3V3-only Schottky-fed case) / nom
VPU = 3.3; RPU = 10e3; RB = 10e3     # ST pull-up, divider bottom R

def e96(x):
    import math
    s = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76,10.0]
    d = 10 ** math.floor(math.log10(x)); return min((v * d for v in s), key=lambda v: abs(v - x))

def k(r): return f"{r/1e3:.3g}k" if r < 1e6 else f"{r/1e6:.3g}M"

# ---- PR1 priority with hysteresis (R_T from IN1 to PR1, R_B to GND, R_H from PR1 to ST) ----
def pr1(rt, rh, vx=XREF):
    fall = vx + rt * (vx / RB - (VPU - vx) / (rh + RPU))
    rise = vx + rt * (vx / RB + vx / rh)
    return fall, rise
PR = {'3V3': (2.10e3, 54.9e3), '5V': (8.25e3, 150e3)}

# ---- OV dividers ----
OV = {'3V3': 26.1e3, '5V': 44.2e3, '5V_RF': 44.2e3, '12V': 118e3}
VNOM = {'3V3': 3.3, '5V': 5.0, '5V_RF': 5.0, '12V': 12.0}

# ---- DIS override: node voltage at OVx when DIS high (worst case: Vaux min, Vf max, VREF max) ----
RDIS = 4.7e3; VF = 0.35
def ovnode(rt, vin, vaux):
    vth = vin * RB / (rt + RB); rth = rt * RB / (rt + RB)
    return (vth / rth + (vaux - VF) / RDIS) / (1 / rth + 1 / RDIS)

# ---- ADC dividers (Pico ADC, 3.3 V full scale) ----
ADC = {'3V3_TGT GP26': (49.9e3, 100e3, 3.83), '5V_TGT GP27': (100e3, 100e3, 5.75), '12V_TGT GP28': (470e3, 100e3, 13.6)}

if __name__ == '__main__':
    print("### PR1 priority (IN1 = PSU preferred), R_B = 10.0k, ST pull-up 10k to +3V3_AUX")
    print("| Rail | R_T | R_H | PSU drop -> USB (V) | PSU back -> PSU (V) | hysteresis |")
    print("|---|---|---|---|---|---|")
    for n, (rt, rh) in PR.items():
        f, r = pr1(rt, rh)
        lo = pr1(rt, rh, XREF * 0.998)[0]; hi = pr1(rt, rh, XREF * 1.002)[0]
        print(f"| {n} | {k(rt)} | {k(rh)} | {f:.2f} | {r:.2f} | {1e3*(r-f):.0f} mV |")
    print("\n### OV cut-off dividers, R_B = 10.0k (OV1 on IN1, OV2 on IN2)")
    print("| Rail | R_T | trip min / typ / max (V) | divider current @ nom |")
    print("|---|---|---|---|")
    for n, rt in OV.items():
        t = [v * (1 + rt / RB) for v in VREF]
        print(f"| {n} | {k(rt)} | {t[0]:.2f} / {t[1]:.2f} / {t[2]:.2f} | {1e6*VNOM[n]/(rt+RB):.0f} uA |")
    print(f"\n### Disable override: R_DIS = {k(RDIS)} to +3V3_AUX, BAT54A Vf <= {VF} V, must exceed VREF_max = {VREF[2]} V")
    print("| Rail | V_OV with input absent, AUX 2.9 V | with input at nom, AUX 2.9 V | margin over 1.10 V |")
    print("|---|---|---|---|")
    for n, rt in OV.items():
        a = ovnode(rt, 0, VAUX[0]); b = ovnode(rt, VNOM[n], VAUX[0])
        print(f"| {n} | {a:.2f} | {b:.2f} | {min(a,b)-VREF[2]:+.2f} V |")
    print(f"I(R_DIS) when Pico pulls DIS low: {1e3*VAUX[1]/RDIS:.2f} mA per rail")
    print("\n### Current limit / soft start / hold-up")
    for r in (100,):
        print(f"- R_ILM = {r}k -> I_LIM ~ {65.2/r**0.861:.2f} A typ (datasheet curve fit; ~0.83-1.65 A spread). J1 contact rating 1 A.")
    print("- C_SS = 100 nF -> ~800 V/s ramp: 3V3 4 ms, 5V 6 ms, 12V 15 ms.")
    for n, c in [('3V3', 44e-6), ('5V', 44e-6), ('12V', 20e-6)]:
        v = {'3V3': 3.00, '5V': 4.52, '12V': 11.0}[n]
        print(f"- {n}: switchover droop = t_FSW*I/C = 5 us * 1 A / {c*1e6:.0f} uF = {5e-6/c*1e3:.0f} mV  (min {v - 5e-6/c:.2f} V from switch point)")
    print("\n### ADC rail monitors (100 nF at each ADC pin)")
    print("| Net -> pin | R_top | R_bot | V_ADC @ nom | V_ADC @ OV trip | back-feed into unpowered Pico |")
    print("|---|---|---|---|---|---|")
    for n, (rt, rb, vmax) in ADC.items():
        vn = VNOM[n.split('_')[0]]
        print(f"| {n} | {k(rt)} | {k(rb)} | {vn*rb/(rt+rb):.2f} V | {vmax*rb/(rt+rb):.2f} V | <= {1e6*(vmax-0.3)/rt:.0f} uA |")
    print("\n### +3V3_AUX / XREF budget")
    i = 2 * VPU / RPU + 4 * VAUX[1] / RDIS + (VAUX[1] - XREF) / 2e3
    print(f"- Loads: 2 ST pull-ups + 4 DIS pull-ups (all ON) + LM4040 = {1e3*i:.1f} mA. TLV70433 at 12 V in: {(12-0.3-3.3)*i*1e3:.0f} mW.")
    print(f"- LM4040 current via 2.00k: {(VAUX[0]-XREF)/2e3*1e6:.0f} uA @ AUX 2.9 V, {(VAUX[1]-XREF)/2e3*1e6:.0f} uA @ 3.3 V (needs >= 60 uA, <= 15 mA).")
    print(f"- MIC2544 R_ILIM = 230/0.5 A = {230/0.5:.0f} -> 464 ohm E96 (V0 has 260 ohm = 0.88 A, too high for USB 2.0).")
