# State of play (13 Sept 2026)

## Where the physical build is
- Perfboard, headers, ribbon, silver wire, drill, vice, transformers: all on hand or ordered.
- Header pin maps: MEASURED (see DESIGN-SPEC §3). This is what triggered the re-route.
- Nothing soldered yet. The user has printed an earlier bench sheet (provisional maps) and
  the v2 sheet (1 jumper). He wanted a jumper-free layout before he starts: v3 below is one.
- Gig deadline context: Bristol, 26 Sept 2026. A decision is needed within days.

## Current recommended build: `solver/routes_v3.py` (NO jumpers), 13 Sept

- Planned 48 x 17 board, every component at its default position. Nothing moved, no extra columns.
- IN header rot 0 (as v2). **OUT header rotated 180°** (GND row at the bottom, row 9).
- **T1 MIRRORED** (hot 4 / cold 1, out hot 11 / cold 7). T2 normal. (v2 had T2 mirrored.)
- Bridges: T1 3-6 col 7, T1 8-12 col 18, T2 3-6 col 26, T2 8-12 col 39.
- Both shield wires end on OUT GND (45,9); (46,9) stays empty.
- Drawings and bench sheet: `outputs/current/`. The v2 set is kept in `outputs/v2-1-jumper/`.
- Bench sheet step B4 checks the rotated OUT header with the meter before any wiring.

Checked four independent ways: `solver/check_routes.py` (terminals rebuilt from the spec, no
shared code with the solver), the checks in `solver/final_routes.py`, CP-SAT with the route fixed
and nothing relaxed (OPTIMAL), and a plain count of holes (the only hole used twice is (45,9),
the two shield wires on the same GND pin).

### Why this layout (reversible)

Zero-jumper layouts exist for 7 of the 16 rotation/mirror combos at the default placement.
Two finalists were tidied with CP-SAT (length, bends, pair loop area, IN/OUT neighbours, other
channel under a can):

| layout | setup | score (lower better) | pair loop area, square hole pitches | wire holes | bends |
|---|---|---|---|---|---|
| **v3** `routes_v3.py` | OUT rot 180°, T1 mirrored | 1214 | 200 | 344 | 56 |
| alternative `results/polished/r01_m00_round2.py` | OUT rot 180°, no mirroring | 1422 | 229 | 390 | 65 |
| v2 (1 jumper), for reference | T2 mirrored | n/a (has jumper) | 240 | | |

The unmirrored alternative wires both transformers straight from the datasheet, but it is longer,
has more bends, and puts 19 holes of the other channel's input pair under a can. v3 was chosen;
to switch, point the drawing scripts at the alternative with `--routes`.

Loop area, for scale: 200 square pitches is about 13 cm² in total over four pairs. Even in a strong
100 µT hum field that is tens of microvolts, roughly 90 dB below line level (an estimate; the field
in the case is unknown). It is a tie-breaker, not a problem to solve.

## Previous build: `solver/routes_v2.py` (1 jumper)
- T1 normal (hot 1 / cold 4, out 7 / 11). T2 MIRRORED (hot 4 / cold 1, out 11 / 7).
- Both headers rot 0 (GND row toward row 0).
- Bridges: T1 3-6 on col 7, T1 8-12 on col 19, T2 3-6 on col 26, T2 8-12 on col 40.
- OUT lanes rows 0/1/2 (L-, shield, L+); IN lanes rows 14/15 (R-, R+).
- Jumper: T2 shield (41,9)->(41,8)->(42,8)->(42,6) bare, then insulated (42,6)->(45,6)
  joining T1's shield wire at (45,6); crosses bare wires at (43,6) and (44,6).

## What the solvers said

- The v1 CP-SAT log's two INFEASIBLE results were time limits, mislabelled by the old script. One of
  them is also plainly wrong: rot 0/0 with T2 mirrored (the v2 configuration) has a zero-jumper layout,
  `solver/results/negotiated/r00_m01_c48_t6-27_tr0_o45_h7_s4.py` (valid, but loop area 372 vs v3's 200).
  The other, rot 0/0 unmirrored, is still open: 70 router attempts found nothing, which proves nothing.
- v3 CP-SAT model (`solver/cpsat_route.py`) validated against v2: accepts it when the two jumper
  holes may be shared, proves it invalid otherwise, rebuilds it from a hint. Details in
  `solver/results/validation.jsonl`. It is too slow to prove anything on the tight full problem.
- The negotiated-congestion router (`solver/negotiate.py`) is what found the zero-jumper layouts
  (`solver/results/negotiate.jsonl`); CP-SAT then tidied them (`solver/results/polish.jsonl`).
- Resource limits after the 13 Sept OOM: see CLAUDE.md, "How to run".

## Superseded notes (before v3)
`solver/cpsat-results.log`: in_rot 0 / out_rot 0 with (m1,m2) = (0,0) and (0,1): INFEASIBLE
in ~50 s each. 14 combos untested. The model has not been validated, so treat "INFEASIBLE"
with suspicion until it reproduces the known 1-jumper solution when the jumper's two crossing
cells are allowed to be shared (a quick relaxation test).

## Ideas not yet tried
- Header rot 1 at either end combined with mirroring (the solver runs 0 1 * *, 1 0 * *, 1 1 * *).
- Letting bridges take non-standard paths (e.g. 8-12 going round the far side of the column)
  to free rows 10/12 for through-routes between the transformers.
- Shield net joining between the transformers (row 10 or 12) instead of at the header.
- One extra column at the OUT end (col 48) to give the middle-row pins a second side approach.
  If that is the only way, say so; the user can cut the board 49 or 50 columns long.
