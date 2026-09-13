#!/usr/bin/env python3
"""Perfboard routing for the WMD -> 2x LL1517 -> Stereo Out Jacks 1U board.
Grid: columns x rows of 2.54 mm holes from the routes file's CONFIG (48 x 17 when it has none), in-line layout.
Coordinates are (col, row); col 0 at the IN end, row 0 at the top edge.

usage: routing.py [--mirror] [--routes solver/routes_v3.py]"""
import matplotlib, os, sys
MIRROR = "--mirror" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
ROUTES = sys.argv[sys.argv.index("--routes") + 1] if "--routes" in sys.argv else os.path.join(HERE, "..", "solver", "routes_v3.py")
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

P = 1.0  # one hole pitch = 1 unit

exec(open(ROUTES).read())
sys.path.insert(0, HERE)
from palette import IN_C, OUT_C, SH_C, BR_C, IN_L, IN_R, OUT_L, OUT_R, wire_colour   # overrides the routes file's colours
# routes_v2.py has no CONFIG: it is IN/OUT rot 0, T2 mirrored, default positions
CONFIG = dict(dict(in_rot=0, out_rot=0, m1=0, m2=1, cols=48, rows=17, t1=6, t2=27, trow=0, in_col=1, out_col=45, hrow=7), **globals().get("CONFIG", {}))
COLS, ROWS = CONFIG["cols"], CONFIG["rows"]
X = (lambda c: COLS - 1 - c) if MIRROR else (lambda c: c)
TR = CONFIG["trow"]

# ---- transformer footprints: primary column, secondary column ----
T1 = dict(name="T1  (LEFT channel)", pc=CONFIG["t1"], sc=CONFIG["t1"] + 14, mirrored=CONFIG["m1"])
T2 = dict(name="T2  (RIGHT channel)", pc=CONFIG["t2"], sc=CONFIG["t2"] + 14, mirrored=CONFIG["m2"])
PRIM_PINS = {pin: r + TR for pin, r in {6: 3, 5: 5, 4: 7, 3: 9, 2: 11, 1: 13}.items()}       # pin -> row
SEC_PINS = {pin: r + TR for pin, r in {12: 3, 11: 5, 9: 9, 8: 11, 7: 13}.items()}

# ---- headers (2x3, cols x rows) ----
HR = CONFIG["hrow"]
IN_HDR = dict(cols=(CONFIG["in_col"], CONFIG["in_col"] + 1), rows=(HR, HR + 1, HR + 2))
OUT_HDR = dict(cols=(CONFIG["out_col"], CONFIG["out_col"] + 1), rows=(HR, HR + 1, HR + 2))
JUMPERS = [r for r in routes if r[3]]

fig, ax = plt.subplots(figsize=(16, 6.4), dpi=170)
ax.set_xlim(-1.2, COLS + 0.2)
ax.set_ylim(ROWS + 1.0, -2.6)  # row 0 at top
ax.set_aspect("equal")
ax.axis("off")

# board outline
ax.add_patch(Rectangle((-0.5, -0.5), COLS, ROWS, fc="#F3EFE4", ec="#8A8A8A", lw=1.2))
# hole grid
for c in range(COLS):
    for r in range(ROWS):
        ax.add_patch(Circle((c, r), 0.11, fc="#B9B3A5", ec="none"))

# transformer bodies (47 x 34 mm = 18.5 x 13.4 holes), centred between pin columns
for T in (T1, T2):
    cx = (X(T["pc"]) + X(T["sc"])) / 2
    ax.add_patch(FancyBboxPatch((cx - 9.25, 8 + TR - 6.7), 18.5, 13.4, boxstyle="round,pad=0,rounding_size=0.6",
                                fc="none", ec="#4A4A4A", lw=1.4, ls="--"))
    ax.text(cx, -1.15, T["name"], ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333")
    ax.text(cx, 8.0 + TR, "LL1517\n(body on top,\nwires underneath)", ha="center", va="center", fontsize=7.5, color="#666")
    for pin, r in PRIM_PINS.items():
        ax.add_patch(Circle((X(T["pc"]), r), 0.34, fc="white", ec="#222", lw=1.0))
        ax.text(X(T["pc"]), r, str(pin), ha="center", va="center", fontsize=6.6, fontweight="bold")
    for pin, r in SEC_PINS.items():
        ax.add_patch(Circle((X(T["sc"]), r), 0.34, fc="white", ec="#222", lw=1.0))
        ax.text(X(T["sc"]), r, str(pin), ha="center", va="center", fontsize=6.6, fontweight="bold")
    mir = " MIRRORED: hot=4, cold=1" if T["mirrored"] else " hot=1, cold=4"
    mis = " MIRRORED: hot=11, cold=7" if T["mirrored"] else " hot=7, cold=11"
    ax.text(X(T["pc"]), 14.2 + TR, "PRIMARY (from WMD)" + mir, ha="center", va="top", fontsize=6.2, color=IN_C)
    ax.text(X(T["sc"]), 14.2 + TR, "SECONDARY (to tile)" + mis, ha="center", va="top", fontsize=6.2, color=OUT_C)

# headers
def header(h, mp, title, colour):
    c0, c1 = sorted((X(h["cols"][0]), X(h["cols"][1]))); r0, r1 = h["rows"][0], h["rows"][-1]
    ax.add_patch(Rectangle((c0 - 0.6, r0 - 0.6), (c1 - c0) + 1.2, (r1 - r0) + 1.2, fc="#DDE3EA", ec=colour, lw=1.4))
    for (c, r), lab in mp.items():
        ax.add_patch(Circle((X(c), r), 0.32, fc="white", ec=colour, lw=1.0))
        ax.text(X(c), r, lab, ha="center", va="center", fontsize=5.2, fontweight="bold", color="#222")
    ax.text((c0 + c1) / 2, r1 + 1.3, title, ha="center", va="top", fontsize=7, color=colour, fontweight="bold")
ROT = lambda r: "\nROTATED 180°: GND row at bottom" if r else "\nGND row at top"
header(IN_HDR, IN_MAP, "IN 2x3 (from WMD)\nMEASURED map" + ROT(CONFIG["in_rot"]), IN_C)
header(OUT_HDR, OUT_MAP, "OUT 2x3 (to tile)\nMEASURED map" + ROT(CONFIG["out_rot"]), OUT_C)

# routes
for label, _, pts, jumper in routes:
    xs = [X(p[0]) for p in pts]; ys = [p[1] for p in pts]
    colour = wire_colour(label)
    if jumper:
        ax.plot(xs, ys, color=colour, lw=2.8, ls=(0, (2, 1.2)), solid_capstyle="round", zorder=6)
        ax.text((xs[0] + xs[-1]) / 2, ys[0] - 0.9, "insulated jumper (dashed)", ha="center", va="center", fontsize=5.6, color=colour, fontweight="bold")
    else:
        ax.plot(xs, ys, color=colour, lw=2.4, solid_capstyle="round", solid_joinstyle="round", zorder=5)

# wire labels: each signal and shield wire named once, on its longest straight run
for label, _, pts, jumper in routes:
    if "bridge" in label or jumper: continue
    colour = SH_C if label.startswith("shield") else (IN_C if ": IN" in label else OUT_C)   # dark ink for small text
    name = "shield T%s" % label.split("T")[1][0] if label.startswith("shield") else label.split(" :")[0] + (" in" if ": IN" in label else " out")
    segs = [((a, b), (c, d)) for (a, b), (c, d) in zip(pts, pts[1:])]
    (a, b), (c, d) = max(segs, key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
    if b == d:
        ax.text((X(a) + X(c)) / 2, b - 0.42, f"{name} (row {b})", ha="center", va="center", fontsize=5.4, color=colour, zorder=7,
                bbox=dict(fc="#F3EFE4", ec="none", pad=0.4))
    else:
        ax.text(X(a) + 0.42, (b + d) / 2, f"{name} (col {a})", ha="center", va="center", fontsize=5.4, color=colour, rotation=90, zorder=7,
                bbox=dict(fc="#F3EFE4", ec="none", pad=0.4))

# legend
lx, ly = 0, -2.25
for i, (col, txt) in enumerate([(IN_L, "IN left (WMD side)"), (IN_R, "IN right (WMD side)"),
                                (OUT_L, "OUT left (tile side)"), (OUT_R, "OUT right (tile side)"),
                                (SH_C, "shield: pin 9 -> OUT ground"), (BR_C, "bridges 3-6, 8-12" + ("; dashed = jumper" if JUMPERS else ""))]):
    x0 = lx + i * 8.05
    ax.plot([x0, x0 + 1.6], [ly, ly], color=col, lw=2.4)
    ax.text(x0 + 2.0, ly, txt, va="center", fontsize=7, color="#333")

SUMMARY = ("One insulated jumper (dashed); everything else crossing-free." if len(JUMPERS) == 1 else
           "No jumpers: no wire crosses or shares a hole with another." if not JUMPERS else f"{len(JUMPERS)} insulated jumpers (dashed).")
VERSION = "v3" if not JUMPERS else "v2"
ax.text(COLS - 0.5, ROWS - 0.15, ("UNDERSIDE VIEW (mirrored): this is what you see with the board flipped, wires on this side." if MIRROR else f"TOP VIEW. {COLS} x {ROWS} holes ({COLS * 2.54:.0f} x {ROWS * 2.54:.0f} mm). {VERSION}, measured headers. {SUMMARY}"),
        ha="right", va="top", fontsize=7, color="#555")

fig.tight_layout()
suffix = "-underside" if MIRROR else ""
fig.savefig(f"outputs/iso-board-routing{suffix}.png", dpi=170, facecolor="white")
fig.savefig(f"outputs/iso-board-routing{suffix}.svg", facecolor="white")
print("saved")
