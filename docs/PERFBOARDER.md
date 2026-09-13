# Perfboarder: visual check of candidate layouts

Steven explores layouts by hand in **Perfboarder** (app.perfboarder.com), a browser perfboard
editor, in parallel with the solver. Use it to show him a candidate routing on a board he can
see, instead of asking him to read coordinates out of a Python file.

## Setup (as of 13 Sept 2026)

- A board named `somnex-iso-board` is open in Steven's browser, sized to match the real board:
  49 x 18 as cut on 13 Sept (it was 48 x 17, the planned cut). It shows FRONT (component side) and BACK (wire side,
  mirrored) side by side: the same convention as `drawing/routing.py` and `drawing/routing.py --mirror`.
- **Current board: `solver/routes_v3.py`.** `perfboarder/somnex-iso-board.json` is the last export;
  `python3 perfboarder/routes_bridge.py check solver/routes_v3.py` confirms it (size, part positions,
  nets, colours and segments).
  **Pending (13 Sept):** the open board and the export are still 48 x 17, so `check` fails on size
  only. The resize below has not been run yet: this session had no bridge (see the port note).
- **48 x 17 to 49 x 18:** the layout keeps its coordinates; the spare column and row go at the OUT
  end and the bottom. On the board that is one call, `resize_board {right: 1, bottom: 1}`: growing on
  the right or bottom moves nothing, so parts, junctions, nets and colours stay put. No rebuild.
- Perfboarder's agent bridge listens on `localhost:4870`. The MCP server process owns that port,
  so only one Claude session at a time has a working bridge (the one started first); in the
  others every tool fails with "no Perfboarder tab is connected".
- `@perfboarder/mcp` (0.1.2) is in `.mcp.json` and enabled in `.claude/settings.json`. MCP config
  is read at session start. The tools are deferred: load their schemas before calling them.
- The board lives in Steven's browser. If the bridge does not answer, the tab may be closed or
  the bridge switched off; ask him rather than working around it.

## Coordinates and parts

- Perfboarder holes are 1-based: our `(col, row)` is Perfboarder `(col+1, row+1)`, same axis
  directions (checked by screenshot). This does not depend on the board size; `routes_bridge.py`
  uses only this.
- Its hole **labels** are different and DO depend on the width: letters count columns from the
  right (OUT) edge, the number counts rows from the top. Label of our `(col, row)`: letter number
  `cols - 1 - col` (A=0 .. Z=25, AA=26 ..) then `row + 1` as two digits. On 49 x 18 that is
  `48 - col`: our col 0 is "AW", col 48 is "A"; row 0 is "01", row 17 is "18".
  `python3 perfboarder/routes_bridge.py labels solver/routes_v3.py` prints every pin's label.
  Derived from the 48 x 17 readings of 13 Sept (IN L+ (1,8) was AU09, OUT R- (45,7) was C08: only
  "from the right" fits the letters, and only "from the top" fits C08). Growing the board at the
  OUT end moves every letter on by one while our coordinates stay: on 49 x 18 expect the IN header
  at AV08 to AU10 (IN L+ (1,8) is AV09, was AU09) and the OUT header at D08 to C10 (OUT R- (45,7) is
  D08, was C08). Not yet read back from the resized board: until it is, trust `@col,row` over the letters.
- Part kinds defined on the board: `lundahl-ll1517` (origin pin 6, pins named "1" to "12",
  secondary column 14 holes right) and `2x3-box-header-gnd-l-r` (origin GND1; pins GND1 GND2 /
  L+ L- / R+ R-). A header at rot 1 is `rotation: 180` with its origin at the lower right pin.
- Wires are stored as pin pairs only. To keep a route's shape, put a junction `@col,row` at every
  corner and connect consecutive points. Pins are addressed as `U1.9`, `J2.GND2`.

## Workflow

1. Get a candidate routing that passes `python3 solver/check_routes.py ROUTES.py` (exit 0).
2. `python3 perfboarder/routes_bridge.py calls ROUTES.py --from CURRENT.py` prints the part
   positions, the `cut` calls for wires that go away and the `connect` calls per net (drop
   `--from` for an empty board). Run them in order. Cuts and merges reshuffle net names, so read
   the `board` tool afterwards, then `name_net` and `colour_net` with the colour each net has in
   the `calls` output. Colours come from `drawing/palette.py`, the same as the drawings (IN left
   #10347D, IN right #7456B8, OUT left #A23125, OUT right #B57A09, shield #328B5F, bridges
   #A0A0A0). Placement changes need `move_part`/`rotate_part` first.
3. Call `export_board`, then `python3 perfboarder/routes_bridge.py check ROUTES.py` must exit 0
   (it compares net colours with the palette as well as the segments).
   Commit `perfboarder/somnex-iso-board.json`.
4. If Steven edits a layout by hand, export it, convert the nets to the routes format and run it
   through `solver/check_routes.py` before treating it as valid (no converter exists yet).

Never call `reroute` or `rearrange`: they replace the routing with Perfboarder's own. Ask Steven
not to press those buttons either (the wires are not locked).

## Saving the board to the repo

Calling the MCP `export_board` tool saves the open board to `perfboarder/<board name>.json`
through a PostToolUse hook (`.claude/settings.json`, `.claude/hooks/save_perfboarder_export.py`).
`updatedAt` is dropped, so an unchanged board gives no diff. Commit the file to keep a history.
The export's `solderedLinks` (and a part's `soldered` flag) is Perfboarder's build checklist:
exporting during the build records soldering progress too.

## What Perfboarder shows that is not a problem

- **Curved wires.** Every wire is drawn as a quadratic curve whose bow depends on the net's index
  (so parallel nets do not overlap). There is no setting to draw straight lines. Read runs
  junction to junction; `drawing/routing.py` draws the true straight layout.
- **"U1/U2 overlaps a junction" (hard).** Corner junctions under a transformer body. On the real
  board they are bends in bare wire on the underside, which the spec allows. Reported once per
  part.
- **"J1/J2 needs to reach a board edge" (soft).** The headers sit in from the ends by design: J1 one
  column (col 0 carries IN L+), J2 two (col 47 carries OUT L+, col 48 is spare).

## Gotcha: Perfboarder's checks are looser than this build

Perfboarder's built-in rule allows **up to three wires on a pad**. This build allows **no two
bare wires in the same hole, ever** (that is a short between nets), and no wire through a pin
hole other than its own endpoints. A layout Perfboarder marks as buildable can still be invalid
here. Do not trust its green verdict. `solver/check_routes.py` is the authority; the checks in
`solver/final_routes.py` are a second opinion.

The one place two wires may meet in a hole is the shield net: T2's pin 9 wire may end on T1's
shield wire (a solder joint, same net). Our checker allows exactly that and nothing else.

## What to look for when judging a layout by eye

These are the project's soft preferences (details and reasons in `docs/DESIGN-SPEC.md` §5,
item 7). Use them to choose between layouts that are already valid:

- Hot and cold of each balanced pair side by side and parallel wherever they run.
- Ground or shield under a transformer is fine; the other channel's input pair under a can is
  the thing to avoid.
