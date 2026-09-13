# CLAUDE.md — task brief for the agent

You are picking up a small but fiddly electronics-routing problem. Read `docs/DESIGN-SPEC.md`
first (5 minutes), then `docs/STATE-OF-PLAY.md`. Everything you need is in this repo.

## The task

Find a **crossing-free** wiring layout for a perfboard, or prove that none exists within the
allowed freedoms and say so plainly.

- Board: planned 48 x 17 holes on a 2.54 mm grid (122 x 43 mm), not cut yet (see freedom 6).
  Coordinates are `(col, row)`,
  col 0 = IN end, row 0 = top edge. Every wire is bare silver wire on the underside, laid
  hole to hole in orthogonal runs. **Two bare wires may never share a hole** (that is a short),
  and no wire may pass through a hole that has a component pin in it, other than its own two
  endpoints.
- Components: two Lundahl LL1517 transformers (footprints in the spec), a 2x3 IN header and a
  2x3 OUT header. Default positions: T1 pin columns 6/20, T2 27/41, IN header cols 1-2 rows 7-9,
  OUT header cols 45-46 rows 7-9. Positions may change (freedom 8). Header pin maps are
  MEASURED and fixed (see spec).
- Nets to route (12 point-to-point nets plus one shield tree): see `docs/DESIGN-SPEC.md` §4.

The current best answer (`solver/routes_v2.py`) needs **one insulated jumper** (3 holes,
crossing two bare wires). The user wants zero jumpers. He is a first-time builder, so a
solution must also be *buildable*: no diagonal wires, no stacked wires, no wire under a
solder joint.

## Allowed freedoms (use any of them)

1. **Header rotation**: either header may be mounted rotated 180° (GND row toward row 16
   instead of row 0). The ribbon plugs either way; only the pin positions on this board change.
2. **Transformer mirroring**: on either transformer you may swap hot/cold on BOTH windings
   together (hot -> pin 4, cold -> pin 1; out hot <- pin 11, out cold <- pin 7). Polarity is
   preserved because both windings reverse. You may NOT reverse only one winding.
3. **Bridge placement**: the series bridges (3-6 and 8-12 on each transformer) can go on either
   side of their pin column, or take any other crossing-free path.
4. **Shield net**: the two pin-9 wires may each go to either GND pin of the OUT header, or one
   may join the other's wire (a solder joint on a pad mid-run is fine). Only ONE GND pin needs a
   wire; they are joined on the tile.
5. **Which GND pin the WMD side leaves unconnected**: both IN GND pins stay empty always.
6. **Board size**: the board may grow if that is what it takes; say so clearly. Prefer more
   columns with the same 17 rows (long and thin beats short and fat). Extra rows are a last
   resort; if a solution needs them, call it out loudly. 48 x 17 is the planned cut.
7. A wire may run under a transformer body (everything is on the underside).
8. **Component placement**: the transformers and headers may be moved. Bodies must stay on the
   board and must not overlap each other or the headers. Headers stay at their own end of the
   board (the ribbons leave through the sleeve ends). Keep the search space small: try a handful
   of discrete placements, not free placement.

## Soft preferences (tie-breakers between otherwise valid layouts, not hard rules)

- Keep hot and cold of each balanced pair adjacent and parallel wherever they run. Small loop
  area between a pair matters more than keeping wires out from under a transformer.
- If something has to run under a transformer body, prefer ground/shield there over the other
  channel's input pair.

_Constraint update, 13 Sept 2026 (from Steven): component positions are no longer fixed, and the
board may grow (columns preferred, rows last resort). Earlier versions of this brief said the
transformers could not move._

Not allowed: crossing wires, insulated wires, top-side wires, changing the header maps, driving
only one winding reversed.

## What has been tried (don't repeat blindly)

- Greedy sequential shortest-path routing with permutations of net order, several header
  positions, domain "lanes" (`solver/reroute3.py`, `solver/reroute5.py`, `solver/search_nojump.py`):
  all fail without jumpers for the measured maps. Greedy order is the weakness.
- An exact CP-SAT formulation (`solver/cpsat_route.py`, OR-Tools, node-disjoint flows, shield as
  a 2-unit flow) reported INFEASIBLE for header rot 0/0 with T1/T2 unmirrored and with T2
  mirrored, at a 45 s limit per config (`solver/cpsat-results.log`). The remaining 14 of 16
  rotation/mirror combos were NOT completed. CP-SAT is the right tool; the model may still have
  bugs (it was written in a hurry and never validated against the known 1-jumper solution).
  **First step: validate the model** by feeding it routes_v2 minus the jumper as a hint, or by
  relaxing one constraint and confirming it finds a solution.

## Definition of done

Either:

A. A routing with zero crossings that passes `solver/final_routes.py`-style checks
   (no shared holes, no wire through a pad, no wire over a solder joint), expressed in the
   same format as `solver/routes_v2.py`, with the drawings and bench sheet regenerated
   (`drawing/routing.py`, `drawing/routing.py --mirror`, `drawing/build_doc.py`), OR

B. A short, plain-language proof or strong evidence (exhaustive CP-SAT over all 16
   rotation/mirror combos, each run to proven infeasibility, not a time limit) that no such
   routing exists at the default placement on 48 columns, plus the smallest change (placement
   moves, extra columns; extra rows only as a last resort) at which one does exist, with that
   routing delivered as in A.

Report which of A or B you delivered and why. If B, keep the 1-jumper solution as the
recommended build and say so.

## How to run

```
pip install ortools matplotlib reportlab
python3 solver/final_routes.py                     # checker for a hard-coded route set
python3 solver/cpsat_route.py IN_ROT OUT_ROT M1 M2 [seconds]   # e.g. 0 0 0 0 120
python3 drawing/routing.py && python3 drawing/routing.py --mirror   # writes outputs/*.png/.svg
python3 drawing/build_doc.py                       # writes outputs/FOH-iso-board_bench-sheet.pdf
```
Run scripts from the repo root. The drawing scripts read `solver/routes_v2.py`; point them at
your new route file when you have one.

## Style notes for the user-facing deliverables

The user has printed an earlier bench sheet. Keep the coordinate system, colours and the
page structure the same (page 1 reference, page 2 top view, page 3 mirrored underside view,
page 4 checklist). No em dashes in any text. Concise, plain language, no marketing tone.
