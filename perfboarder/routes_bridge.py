"""Bridge between solver route files and the Perfboarder board.

  python3 perfboarder/routes_bridge.py calls ROUTES.py [--from OLD_ROUTES.py]
      Parts to add, then Perfboarder MCP calls as JSON lines: `cut` (only with --from: wires in
      OLD but not in ROUTES) and `connect`, grouped per net with its name and colour. Run them in
      order, then rename/colour nets from the `board` tool (cuts and merges reshuffle names).
  python3 perfboarder/routes_bridge.py labels ROUTES.py
      Every pin with its (col, row) and the hole label Perfboarder shows for it, to compare with
      the `board` tool.
  python3 perfboarder/routes_bridge.py check ROUTES.py [BOARD.json]
      Exit 0 if the exported board (default perfboarder/somnex-iso-board.json) has the size, part
      positions, nets, net colours and straight segments of ROUTES.py.

Perfboarder holes are 1-based: our (col, row) is Perfboarder (col+1, row+1). Every corner is a
junction "@col,row", so each wire is one straight run of the route.

Hole labels are different: letters count columns from the RIGHT (OUT) edge, A = our col cols-1,
and the number counts rows from the top, 01 = our row 0. So the letters depend on the board width.
"""
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drawing"))
from palette import wire_colour  # same colours as the drawings, not the routes file's own

T_PRI = ("6", "5", "4", "3", "2", "1")  # rows 3,5,7,9,11,13 (+trow)
T_SEC = ("12", "11", None, "9", "8", "7")


def load(path):
    spec = importlib.util.spec_from_file_location("routes", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert not any(j for *_, j in mod.routes), f"{path}: jumpers are not supported"
    return mod


def layout(cfg):
    """Pin names by our (col, row), and add_part arguments, for a route file's CONFIG."""
    pins, parts = {}, []
    for ref, t in (("U1", cfg["t1"]), ("U2", cfg["t2"])):
        for i, (p, s) in enumerate(zip(T_PRI, T_SEC)):
            r = 3 + 2 * i + cfg["trow"]
            pins[(t, r)] = f"{ref}.{p}"
            if s:
                pins[(t + 14, r)] = f"{ref}.{s}"
        parts.append({"ref": ref, "kindId": "lundahl-ll1517", "col": t + 1, "row": 4 + cfg["trow"], "rotation": 0})
    h = cfg["hrow"]
    for ref, c, rot in (("J1", cfg["in_col"], cfg["in_rot"]), ("J2", cfg["out_col"], cfg["out_rot"])):
        names = ("GND1", "GND2", "L+", "L-", "R+", "R-")
        holes = [(c, h), (c + 1, h), (c, h + 1), (c + 1, h + 1), (c, h + 2), (c + 1, h + 2)]
        if rot:  # 180 degrees about the header centre; origin GND1 moves to the far corner
            holes = [(2 * c + 1 - x, 2 * h + 2 - y) for x, y in holes]
        pins.update(zip(holes, (f"{ref}.{n}" for n in names)))
        parts.append({"ref": ref, "kindId": "2x3-box-header-gnd-l-r", "col": holes[0][0] + 1, "row": holes[0][1] + 1, "rotation": 180 if rot else 0})
    return pins, parts


def hole_label(col, row, cols):
    n = cols - 1 - col  # A..Z, then AA..AZ, BA..
    return (chr(65 + n) if n < 26 else chr(64 + n // 26) + chr(65 + n % 26)) + f"{row + 1:02d}"


def net_name(label):
    side = label.split(" :")[0]
    if label.startswith("shield"):
        return "SHIELD"
    return f"IN {side}" if " : IN" in label else f"OUT {side}" if "-> OUT" in label else label


def segments(mod):
    return {frozenset(ab): label for label, _, pts, _ in mod.routes for ab in zip(pts, pts[1:])}


def calls(path, old_path=None):
    mod = load(path)
    pins, parts = layout(mod.CONFIG)
    name = lambda p: pins.get(p, f"@{p[0] + 1},{p[1] + 1}")
    keep = set()
    for part in parts:
        print(json.dumps({"add_part": part}))
    if old_path:
        old = load(old_path)
        old_pins, _ = layout(old.CONFIG)
        assert old_pins == pins, "part placement differs: move/rotate parts before rewiring"
        new_segs, old_segs = segments(mod), segments(old)
        keep = new_segs.keys() & old_segs.keys()
        for label, _, pts, _ in old.routes:
            for a, b in zip(pts, pts[1:]):
                if frozenset((a, b)) not in keep:
                    print(json.dumps({"cut": [name(a), name(b)]}))
    for label, _, pts, _ in mod.routes:
        segs = [[name(a), name(b)] for a, b in zip(pts, pts[1:]) if frozenset((a, b)) not in keep]
        print(json.dumps({"net": net_name(label), "colour": wire_colour(label), "connect": segs}))


def check(path, board_path="perfboarder/somnex-iso-board.json"):
    mod, board = load(path), json.load(open(board_path))
    pins, parts = layout(mod.CONFIG)
    # Pins are matched by name, so without these a board of the wrong size or with a part moved would still pass.
    size_ok = (board["board"]["cols"], board["board"]["rows"]) == (mod.CONFIG["cols"], mod.CONFIG.get("rows", 17))
    if not size_ok:
        print(f"SIZE board is {board['board']['cols']} x {board['board']['rows']}, routes are {mod.CONFIG['cols']} x {mod.CONFIG.get('rows', 17)}")
    got_p = {p["ref"]: (p["at"]["col"], p["at"]["row"], p["rotation"]) for p in board["parts"]}
    want_p = {p["ref"]: (p["col"], p["row"], p["rotation"]) for p in parts}
    bad_p = sorted(r for r in want_p.keys() | got_p.keys() if want_p.get(r) != got_p.get(r))
    for r in bad_p:
        print(f"PART {r}: board has (col, row, rotation) {got_p.get(r)}, routes have {want_p.get(r)}")
    holes = {v: k for k, v in pins.items()}
    pt = lambda s: tuple(int(v) - 1 for v in s[1:].split(",")) if s.startswith("@") else holes[s]
    got = {n["name"]: {frozenset(map(pt, w)) for w in n["wires"]} for n in board["nets"]}
    want = {}
    for seg, label in segments(mod).items():
        want.setdefault(net_name(label), set()).add(seg)
    bad = sorted(n for n in want.keys() | got.keys() if want.get(n) != got.get(n))
    for n in bad:
        print(f"MISMATCH {n}: board has {len(got.get(n, ()))} segments, routes have {len(want.get(n, ()))}")
    got_c = {n["name"]: n.get("colour", "").lower() for n in board["nets"]}
    want_c = {net_name(label): wire_colour(label).lower() for label, *_ in mod.routes}
    bad_c = sorted(n for n in want_c if got_c.get(n) != want_c[n])
    for n in bad_c:
        print(f"COLOUR {n}: board has {got_c.get(n)}, palette has {want_c[n]}")
    print(f"{len(got)} nets, {sum(map(len, got.values()))} segments: {'match' if not bad else 'DIFFERENT'}; colours {'match' if not bad_c else 'DIFFERENT'}; "
          f"size and parts {'match' if size_ok and not bad_p else 'DIFFERENT'}")
    return not bad and not bad_c and size_ok and not bad_p


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["calls"] and len(args) in (2, 4):
        calls(args[1], args[3] if len(args) == 4 and args[2] == "--from" else None)
    elif args[:1] == ["labels"] and len(args) == 2:
        cfg = load(args[1]).CONFIG
        assert hole_label(1, 8, 48) == "AU09" and hole_label(45, 7, 48) == "C08"  # read off the 48 x 17 board, 13 Sept
        for (c, r), p in sorted(layout(cfg)[0].items(), key=lambda kv: kv[1]):
            print(f"{p:8s} ({c}, {r})  {hole_label(c, r, cfg['cols'])}")
    elif args[:1] == ["check"] and len(args) in (2, 3):
        sys.exit(0 if check(*args[1:]) else 1)
    else:
        sys.exit(__doc__)
