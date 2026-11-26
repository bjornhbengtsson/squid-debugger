# Squid Debugger — SDSL (ASU Sun Devil Satellite Laboratory)

Handoff from a claude.ai design chat (Nov 5 2026). Claude Code reads this file automatically; it is the
project memory. Keep it updated as decisions change.

## REPO (Nov 26 2026): this folder is the git repo (private GitHub "squid-debugger")
- Working Altium project = `hardware/` (copied from `Documents/Altium/Debugging Board V1/`, which is now an ARCHIVE,
  still linked to Altium 365 VCS - do not edit it). Open `hardware/Debugging Board V1.PrjPcb`.
- Docs for humans: README.md + docs/01..06. Keep them in sync with design changes.
- Tools are repo-relative: gen_sheet2.py (templates in tools/templates), verify_gen.py, compare_nets.py, schnet.py,
  libpins.py, intlib_extract.py; one-off sheet-1 scripts in tools/oneoff/.
- Vendor PDFs in reference/ are gitignored (links in reference/datasheets.md).

## Who / how to work
- User: Bjorn Bengtsson, EE student (embedded, avionics, drones). Co-designer: Alex Jaber (V0 author).
- Wants: concise but complete, technical, step-by-step math with defined variables, real part numbers,
  tradeoffs, and direct correction of mistakes. C/C++ / STM32 / RP2040 mindset.
- Altium Designer 26.10.1. Work LOCALLY first (they lost work with workspace git), upload to the
  Altium 365 workspace later. Claude cannot edit .SchDoc/.PcbDoc; it produces values, net tables,
  diagrams and checks, and the user captures them in Altium.

## The board
Bench/flight debugger for SquidSat (modular 3U CubeSat, CAN-networked boards, EPS rails
3.3 V / 5 V / 5 V_RF (LDO, low noise) / 12 V (boost) from a 2S Li-ion pack — see reference/SSC26 paper).
- U1 Raspberry Pi Pico (RP2040): USB to PC, SWD/UART/CAN debug firmware.
- CAN: Pico SPI1 → U6 MCP2515 (Y1 16 MHz, C7/C8 22 pF) → U2 TCAN330 → CAN_P/CAN_N.
- J1 "Squid Standard Debug Port": JST-GH 12-pin BM12B-GHS-TBT, 1 A/contact.
  1 +3.3V · 2 +5V · 3 +12V · 4 +5V_RF · 5,6 GND · 7 CAN_P · 8 CAN_N · 9 SWO · 10 SWCLK · 11 SWDIO ·
  12 MCU_RESET · 13,14 GND (mech). P3/P4 = 2.54 mm breakouts of the same signals.
- PSU input: banana jacks TP1–TP5. USB: Pico VBUS → U4 MIC2544 → U13 AP63203 buck (3.3 V).
- Pico pin map (V0, verified from schematic): GP2 SWCLK, GP3 SWDIO, GP4 RST, GP5 SWO, GP6 CAN_S,
  GP7 CAN_SHDN, GP8 UART_TX, GP9 UART_RX, GP10–13 CAN SPI (SCK/MOSI/MISO/CS), GP20 CAN_INT, GP21 CAN_RST.
  FREE: GP0/1 (keep for Pico console), GP14–19, GP22, GP26–28 (ADC).

## Power architecture — CURRENT STATUS (read this first)
History:
1. v1 page: two-stage TPS2121 chain, Stack>PSU in stage A, then vs USB in stage B.
2. v2 page (design/power-path-v2.html, power-block-diagram-v2.png): user's original order —
   stage A = PSU (IN1) vs USB (IN2), stage B = Stack (IN1) vs stage-A output (IN2). 5V_RF/12V: Stack vs PSU.
3. THEN found: stack power has no separate input. On real targets (OBC Rev2, screenshots 08/09/11/12)
   stack power enters via the backplane connector J2 (pin 3 EPS_+3V3, CAN 19/21, GND 17/20/22/23), and
   the OBC already muxes USB vs EPS_+3V3 locally (ESD/REG/MUX block U1/U2/U4). OBC Rev2 has NO JST-GH
   debug port (P1 2x6 header is likely its debug header — unverified).
   If stack power arrived on J1, mux IN1 and OUT would be the same net → TPS2121 oscillates. v2 is invalid.

RECOMMENDED (awaiting user + Alex sign-off; page/diagram NOT yet updated):
- Port standard: J1 power pins are INPUTS to the target. Each target feeds them into its own power-path
  mux at LOWEST priority (like OBC's USB). Targets never drive power out on J1. "Stack first" happens on
  the target. Unused rails NC on target.
- Debugger = pure source:
  - U3: 3V3 PSU(IN1) vs +3V3_USB(IN2) → +3V3_PU.  U7: 5V PSU(IN1) vs +VBUS_PROT(IN2) → +5V_PU.
  - 12 V and 5 V_RF: PSU only.
  - Per-rail output switch to J1, OFF by default: reuse TPS2121 (IN2=GND, PR1/CP2=GND, OV1 as active-high
    disable). Back-to-back FETs block both directions when off.
  - TGT_PWR_EN from Pico GP22 + slide switch OFF / PICO / ON (PSU-only use without laptop).
  - ST of U3/U7 → GP14/GP15. ADC GP26–28 read 3V3/5V/12V outputs via dividers.
  - XREF diode-OR shrinks to 4 PSU rails + VBUS (3× BAT54C).

## Proven design values (TPS2121RUXR, datasheet SLVSEA3F §10.4 XREF)
Pins (RUX): IN1 7 · IN2 2 · OUT 1,8 · CP2 3 · OV2 4 · OV1 5 · PR1 6 · ST 9 · ILM 10 · SS 11 · GND 12.
VREF 1.06 V typ (1.01–1.10). OVx ≥ VREF disables channel. PR1 > CP2 → IN1 preferred. CP2 ≥ VREF enables
fast switchover (t_FSW ≈ 5 µs). Only one valid input → it powers OUT regardless of PR1/CP2.
- XREF_2V5: VAUX (Schottky OR) → U14 TLV70433 (+3V3_AUX) → 2.00 kΩ → U15 LM4040-2.5 B (150–400 µA).
- PR1 divider (R_B = 10.0k), hysteresis R_H from PR1 to ST (ST pulled up 10k to +3V3_AUX):
  V_fall = Vx + R_T[Vx/R_B − (3.3−Vx)/(R_H+R_PU)],  V_rise = Vx + R_T[Vx/R_B + Vx/R_H]
  3V3: R_T 2.10k, R_H 54.9k → 3.00 / 3.12 V.  5V & 5V_RF: 8.25k, 150k → 4.52 / 4.70 V.
  12V: 34.8k, 287k → 11.1 / 11.5 V.  (TI's 1 MΩ does nothing with these low-Z dividers.)
- OV dividers (R_B 10.0k): 3V3 26.1k → 3.83 V; 5V 44.2k → 5.75 V; 12V 118k → 13.6 V.
- ILM 100k (max) → 1.24 A typ (≈0.83–1.65 A); I_LIM ≈ 65.2/R_ILM[kΩ]^0.861. SS 100 nF (~800 V/s).
- C_OUT: 2× 22 µF (GCM31CR71A226KE02K) on rails driving J1; 12 V: 2× 10 µF 35 V (CGA5L1X7R1V106K160AE).
  Droop: V_min = V_SW − t_FSW·I/C → 3.00 − 5 µs·1 A/44 µF = 2.89 V.
- MIC2544: R5 261 Ω → 464 Ω (I = 230/R = 0.5 A, USB 2.0 budget).
- tools/calc.py recomputes all of this.

## V1 STATUS (Nov 26 2026) — architecture decided, schematic cleaned
- Plan + all math: design/V1_PLAN.md (numbers from tools/calc_v1.py). One TPS2121 per rail; DIS_x → BAT54A →
  OV1/OV2 for off-by-default enable; Pico GP16–19 via 2N7002 + DIP force-on; ADC GP26–28.
- Backup of untouched V0: C:\Users\Public\Documents\Altium\Debugging Board V0 backup 2026-11-26\
- Done in Altium (saved locally, NOT committed / not saved to server):
  sheet 2 DebugBoardMuxes emptied (title block kept); sheet 1: U3, unwired TPS2121, R11–R18, P1 jumper deleted;
  nets renamed: +5V_PSU, +3V3_PSU, +12V_PSU, +5V_RF_PSU (banana), +3V3_TGT/+5V_TGT/+12V_TGT/+5V_RF_TGT (J1, P3),
  +3V3_RPI (Pico 3V3 + CAN chips), +3V3_USB, +VBUS_PROT, CAN_P/N→CAN_H/L, RST→MCU_RESET; R5 → 464 Ω + note.
- MIC2544-2 is active-LOW EN (datasheet checked) → with EN tied to VBUS, U4 was always off. DONE Nov 26:
  U4 = MIC2544-1YMM-TR (workspace CMP-00008-1, footprint FP-MSOP-8LD-PL-1-MFG), rewired and netlist-verified
  (IN+EN=+VBUS, OUT=+VBUS_PROT, FLG→D1/R3, ILIM→R5 576 Ω→GND). C4 100 nF on +VBUS_PROT (output HF bypass).
  C23 = 1 µF 25 V ceramic 0805 (−55…125 °C → X7R-class) on +VBUS (U4 IN bypass), verified Nov 26.
  No MPN parameter on the symbol — check ActiveBOM shows a part choice. PCB: C23 at U4 pin 7, C4 at pins 6/8.
- Altium popups (dropdown lists, Components panel, replace dialogs) are invisible to computer-use screenshots;
  docked Properties panel + modal dialogs work. Leave part swaps / font picks to the user.
- Sheet 1 has a "NET SUFFIX CONVENTION" text frame (Times font; user may switch it to Courier New).
- Datasheet review done (V1_PLAN §8): TPS2121/AP63203/TCAN330G/MCP2515/TLV704/LM4040 all match plan & schematic.
  Datasheet PDFs: fetch with WebFetch, then `pdftotext -layout` (in /mingw64/bin) on the saved file.
  Open sheet-1 issues: UART LED R6/R7 260 Ω load lines (→1.5–2.2 k), no CAN 120 Ω
  termination, no SWD series R. Pico/RP2040 verified (reference/ PDFs): 3V3 out <300 mA; GPIO V_PIN ≤ IOVDD+0.5 V
  → stack-powered target can back-power an unplugged Pico via J1 signals: add series R (100 Ω out / 1 kΩ on
  SWO, UART_RX) or an Ioff buffer. Still unverified: BAT54A/C pinout, Y1 C_L.
- DONE Nov 26: R6/R7 2.2k; series R R2 SWCLK/R4 SWDIO/R8 MCU_RESET/R11 UART_TX = 100 Ω, R9 SWO/R12 UART_RX = 1k
  (between Pico pins and ports; labels overlap → tidy). 50 parts.
- Computer use: NEVER call open_application on Altium when it's running (it spawns extra X2.exe instances);
  click its window instead. Multi-select via SCH Filter query (e.g. IsPart And (Designator = 'R?')), then
  Properties edits all; Tools→Annotation→Annotate Schematics Quietly for designators.
- Local backup lib: Debugging Board V1/Libraries/SquidDebugger_V1/ (LibPkg + compiled IntLib, 13 parts, verified).
  Bring Altium forward with PowerShell AppActivate(5656) — never open_application.
- Sheets: 1 DebugBoard, 2 DebugBoardMuxes (inputs/AUX/5V RF/12V), 3 DebugBoardPowerControl, 4 DebugBoard3V3Mux,
  5 DebugBoard5VMux. Sheets 2-5 are GENERATED by tools/gen_sheet2.py (4 output paths) in the "wired" style
  (tools/wired.py Block + tools/wired_blocks.py layouts; templates in tools/templates); verify with tools/verify_gen.py
  (93/93, errors=0). Sheet grid = sheet 1 (snap 5, visible 10, mils). After regenerating: Altium Reload = Yes,
  stale copies = Don't Save / Save None. Sheet 1 still has 12 pre-existing off-grid ports (CAN/UART/MCU_RESET).
  Hand edits in Altium are fine now, but regenerating would overwrite them.
  Sheet-1 Pico ports added by tools/patch_sheet1_pico.py. SchDoc header Weight must = record count.
- Change log for presentation: design/V1_CHANGELOG.md (what/why/alternatives) — append every change.
- Net scope Global (HierarchyMode=3) DONE. TPS2121RUXR = CMP-019-00076-1 (pins verified).
- MPS panel is a slide-out + right-click menu: invisible to computer use → user creates workspace parts.
- Next: remaining parts (V1_PLAN shopping list), then capture V1_PLAN §3 on sheet 2.

## Earliest V0 (seen in A365 viewer, Nov 26)
Used 2× TPS2113ADRB muxes: 5V (IN1 +5V_BNN, IN2 +VBUS_O, caps C2/C3, R2 260 ILIM) and 3.3V (IN1 +3.3V_RPI =
Pico 3V3 out, IN2 +3.3V_BNN, caps C5/C6, R8 260). No AP63203 buck yet. C2/C3/C5/C6 are leftovers of those
muxes → V1: C2 = 5V mux IN1 cap, C3 = 5V mux IN2 cap, C6 = 3V3 mux IN1 cap, C5 optional/delete.
260 Ω values came from TPS2113A I = 500/R_ILIM, not the MIC2544's 230/R.

## V0 as-built netlist audit (Nov 26 2026, tools/schnet.py on the real SchDocs)
Altium project: C:\Users\Public\Documents\Altium\Debugging Board V1\ (DebugBoard.SchDoc, DebugBoardMuxes.SchDoc).
- No rail on J1 has a real source: U3 OUT = +5V_PRI and U5 OUT = +3.3V_PRI drive nothing; J1 +3.3V/+5V nets
  have no driver. Banana nets are "+5V BNN"/"+3.3V BNN" (caps only) but mux inputs are +5V_PSU/+3.3V_PSU.
  +5V_STACK/+3.3V_STACK have no source. +3.3V_USB (U13 out) feeds nothing. 12V and 5V RF: banana → J1 direct.
- CAN chips (U2 VCC, U6 VDD, R10 pull-up) sit on +3.3V = J1 pin 1 → only powered when the TARGET powers J1.
- Divider taps wired to the rail, not the mid-node (bottom R goes rail→GND):
  U3: OV1 = +5V_STACK via 23.7k, no pull-down → IN1 always disabled. OV2 divider R15/R18 top floating → OV2=0.
  PR1 = rail via 8.2k, CP2 = rail via 10.2k, both no pull-down → PR1≈CP2, priority undefined.
  U5: OV2 = +3.3V_PSU via 23.7k, no pull-down → IN2 always disabled; PR1/CP2 same problem; OV1 OK (trip 6.1 V).
- ILM/SS/ST floating on U3 and U5. Second TPS2121 on each sheet fully unwired. Sheet-2 parts unannotated (R?).
- U4 is MIC2544-2 with EN tied to VBUS — check enable polarity (-1 vs -2 variant) in datasheet.
- Duplicate names: CAN_H/CAN_P and MCU_RESET/RST on one net each. Lib paths point to %TEMP% zips.

## V0 schematic fixes still to do
1. U3 values came from TI §10.5 XCOMP (10.2k/5k) — redo per XREF.
2. ILM / SS / ST appear unconnected on both TPS2121 instances.
3. TPS2121s split over sheets 1 and 2, unannotated R? parts → one Power_Mux.SchDoc, re-annotate.
4. Power MCP2515/TCAN330 from +3.3V_RPI (avoid back-powering RP2040); 33 Ω series on SWDIO/SWCLK.
5. P1 5V↔5V_RF jumper shorts two outputs — warn on silk or remove.
6. TVS on PSU banana inputs: SMBJ3.3A, SMBJ5.0A ×2, SMBJ13A.
7. Rename nets +5V_BNN → +5V_PSU etc.; BOM typo +5V_INN; drop BOM lines 9 and 15 (TPS2113).
8. Net Identifier Scope → Global (Netlabels and ports global).
9. Optional: switchable 120 Ω CAN termination (open BOM item).

## Open questions
- Alex/team: approve "J1 power pins are target inputs" as the Squid Debug Port standard?
- Board-under-test current per rail: unknown; design to 1 A connector limit, measure on bench later.
- Confirm OBC P1 2x6 header function.

## Next steps
1. Get sign-off on the port standard.
2. Update tools/template.html + tools/diagram.py to the recommended architecture → regenerate v3
   (`python3 tools/build.py`), and write a one-page Squid Debug Port spec for other board designers.
3. Update BOM xlsx (reference/SDSL_Squid_Debugger_V1_BOM.xlsx) with the delta.
4. Capture Power_Mux.SchDoc in Altium (local copy: Project » Project Packager, "Unlink project from the
   server during packaging"; Auto Save + Local History on; later right-click → Make Project Available Online).

## Files
- design/  power-path-v2.html (published: https://claude.ai/artifact/DuwyN3ywnTesMGacN4ii11),
  power-block-diagram-v2.png (for placing on the schematic). Both show the superseded v2 order.
- tools/   diagram.py (SVG generator), template.html (page, {{SVG}} placeholder), calc.py, shot.js,
  build.py (diagram + page + PNG). Needs Python 3 and Node + `npm i playwright` (+ `npx playwright install chromium`).
- reference/ Notes.docx, BOM xlsx, SquidSat SSC26 paper, TI §10.4 excerpt.
- screenshots/ V0 PCB/schematics, whiteboard, J1 close-ups, OBC Rev2 board and crops.
