# Perfboarder: visual check of candidate layouts

Steven explores layouts by hand in **Perfboarder** (app.perfboarder.com), a browser perfboard
editor, in parallel with the solver. Use it to show him a candidate routing on a board he can
see, instead of asking him to read coordinates out of a Python file.

## Setup (as of 13 Sept 2026)

- A board named `somnex-iso-board` is open in Steven's Chrome, sized 48 x 17 to match the planned
  cut. It shows FRONT (component side) and BACK (wire side, mirrored) side by side: the same
  convention as `drawing/routing.py` and `drawing/routing.py --mirror`.
- Perfboarder's agent bridge listens on `localhost:4870`.
- `@perfboarder/mcp` is registered in Claude Code at project scope for this repo
  (`/Users/steven/src/llwt/somnex-iso-board`). MCP config is read at session start, so its tools
  only appear in sessions started after it was added. List the tools before using them; do not
  guess their names or arguments.
- The board lives in Steven's browser. If the bridge does not answer, the tab may be closed or
  the bridge switched off; ask him rather than working around it.

## Workflow

1. Get a candidate routing that passes `python3 solver/check_routes.py ROUTES.py` (exit 0).
2. Before pushing a whole routing, check the coordinate mapping: place one known item (for
   example T1 pin 1 at `(6,13)` in this repo's `(col, row)` system, col 0 = IN end, row 0 = top
   edge) and confirm it lands where expected on both FRONT and BACK. Do not assume Perfboarder's
   origin or axis direction matches ours.
3. Push the components and wires to the open board for Steven to look at.
4. If Steven edits a layout by hand, read it back, convert it to the `routes_v2.py` format and run
   it through `solver/check_routes.py` before treating it as valid.

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
