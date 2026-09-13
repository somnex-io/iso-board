#!/usr/bin/env python3
"""Independent checker for a routes file (routes_v2.py format).

Deliberately shares no code with cpsat_route.py: terminals are rebuilt here from
the tables in docs/DESIGN-SPEC.md, and each route is identified by its endpoints,
not by its label.

usage: check_routes.py ROUTES_FILE [IN_ROT OUT_ROT M1 M2]
       (config and placement default to CONFIG in the routes file; without CONFIG the
        default placement from the spec is used)
Exit code 0 only if the layout is valid and has zero jumpers.
"""
import sys
from itertools import combinations

# DESIGN-SPEC section 3 tables, pin rows as on the 48 x 17 board; CONFIG trow 1 gives the 50 x 19 rows
PRIMARY = {6: 3, 5: 5, 4: 7, 3: 9, 2: 11, 1: 13}
SECONDARY = {12: 3, 11: 5, 9: 9, 8: 11, 7: 13}
HDR_ROT0 = {(0, 0): "GND", (1, 0): "GND", (0, 1): "L+", (1, 1): "L-", (0, 2): "R+", (1, 2): "R-"}
HDR_ROT1 = {(0, 0): "R-", (1, 0): "R+", (0, 1): "L-", (1, 1): "L+", (0, 2): "GND", (1, 2): "GND"}


def spec(in_rot, out_rot, m1, m2, t1=6, t2=27, trow=0, in_col=1, out_col=45, hrow=7, **_):
    def tp(pc, sc, p): return (pc, PRIMARY[p] + trow) if p in PRIMARY else (sc, SECONDARY[p] + trow)
    T1 = lambda p: tp(t1, t1 + 14, p)
    T2 = lambda p: tp(t2, t2 + 14, p)
    def header(c0, rot):
        m = {}
        for (dc, dr), lab in (HDR_ROT1 if rot else HDR_ROT0).items():
            m.setdefault(lab, []).append((c0 + dc, hrow + dr))
        return m
    ih, oh = header(in_col, in_rot), header(out_col, out_rot)
    in_hot1, in_cold1, out_hot1, out_cold1 = (4, 1, 11, 7) if m1 else (1, 4, 7, 11)
    in_hot2, in_cold2, out_hot2, out_cold2 = (4, 1, 11, 7) if m2 else (1, 4, 7, 11)
    nets = {
        "T1 3-6": {T1(3), T1(6)}, "T1 8-12": {T1(8), T1(12)},
        "T2 3-6": {T2(3), T2(6)}, "T2 8-12": {T2(8), T2(12)},
        "IN L+": {ih["L+"][0], T1(in_hot1)}, "IN L-": {ih["L-"][0], T1(in_cold1)},
        "IN R+": {ih["R+"][0], T2(in_hot2)}, "IN R-": {ih["R-"][0], T2(in_cold2)},
        "OUT L+": {T1(out_hot1), oh["L+"][0]}, "OUT L-": {T1(out_cold1), oh["L-"][0]},
        "OUT R+": {T2(out_hot2), oh["R+"][0]}, "OUT R-": {T2(out_cold2), oh["R-"][0]},
    }
    pads = {T1(p) for p in [*PRIMARY, *SECONDARY]} | {T2(p) for p in [*PRIMARY, *SECONDARY]}
    pads |= {c for v in ih.values() for c in v} | {c for v in oh.values() for c in v}
    # body outline 18.5 x 13.4 holes centred on the pins: hole centres inside it
    bodies = {"T1": {(c, r) for c in range(t1 - 2, t1 + 17) for r in range(2 + trow, 15 + trow)},
              "T2": {(c, r) for c in range(t2 - 2, t2 + 17) for r in range(2 + trow, 15 + trow)}}
    windings = {"IN L": (T1(1), T1(3), T1(6), T1(4)), "IN R": (T2(1), T2(3), T2(6), T2(4)),
                "OUT L": (T1(7), T1(8), T1(12), T1(11)), "OUT R": (T2(7), T2(8), T2(12), T2(11))}
    return nets, pads, [T1(9), T2(9)], oh["GND"], ih["GND"], bodies, windings


def holes(pts):
    out = [pts[0]]
    for (a, b), (c, d) in zip(pts, pts[1:]):
        if (a != c) == (b != d): raise ValueError(f"segment {(a, b)}->{(c, d)} is not a straight orthogonal run")
        step = ((c > a) - (c < a), (d > b) - (d < b))
        while out[-1] != (c, d): out.append((out[-1][0] + step[0], out[-1][1] + step[1]))
    return out


def check(routes, cfg, cols=48, place=None, rows=17):
    nets, pads, sh_src, out_gnd, in_gnd, bodies, windings = spec(*cfg, **(place or {}))
    errs, notes = [], []
    H = []
    for label, _c, pts, jumper in routes:
        if jumper: errs.append(f"JUMPER: {label}")
        try: h = holes(pts)
        except ValueError as ex: errs.append(f"GEOMETRY {label}: {ex}"); h = list(pts)
        if len(set(h)) != len(h): errs.append(f"SELF-OVERLAP {label}")
        for c, r in h:
            if not (0 <= c < cols and 0 <= r < rows): errs.append(f"OFF BOARD {label} {(c, r)}")
        H.append(h)
    # classify every route by endpoints
    kind = []
    for (label, *_), h in zip(routes, H):
        ends = {h[0], h[-1]}
        k = next((n for n, t in nets.items() if ends == t), None)
        kind.append(k or "SH?")
    for n in nets:
        cnt = kind.count(n)
        if cnt != 1: errs.append(f"NET {n}: {cnt} routes connect its terminals {sorted(nets[n])}")
    sh = [i for i, k in enumerate(kind) if k == "SH?"]
    sh_holes = {c for i in sh for c in H[i]}
    for i in sh:
        label = routes[i][0]
        for end in (H[i][0], H[i][-1]):
            on_other = any(end in H[j] for j in sh if j != i)
            if end not in sh_src and end not in out_gnd and not on_other:
                errs.append(f"UNCLASSIFIED ROUTE {label}: endpoint {end} is not a terminal of any net or on a shield wire")
    # shield connectivity: holes adjacent along a route are joined
    adj = {}
    for i in sh:
        for a, b in zip(H[i], H[i][1:]): adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    for s in sh_src:
        seen, st = {s}, [s]
        while st:
            u = st.pop()
            for w in adj.get(u, ()):
                if w not in seen: seen.add(w); st.append(w)
        if not seen & set(out_gnd): errs.append(f"SHIELD: pin 9 at {s} does not reach an OUT GND pin")
    # shared holes
    for i, j in combinations(range(len(routes)), 2):
        common = set(H[i]) & set(H[j])
        if not common: continue
        li, lj = routes[i][0], routes[j][0]
        if kind[i] == kind[j] == "SH?":
            ends = {H[i][0], H[i][-1], H[j][0], H[j][-1]}
            bad = [c for c in common if c not in ends]
            if len(common) > 1 or bad: errs.append(f"SHIELD STACK/CROSS {li} | {lj} at {sorted(common)}")
            else: notes.append(f"shield joint at {sorted(common)[0]}: {li} | {lj}")
        else:
            errs.append(f"SHORT {li} | {lj} share {sorted(common)}")
    # through a pad (interior hole on any pin or header hole)
    for (label, *_), h in zip(routes, H):
        hit = set(h[1:-1]) & pads
        if hit: errs.append(f"THROUGH A PAD {label} {sorted(hit)}")
        for end in (h[0], h[-1]):
            if end in in_gnd: errs.append(f"IN GND USED {label} {end}")
    # domain separation (informational)
    IN = {c for i, k in enumerate(kind) if k.startswith("IN") or k.endswith("3-6") for c in H[i]}
    OUT = {c for i, k in enumerate(kind) if k.startswith("OUT") or k.endswith("8-12") or k == "SH?" for c in H[i]}
    touch = sum(1 for (c, r) in IN for d in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (c + d[0], r + d[1]) in OUT)
    notes.append(f"IN/OUT adjacent hole pairs: {touch}; total wire holes: {sum(len(h) for h in H)}")
    notes.append(f"wire holes on the outer ring of the board: {sum(1 for h in H for c, r in h if c in (0, cols - 1) or r in (0, rows - 1))}")
    # soft preferences (tie-break score, lower is better; weights as in cpsat_route.py)
    by = {k: set(h) for k, h in zip(kind, H) if k != "SH?"}
    wires = sum(len(h) for k, h in zip(kind, H) if k != "SH?") + len(sh_holes)
    bends = sum(1 for h in H for a, b, c in zip(h, h[1:], h[2:]) if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]))
    unpaired = 0
    for p, q in (("IN L+", "IN L-"), ("IN R+", "IN R-"), ("OUT L+", "OUT L-"), ("OUT R+", "OUT R-")):
        for a, b in ((p, q), (q, p)):
            unpaired += sum(1 for (c, r) in by.get(a, ()) if not {(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)} & by.get(b, set()))
    under_in = sum(len(by.get(n, set()) & bodies[t]) for t, ch in (("T1", "R"), ("T2", "L")) for n in (f"IN {ch}+", f"IN {ch}-"))
    under_out = sum(len(by.get(n, set()) & bodies[t]) for t, ch in (("T1", "R"), ("T2", "L")) for n in (f"OUT {ch}+", f"OUT {ch}-"))
    score = wires * 1 + bends * 2 + unpaired * 3 + under_in * 2 + under_out * 1 + touch * 2  # + 2 x loop area, below
    # loop area of each balanced pair, in square hole pitches: hot wire, then straight down the pin
    # column through winding A, the series bridge and winding B, cold wire, back across the header.
    # An estimate of the on-board loop that picks up stray flux. The bridge is counted as straight so
    # a snaking bridge cannot cancel area.
    path_of = {k: h for k, h in zip(kind, H) if k != "SH?"}
    areas = {}
    for pair, (a0, a1, b0, b1) in windings.items():
        side, ch = pair.split()
        hot = next(path_of[n] for n in (f"{pair}+", f"{pair}-") if a0 in (path_of[n][0], path_of[n][-1]))
        cold = next(path_of[n] for n in (f"{pair}+", f"{pair}-") if b1 in (path_of[n][0], path_of[n][-1]))
        hot = hot if hot[-1] == a0 else hot[::-1]           # header -> a0
        cold = cold if cold[0] == b1 else cold[::-1]        # b1 -> header
        poly = hot + [a1, b0] + cold
        areas[pair] = abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))) / 2
    score += round(2 * sum(areas.values()))
    notes.append("loop area (hole pitch^2): " + ", ".join(f"{k} {v:g}" for k, v in areas.items()) + f", total {sum(areas.values()):g}")
    notes.append(f"score {score} (includes 2 x loop area): wire holes {wires}, bends {bends}, pair holes with no partner beside them {unpaired}, "
                 f"other channel's IN pair under a body {under_in}, OUT pair {under_out}, IN/OUT neighbouring holes {touch}")
    return errs, notes


if __name__ == "__main__":
    args = sys.argv[1:]
    ns = {}; exec(open(args[0]).read(), ns)
    conf = ns.get("CONFIG", {})
    cfg = tuple(map(int, args[1:5])) if len(args) >= 5 else (conf["in_rot"], conf["out_rot"], conf["m1"], conf["m2"])
    place = {k: conf[k] for k in ("t1", "t2", "trow", "in_col", "out_col", "hrow") if k in conf}
    errs, notes = check(ns["routes"], cfg, conf.get("cols", 48), place, conf.get("rows", 17))
    for n in notes: print("  note:", n)
    for e in errs: print("  ERROR:", e)
    print("VALID, zero jumpers" if not errs else f"INVALID ({len(errs)} problems)")
    sys.exit(0 if not errs else 1)
