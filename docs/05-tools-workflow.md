# 5. Tools and workflow

All tools are plain Python 3 (standard library only). They read and write Altium's binary files directly, so the
design can be checked in CI or on a machine without Altium.

## Checking

| Command | What it does |
|---|---|
| `python tools/schnet.py hardware/DebugBoard.SchDoc` | Prints components and nets of a sheet (geometric netlist). |
| `python tools/verify_gen.py` | Checks sheets 2–6 pin-by-pin against the design spec in `gen_sheet2.py`. Expect `errors=0` (115 parts). |
| `python tools/verify_sheet1.py` | Checks sheet 1 against its frozen source: every net, its pins and its name. Expect `errors=0`. |
| `python tools/compare_nets.py a.SchDoc b.SchDoc` | Connectivity diff of two versions of a sheet. Use it before and after any cosmetic edit. |
| `python tools/libpins.py some.SchLib` | Lists symbol pins and linked footprints of a library (works on IntLibs too). |
| `python tools/calc_v1.py` | Recomputes every resistor/threshold value in the power design. |

## How sheets 2–5 were made

`tools/gen_sheet2.py` **generates** all four power sheets from a data description of the circuit (the `blocks` list:
every part, value and pin → net). That description mirrors the per-mux table in `design/V1_PLAN.md`.
It uses `tools/templates/*.SchDoc` (one placed instance of each part) as symbols, lays the blocks out on A3,
and draws frames and headings in the sheet-1 style.

Every block is drawn in the **wired** style by two modules:
- `tools/wired.py`: the `Block` class. `part()` places a symbol so a chosen pin lands on a point (with rotation),
  `wire()`, `gnd()`, `pwr()`, `port()` and `label()` add the rest, and junction dots are added automatically wherever
  three or more connections meet.
- `tools/wired_blocks.py`: one hand-laid layout per block (dual mux, single mux, Bench Inputs, AUX, Rail Enable,
  Rail Monitors), in 10-mil units relative to the block origin.

Block origins snap to 100 mil, and the sheets get sheet 1's grid (50 mil snap, 100 mil visible, mils), so Altium
reports no off-grid objects.

```
python tools/gen_sheet2.py hardware/DebugBoardMuxes.SchDoc hardware/DebugBoardPowerControl.SchDoc \n    hardware/DebugBoard3V3Mux.SchDoc hardware/DebugBoard5VMux.SchDoc
python tools/verify_gen.py
```

**Hand edits vs. regeneration:** it's fine to edit sheets 2–5 in Altium from now on, but re-running the generator
overwrites those edits. Either change the spec in `gen_sheet2.py` and regenerate, or stop using the generator.

Low-level pieces: `tools/cfb.py` (Compound File reader), `tools/schgen.py` (record parser/writer, CFB writer,
component cloning).

Gotchas learned the hard way:
- A SchDoc's header `Weight` must equal the number of records, or Altium silently stops loading partway through.
- After regenerating, Altium may hold old copies in memory. Accept "Reload", and answer **Don't Save** /
  **Save None** to any offer to save the old copies.
- Moves must stay on the grid (multiples of 100 mil), or wires stop touching pins.
- Empty `||` segments inside records are significant and must be preserved byte-for-byte.

## PCB checks

| Command | What it checks |
|---|---|
| `python tools/pcb_place.py` | Rebuilds the placement script and preview. Lists parts too close, designators with no room, 3D models not signed off. |
| `python tools/pcb_check.py` | The real board (run `DumpV1` in Altium and save first): positions, spacing, designators, layer stack, 3D models seated and signed off. Expect `errors = 0`. |
| `python tools/drc_summary.py` | Altium's DRC report, counted per rule. |

Before adding or re-turning a 3D model, read the rule in `design/V1_LAYOUT.md` ("Guard against upside-down models").

Scripts worth knowing (File » Run Script » `SquidPcbTools.PrjScr`): `PlaceV1` (place parts, designators, 3D models),
`DumpV1` (write real geometry for the checks), `FixDDA` (the script-made eFuse footprint has its pads far from its
reference point; this moves them onto it, run it once after importing or updating those parts), `EndCommand` (if a
script stopped half-way and Altium refuses to save), `ViewFront` / `ViewBack` / `ViewBoth`.
`python tools/doc_diagrams.py` redraws the SVG twins of the docs' Mermaid diagrams (`docs/img/`).

**Pictures for the repo.** `python tools/pcb_shots.py` takes the six board pictures from the open Altium window
(hands off the mouse for about a minute). For the schematic: File » Smart PDF » Current Project » Finish, then
`python tools/sch_images.py`. **Hand-placed designators:** after moving text in Altium run `DumpV1`, then
`python tools/pcb_place.py pin`, so the next `PlaceV1` keeps your positions.

## How sheet 1 is made

`tools/gen_sheet1.py` redraws sheet 1 in the same wired style. Its input is `tools/templates/sheet1_source.SchDoc`,
the hand-captured sheet 1 frozen on Nov 26, 2026. Each placed part is reused as its own template, so symbols,
footprints, parameters and designators carry over unchanged. Layouts are one function per block. Frame boxes are in
`BOXES` (ANSI B sheet; the title block, revision table and disclaimer are kept clear).

```
python tools/gen_sheet1.py hardware/DebugBoard.SchDoc
python tools/verify_sheet1.py
```

`verify_sheet1.py` also flags a name used as both a net label and a port. Altium only joins labels to labels and
ports to ports, so such a name splits the net. That's why P4's SWD pins use net labels, matching the J1 side.
To change a part or value on sheet 1: edit it in Altium, copy the saved sheet over `sheet1_source.SchDoc`, then
regenerate. Otherwise stop using the generator for sheet 1.

`tools/oneoff/` holds the scripts used once for V1 edits to sheet 1 (Pico ports, re-layout, cap move). They're kept
for the record.

## Altium notes
- The project links `hardware/Libraries/SquidDebugger_V1/Project Outputs/SquidDebugger_V1.IntLib` (13 vendor parts,
  pin-verified). Its sources are in `SquidDebugger_V1/` (a LibPkg). Workspace parts: TPS2121 (CMP-019-00076-1),
  TLV70433 (CMP-019-00077-1), MIC2544-1 (CMP-00008-1).
- When Altium says "file modified outside, reload?", answer **Yes** for project files. If it then offers to save
  an older in-memory copy, answer **Don't Save**.
- The original Altium 365-linked project folder (`Documents/Altium/Debugging Board V1/`) is kept as an archive.
  This repo's `hardware/` is now the working copy.

## Backups
Dated full-project backups were taken before each larger edit (`Documents/Altium/Debugging Board V1 backup <date_time>/`).
With the project in git, commits replace that habit.
