# Datasheets

Vendor PDFs are not committed: they're copyrighted and large. Each link goes to the manufacturer's current
document. The revision used for the V1 design review is noted.

| Part | Use | Datasheet (revision reviewed) |
|---|---|---|
| TPS2121 | Rail power mux U3/U5/U7/U8 | [TI SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf) |
| TPS259621 | Bench-rail current limit (eFuse) U14–U17 | [TI SLVSET8A](https://www.ti.com/lit/ds/symlink/tps2596.pdf) ; package drawing [DDA0008B](https://www.ti.com/lit/pdf/pptd058) |
| MIC2544-1 | USB current limit U4 | [Microchip MIC2544/48](https://ww1.microchip.com/downloads/en/DeviceDoc/MIC2544.pdf) |
| AP63203 | USB 3.3 V buck U13 | [Diodes DS41326](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf) |
| TLV70433 | AUX LDO U9 | [TI SBVS148F](https://www.ti.com/lit/ds/symlink/tlv704.pdf) |
| LM4040-2.5 (B) | 2.5 V reference U10 | [TI SNOS633N](https://www.ti.com/lit/ds/symlink/lm4040-n.pdf) |
| TCAN330G | CAN transceiver U2 | [TI SLLSEQ7F](https://www.ti.com/lit/ds/symlink/tcan330.pdf) |
| MCP2515 | CAN controller U6 | [Microchip DS20001801J](https://ww1.microchip.com/downloads/en/DeviceDoc/MCP2515-Stand-Alone-CAN-Controller-with-SPI-20001801J.pdf) |
| Raspberry Pi Pico | U1 | [RP-008307-DS](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf) |
| RP2040 | Pico MCU | [RP-008371-DS](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf) |
| BAT54A / BAT54C | Disable diodes / VAUX OR | [Nexperia BAT54 series](https://assets.nexperia.com/documents/data-sheet/BAT54_SER.pdf) |
| BZX84-C4V7 | PR1 clamp | [Nexperia BZX84 series](https://assets.nexperia.com/documents/data-sheet/BZX84_SER.pdf) |
| 2N7002-7-F | Enable FETs | [Diodes 2N7002](https://www.diodes.com/assets/Datasheets/ds11303.pdf) |
| SMBJ5.0A / SMBJ13A | Input TVS | [Littelfuse SMBJ](https://www.littelfuse.com/assetdocs/littelfuse-tvs-diode-smbj-datasheet) |
| 219-4MST | DIP switch | [CTS 219 series](https://www.ctscorp.com/wp-content/uploads/219.pdf) |
| JST BM12B-GHS-TBT | J1 | [JST GH series](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf) |

Ordering links (DigiKey/Octopart) for every new V1 part: [`design/V1_PARTS_LINKS.md`](../design/V1_PARTS_LINKS.md).
`TPS2121_datasheet_sec10.4_XREF.png` is a short excerpt of the TPS2121 datasheet's XREF example, used in the
design discussion.
