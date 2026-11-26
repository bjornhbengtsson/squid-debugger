# 4. Firmware notes (Pico)

The hardware assumes the firmware follows these rules.

## Power control
- **Boot with every rail OFF.** `EN_3V3`, `EN_5V`, `EN_5VRF` and `EN_12V` (GP16–19) stay low or Hi-Z until the user
  asks for a rail. The 100 kΩ gate pull-downs already hold the rails off before the firmware runs.
- **Enable a rail:** drive `EN_x` high. Then confirm it on the ADC (GP26–28) after the soft-start time:
  ≈4 ms (3V3), ≈6 ms (5V), ≈15 ms (12V).
- **Read rail voltages:** V_rail = V_adc × 1.499 (3V3), × 2.0 (5V), × 5.7 (12V). 5V RF has no monitor.
- **Source status:** GP14 / GP15 (`PICO_ST_3V3/5V`): high = running from the bench PSU, low = running from USB.
  Disable the Pico's internal pulls on these pins: the line is driven through 100 kΩ.
- The DIP switch can force rails on regardless of firmware. Report it if a rail is up but `EN_x` is low.

## Debug signals
- **MCU_RESET (GP4):** drive it **low or Hi-Z only, never actively high** (emulate open drain). The target has its
  own reset pull-up.
- **Keep SWCLK/SWDIO/SWO/UART Hi-Z until the target rail is confirmed up** (from the ADC, or by sensing the target),
  to avoid back-powering an unpowered target.
- Series resistors are fitted: 100 Ω (SWCLK, SWDIO, RESET, UART_TX) and 1 kΩ (SWO, UART_RX).

## CAN (MCP2515 on SPI1)
- SPI ≤ 10 MHz. Crystal 16 MHz.
- Pins: GP10 SCK, GP11 MOSI, GP12 MISO, GP13 CS, GP20 INT (active low), GP21 RESET (active low, 10 k pull-up).
- TCAN330: GP6 = S (high = silent / listen-only, good for sniffing), GP7 = SHDN (high = shutdown).
- No 120 Ω termination on the debugger yet (open item). On a bench with one target, terminate at both ends.

## USB budget
Everything powered from USB (Pico + U4 output) stays under 500 mA. U4 limits at 0.32–0.48 A. Heavy targets belong
on the bench PSU.
