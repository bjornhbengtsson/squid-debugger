# Squid Debugger V0 → V1: Change Log (for review / presentation)
Running log, newest at the bottom. Each entry gives **what** changed, **why**, and the **alternatives** we considered.
Numbers are backed by `tools/calc_v1.py` and the datasheets cited in `V1_PLAN.md` §8.

---

## 1. Power architecture: the debugger is a pure source (decided Nov 26 2026)
- **What:** J1 power pins only *output* power to the target. The target ORs J1 in at its lowest priority; the
  debugger never accepts power back.
  - One TPS2121 per rail does source select, current limit, reverse blocking and on/off.
  - Rails are OFF by default and enabled by the Pico (GP16–19) or a DIP switch.
- **Why:** real targets (e.g. OBC Rev2) already take stack power on their backplane and mux USB/EPS locally.
  If stack power also came in on J1, a mux's input and output would be the same net, and it would oscillate.
- **Alternatives considered:**
  - *v1 page:* a two-stage mux chain (Stack>PSU, then vs USB). Rejected: no stack input exists on the debugger.
  - *v2 page:* PSU vs USB, then Stack vs that. Rejected for the same reason.
  - *Per-rail output switch as a separate TPS2121 or eFuse (e.g. TPS25947):* rejected in favour of one TPS2121
    per rail, with OV1/OV2 driven high through a diode to switch it off. That's 4 chips instead of 6, and the TPS2121
    datasheet confirms OUT = Hi-Z when both OVx are above VREF.

## 2. V0 audit and clean-up (Nov 26)
- **What (sheet 1):**
  - Deleted U3 (TPS2121), its 8 divider resistors R11–R18, the unwired second TPS2121 and the P1 5V↔5V_RF jumper.
  - Sheet 2 (DebugBoardMuxes) emptied. Untouched V0 backup: `Debugging Board V0 backup 2026-11-26`.
- **Why:** the netlist extraction showed:
  - The mux dividers were wired to the rail instead of the mid-node, which permanently disabled IN1 (5 V) or
    IN2 (3.3 V).
  - The mux outputs drove nothing, and the banana-jack nets never reached the muxes.
  - ILM, SS and ST were left floating.
  - P1 shorted two supply outputs together.
- **Alternatives:** patch the V0 muxes in place. Rejected: nearly every connection was wrong, and the architecture
  changed anyway.

## 3. Net naming convention (Nov 26)
- **What:** `_PSU` = banana input, `_USB` / `+VBUS_PROT` = laptop USB, `_RPI` = Pico 3V3, `_AUX` = always-on
  housekeeping, `_TGT` = switched output on J1/P3. A legend text frame is on sheet 1.
  - Also renamed: CAN_P/N → CAN_H/L, RST → MCU_RESET, +VBUS_O → +VBUS_PROT.
- **Why:** V0 used the same name (`+5V`) for "whatever reaches J1", which hid the unconnected mux outputs. The
  suffix shows which side of the switch a net is on.
- **Alternatives:** `_OUT`, `_J1` or `_DUT` instead of `_TGT`. `_TGT` matches debug-probe convention (VTarget).

## 4. CAN chips moved to the Pico's 3V3 (Nov 26)
- **What:** U2 TCAN330G, U6 MCP2515 and R10 moved from `+3.3V` (J1 pin 1) to `+3V3_RPI`.
- **Why:** in V0 they were only powered when the *target* powered J1. Pico 3V3 out is rated < 300 mA (Pico
  datasheet), and the CAN chips draw only tens of mA.
- **Alternatives:** feed them from +3V3_AUX or +3V3_USB. Rejected: they must share the Pico's I/O voltage domain.

## 5. USB current limit U4: enable polarity fixed and limit lowered (Nov 26)
- **What:**
  - U4 MIC2544-2YMM-TR → **MIC2544-1YMM-TR** (new workspace part CMP-00008-1, same MSOP-8 footprint), rewired.
  - R5 260 Ω → **576 Ω** (I = 230/R ±20 % → 0.40 A typ, 0.32–0.48 A).
- **Why:**
  - The -2 has an **active-low** enable, and EN was tied to VBUS, so the whole USB power path (and +3V3_USB)
    never turned on. This bug went back to the very first V0.
  - USB 2.0 guarantees only 500 mA, and the 0.88 A setting would trip the laptop port, which resets the Pico.
- **Alternatives:**
  - Keep the -2 and tie EN to GND (no BOM change).
  - Use 464 Ω (0.50 A typ, but up to 0.60 A).
  - Keep 260 Ω for USB-3/USB-C-only use (0.88 A).
- **Note:** the 260 Ω values came from the TPS2113A formula in the earliest V0 (I = 500/R), not the MIC2544's.

## 6. U4 input bypass capacitor added (Nov 26)
- **What:** **C23 = 1 µF 25 V X7R-class 0805** on +VBUS at U4 IN. C4 100 nF stays on the output (+VBUS_PROT).
- **Why:** the rewire moved C4 to the output, which left U4's input with no local bypass. That causes ringing
  on current-limit and turn-on edges.
- **Alternatives:** move C4 back to the input (then the output loses its high-frequency bypass). A 10 V 0805 was
  rejected because of DC-bias derating at 5 V.

## 7. Leftover V0 decoupling capacitors reassigned (plan, Nov 26)
- **What:** C2, C3, C5 and C6 were the input caps of the earliest V0's TPS2113A muxes.
  - V1 reuses C2 (5V mux IN1), C3 (5V mux IN2) and C6 (3V3 mux IN1), upgraded to 1 µF 0805.
  - 3 new input caps go on the other inputs (the one on 12 V is rated 50 V).
  - C5 is optional.
- **Alternatives:** delete them all and add new caps (same BOM count, loses traceability).

## 8. Datasheet review (Nov 26)
- TPS2121, AP63203, MIC2544, TCAN330G, MCP2515, TLV70433, LM4040, Pico and RP2040 were checked; details are in
  `V1_PLAN.md` §8.
  - The AP63203 buck already matches its datasheet's recommended L and C values exactly.
- **R3 (fault LED) kept at 260 Ω:** MIC2544 FLG is rated 50 mA abs max, and 11.5 mA is fine.
  - *Alternative:* 1 kΩ for a dimmer LED and less current (not needed).
- **Still to verify:** BAT54A/C pinout, crystal Y1 load capacitance.

## 9. UART LED resistors R6/R7 260 Ω → 2.2 kΩ (DONE Nov 26)
- **Why:** each LED drew ≈5.4 mA straight off UART_TX (the Pico pin) and UART_RX (the **target's** TX pin). The
  RP2040 only guarantees VOH ≥ 2.62 V up to its selected drive (default 4 mA). The LEDs were also lit at idle.
  2.2 kΩ → ≈0.6 mA.
- **Alternatives:**
  - Raise GP8 drive strength to 8 mA in firmware (does not help the target's pin).
  - Drive the LEDs from spare GPIOs GP14/GP15 as firmware activity blinkers.
  - Add a buffer for the LEDs.

## 10. J1 signal protection: series resistors (DONE Nov 26)
- **What:** each resistor sits on the wire between the Pico pin and its port (the Pico-side nets are unnamed):

  | Resistor | Value | Signal | Pico pin |
  |---|---|---|---|
  | R2 | 100 Ω | SWCLK | GP2 |
  | R4 | 100 Ω | SWDIO | GP3 |
  | R8 | 100 Ω | MCU_RESET | GP4 |
  | R9 | **1 kΩ** | SWO | GP5 |
  | R11 | 100 Ω | UART_TX | GP8 |
  | R12 | **1 kΩ** | UART_RX | GP9 |

  - All six are the generic 0805 workspace resistor (CMP-009-00183-1).
  - The UART LEDs (R6/D2, R7/D3) stay on the connector side. Done with R6/R7 = 2.2 kΩ.
  - Note: UART reaches the outside only through P2. J1 has no UART pins.
- **Why:** the RP2040 abs max is V_PIN ≤ IOVDD + 0.5 V. A target powered from the stack, with the debugger's USB
  unplugged, would drive 3.3 V into unpowered RP2040 pins and back-power the Pico through its ESD diodes. The
  resistors cap that fault current at ≈3 mA, and they also damp ringing on the SWD lines.
- **Alternatives:**
  - **Power-off-isolating buffers** (74LVC1T45 / SN74LVC2G125 with Ioff), powered from +3V3_RPI. They go fully
    Hi-Z when the Pico is off, at the cost of 3–4 ICs and direction control for SWDIO.
  - Firmware-only (keep pins Hi-Z until the target rail is seen on the ADC). Doesn't cover an unpowered Pico.
- **Firmware rules that go with it:** drive MCU_RESET open-drain style (low or Hi-Z), and keep the debug pins Hi-Z
  until the target rail is up.

## 11. Project setting: Net Identifier Scope → Global (DONE Nov 26)
- **What:** Project Options → Net Identifier Scope = *Global (Netlabels and ports global)*. The .PrjPcb now has
  `HierarchyMode=3`.
- **Why:** sheet 2 needs Pico signals from sheet 1 (EN_x on GP16–19, ADC_x on GP26–28) by net label alone.
- **Alternatives:** *Hierarchical* (needs sheet symbols and entries; overkill for 2 sheets), or *Flat* (ports only,
  so every crossing would need a port instead of a net label).

## 12. TPS2121RUXR workspace part (DONE Nov 26)
- CMP-019-00076-1 (Integrated Circuits). Symbol pins verified against the datasheet RUX pinout: IN1 7, IN2 2,
  OUT 1/8, CP2 3, OV2 4, OV1 5, PR1 6, ST 9, ILM 10, SS 11, GND 12. This replaces the V0 symbol that was loaded
  from %TEMP%.

## 13. Local backup component library (DONE Nov 26)
- **What:** `Debugging Board V1/Libraries/SquidDebugger_V1/`
  - `SquidDebugger_V1.LibPkg`: 13 SchLib + 12 PcbLib sources, plus a 3D folder.
  - `Project Outputs/SquidDebugger_V1.IntLib`, compiled in Altium. It contains 13 components; every symbol is linked
    to its footprint and its pins are verified with `tools/libpins.py`.
  - Parts: TLV70433DBVR, LM4040BIM3-2.5/NOPB, BAT54C,215, BAT54A,215, BZX84-C4V7,215, 2N7002-7-F, SMBJ13A,
    219-4MST, GCM31CR71A226KE02K, CGA5L1X7R1V106K160AE, CL21B105KAFNNNE, GRM21BR71H105KA12L, MIC2544-1YMM-TR.
  - Sources come from vendor downloads (SnapEDA, SamacSys, Ultra Librarian, Murata/TDK/Samsung). The cap IntLibs
    were unpacked with `tools/intlib_extract.py`.
- **Why:** a backup that doesn't depend on the 365 workspace, and a single file to bulk-upload with the Library Importer.
- **Not included:**
  - TPS2121RUXR: the vendor symbol has stray duplicate pins; the workspace part CMP-019-00076-1 is used instead.
  - SMBJ5.0A: it reuses the SMBJ13A symbol and footprint (change the part number at placement or in the workspace).
- **Alternatives:** create each workspace part one by one in the component editor (slow, and pop-ups block automation),
  or use the SamacSys Library Loader for the `.epw` files.

## 14. Power sheets generated from the plan (Nov 26), staged in `Debugging Board V1/_generated/`
- **What:** `tools/gen_sheet2.py` builds the V1 power circuitry straight from V1_PLAN §3 as two A3 sheets:
  - **PowerPath.SchDoc** (62 parts):
    - Bench inputs: TVS + input caps.
    - Always-on AUX: 3× BAT54C diode-OR, TLV70433, LM4040 2.5 V reference.
    - U3 (3V3) and U5 (5V) muxes, PSU > USB, with priority + hysteresis, OV dividers, the BZX84 PR1 clamp and the
      BAT54A disable.
    - U7 (5V_RF) and U8 (12V) single-input switches.
  - **PowerControl.SchDoc** (28 parts):
    - 4× enable (4.7k DIS pull-up, 2N7002, 100R/100k gate).
    - SW1 DIP force-on.
    - ADC dividers (49.9k/100k, 100k/100k, 470k/100k + 100 nF).
    - New: **100k series resistors from the mux ST pins to the Pico** (limits back-feed to ≤ 27 µA).
  - Style: every pin has a wire stub with a net label (GND power port); blocks are headed.
  - `tools/verify_gen.py` confirms all 90 parts and every pin against the spec, with 0 errors.
- **Why generated:** placing ~90 parts and ~250 connections by GUI was impractical, and the spec can be verified
  before Altium opens it. `tools/schgen.py` reads/writes the SchDoc container byte-exactly. Note: the header `Weight`
  must equal the record count, or Altium silently stops loading partway through.
- **Why two sheets:** all 8 blocks don't fit one A3 at readable size (checked with a layout search).
- **Alternatives:** draw by hand in Altium (hours); one A2 sheet (needs a new title-block template); a smaller font.
- **Notes:** the SMBJ5.0A parts reuse the SMBJ13A symbol with comment "SMBJ5.0A", so swap the part choice before the
  BOM. U7/U8 ST pins go to GND (per TI: "connect to GND if not required").

## 15. Power sheets integrated, in sheet-1 style (DONE Nov 26)
- **What:**
  - **Sheet 2** `DebugBoardMuxes.SchDoc` = Power Path, 62 parts.
  - **Sheet 3** `DebugBoardPowerControl.SchDoc` = Power Control, 28 parts.
  - Styled like sheet 1:
    - Sections boxed with heavy frame lines and big Times-24 headings: AUX Supply & 2.5V Reference, 3V3 Power Mux,
      5V Power Mux, 12V Switch, Bench Inputs, 5V RF Switch, Rail Enable, Rail Monitors.
    - Rails use power-port symbols; signals use yellow ports; GND uses ground symbols.
  - **Sheet 1:** 9 new ports on the Pico: GP16–19 → EN_3V3/5V/5VRF/12V, GP26–28 → ADC_3V3/5V/12V,
    GP14/15 → PICO_ST_3V3/5V.
  - **Project:** sheet 3 added, Allow Ports to Name Nets = ON. New ports are type Unspecified (avoids Output vs
    Bidirectional errors).
  - Backups: `_generated/DebugBoard_backup_before_pico_ports.SchDoc`,
    `_generated/DebugBoardMuxes_backup_placeholders.SchDoc`.
- **Verified:** `tools/verify_gen.py` checks all 90 parts and every pin (0 errors). In Altium, Validate PCB Project
  shows no unconnected pins on the new sheets.
  - Remaining errors are expected pin-type complaints: OUT1/OUT8 on one net, and U7/U8 ST tied to GND per TI.
  - Older sheet-1 items remain: CAN ports (bidirectional), the CAN_H/L differential-pair directive, and MCP2515
    TXnRTS left open.
  - **The TCAN330 library symbol has TXD/RXD electrical types swapped** (wiring is correct; ERC complains).
- **Alternatives:** net labels instead of ports (the first generated version; less like sheet 1). One A2 sheet.

## 16. TCAN330 (U2) TXD/RXD pin types corrected (DONE Nov 26)
- **What:** on U2, pin 1 TXD changed from Output to **Input**, and pin 4 RXD from Input to **Output**, matching the
  TCAN33x datasheet (TXD = CAN transmit data input, RXD = receive data output). Wiring is unchanged: CAN_TX =
  U6.TXCAN → U2.TXD, CAN_RX = U2.RXD → U6.RXCAN.
  - Effect on validation: the "CAN_TX multiple Output Pins" and "CAN_RX floating input pins" errors are gone.
  - Backup: `_generated/DebugBoard_backup_before_tcan_fix.SchDoc`.
- **Caveat:** this is a fix on the placed U2 only. The workspace component **CMP-031-00060-1** still has the swap, so
  "Update from Libraries" would bring it back. Fix it in the workspace: edit the component's symbol, set the pin types,
  then release.
- **Alternatives:** fix the workspace part first and update U2 from it (permanent, needs the editor), or suppress
  the ERC messages (hides the real library bug).

## 17. Sheet-1 CAN ports set to Unspecified (DONE Nov 26)
- **What:** all 30 CAN_* ports (14 nets) on sheet 1 changed from Bidirectional to Unspecified, matching the new power
  ports. Connections are unchanged (checked with schnet.py).
  - Backup: `_generated/DebugBoard_backup_before_port_types.SchDoc`.
- **Effect:** Validate errors 16 → 11. The five "Output Pin and Bidirectional Port" errors (CAN_INT, CAN_OSC_2,
  CAN_RX, CAN_SPI_MISO, CAN_TX) are gone.
  - Remaining errors are all expected: TPS2121 OUT1/OUT8 on one net (×4) and U7/U8 ST on GND (×2).
  - Also remaining: CAN_H/L differential-pair directive without a negative-net pairing, and MCP2515 TXnRTS left open
    (internal pull-ups).
- **Left as-is:** the SWD/UART ports (MCU_RESET, SWCLK, SWDIO, SWO, UART_RX/TX) are still Bidirectional and raise no
  errors.
- **Alternatives:** loosen the Connection Matrix in Project Options (hides the check for the whole project).

## 18. Sheet 1 reorganized into boxed sections (DONE Nov 26)
- **What:** every section on sheet 1 is now boxed (sheet-1 heavy frame lines, Times-24 headings).
  - Top-right row: **Squid Standard Debug Port | Banana Jacks | Mounting Holes**.
  - **UART LEDs and Headers** sits above the title block.
  - **Supply Decoupling** is a new box holding C2/C3/C5/C6 (the loose caps), now in one row.
  - **2.54mm Header Breakout** is re-centred in a widened box.
  - Pico, CAN, VBUS limit and buck are unchanged.
  - The NET SUFFIX CONVENTION text frame was removed (the convention lives in V1_PLAN/CHANGELOG #3).
- **How:** `tools/organize_sheet1.py` moves each section as a group, with all shifts snapped to the 100-mil grid.
  `tools/compare_nets.py` confirms connectivity is identical: 50 parts, 42 named + 27 unnamed nets, 0 differences.
  - An earlier attempt with fractional shifts broke the UART connections. The compare caught it before install.
- **Backups:** `_generated/DebugBoard_backup_before_organize.SchDoc`, plus a full project copy in
  `Altium/Debugging Board V1 backup <date_time>/`.
- **Alternatives:** keep the note (now redundant); move C2/C3/C6 to sheet 2 beside their muxes (the plan's
  original idea; better for the PCB, but more churn on the generated sheet).

## 19. Leftover decoupling caps moved to their muxes; C5 removed (DONE Nov 26)
- **What:**
  - **C2** (+5V_PSU → U5 IN1), **C3** (+VBUS_PROT → U5 IN2) and **C6** (+3V3_PSU → U3 IN1) moved from sheet 1 into their
    mux boxes on sheet 2. They're now **1 µF 25 V X7R 0805 (CL21B105KAFNNNE)**, matching every other mux input cap,
    and replace the old generic 100 nF 1210. The designators are kept, so the PCB sees them as the same parts.
  - **Consistent rule:** every TPS2121 IN pin has one 1 µF cap inside its own mux box:
    - C6/C26 on U3, C2/C3 on U5, C24 on U7, and C25 (50 V) on U8.
    - The Bench Inputs box now holds only the TVS diodes.
  - **C5 deleted.** +3V3_RPI already has C1 at the TCAN330 VCC, C9 at the MCP2515 VDD, and the Pico's on-board output caps.
  - Sheet 1: the Supply Decoupling box was removed and merged into the USB Buck Converter box, with content re-centred.
- **Verified:**
  - Sheet 1 compare: the only differences are the removed C2/C3/C5/C6 pins.
  - Sheets 2/3 verify: 93/93 parts, 0 errors.
  - No duplicate designators across all 139 parts.
  - The files on disk byte-match the verified versions.
- **Backups:** `_generated/*_backup_before_cap_move.SchDoc` and `Altium/Debugging Board V1 backup 2026-11-26_1427/`.
- **Alternatives:** keep C5 as extra bulk on +3V3_RPI (harmless but redundant); keep the input caps in the Bench Inputs
  box (it's more natural for the PCB to place each one at its IN pin).

## 20. TRIAL: 3V3 Power Mux redrawn in "wired" style on its own sheet (Nov 26, approved)
- **What:** U3 and its 16 parts are drawn the conventional way.
  - Real wires run from the pins, and parts hang off the lines (input caps under the IN rails, divider stacks
    rail → R → node → R → GND, output caps under the OUT rail).
  - Rails use power-port symbols; only sheet-crossing signals (ST_3V3, DIS_3V3) use ports; there are no wire crossings.
  - Internal nodes keep small net labels (OV1_3V3, OV2_3V3, PR1_3V3, ILM_3V3, SS_3V3).
  - New sheet 4 `hardware/DebugBoard3V3Mux.SchDoc`; sheet 2 keeps the other power blocks.
  - Tools: `tools/wired.py` (part rotation, wiring, auto-junctions); layout in `gen_sheet2.py: wired_mux_3v3()`.
  - D12/D14: the BAT54A's two cathodes are swapped (K1 = OV2, K2 = OV1). They're identical diodes; the swap avoids a
    wire crossing.
- **Verified:** 93/93 parts, every pin on its spec net (`verify_gen.py`), 0 errors.
- **Alternatives:** keep the label-per-pin style (compact, but hard to follow); one A2 sheet for all four muxes.

## 21. All power blocks redrawn in "wired" style; power path split over sheets 2–5 (DONE Nov 26)
- **What:** after the 3V3 trial (#20) was approved, every generated block now uses the same wired style.
  - **Sheet 2** `DebugBoardMuxes`: Bench Inputs (TVS), AUX & 2.5V Reference, 5V RF Switch U7, 12V Switch U8.
  - **Sheet 3** `DebugBoardPowerControl`: Rail Enable (4× 2N7002 + DIP SW1), Rail Monitors (ADC dividers, ST taps).
  - **Sheet 4** `DebugBoard3V3Mux`: U3. **Sheet 5** `DebugBoard5VMux` (new): U5, drawn exactly like U3.
  - Single-input switches (U7/U8): the unused IN2/OV2/CP2/PR1 pins get short GND stubs, and ST is tied to the GND pin.
  - The layouts live in `tools/wired_blocks.py`, and `tools/wired.py` is the shared drawing engine.
  - Grid: the generated sheets came from a 1 mm template, so Altium flagged every part "Off grid". They now use
    sheet 1's grid (50 mil snap, 100 mil visible, mils), and block origins snap to 100 mil.
    Result: **0 off-grid warnings on sheets 2–5**, and 404 → 94 Validate messages.
  - Label and port positions adjusted so no text overlaps a part, wire or another label.
- **Verified:**
  - `verify_gen.py`: 93/93 parts, every pin on its spec net, 0 errors.
  - Altium Validate: the same 11 known errors as before. These are TPS OUT1/OUT8 on one net, ST tied to GND on U7/U8,
    the CAN_H/L differential-pair warning, and the unconnected MCP2515 pins U6-4/5/6.
- **Alternatives:**
  - one A2 sheet holding all four muxes (everything in one view, but awkward to print and to read on screen);
  - keep the label-per-pin style (compact, but the circuit can't be followed by eye);
  - put each single-input switch on its own sheet too (consistent, but 2 near-empty sheets).

## 22. Sheet 1 redrawn in the wired style; off-grid ports fixed (DONE Nov 26)
- **What:**
  - Sheet 1 is now generated (`tools/gen_sheet1.py`) in the same style as sheets 2–5. It has the same 10 blocks,
    with real wires inside each block, and ports only for signals that leave a block.
  - The frozen hand capture (`tools/templates/sheet1_source.SchDoc`) is the source, and every part is reused as its own
    template, so footprints, parameters and designators are unchanged.
  - **New layout (ANSI B):** Pico / CAN Transceiver / CAN Controller in the left column. Debug Port, Banana Jacks and
    Mounting Holes on top. VBUS Current Limit and UART in the middle. Buck converter, then Header Breakout, at the bottom.
  - **Series resistors** R2/R4/R8/R9 now sit next to J1, and R11/R12 next to P2.
    - Their Pico-side nodes, unnamed before, are now `PICO_SWCLK`, `PICO_SWDIO`, `PICO_MCU_RESET`, `PICO_SWO`,
      `PICO_UART_TX` and `PICO_UART_RX`. The connector-side nets keep their names.
    - This lets the Pico block be a clean pin-to-port symbol, and the UART LED taps sit on a wired TX/RX line.
  - **Crystal:** Y1 is turned 180° below the OSC pins, so OSC1/OSC2 reach it without crossing.
  - **No-ERC** markers on all unused pins (Pico GP0/1/22, RUN, VSYS, 3V3_EN, ADC_VREF; MCP2515 TXnRTS/RXnBF/CLKOUT;
    MIC2544 NC). Before, the MCP2515 TXnRTS pins had dangling wires, which gave 3 "floating input" errors.
  - The **CAN differential-pair directive** was dropped. Altium needs `_P`/`_N` net names for a pair, so with
    CAN_H/CAN_L it only produced 2 errors. Define the pair in the PCB (Differential Pair Editor) instead.
  - The stale "5V Input" text was dropped; the ILIM note is kept.
  - The 12 off-grid ports are gone, because every object is regenerated on the 100-mil grid.
- **Verified:**
  - `verify_sheet1.py`: 46/46 parts, all 69 nets have identical pins and names (except the 6 renames above), 0 errors.
  - Altium Validate: **6 errors** (was 11), all the known TPS2121 ones (OUT1/OUT8 on one net, ST tied to GND on U7/U8).
    No off-grid warnings on any sheet.
- **Caught on the way:** Altium joins a net label only to net labels and a port only to ports. P4's SWD pins at first
  had ports while J1's wires had labels, which split 4 nets. They now use labels, and the verifier flags this case.
- **Backup:** `_backup/DebugBoard_before_wired_20261126_1523.SchDoc` (local, gitignored) and the source template.
- **Alternatives:**
  - keep the series resistors at the Pico pins (they'd need a fan-out of jogged wires at 100-mil pin pitch);
  - one big wired drawing with no ports between blocks (it'd be a tangle across the Pico's 40 pins);
  - keep CAN_OSC as labels (it'd be simpler, but you couldn't follow the line).

## 23. PCB: layout chosen, V1 parts imported and placed (DONE Nov 27, not routed)
- **What:**
  - Three layout options were sketched and scored (`design/V1_LAYOUT.md`). **Option A, "V0 classic, two-sided"** won
    (400 / 500): same 61 x 100 mm outline, same four M3 holes, Pico / jacks / J1 where V0 had them.
  - Stack-up confirmed as SIG / GND / GND / SIG, 1.6 mm, standard 7628 build. The numbers are in `V1_LAYOUT.md` section 4.
    **They are not yet entered in the Layer Stack Manager.**
  - V1 schematic imported into `hardware/DebugBoard.PcbDoc` (ECO): 139 components, V0 routing and pours removed.
  - All 139 parts placed by script (`tools/pcb_place.py` -> `tools/altium/place_v1.pas`). The four power switches sit
    beside their jacks. Dividers, rail enables and ADC dividers are on the bottom side.
  - The four corner jacks moved 2.7 mm outward so a TVS fits beside each. The GND jack moved up 5.4 mm to make room for
    the DIP switch.
- **Fixed on the way:**
  - Q1-Q4 (2N7002) pointed at a footprint path from a vendor converter (`C:\altium-converter\...`), so the ECO
    reported "Footprint Not Found". The path was removed from sheet 3 (and `tools/schgen.py` now strips it), and
    `SOT103P240X110-3N.PcbLib` was added to the project. The compiled IntLib is missing that footprint.
  - L1's footprint origin is about 1.9 m from its pads. The script places it by bounding box.
- **Verified:** `python tools/pcb_check.py` -> 139 / 139 on the board, all at the table position. Sheet 3 nets unchanged.
- **Not verified:** DRC has not been run. Component rotations for the TPS2121s are not yet tuned to their pinout.
- **Alternatives:** B "power spine" (jacks in one column, 390 / 500); C "wide single-sided" (375 / 500, breaks the outline).

## 24. PCB placement redone from real geometry; silkscreen, stack-up and DRC (DONE Nov 27, not routed)
- **What:**
  - The placement now uses Altium's real footprint boxes and pads (`DumpV1` -> `tools/altium/pcb_dump.txt`), not
    estimated sizes. Every part keeps >= 0.25 mm to its neighbours.
  - **Centre rearranged:** U6 and the GND jack sit side by side under the Pico, SW1 is raised, the CAN transceiver is
    left of SW1. The real SW1, U6 and jack do not fit in one column; in entry 23 the jack pad overlapped SW1's pads.
  - **TPS2121 blocks** are arranged around the IC's pinout (bypass caps at the IN pins, output caps at the OUT pins).
  - **Designators:** all 139 are 0.8 mm / 0.15 mm stroke, beside their part, off pads, holes and vias, inside the board.
  - **Layer stack** entered: 0.035 / 0.21 / 0.0175 / 1.065 / 0.0175 / 0.21 / 0.035 mm (SIG / GND / GND / SIG, 1.59 mm).
  - V0 bottom-side artwork kept; halftone dots removed only under bottom pads and text. Title text now says V1.
- **DRC:** 376 violations = 320 un-routed nets (expected) + 56 inside vendor footprints (16 TPS2121 vias x 3 rules,
  8 SOIC mask slivers). Clearance, shorts, component clearance and silkscreen rules are clean.
- **Found by DRC and fixed:** 6 shorts (bottom resistors on TPS2121 through vias; footprint vias without nets),
  parts on the P3/P4 pin labels, U6 too close to a Pico pad, an off-board placement room.
- **J1 pin 1 is on the right**, so +3V3_TGT and +12V_TGT must cross on the bottom layer under SW1. The layout
  keeps that channel free.
- **Verified:** `pcb_check.py` errors = 0 (positions, spacing, designators, stack read back from the saved file).
- **Alternatives:**
  - keep the GND jack on the centre line and move U6 to the bottom side (breaks the low-profile bottom rule);
  - 0.6 mm designators (fits tighter, but below the usual 0.8 mm legibility minimum);
  - delete the V0 bottom artwork entirely (cleaner silk, loses the V0 look).

## 25. Board lengthened to 61 x 107 mm; GND jack back on the centre line (DONE Nov 27, not routed)
- **What:**
  - Board outline is 7 mm longer (61 x 107 mm). The top mounting holes moved with the edge: pattern 51 x 97 mm.
  - GND jack TP5 is on the centre line again (SW1, jack, CAN controller in one column, as V0). The crystal sits at
    U6's lower right; C9 and R10 at its left.
  - Pico, +3V3 and +5V jacks, buck and VBUS limiter moved up 7 mm. UART stays in its V0 silk frame.
  - TPS2121 footprint vias enlarged on the board from 0.2 / 0.4 mm to 0.25 / 0.52 mm. The hole-size and annular-ring
    violations are gone.
  - Clarke quote removed from the bottom silk. Title now reads "Squid Debugger V1 / By: Bjorn Bengtsson and Alex Jaber".
- **Why:** the user wanted the GND jack where V0 had it. The real parts need 37 mm in that column; V0 has 35 mm.
- **DRC:** 344 = 320 un-routed nets + 16 net antennae (TPS2121 vias, clear when routed) + 8 SOIC mask slivers on U6.
- **Verified:** `pcb_check.py` errors = 0. Images: `screenshots/V1_pcb_top.jpg`, `V1_pcb_bottom.jpg`, `V1_pcb_placement_plan.png`.
- **Watch:** the hole pattern differs from V0 (97 mm instead of 90 mm). Confirm it against the flight stack mounts.
- **Alternatives:** keep 100 mm with the jack beside U6 (entry 24); move U6 to the bottom side; a smaller DIP switch.

## 26. Board shape fixed to the 107 mm outline; 3D models attached (DONE Nov 27, not routed)
- **What:**
  - Entry 25 moved the outline but not the board region, so the solid board still ended at 100 mm and the top holes
    hung off it. `RegionV1` rebuilds the region from the outline. The saved file now has both at 107 mm.
  - 17 parts had no 3D body: SW1, C31/C32/C34/C35/C37/C38, D8-D16, U10. Their STEP files were already in
    `hardware/Libraries/SquidDebugger_V1/3D`; `PlaceV1` now attaches them. Only MH1-MH4 and the logo have no body.
  - SW1's STEP file is modelled lying on its side. `TurnSW1` rotates it 90 degrees about X.
  - `ViewFront` / `ViewBack` / `ViewBoth` show one side of the board at a time.
- **Verified:** `pcb_check.py` errors = 0; DRC unchanged (320 un-routed, 16 antennae, 8 SOIC mask slivers).
- **Not verified:** SW1's model height above the board (it looks right from the top and no longer pokes through the bottom).
- **Note:** the models are attached to the parts on the board, not to the library footprints. *Update From PCB
  Libraries* would drop them; re-run `PlaceV1` (and `TurnSW1`) afterwards.

## Open (not yet changed)
- Switchable 120 Ω CAN termination (alternatives: solder jumper, 2-pin header, or split 2×60 Ω + 4.7 nF).
- Net Identifier Scope → Global; remove the %TEMP% library links; create the TPS2121 workspace part.
