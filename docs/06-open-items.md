# 6. Open items before ordering boards

## Schematic / BOM
- [ ] **Switchable 120 Ω CAN termination** (solder jumper or 2-pin header; or split 2×60 Ω + 4.7 nF).
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
- [ ] Measure per-rail current of real targets (the design allows about 1.2 A per rail; J1 contacts are rated 1 A).

## PCB (V1 layout not started)
- [ ] Update the PCB from the schematic (ECO). Expect many new parts and the removal of C5.
- [ ] Placement: each 1 µF input cap at its TPS2121 IN pin; C23 at U4 pin 7; C4 at U4 pins 6/8; output caps at J1.
- [ ] TPS2121 thermal pad / copper area for up to 1.65 A.
- [ ] Re-check J1 footprint orientation against the target boards.
