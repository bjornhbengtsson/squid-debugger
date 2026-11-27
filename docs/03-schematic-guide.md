# 3. Schematic guide: sheet by sheet

Every part on the board and why it's there. Sections match the boxed headings on each sheet.

## Sheet 1: `DebugBoard.SchDoc` (main board, 46 parts)

Drawn in the same wired style as the power sheets (image: [sheet 1](../screenshots/V1_sheet1_DebugBoard.png)).
Inside a block, follow the wires. A signal that leaves its block ends in a port with the net name. Rails use power
symbols. Unused pins carry a red No-ERC cross.

### Raspberry Pi Pico
- **U1** Raspberry Pi Pico: USB device to the PC, runs the debugger firmware. Powered from USB VBUS.
  Its 3.3 V output (`+3V3_RPI`) powers only the debugger's own logic (the CAN chips).
- **Series resistors** on every signal that leaves the board. They limit current if the target is powered while the
  Pico isn't (RP2040 pins tolerate only IOVDD + 0.5 V), and they damp ringing:
  - **R2 / R4 / R8 / R11 = 100 Ω** on SWCLK, SWDIO, MCU_RESET and UART_TX (Pico-driven).
  - **R9 / R12 = 1 kΩ** on SWO and UART_RX (target-driven inputs, so they get the larger value).
  - They are drawn beside the connector they protect (J1 in Debug Port, P2 in UART). The Pico side of each one is
    the net `PICO_<signal>` (`PICO_SWCLK`, `PICO_SWDIO`, `PICO_MCU_RESET`, `PICO_SWO`, `PICO_UART_TX`, `PICO_UART_RX`);
    the connector side keeps the plain name (`SWCLK` …).
- Ports on the spare pins connect to sheets 2/3: `EN_x` (GP16–19), `ADC_x` (GP26–28), `PICO_ST_x` (GP14/15).

### CAN Transceiver
- **U2 TCAN330G**: 3.3 V CAN transceiver, rated to 5 Mbps (the "G" grade). Turns CAN_TX/RX logic into CAN_H/L.
  - **S** (silent, pin 8) has an internal pull-down. **R1 10 k** to GND adds an explicit default. The Pico drives it
    via GP6 (listen-only sniffing).
  - **SHDN** (pin 5): the Pico drives it via GP7.
  - The symbol's TXD/RXD pin types were corrected to Input/Output (see changelog #16).
- **C1 100 nF**: U2 supply decoupling.

### CAN Controller
- **U6 MCP2515**: SPI-to-CAN controller (the RP2040 has no CAN peripheral). SPI on GP10–13, INT → GP20, RESET ← GP21.
  - **R10 10 k**: RESET pull-up.
  - **C9 100 nF**: supply decoupling.
  - TX0RTS–TX2RTS are unused (internal pull-ups); RX0BF/RX1BF/CLKOUT are unused outputs.
- **Y1 16 MHz** crystal with **C7 / C8 22 pF** load caps. Y1 is drawn turned 180°, below the OSC pins: OSC1 runs
  round the outside to Y1's left terminal and OSC2 goes to its right terminal, so the two lines never cross. 16 MHz is within the MCP2515's 25 MHz limit at 3.3 V.
  (Open item: check Y1's load capacitance spec.)

### VBUS Current Limit
- **U4 MIC2544-1YMM** (the "-1" is active-high enable): current-limited switch from laptop `+VBUS` to `+VBUS_PROT`.
  - EN is tied to VBUS, so it's always on when USB is present. (V0 used the "-2", active-low, so it never turned on.)
  - **R5 576 Ω** sets the limit: 230/576 = 0.40 A typ (0.32–0.48 A).
  - **D1 + R3 260 Ω**: red fault LED on FLG (open drain, rated 50 mA; this draws about 11.5 mA).
  - **C23 1 µF**: input bypass. **C4 100 nF**: output bypass.

### USB 5V to 3.3V Buck Converter
- **U13 AP63203** (fixed 3.3 V, 1.1 MHz, 2 A): `+VBUS_PROT` → `+3V3_USB`, the USB fallback for the 3.3 V rail.
  Parts exactly as the datasheet's table recommends:
  - **L1 3.9 µH**
  - **C18 10 µF + C22 100 nF** input
  - **C19/C20 22 µF** output
  - **C21 100 nF** bootstrap

### Squid Standard Debug Port
- **J1** JST-GH 12-pin: the cable to the target. Pinout in [01-overview](01-overview.md).

### Banana Jacks
- **TP1–TP5**: bench-supply inputs: +5V_PSU, +12V_PSU, +3V3_PSU, +5V_RF_PSU, GND.

### Mounting Holes
- **MH1–MH4**, tied to GND.

### UART LEDs and Headers
- **P2**: 2-pin UART header (TX/RX).
- **D2 / D3 + R6 / R7 2.2 kΩ**: TX/RX activity LEDs. They draw about 0.6 mA, small enough not to load the lines.
  The old 260 Ω pulled about 5 mA off the target's TX pin.

### 2.54mm Header Breakout
- **P3**: the four `_TGT` rails + GND on 0.1" pins.
- **P4**: SWD + CAN on 0.1" pins, for flying-lead debugging.

## Sheets 2, 4, 5: power path (65 parts)

Sheet 2 `DebugBoardMuxes.SchDoc` (31 parts) holds Bench Inputs, AUX & 2.5V Reference, the 5V RF and 12V switches.
Images: [sheet 2](../screenshots/V1_sheet2_DebugBoardMuxes.png), [sheet 4](../screenshots/V1_sheet4_DebugBoard3V3Mux.png),
[sheet 5](../screenshots/V1_sheet5_DebugBoard5VMux.png).
The two dual-input muxes each have their own sheet: 3V3 on sheet 4 `DebugBoard3V3Mux.SchDoc`, 5V on sheet 5
`DebugBoard5VMux.SchDoc` (17 parts each). How to read a mux sheet, left to right: the two input rails enter at the top
left with their input caps, the three divider stacks (OV1, OV2, PR1) hang below, the BAT54A disable diode joins both
OV nodes to the `DIS_x` port, and the OUT rail leaves at the top right over its output caps, ILM resistor and SS cap.
The two cathodes of the BAT54A go K1 → OV2 and K2 → OV1. The diodes are identical, and this order avoids a wire crossing.

### Bench Inputs
- **D4–D6 SMBJ5.0A, D7 SMBJ13A**: TVS clamps on +3V3_PSU, +5V_PSU, +5V_RF_PSU and +12V_PSU.
  - Note: D4–D6 use the SMBJ13A symbol with comment "SMBJ5.0A". Set the right part choice before the BOM goes out.

### AUX Supply & 2.5V Reference
- **D8–D10 BAT54C** (common cathode): diode-OR of all inputs into `VAUX`.
- **C27 1 µF 50 V** on VAUX.
- **U9 TLV70433** → `+3V3_AUX`, with **C28 1 µF** on its output (required for stability).
- **R13 2.00 k + U10 LM4040-2.5**: the `XREF_2V5` reference, with **C29 1 µF**.

### 3V3 Power Mux (sheet 4): U3 TPS2121 (IN1 = +3V3_PSU, IN2 = +3V3_USB → +3V3_TGT)
| Part | Role |
|---|---|
| C6, C26 | 1 µF input caps on IN1 / IN2 |
| R14 2.10k / R15 10.0k | PR1 priority divider (switch to USB below 3.00 V) |
| R16 54.9k, R17 10.0k | hysteresis to ST, ST pull-up to +3V3_AUX |
| D11 BZX84-C4V7 | clamps PR1 if the wrong supply is plugged in |
| R20 26.1k / R21 10.0k | OV1 divider (PSU input, trips at 3.83 V) |
| R18 26.1k / R19 10.0k | OV2 divider (USB input) |
| D12 BAT54A | lets `DIS_3V3` force both OV pins high (rail off) |
| R22 100k | current limit (≈1.24 A) |
| C30 100 nF | soft start |
| C31, C32 22 µF | output caps |

### 5V Power Mux (sheet 5): U5 (IN1 = +5V_PSU, IN2 = +VBUS_PROT → +5V_TGT)
Same structure as U3: C2/C3 input caps, R23 8.25k / R24 10.0k PR1 (4.52 V), R25 150k / R26 10.0k hysteresis/ST,
D13 PR1 clamp, R29/R30 and R27/R28 44.2k/10.0k OV dividers (5.75 V), D14 disable diodes, R31 current limit,
C33 soft start, C34/C35 output caps.

### 5V RF Switch (sheet 2): U7 (IN1 = +5V_RF_PSU only → +5V_RF_TGT)
Single input: IN2/PR1/CP2/OV2/ST tied to GND.
- C24 input cap, R32 44.2k / R33 10.0k OV1 divider, D15 disable diode, R34 current limit, C36 soft start,
  C37/C38 output caps.

### 12V Switch (sheet 2): U8 (IN1 = +12V_PSU only → +12V_TGT)
Like U7:
- C25 1 µF **50 V** input cap, R35 118k / R36 10.0k OV1 (13.6 V), D16 disable diode, R37 current limit,
  C39 soft start, C40/C41 **10 µF 35 V** output caps.

## Sheet 3: `DebugBoardPowerControl.SchDoc` (Power Control, 28 parts)

Image: [sheet 3](../screenshots/V1_sheet3_DebugBoardPowerControl.png).

### Rail Enable (one set per rail: 3V3, 5V, 5VRF, 12V)
| Part (3V3 / 5V / 5VRF / 12V) | Role |
|---|---|
| R38 / R41 / R44 / R47 4.7k | `DIS_x` pull-up to +3V3_AUX: the rail is off by default |
| Q1 / Q2 / Q3 / Q4 2N7002 | pulls `DIS_x` low when the Pico sets `EN_x` high |
| R39 / R42 / R45 / R48 100R | gate series resistor |
| R40 / R43 / R46 / R49 100k | gate pull-down: off while the Pico is booting or absent |
| SW1 219-4MST | DIP switch, position n forces rail n on (DIS → GND) |

### Rail Monitors
- **R50/R51, R52/R53, R54/R55**: dividers from +3V3_TGT, +5V_TGT and +12V_TGT to ADC_3V3/5V/12V.
- **C42–C44 100 nF**: ADC filter caps.
- **R56 / R57 100k**: mux ST (status) → PICO_ST_3V3/5V, with back-feed limited.
