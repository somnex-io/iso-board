# Design spec — FOH isolation board (Somnex)

## 1. What the board is

A passive 1:1 transformer isolation board that sits in the ribbon between a WMD Performance
Mixer MKII (rear 6-pin BALANCED OUT header) and an Intellijel Stereo Out Jacks 1U tile
(6-pin header). Two Lundahl LL1517 output transformers, one per channel. Purpose: galvanic
isolation of the FOH feed, blocking phantom power and ground loops. Nothing else on the board.

Signal order in the rig: WMD mix bus -> master insert (IMC compressor) -> MSTR pot -> DRV135
balanced driver -> rear header -> **this board** -> tile jacks -> FOH.

## 2. Board and grid

- Perfboard: Rademacher UP 832EP, epoxy 1.5 mm, pads on both faces, NOT plated through,
  1.0 mm holes on 2.54 mm pitch. Cut to **48 columns x 17 rows** (122 x 43 mm).
- Coordinates `(col, row)`: col 0 at the IN (WMD) end, col 47 at the OUT (tile) end;
  row 0 is the top edge, row 16 the bottom edge. Drawings show the TOP (component) side;
  the "underside" drawing is the same thing mirrored left-right.
- All wiring is on the underside. Components (transformers, headers) sit on top. Wires may run
  under transformer bodies. Wires are bare 0.6 mm silver-plated copper laid flat from pad to pad
  in straight orthogonal runs; corners are made at a hole.

## 3. Components and their pins

### LL1517 (datasheet in `reference/LL1517-datasheet.pdf`)

Two three-section coils, primaries and secondaries separated by electrostatic shields,
mu-metal housing. 1+1 : 1+1. Pin rows 35.56 mm apart (= 14 holes), pins on 5.08 mm pitch
(= 2 holes). Top view, pins in two columns:

```
 primary column (WMD side)      secondary column (tile side)
   pin 6  (row 3)                 pin 12 (row 3)
   pin 5  (row 5)                 pin 11 (row 5)
   pin 4  (row 7)                 (no pin at row 7)
   pin 3  (row 9)                 pin 9  (row 9)
   pin 2  (row 11)                pin 8  (row 11)
   pin 1  (row 13)                pin 7  (row 13)
```

Windings: primary A = pins 1(+)..3, primary B = pins 6(+)..4, centre taps 2 and 5 (unused).
Secondary A = 7(+)..8, secondary B = 12(+)..11. Pin 9 = core + housing + shields.

Series-series 1:1 wiring per transformer (the datasheet's "suggested use"):
- bridge **3 to 6** (primaries in series), signal in across **1 and 4**
- bridge **8 to 12** (secondaries in series), signal out across **7 and 11**
- pin 9 to the OUT-side ground ONLY. Never to WMD ground.
- pins 2 and 5: nothing.

Normal polarity assignment: IN hot -> 1, IN cold -> 4, OUT hot <- 7, OUT cold <- 11.
**Mirrored assignment (allowed, polarity-preserving):** IN hot -> 4, IN cold -> 1,
OUT hot <- 11, OUT cold <- 7. Both windings must be reversed together.

Placement on the grid (fixed):
- **T1 (left channel):** primary column at **col 6**, secondary column at **col 20**.
- **T2 (right channel):** primary column at **col 27**, secondary column at **col 41**.
- Pin rows as in the table above (rows 3,5,7,9,11,13 primary; 3,5,9,11,13 secondary).
- Bodies are 47 x 34 mm (18.5 x 13.4 holes), centred between the pin columns, rows ~1.3 to 14.7.

So the pin holes are:
```
T1: (6,3)=6 (6,5)=5 (6,7)=4 (6,9)=3 (6,11)=2 (6,13)=1   (20,3)=12 (20,5)=11 (20,9)=9 (20,11)=8 (20,13)=7
T2: (27,3)=6 (27,5)=5 (27,7)=4 (27,9)=3 (27,11)=2 (27,13)=1   (41,3)=12 (41,5)=11 (41,9)=9 (41,11)=8 (41,13)=7
```
No wire may pass through any of these 22 holes except as the endpoint of its own net.

### Headers (2x3 shrouded box headers, 2.54 mm)

Both maps were **measured with a meter** on the real WMD and the real tile, viewed from the
component side. Both are identical: top row GND GND, middle row L+ L-, bottom row R+ R-.

Mounted with the GND row toward row 0 ("rot 0"):
```
IN  header (WMD):  (1,7)=GND  (2,7)=GND    (1,8)=L+  (2,8)=L-    (1,9)=R+  (2,9)=R-
OUT header (tile): (45,7)=GND (46,7)=GND   (45,8)=L+ (46,8)=L-   (45,9)=R+ (46,9)=R-
```
Rotated 180° ("rot 1") the same header reads, top to bottom: R- R+ / L- L+ / GND GND.

Header holes are usable only as endpoints of the net that terminates there. The two IN GND
holes are ALWAYS unused (WMD ground must not touch the board). Of the two OUT GND holes at
least one is used by the shield net; the other may be used by the shield net or left empty.

The polarising notch on the header is on a long side; it does not affect this problem.

## 4. Nets

Twelve point-to-point nets, all bare wire, node-disjoint from each other:

| Net | From | To |
|---|---|---|
| T1 3-6 | T1 pin 3 (6,9) | T1 pin 6 (6,3) |
| T1 8-12 | T1 pin 8 (20,11) | T1 pin 12 (20,3) |
| T2 3-6 | T2 pin 3 (27,9) | T2 pin 6 (27,3) |
| T2 8-12 | T2 pin 8 (41,11) | T2 pin 12 (41,3) |
| IN L+ | IN header L+ | T1 pin 1 (6,13), or pin 4 (6,7) if T1 mirrored |
| IN L- | IN header L- | T1 pin 4 (6,7), or pin 1 if T1 mirrored |
| IN R+ | IN header R+ | T2 pin 1 (27,13), or pin 4 (27,7) if T2 mirrored |
| IN R- | IN header R- | T2 pin 4 (27,7), or pin 1 if T2 mirrored |
| OUT L+ | T1 pin 7 (20,13), or pin 11 (20,5) if T1 mirrored | OUT header L+ |
| OUT L- | T1 pin 11 (20,5), or pin 7 if T1 mirrored | OUT header L- |
| OUT R+ | T2 pin 7 (41,13), or pin 11 (41,5) if T2 mirrored | OUT header R+ |
| OUT R- | T2 pin 11 (41,5), or pin 7 if T2 mirrored | OUT header R- |

Plus the **shield net**: a tree connecting T1 pin 9 (20,9), T2 pin 9 (41,9) and at least one
OUT GND hole. It may branch/join (a solder joint on a pad mid-run is fine).

Left and right channels must end up with the same polarity, which mirroring preserves.

## 5. Rules for a valid layout

1. No two nets share a hole.
2. No net passes through a pin hole (transformer or header) other than its own endpoints.
3. Orthogonal runs only; a corner is at a hole.
4. Preferred but not required: WMD-side (IN) wires and tile-side (OUT) wires keep to different
   regions of the board, so a slip of the iron cannot bridge the two worlds. In earlier drafts
   IN long runs used the bottom rows (14-16) and OUT long runs the top rows (0-2). Adjacent
   holes 2.54 mm apart are normal perfboard practice and acceptable.
5. The bench-test that proves the isolation: every IN pin to every OUT pin must read OPEN.

## 6. Why it is hard (the structural problem)

With L+/L- in the middle row of a 2x3 header, those two pins can only be entered from the
sides (col 44 and col 47 at the OUT end). Those two side approaches split the header's
neighbourhood into a top half (GND row, from above) and a bottom half (R row, from below).
T1's three wires (L+, L-, shield) arrive from the far end of the board; T2's three wires
(R+, R-, shield) start at col 41 rows 5, 9 and 13. Whichever way L+ is brought to (44,8), it
fences off either the GND pins from T2's shield, or the R pins from T2's signal wires. The
1-jumper solution in `solver/routes_v2.py` resolves this by letting T2's shield cross two
bare wires under insulation. Mirroring, header rotation and bridge placement change the
picture and have not been exhausted; that is the job.

## 7. Files

- `solver/routes_v2.py` — current best (1 insulated jumper). Format: list of
  `(label, colour, [(col,row), ...], is_jumper)`.
- `solver/final_routes.py` — standalone checker pattern (BARE/INSUL dicts; run it to see checks).
- `solver/cpsat_route.py` — exact CP-SAT model (OR-Tools). Unvalidated; see CLAUDE.md.
- `solver/reroute3.py`, `reroute5.py`, `search_nojump.py` — heuristic searches (failed).
- `drawing/routing.py` — renders top and mirrored underside PNG/SVG from a route file.
- `drawing/build_doc.py` — builds the 4-page bench sheet PDF (reportlab).
- `outputs/current/` — current drawings and bench sheet (v2, 1 jumper).
- `reference/LL1517-datasheet.pdf`, `reference/build_tracker.py` (buy list and build checklist).
