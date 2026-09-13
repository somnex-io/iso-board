# State of play (13 Sept 2026)

## Where the physical build is
- Perfboard, headers, ribbon, silver wire, drill, vice, transformers: all on hand or ordered.
- Header pin maps: MEASURED (see DESIGN-SPEC §3). This is what triggered the re-route.
- Nothing soldered yet. The user has printed an earlier bench sheet (provisional maps) and
  the v2 sheet (1 jumper). He would prefer a jumper-free layout before he starts.
- Gig deadline context: Bristol, 26 Sept 2026. A decision is needed within days.

## Current recommended build: `solver/routes_v2.py` (1 jumper)
- T1 normal (hot 1 / cold 4, out 7 / 11). T2 MIRRORED (hot 4 / cold 1, out 11 / 7).
- Both headers rot 0 (GND row toward row 0).
- Bridges: T1 3-6 on col 7, T1 8-12 on col 19, T2 3-6 on col 26, T2 8-12 on col 40.
- OUT lanes rows 0/1/2 (L-, shield, L+); IN lanes rows 14/15 (R-, R+).
- Jumper: T2 shield (41,9)->(41,8)->(42,8)->(42,6) bare, then insulated (42,6)->(45,6)
  joining T1's shield wire at (45,6); crosses bare wires at (43,6) and (44,6).

## What the exact solver said so far
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
