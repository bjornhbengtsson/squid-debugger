# 7. Bench procedure

How to connect the debugger without surprising the target, and the two tests to run on a new board.

## 7.1 Connecting

1. **Start with everything off.** DIP switch SW1: all four positions off. Bench supply outputs off. USB unplugged.
2. **Set the bench supply first:** 3.3 V, 5.0 V, 5.0 V (RF) and 12.0 V, each with its current limit at about 1.2 A.
   The board's own eFuses limit at 0.9 A; the supply's limit is only a second line. Do not set 5 V above 5.0 V
   (TVS stand-off) or 12 V above 13.0 V.
3. **Ground first.** Plug the GND jack (TP5), then the rail jacks. Unplug in the reverse order.
4. **Connect the J1 cable to the target while the rails are off.**
5. **Plug in USB before enabling any rail.** A powered target next to an unpowered Pico pushes about 3 mA into the
   Pico through SWO and UART_RX (docs/02 §2.8).
6. **Enable rails** from the PC tool (Pico GP16–19), or with the DIP switch when working without a laptop.
7. **Power down:** rails off, then USB, then the cable.

## 7.2 Target in a live stack

When the target sits in a powered SquidSat stack:

- **Leave all four debugger rails OFF.** The stack powers the target. Use only SWD, UART, CAN and GND. The port rule
  (target ORs J1 power in at lowest priority) makes an accidental ON harmless, but there is no reason to have two
  supplies on one board.
- **CAN termination: open.** The stack already has its two 120 Ω terminators. A third one drops the bus to 40 Ω.
- Connect ground before anything else, and keep the stack's supply and the PC on the same mains strip.

## 7.3 Single target on the bench

- **CAN termination: closed, at both ends.** A two-node bench bus needs 120 Ω at the debugger and 120 Ω at the
  target (60 Ω measured between CAN_H and CAN_L with power off). The V1 board has no fitted terminator yet (open
  item): until then, put 120 Ω across CAN_H / CAN_L at P4.
- Budget ≤ 0.8 A per rail. On USB alone, ≤ 0.3 A total.

## 7.4 Ground loops

The laptop's USB ground, the bench supply's negative terminals and the scope ground all meet on this board.

- Use the supply's outputs **floating** (no link from "−" to the earth terminal). The board ties the four returns
  together at TP5.
- For noise measurements on 5 V RF, run the laptop on battery: a grounded laptop charger closes a mains loop through
  the USB shield.
- Scope ground clips go to GND only (TP5 or a mounting hole), never to a rail.

## 7.5 Test: current limit (each bench rail)

| Step | Expect |
|---|---|
| Rail on, electronic load ramping 0 → 1.2 A | output follows up to 0.83–0.97 A, then the voltage folds back |
| Hard short at J1 (through an ammeter) | 0.9 A pulses; the eFuse shuts down hot and retries every 95 ms; nothing else on the board resets |
| Remove the short | rail returns by itself within 0.1 s |
| ADC reading during the short (3V3, 5V, 12V) | low / pulsing while `EN_x` is high |

## 7.6 Test: hot-plug glitch (3V3 and 5V muxes)

Purpose: confirm the PSU ↔ USB switch-over does not reset a target.

1. USB plugged in, bench supply on, rail enabled, 0.3 A load on the rail. Scope on `+x_TGT` at J1 (AC-coupled,
   50 mV/div, 20 µs/div, trigger on a falling edge), second channel on the mux's ST pin.
2. Pull the bench supply's banana plug.
3. **Pass:** the rail dips by no more than about 50 mV for the 5 µs switch-over (droop = t × I / C = 5 µs × 0.3 A /
   44 µF = 34 mV, plus the step to the USB source's voltage), and never goes below 3.0 V (3V3) or 4.4 V (5V).
4. Plug the bench supply back in. The rail steps back to the PSU voltage above 3.12 V (3V3) / 4.70 V (5V) with no
   dip.
5. Repeat at the largest current the target really draws on USB.

If the rail dips further: check the output caps (2 × 22 µF fitted?) and that `XREF_2V5` reads 2.500 V.
