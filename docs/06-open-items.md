# 6. Open items before ordering boards

## Schematic / BOM
- [ ] **Switchable 120 Ω CAN termination**: a 2-pin jumper (or solder jumper) with silkscreen text
      "CAN TERM: open in stack, closed on bench" (or split 2×60 Ω + 4.7 nF).
- [ ] **Ioff buffers on SWO / UART_RX** (or all debug lines), so a powered target cannot feed an unpowered Pico
      (about 3 mA per line today, see docs/02 §2.8).
- [ ] **eFuse footprint check:** `SOIC127P600X170-9N` (script-made) against TI land pattern DDA0008: pad sizes and
      the 2.4 × 3.1 mm thermal pad. Also set the library footprint's reference point to its centre.
- [ ] Optional: eFuse `FLT` pins wire-ORed to Pico GP22, so firmware sees an over-current directly.
- [ ] Optional: D7 SMBJ13A → SMBJ12A (clamps at 19.9 V instead of 21.5 V; the eFuse's maximum is 21 V).
- [ ] **D4–D6 part choice → SMBJ5.0A** (they currently borrow the SMBJ13A symbol and comment).
- [ ] **Real MPNs for the generic parts** (0805 resistors, 100 nF caps) in ActiveBOM.
- [ ] **Fix the TCAN330 workspace component** (CMP-031-00060-1): set TXD = Input, RXD = Output, so "Update from
      Libraries" doesn't undo the local fix.
- [ ] **Verify crystal Y1** (TXC 7M-16.000MAHL-T) load capacitance against C7/C8 = 22 pF.
- [ ] **Verify the BAT54A/BAT54C pinout** against Nexperia's datasheet (the vendor symbols match the standard pinout).
- [ ] **2N7002-7-F footprint:** uses 2.03 mm pad pitch; consider the standard SOT-23 footprint (`SOT95P230X110-3N`).
- [ ] Optional: `100` → `100R` style values, so ohms are unambiguous.
- [ ] Optional: rail LEDs on the `_TGT` rails.
- [ ] Remove the dead `%TEMP%` library links from the project file.
- [ ] Upload `SquidDebugger_V1.IntLib` to the SDSL Altium 365 workspace (Library Importer) and swap the parts to
      workspace items.

## Team decisions
- [ ] Alex/team sign-off on the **port rule** (J1 power pins are target inputs at lowest priority).
- [ ] Confirm the OBC Rev2 P1 2×6 header function.
- [ ] Measure per-rail current of real targets (each bench rail is limited to 0.9 A; J1 contacts are rated 1 A).

## PCB (161 parts placed, not routed)
- [ ] **Routing**, after sign-off on the placement (`design/V1_LAYOUT.md`).
- [ ] Copper under each eFuse thermal pad (vias to the GND planes).
- [ ] Bottom-side height: the eFuses are 1.7 mm tall. Confirm the standoff height with the flight-stack envelope.
- [ ] L1 footprint origin (workspace part) is far from its pads; fix it in the workspace library.
- [ ] Re-check J1 footprint orientation against the target boards.
- [ ] New bottom-side silkscreen artwork (mantis + ladybug), after everything else.

## Bench
- [ ] Run the bring-up tests in [docs/07](07-bench-procedure.md): current-limit test per rail and the hot-plug glitch test.
