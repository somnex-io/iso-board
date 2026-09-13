#!/usr/bin/env python3
"""Perfboard routing for the WMD -> 2x LL1517 -> Stereo Out Jacks 1U board.
Grid: 48 columns x 17 rows of 2.54 mm holes (122 x 43 mm), in-line layout.
Coordinates are (col, row); col 0 at the IN end, row 0 at the top edge."""
import matplotlib, sys
MIRROR = "--mirror" in sys.argv
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

COLS, ROWS = 48, 17
X = (lambda c: COLS - 1 - c) if MIRROR else (lambda c: c)
P = 1.0  # one hole pitch = 1 unit

# ---- transformer footprints: primary column, secondary column ----
T1 = dict(name="T1  (LEFT channel)", pc=6, sc=20)
T2 = dict(name="T2  (RIGHT channel)", pc=27, sc=41)
PRIM_PINS = {6: 3, 5: 5, 4: 7, 3: 9, 2: 11, 1: 13}       # pin -> row
SEC_PINS = {12: 3, 11: 5, 9: 9, 8: 11, 7: 13}

# ---- headers (2x3, cols x rows) ----
IN_HDR = dict(cols=(1, 2), rows=(7, 8, 9))
OUT_HDR = dict(cols=(45, 46), rows=(7, 8, 9))
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "solver", "routes_v2.py")).read())

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
    ax.add_patch(FancyBboxPatch((cx - 9.25, 8 - 6.7), 18.5, 13.4, boxstyle="round,pad=0,rounding_size=0.6",
                                fc="none", ec="#4A4A4A", lw=1.4, ls="--"))
    ax.text(cx, -1.15, T["name"], ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333")
    ax.text(cx, 8.0, "LL1517\n(body on top,\nwires underneath)", ha="center", va="center", fontsize=7.5, color="#666")
    for pin, r in PRIM_PINS.items():
        ax.add_patch(Circle((X(T["pc"]), r), 0.34, fc="white", ec="#222", lw=1.0))
        ax.text(X(T["pc"]), r, str(pin), ha="center", va="center", fontsize=6.6, fontweight="bold")
    for pin, r in SEC_PINS.items():
        ax.add_patch(Circle((X(T["sc"]), r), 0.34, fc="white", ec="#222", lw=1.0))
        ax.text(X(T["sc"]), r, str(pin), ha="center", va="center", fontsize=6.6, fontweight="bold")
    mir = " MIRRORED: hot=4, cold=1" if T is T2 else " hot=1, cold=4"
    mis = " MIRRORED: hot=11, cold=7" if T is T2 else " hot=7, cold=11"
    ax.text(X(T["pc"]), 14.2, "PRIMARY (from WMD)" + mir, ha="center", va="top", fontsize=6.2, color=IN_C)
    ax.text(X(T["sc"]), 14.2, "SECONDARY (to tile)" + mis, ha="center", va="top", fontsize=6.2, color=OUT_C)

# headers
def header(h, mp, title, colour):
    c0, c1 = sorted((X(h["cols"][0]), X(h["cols"][1]))); r0, r1 = h["rows"][0], h["rows"][-1]
    ax.add_patch(Rectangle((c0 - 0.6, r0 - 0.6), (c1 - c0) + 1.2, (r1 - r0) + 1.2, fc="#DDE3EA", ec=colour, lw=1.4))
    for (c, r), lab in mp.items():
        ax.add_patch(Circle((X(c), r), 0.32, fc="white", ec=colour, lw=1.0))
        ax.text(X(c), r, lab, ha="center", va="center", fontsize=5.2, fontweight="bold", color="#222")
    ax.text((c0 + c1) / 2, r1 + 1.3, title, ha="center", va="top", fontsize=7, color=colour, fontweight="bold")
header(IN_HDR, IN_MAP, "IN 2x3 (from WMD)\nMEASURED map", IN_C)
header(OUT_HDR, OUT_MAP, "OUT 2x3 (to tile)\nMEASURED map", OUT_C)

# routes
for label, colour, pts, jumper in routes:
    xs = [X(p[0]) for p in pts]; ys = [p[1] for p in pts]
    if jumper:
        ax.plot(xs, ys, color=colour, lw=2.8, ls=(0, (2, 1.2)), solid_capstyle="round", zorder=6)
        ax.text(X(38.2), 6.1, "insulated jumper\n(dashed): T2 shield\njoins T1 shield at col 45", ha="center", va="center", fontsize=5.6, color=colour, fontweight="bold")
    else:
        ax.plot(xs, ys, color=colour, lw=2.4, solid_capstyle="round", solid_joinstyle="round", zorder=5)

# lane labels
ax.text(X(30) - (6 if MIRROR else 0), -0.45, "L-  (row 0)", va="center", fontsize=6.5, color=OUT_C, backgroundcolor="#F3EFE4")
ax.text(X(30) - (6 if MIRROR else 0), 0.55, "shield (row 1)", va="center", fontsize=6.5, color=SH_C, backgroundcolor="#F3EFE4")
ax.text(X(30) - (6 if MIRROR else 0), 1.55, "L+  (row 2)", va="center", fontsize=6.5, color=OUT_C, backgroundcolor="#F3EFE4")
ax.text(X(12) - (6 if MIRROR else 0), 15.45, "R+  (row 15)", va="center", fontsize=6.5, color=IN_C, backgroundcolor="#F3EFE4")
ax.text(X(12) - (6 if MIRROR else 0), 13.55, "R-  (row 14)", va="center", fontsize=6.5, color=IN_C, backgroundcolor="#F3EFE4")

# legend
lx, ly = 0, -2.25
for i, (col, txt) in enumerate([(IN_C, "IN domain (WMD side, primaries)"), (OUT_C, "OUT domain (tile side, secondaries)"),
                                (SH_C, "shield: pin 9 + can -> OUT ground only"), (BR_C, "series bridges 3-6 and 8-12  |  dashed = insulated jumper")]):
    ax.plot([lx + i * 11.5, lx + i * 11.5 + 1.4], [ly, ly], color=col, lw=2.4)
    ax.text(lx + i * 11.5 + 1.8, ly, txt, va="center", fontsize=7, color="#333")

ax.text(COLS - 0.5, ROWS - 0.15, ("UNDERSIDE VIEW (mirrored): this is what you see with the board flipped, wires on this side." if MIRROR else "TOP VIEW. 48 x 17 holes (122 x 43 mm). v2, measured headers. One insulated jumper (dashed); everything else crossing-free."),
        ha="right", va="top", fontsize=7, color="#555")

fig.tight_layout()
suffix = "-underside" if MIRROR else ""
fig.savefig(f"outputs/iso-board-routing{suffix}.png", dpi=170, facecolor="white")
fig.savefig(f"outputs/iso-board-routing{suffix}.svg", facecolor="white")
print("saved")
