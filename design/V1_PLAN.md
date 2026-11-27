# Squid Debugger V1 — Power Rework Plan
Nov 26 2026 · numbers from `tools/calc_v1.py` · V0 audit from `tools/schnet.py`

## 1. Architecture (decided)
- **J1 power pins are outputs of the debugger, inputs of the target.** The target ORs them in at lowest
  priority. The debugger never accepts power back on J1.
- **One TPS2121 per rail** does everything for that rail: picks the source, limits current, blocks reverse
  current and switches the rail on or off. That is 4× TPS2121RUXR in total (V0 had 4 placed, only 2 wired).

| Rail → J1 pin | Mux | IN1 (preferred) | IN2 (backup) | OUT net |
|---|---|---|---|---|
| 3V3 → pin 1 | U3 | `+3V3_PSU` (banana) | `+3V3_USB` (U13 buck) | `+3V3_TGT` |
| 5V → pin 2 | U5 | `+5V_PSU` (banana) | `+VBUS_PROT` (U4 out) | `+5V_TGT` |
| 12V → pin 3 | U8 | `+12V_PSU` (banana) | GND | `+12V_TGT` |
| 5V_RF → pin 4 | U7 | `+5V_RF_PSU` (banana) | GND | `+5V_RF_TGT` |

**On/off control (per rail).**
- Each rail has a net `DIS_x`, pulled up to `+3V3_AUX` through 4.7 k. A BAT54A (common anode) drives OV1 and OV2 high, which turns both input channels off, so the rail is **off by default**. That includes reset, when the Pico is unpowered, and when only the PSU is connected.
- Pico GPIO → 2N7002 pulls `DIS_x` low → rail on.
- A 4-position DIP switch can also short `DIS_x` to GND → **manual force-on**, for PSU-only bench use without a laptop.

**Net suffix convention** (also placed as a text frame on sheet 1):

| Suffix | Meaning |
|---|---|
| `_PSU` | Bench supply input from the banana jacks, always live |
| `_USB` | From the laptop's USB. `+VBUS_PROT` = after the U4 current limit |
| `_RPI` | Pico 3V3 output: debugger logic, CAN chips |
| `_AUX` | Always-on housekeeping: XREF, pull-ups (V1 power sheet) |
| `_TGT` | Switched output to the target on J1/P3, OFF by default. Turned on by Pico GP16–19 or the DIP switch |

## 2. Math (verified by script)
**PR1 priority** (3V3 and 5V only). PR1 is compared against XREF = 2.5 V on CP2. R_B = 10.0 k. R_H runs from PR1 to ST, and ST is pulled up 10 k to `+3V3_AUX`.

| Rail | R_T | R_H | PSU → USB below | back to PSU above | hyst |
|---|---|---|---|---|---|
| 3V3 | 2.10 k | 54.9 k | 3.00 V | 3.12 V | 122 mV |
| 5V | 8.25 k | 150 k | 4.52 V | 4.70 V | 179 mV |

**OV cut-off** (R_B = 10.0 k on each OV pin): R_T sets the trip voltage, typical (min–max):
- 3V3: 26.1 k → 3.83 V (3.65–3.97)
- 5V and 5V_RF: 44.2 k → 5.75 V (5.47–5.96)
- 12V: 118 k → 13.6 V (12.9–14.1)

**Disable override.**
- Worst-case OV-node voltage with DIS high is 1.55 V, which beats VREF_max = 1.10 V by ≥ +0.45 V on every rail. That worst case is AUX = 2.9 V, Vf = 0.35 V, input absent.
- When a rail is ON, DIS draws 0.70 mA.

**Current limit and soft start (all 4 parts).**
- R_ILM = 100 k → I_LIM ≈ 1.24 A typ (0.83–1.65 A).
- C_SS = 100 nF → ≈ 800 V/s (12 V ramps in ≈ 15 ms).

**Switchover droop** at 1 A with t_FSW = 5 µs:
- 3V3: 44 µF → −114 mV (min 2.89 V).
- 5V: 44 µF → −114 mV (min 4.41 V).

**XREF / +3V3_AUX.**
- VAUX is a Schottky OR (3× BAT54C) of `+3V3_PSU`, `+5V_PSU`, `+5V_RF_PSU`, `+12V_PSU` and `+VBUS`.
- TLV70433 (24 V in) → `+3V3_AUX` → 2.00 k → LM4040B25 → `XREF_2V5`. LM4040 current: 200–400 µA.
- Total AUX load is 3.9 mA, which dissipates 32 mW at 12 V in.

**ADC monitors** (100 nF at each pin). Each row: divider R_top/R_bot → V_ADC at nominal / at OV trip.
- `+3V3_TGT` → GP26: 49.9 k/100 k → 2.20 / 2.56 V.
- `+5V_TGT` → GP27: 100 k/100 k → 2.50 / 2.88 V.
- `+12V_TGT` → GP28: 470 k/100 k → 2.11 / 2.39 V.
- Back-feed into an unpowered Pico is ≤ 71 µA.

**USB limit.** MIC2544 R_ILIM: 260 Ω (0.88 A) → **464 Ω** (0.50 A, USB 2.0).

## 3. Per-mux pin table (capture this in Altium)
| Pin | U3 (3V3) | U5 (5V) | U7 (5V_RF) | U8 (12V) |
|---|---|---|---|---|
| 7 IN1 | +3V3_PSU | +5V_PSU | +5V_RF_PSU | +12V_PSU |
| 2 IN2 | +3V3_USB | +VBUS_PROT | GND | GND |
| 1,8 OUT | +3V3_TGT | +5V_TGT | +5V_RF_TGT | +12V_TGT |
| 6 PR1 | IN1–2.10k–PR1–10.0k–GND; 54.9k PR1→ST | IN1–8.25k–PR1–10.0k–GND; 150k PR1→ST | GND | GND |
| 3 CP2 | XREF_2V5 | XREF_2V5 | GND | GND |
| 5 OV1 | IN1–26.1k–OV1–10.0k–GND; BAT54A from DIS_3V3 | IN1–44.2k–OV1–10.0k–GND; BAT54A from DIS_5V | IN1–44.2k–OV1–10.0k–GND; diode from DIS_5VRF | IN1–118k–OV1–10.0k–GND; diode from DIS_12V |
| 4 OV2 | IN2–26.1k–OV2–10.0k–GND; 2nd BAT54A diode | IN2–44.2k–OV2–10.0k–GND; 2nd BAT54A diode | GND | GND |
| 9 ST | 10k to +3V3_AUX (+ R_H) | 10k to +3V3_AUX (+ R_H) | NC | NC |
| 10 ILM | 100k to GND | 100k | 100k | 100k |
| 11 SS | 100nF to GND | 100nF | 100nF | 100nF |
| 12 GND | GND | GND | GND | GND |
| C_IN on IN1 | **C6** (reuse, `+3V3_PSU`) | **C2** (reuse, `+5V_PSU`) | NEW (`+5V_RF_PSU`) | NEW, 50 V (`+12V_PSU`) |
| C_IN on IN2 | NEW (`+3V3_USB`) | **C3** (reuse, `+VBUS_PROT`) | — (IN2 = GND) | — (IN2 = GND) |
| C_OUT | 2× 22 µF GCM31CR71A226KE02K | 2× 22 µF | 2× 22 µF | 2× 10 µF 35 V CGA5L1X7R1V106K160AE |

**Input caps: what's reused.** C2, C3, C5 and C6 are leftovers from the earliest V0, where they were the input caps of
two TPS2113A muxes. They keep the same job in V1:
- **C2, C3, C6:** move them from sheet 1 to sheet 2, next to the mux pin each one serves. Swap each to the
  **1 µF 25 V X7R 0805** vault part (the same item C23 uses), replacing the old generic `CAP_1210` 100 nF.
- **3 NEW caps:** U3 IN2 (`+3V3_USB`) and U7 IN1 (`+5V_RF_PSU`) each get the same 1 µF 25 V 0805.
  U8 IN1 (`+12V_PSU`) gets a **1 µF 50 V X7R 0805**, for DC-bias margin at 12 V.
  - The `+3V3_USB` cap can be skipped only if U3 is laid out right beside U13's output caps (C19, C20).
- **C5** (`+3V3_RPI`): **deleted Nov 26** (redundant with C1, C9 and the Pico's own caps).
- **PCB:** each C_IN goes at its TPS2121 IN pin, on the same side as the chip, with a short via to the GND plane.

For U7 and U8, one BAT54A provides both diodes: one cathode goes to OV1 and the other is left unused. A single BAT54 (or 1N4148W) is also fine.

**Control.** Q1–Q4: 2N7002 (or 2× 2N7002DW).
- Gate: 100 Ω from the GPIO, plus 100 k to GND.
- Drain: `DIS_x`. Source: GND.
- SW1: 4-position SMD DIP switch, each position from `DIS_x` to GND.

**Banana inputs.**
- TVS: **SMBJ5.0A ×3** (3V3, 5V, 5V_RF) and SMBJ13A (12V), all Littelfuse. SMBJ3.3A was dropped Nov 26: only no-name
  makers, with no Altium models. On 3V3, SMBJ5.0A gives V_BR ≥ 6.4 V (no conduction even with 5 V plugged in) and
  clamps ≤ 9.2 V. That clamp is safe for TPS2121 IN (24 V abs) and OV1 (2.55 V), and PR1 is covered by the 4.7 V zener (item 5).
- 1 µF on each input.

**Rail LEDs** (optional): green 0603 on each `_TGT` rail, with 1.00 k (3V3), 2.00 k (5V ×2) or 10.0 k (12V).

## 4. Pico pin map V1
- Unchanged from V0:
  - GP2 SWCLK, GP3 SWDIO, GP4 RST, GP5 SWO
  - GP6 CAN_S, GP7 CAN_SHDN, GP8/9 UART
  - GP10–13 CAN SPI, GP20 CAN_INT, GP21 CAN_RST
- **New:**
  - GP16 EN_3V3, GP17 EN_5V, GP18 EN_5V_RF, GP19 EN_12V
  - GP26 ADC_3V3, GP27 ADC_5V, GP28 ADC_12V
- Free: GP0/1 (console), GP14, GP15, GP22.

## 5. V0 → V1: keep / fix / discard
| Block | Verdict | Action |
|---|---|---|
| U1 Pico + pin map | KEEP | add GP16–19 and GP26–28 nets |
| CAN: U6 MCP2515, Y1, C7, C8, U2 TCAN330, R1, R10, C1, C9 | KEEP + FIX | move the supply from `+3.3V` (J1 pin 1, target-powered!) to `+3.3V_RPI`. Name the bus `CAN_H`/`CAN_L` (drop CAN_P/CAN_N) |
| J1 JST-GH, P3/P4 breakouts | KEEP + FIX | rail nets → `+3V3_TGT`, `+5V_TGT`, `+12V_TGT`, `+5V_RF_TGT`. Use one name `MCU_RESET` (drop the RST alias) |
| UART LEDs D2/D3, R6/R7, P2 | KEEP | — |
| Mounting holes MH1–4 | KEEP | — |
| Banana TP1–TP5 | KEEP + FIX | rename `+5V BNN`→`+5V_PSU`, `+3.3V BNN`→`+3V3_PSU`, `+12V`→`+12V_PSU`, `+5V RF`→`+5V_RF_PSU`. Add TVS |
| U4 MIC2544 + D1/R3, C3, C4 | KEEP + FIX | R5 260 → 464 Ω. Output net `+VBUS_O` → `+VBUS_PROT`. **Verify the -2 variant's EN polarity** (EN is tied to VBUS) |
| U13 AP63203 buck, L1, C18–C22 | KEEP | output `+3V3_USB` now feeds U3 IN2 |
| U3 TPS2121 (sheet 1) + R11–R18 | DISCARD | dividers wired to the wrong node, output went nowhere |
| Unplaced TPS2121 on sheet 1 | DISCARD | — |
| U5 TPS2121 (sheet 2) + 8× R? | DISCARD | same wiring faults |
| Unplaced TPS2121 on sheet 2 | DISCARD | — |
| TI app-note picture and notes on sheet 2 | DISCARD | replaced by this plan |
| P1 5V↔5V_RF jumper | DISCARD | shorts two supply rails |
| TPS2113 / %TEMP% library links | DISCARD | move parts into the project SchLib |

## 6. Sheet structure V1
- **Sheet 1 `DebugBoard.SchDoc`:** Pico, CAN, J1/P3/P4, UART, holes, USB limit + buck.
- **Sheet 2 `DebugBoardMuxes.SchDoc`** (rename it Power later): banana inputs + TVS, VAUX/XREF, 4× TPS2121 blocks, enable FETs + DIP, ADC dividers, rail LEDs.
- Project Options → Net Identifier Scope: **Global**, so the net labels connect across both sheets.

## 7. Open items
1. **MIC2544 enable polarity: DONE.** `-2` is active-low and `-1` is active-high. U4 is now **MIC2544-1YMM-TR**
   (CMP-00008-1), rewired, with R5 = 576 Ω → 0.40 A typ (0.32–0.48 A).
2. **TPS2121 with IN2 = GND: CLOSED.** The datasheet (SLVSEA3F, §9.5) says "if only one input voltage is valid,
   then that input will power the output". IN-to-OUT leakage is at most ±80 µA at 22 V.
3. Pick the DIP switch part (e.g. CTS 219-4MST) and check the footprint.
4. Per-rail current of the board under test: measure on the bench. The datasheet limit at 80 kΩ is 1.0/1.5/2.0 A
   (min/typ/max). Our 100 kΩ (the maximum allowed) gives ≈1.24 A typ, roughly 0.8–1.7 A. The connector is rated 1 A
   per contact: OK for faults, not for continuous overload.

## 8. Datasheet review (Nov 26 2026)
Read from the vendor PDFs. "OK" means the schematic or plan matches the datasheet.

| Part | Checked | Result |
|---|---|---|
| TPS2121 (SLVSEA3F) | Pins, VREF 1.01/1.06/1.10 V, OV/PR1/CP2/ST 0–5.5 V (6 V abs max), R_ILM 18–100 kΩ, I_LM = 65.2/R^0.861, SS 100 nF = 780 V/s, truth table | **OK.** Both OVx > VREF → OUT Hi-Z, which confirms the DIS on/off scheme. If both inputs are valid and PR1 > CP2 (XREF), IN1 is used. ST is high for IN1/Hi-Z and low for IN2. UVLO is 2.5–2.8 V. Fast-trip current limit is 2.4×I_LM, with a 25 ms retry. |
| AP63203 (DS41326) | Pinout FB1 EN2 VIN3 GND4 SW5 BST6, VIN 3.8–32 V, 2 A, 1.1 MHz | **OK.** The datasheet table gives L 3.9 µH, C_IN 10 µF, C_OUT 2×22 µF, C_BST 100 nF, which exactly matches L1, C18, C19/C20 and C21. EN may tie to VIN. |
| MIC2544-1 | EN active-high, I = 230/R, ±20 % | **OK** after the swap. |
| TCAN330G (SLLSEQ7F) | Pin 5 SHDN (high = off, internal pull-down), pin 8 S (high = silent, internal pull-down), VCC 3.0–3.6 V | **OK.** "G" = 5 Mbps rated. R1 duplicates the internal pull-down (harmless). |
| MCP2515 (DS20001801J) | VDD 2.7–5.5 V, F_OSC ≤ 25 MHz over the full VDD range, TXnRTS internal 100 k pull-ups, SPI ≤ 10 MHz | **OK.** 16 MHz at 3.3 V is fine, and unused TXnRTS/RXnBF/CLKOUT can float. Firmware: SPI ≤ 10 MHz. |
| TLV70433 (SBVS148F) | VIN 2.5–24 V, 150 mA, C_OUT ≥ 0.47 µF, C_IN ≥ 0.1 µF recommended | **OK.** Use 1 µF in and out. 12 V + SMBJ13A clamp (~21.5 V) < 24 V. |
| LM4040-2.5 B (SNOS633N) | ±0.2 % initial (±0.85 % over temperature), I_min 60 µA max | **OK.** Bias is 200–400 µA. Thresholds move about ±0.85 % over temperature. |
| BAT54A / BAT54C | Pinout | **Not verified** (Nexperia PDF blocked). The plan assumes A = common anode (DIS → OV1/OV2) and C = common cathode (VAUX OR). Check against the chosen part's datasheet. |
| Raspberry Pi Pico (RP-008307-DS-3) | VBUS = micro-USB pin 1 (then Schottky → VSYS), 3V3 out "keep load < 300 mA", ADC_VREF = filtered 3V3, 3V3_EN 100 k pull-up to VSYS | **OK.** U4 on VBUS and the CAN chips on 3V3 (≈ tens of mA) are fine. |
| RP2040 (RP-008371-DS-2, §5.5.3) | IOVDD 3.3 V: VIH ≥ 2.0 V, VOH ≥ 2.62 V at the selected drive (2/4/8/12 mA, default 4), VOL ≤ 0.5 V, pull-ups 50–80 kΩ, **V_PIN abs max = IOVDD + 0.5 V** | **Not 5 V tolerant, and not safe to drive while the Pico is unpowered** (IOVDD = 0 → 0.5 V max). This affects every J1 signal a powered target drives back (UART_RX, SWO, SWDIO, MCU_RESET); see issue 4. ADC inputs must not exceed IOVDD. |
| Crystal Y1 7M-16.000MAHL-T | Load capacitance | **Not checked.** C7/C8 = 22 pF assumes C_L ≈ 12–18 pF. Check the TXC datasheet (C_load ≈ 2·(C_L − ~4 pF)). |

### Issues found in the current schematic (sheet 1)
1. **[DONE: R6/R7 = 2.2 kΩ] UART LEDs load the lines.** D2/D3 have 260 Ω to GND straight on UART_TX and UART_RX. Each draws ≈5–6 mA
   from the driving pin: the Pico's GP8 and the **target's TX pin**. The RP2040 only guarantees VOH ≥ 2.62 V up to the
   selected drive (default 4 mA), so ≈5.4 mA exceeds it. Margin to a receiver's VIH (≈2.0–2.3 V) shrinks. The LEDs are
   also lit at idle (UART idles high). Fix: raise R6/R7 to **2.2 kΩ** (≈0.6 mA), or drive the LEDs from GP14/GP15
   as activity blinkers in firmware.
2. **Fault LED current: OK as-is (checked).** R3 260 Ω gives ≈11.5 mA into FLG. MIC2544 datasheet: FLG is an
   open-drain N-MOSFET, abs max I_FLG = 50 mA, R_on 4 Ω typ / 15 Ω max at 10 mA. No change needed.
3. **No CAN termination on the debugger.** A single target on the bench needs 120 Ω at each end. Add a switchable
   120 Ω (solder jumper or 2-pin header), or split 2×60 Ω + 4.7 nF.
4. **[DONE: R2/R4/R8/R11 = 100 Ω, R9/R12 = 1 kΩ] J1 signal protection (SWD, RESET, UART).** There are no series resistors on SWCLK/SWDIO/SWO/MCU_RESET/
   UART_TX/UART_RX. Per RP2040 §5.5.3, V_PIN ≤ IOVDD + 0.5 V. A **target powered from the stack, with the Pico
   unplugged**, would drive 3.3 V into unpowered RP2040 pins and back-power the Pico through its ESD diodes. The
   reverse case (Pico driving an unpowered target) back-powers the target.
   - Minimum fix: **100 Ω** in series on SWCLK/SWDIO/MCU_RESET/UART_TX, and **1 kΩ** on the target-driven inputs
     SWO and UART_RX. 1 kΩ limits the fault current to ≈3 mA.
   - Better fix: a buffer powered from +3V3_RPI with power-off isolation (Ioff), e.g. 74LVC1T45 or SN74LVC2G125
     per signal group. It goes hi-Z when the Pico is unpowered.
   - Firmware: drive MCU_RESET open-drain style (low or hi-Z, never push high). Keep the debug pins hi-Z until
     the target rail is confirmed up (via the ADC).
5. **Project settings.** Net Identifier Scope is still Automatic (HierarchyMode=0). Power ports are global, but
   EN_x and ADC_x must cross between sheets: set Scope = Global, or use ports.
6. **Libraries.** The project still links schematic libraries from %TEMP% (TPS2121, TPS2113, TCAN330,
   RC0805FR). Create the TPS2121 as a workspace part via Manufacturer Part Search (the same flow as U4), then
   remove the dead links.
7. `+12V_PSU` and `+5V_RF_PSU` currently connect to one pin each. This is expected until sheet 2 is drawn.

### Kept from the earliest V0 (cross-check)
All functional blocks survive: Pico, CAN controller and transceiver, USB current limit, USB buck, J1, P3/P4, the UART
LEDs + P2, the banana jacks and the mounting holes.

Removed:
- The P1 jumper, which shorted two supply rails.
- Both generations of muxes: the TPS2113A ones and the miswired TPS2121 ones.

Leftover caps are reassigned per §3.
5. **PR1 overvoltage when the wrong supply is plugged in (found Nov 26).** PR1 abs max is 6 V (recommended max 5.5 V),
   with R_T/R_B = 2.10k/10k on 3V3 and 8.25k/10k on 5V:
   - 3V3 jack: 12 V in → PR1 = 9.9 V (damage). It exceeds 6 V above ≈7.3 V in.
   - 5V jack: 12 V in → 6.6 V (damage).
   - OV1 is fine in both cases (≤ 3.3 V), so the output still shuts off. Only the PR1 pin is at risk.
   - Fix: a 4.7 V zener (BZX84C4V7, SOT-23) from PR1 to GND on U3 and U5. At the nominal 2.7–2.8 V it barely
     conducts (µA leakage → < 0.1 % threshold shift; verify against the zener's I_R spec).
   - Alternative: a BAT54 from PR1 to +3V3_AUX (clamps ≈3.6 V; dumps the fault current into AUX).
   - The TVS doesn't fix this: steady-state miswiring isn't a transient.

## 9. Vendor libraries (Nov 26): `Debugging Board V1/Libraries/Vendor/`
Pins read from each symbol with `tools/libpins.py` and checked against the datasheet where noted.

| Part | Symbol pins | Footprint | Check |
|---|---|---|---|
| TLV70433DBVR | 1 GND, 2 IN, 3 OUT, 4/5 NC | SOT95P280X145-5N | ✅ TLV704 datasheet Table 5-1. **No EN pin** (the earlier note was wrong). C_OUT ≥ 1 µF required. |
| LM4040BIM3-2.5/NOPB | 1 +, 2 −, 3 NC | SOT95P237X112-3N | ✅ Datasheet: pin 3 must float or tie to pin 2. |
| BAT54C,215 | 1 A1, 2 A2, 3 common K | BAT54C215 | ✅ Common cathode (vendor model; Nexperia standard). |
| BAT54A,215 | 1 K1, 2 K2, 3 common A | SOT95P230X110-3N | ✅ Common anode. |
| 2N7002-7-F | 1 G, 2 S, 3 D | SOT103P240X110-3N | ✅ Standard SOT-23 FET. |
| 219-4MST | 1–8 (switch n = pins n / 9−n) | 2194MST | OK |
| GCM31CR71A226KE02K / CGA5L1X7R1V106K160AE | 1, 2 | CAPC3116 / CAPC3216 | OK |
| CL21B105KAFNNNE / GRM21BR71H105KA12L | 1, 2 | CAPC2012 (0805) | OK |
| MIC2544-1YMM-TR | Matches workspace CMP-00008-1 | MSOP-8 | Already in use. |
| TPS2121RUXR (UL) | Extra pins 1_1/2_1/7_1/8_1 | IC_TPS2121RUXR | ⚠ Use the workspace part CMP-019-00076-1 instead. |
| SMBJ13A (SnapEDA) | A, C (unidirectional TVS) | DIOM4336X265N (SMB/DO-214AA), pads A/C match the pins | ✅ The data's manufacturer is Taiwan Semi; set the part choice to Littelfuse SMBJ13A (same JEDEC part). The STEP is an ST SMB body (generic). |
| SMBJ5.0A | — | — | Reuse the SMBJ13A symbol and footprint (same SMB package and TVS symbol); only the MPN and part choice change. |
| BZX84-C4V7,215 | 1 A, 3 C (pin 2 NC, no symbol pin) | SOT95P230X110-3N (same as BAT54A), pads 1–3 | ✅ Nexperia SOT-23 zener pinout: 1 anode, 2 NC, 3 cathode. In the circuit: cathode → PR1, anode → GND. |
| 2N7002-7-F footprint note | — | SOT103P240X110-3N: pads 2.03 mm apart (std SOT-23 1.90) | ⚠ Consider using SOT95P230X110-3N (the BAT54/BZX84 footprint) instead. |

## 9. PSU current limit (added Nov 27, changelog #29)

The TPS2121 limit (ILM = 100 kΩ, 1.24 A typical, 0.83–1.65 A) is that chip's minimum and can exceed J1's 1 A contact
rating. One TPS259621DDAR eFuse per bench rail now sits between the jack and IN1:

- I_LIM = 903 / R_ILM + 0.0112 A, R_ILM = 1.02 kΩ → 0.90 A typical (0.83–0.97 A).
- EN/UVLO (1.20 V rising, 1.10 V falling, 7 V maximum): 100 k / 100 k → on at 2.40 V; 470 k / 100 k on 12 V → on at 6.84 V.
- OVCSEL: GND → 3.8 V clamp (3V3); 402 kΩ → 5.7 V (5V, 5V RF); open → 13.8 V (12V).
- Drop at 0.9 A: 89 mΩ × 0.9 A = 80 mV, plus 50 mV in the TPS2121.

Full description: docs/02-power-architecture.md section 2.9.

