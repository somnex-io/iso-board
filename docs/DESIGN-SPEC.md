# Design spec — FOH isolation board (Somnex)

_Constraint update, 13 Sept 2026: component positions are no longer fixed and the board may grow
(more columns preferred, extra rows only as a last resort). See §2, §3 and §5._

_Board update, 13 Sept 2026 (Steven): the planned cut is 50 x 19, the 48 x 17 layout moved +1 column and
+1 row so the outer ring of holes is an empty border. All coordinates below are on the 50 x 19 board.
`solver/routes_v2.py`, `solver/results/` and the solver scripts still use 48 x 17 coordinates (subtract
1 from each col and row to compare)._

## 1. What the board is

A passive 1:1 transformer isolation board that sits in the ribbon between a WMD Performance
Mixer MKII (rear 6-pin BALANCED OUT header) and an Intellijel Stereo Out Jacks 1U tile
(6-pin header). Two Lundahl LL1517 output transformers, one per channel. Purpose: galvanic
isolation of the FOH feed, blocking phantom power and ground loops. Nothing else on the board.

Signal order in the rig: WMD mix bus -> master insert (IMC compressor) -> MSTR pot -> DRV135
balanced driver -> rear header -> **this board** -> tile jacks -> FOH.

## 2. Board and grid

- Perfboard: Rademacher UP 832EP, epoxy 1.5 mm, pads on both faces, NOT plated through,
  1.0 mm holes on 2.54 mm pitch. Planned cut **50 columns x 19 rows** (127 x 48 mm); not cut
  yet. It may be made longer if needed: prefer more columns with the same 19 rows (long and
  thin beats short and fat). Extra rows are a last resort.
- **Border ring:** the outermost holes (col 0, col 49, row 0, row 18) carry no wire and no pin. They
  are sacrificial: a rough cut or a lifted edge pad there cannot break a net. `solver/check_routes.py`
  reports how many wire holes sit on the ring (0 for v3).
- Coordinates `(col, row)`: col 0 at the IN (WMD) end, col 49 at the OUT (tile) end;
  row 0 is the top edge, row 18 the bottom edge. Drawings show the TOP (component) side;
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
   pin 6  (row 4)                 pin 12 (row 4)
   pin 5  (row 6)                 pin 11 (row 6)
   pin 4  (row 8)                 (no pin at row 8)
   pin 3  (row 10)                pin 9  (row 10)
   pin 2  (row 12)                pin 8  (row 12)
   pin 1  (row 14)                pin 7  (row 14)
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

Default placement on the grid (may be moved, see §5):
- **T1 (left channel):** primary column at **col 7**, secondary column at **col 21**.
- **T2 (right channel):** primary column at **col 28**, secondary column at **col 42**.
- Pin rows as in the table above (rows 4,6,8,10,12,14 primary; 4,6,10,12,14 secondary).
- Bodies are 47 x 34 mm (18.5 x 13.4 holes), centred between the pin columns, rows ~2.3 to 15.7.
- In a routes file's `CONFIG` this is `t1 7, t2 28, trow 1`: the tools' pin tables are written for
  the 48 x 17 rows (3 to 13) and `trow` adds the row offset.

So the pin holes are:
```
T1: (7,4)=6 (7,6)=5 (7,8)=4 (7,10)=3 (7,12)=2 (7,14)=1   (21,4)=12 (21,6)=11 (21,10)=9 (21,12)=8 (21,14)=7
T2: (28,4)=6 (28,6)=5 (28,8)=4 (28,10)=3 (28,12)=2 (28,14)=1   (42,4)=12 (42,6)=11 (42,10)=9 (42,12)=8 (42,14)=7
```
No wire may pass through any of these 22 holes except as the endpoint of its own net.

### Headers (2x3 shrouded box headers, 2.54 mm)

Both maps were **measured with a meter** on the real WMD and the real tile, viewed from the
component side. Both are identical: top row GND GND, middle row L+ L-, bottom row R+ R-.

Default positions, mounted with the GND row toward row 0 ("rot 0"):
```
IN  header (WMD):  (2,8)=GND  (3,8)=GND    (2,9)=L+  (3,9)=L-    (2,10)=R+  (3,10)=R-
OUT header (tile): (46,8)=GND (47,8)=GND   (46,9)=L+ (47,9)=L-   (46,10)=R+ (47,10)=R-
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
| T1 3-6 | T1 pin 3 (7,10) | T1 pin 6 (7,4) |
| T1 8-12 | T1 pin 8 (21,12) | T1 pin 12 (21,4) |
| T2 3-6 | T2 pin 3 (28,10) | T2 pin 6 (28,4) |
| T2 8-12 | T2 pin 8 (42,12) | T2 pin 12 (42,4) |
| IN L+ | IN header L+ | T1 pin 1 (7,14), or pin 4 (7,8) if T1 mirrored |
| IN L- | IN header L- | T1 pin 4 (7,8), or pin 1 if T1 mirrored |
| IN R+ | IN header R+ | T2 pin 1 (28,14), or pin 4 (28,8) if T2 mirrored |
| IN R- | IN header R- | T2 pin 4 (28,8), or pin 1 if T2 mirrored |
| OUT L+ | T1 pin 7 (21,14), or pin 11 (21,6) if T1 mirrored | OUT header L+ |
| OUT L- | T1 pin 11 (21,6), or pin 7 if T1 mirrored | OUT header L- |
| OUT R+ | T2 pin 7 (42,14), or pin 11 (42,6) if T2 mirrored | OUT header R+ |
| OUT R- | T2 pin 11 (42,6), or pin 7 if T2 mirrored | OUT header R- |

Plus the **shield net**: a tree connecting T1 pin 9 (21,10), T2 pin 9 (42,10) and at least one
OUT GND hole. It may branch/join (a solder joint on a pad mid-run is fine).

Left and right channels must end up with the same polarity, which mirroring preserves.

## 5. Rules for a valid layout

1. No two nets share a hole.
2. No net passes through a pin hole (transformer or header) other than its own endpoints.
3. Orthogonal runs only; a corner is at a hole.
4. Preferred but not required: WMD-side (IN) wires and tile-side (OUT) wires keep to different
   regions of the board, so a slip of the iron cannot bridge the two worlds. In earlier drafts
   IN long runs used the bottom rows (14-16) and OUT long runs the top rows (0-2) of the 48 x 17 board. Adjacent
   holes 2.54 mm apart are normal perfboard practice and acceptable.
5. The bench-test that proves the isolation: every IN pin to every OUT pin must read OPEN.
6. Placement: transformers and headers may move from their default positions. Bodies stay on
   the board and do not overlap each other or the headers; each header stays at its own end.
   A transformer body is 13.4 holes tall on a 19-row board, so it can shift at most about two
   rows up or down from centre (and any wire it forces onto the border ring breaks §2).
7. Soft preferences (tie-breakers between otherwise valid layouts, not hard rules):
   - **Running wire under a transformer is safe.** The body is on top, the wires are on the
     underside, the board is in between. There is no contact and no hazard at line level.
   - **The concern is noise, and it depends on which wire goes there.** Prefer ground or shield
     under a transformer. Avoid putting the other channel's input pair under a can: it is the
     lowest signal level on the board, and anything it picks up there shows up as
     channel-to-channel crosstalk.
   - **Bigger lever than transformer proximity: keep hot and cold of a balanced pair adjacent
     and parallel wherever they run.** The loop area between the two legs of a pair is what
     turns stray magnetic flux into a differential signal, which the transformer passes on
     instead of rejecting. A pair running together under a can beats one leg of the pair
     detouring around it.
   - Scored by `solver/check_routes.py` (and the `--opt` objective in `solver/cpsat_route.py`):
     pair holes with no partner hole beside them weigh more than the other channel's wires
     under a body.

## 6. Why it is hard (the structural problem)

With L+/L- in the middle row of a 2x3 header, those two pins can only be entered from the
sides (col 45 and col 48 at the OUT end). Those two side approaches split the header's
neighbourhood into a top half (GND row, from above) and a bottom half (R row, from below).
T1's three wires (L+, L-, shield) arrive from the far end of the board; T2's three wires
(R+, R-, shield) start at col 42 rows 6, 10 and 14. Whichever way L+ is brought to (45,9), it
fences off either the GND pins from T2's shield, or the R pins from T2's signal wires. The
1-jumper solution in `solver/routes_v2.py` resolves this by letting T2's shield cross two
bare wires under insulation. Mirroring, header rotation, bridge placement and (since 13 Sept) component placement and
board length change the picture and have not been exhausted; that is the job.

## 7. Files

- `solver/routes_v3.py`: current build (no jumpers, 50 x 19). `solver/routes_v2.py`: previous build
  (1 insulated jumper, 48 x 17). Format: list of `(label, colour, [(col,row), ...], is_jumper)`.
- `solver/final_routes.py`: standalone checker pattern (BARE/INSUL dicts; pass a routes file to check it).
- `solver/cpsat_route.py`: exact CP-SAT model (OR-Tools). Unvalidated; see CLAUDE.md.
- `solver/reroute3.py`, `reroute5.py`, `search_nojump.py`: heuristic searches (failed).
- `drawing/routing.py`: renders top and mirrored underside PNG/SVG from a route file.
- `drawing/build_doc.py`: builds the 4-page bench sheet PDF (reportlab).
- `outputs/current/`: current drawings and bench sheet (v3, no jumpers, 50 x 19).
- `reference/LL1517-datasheet.pdf`, `reference/build_tracker.py` (buy list and build checklist).
