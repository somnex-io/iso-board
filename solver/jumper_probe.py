#!/usr/bin/env python3
"""Costing probe: how small can the OUT L loop get with at most K insulated jumpers, everything else fixed?

Reroutes only OUT L+ and OUT L- on the holes the other wires of a routes file leave free. A jumper is
a straight insulated run between two free holes that may pass over other wires' holes; never over a
pin or header hole, and never over either OUT L wire. Minimises the OUT L loop area (same polygon as
check_routes.py), then wire length. Writes the result as a routes file whose OUT L wires include the
jumper as a straight run (so check_routes.py reports the jumper's crossings as shorts, and nothing else).

usage: memguard.py 4000 -- python3 jumper_probe.py [--routes solver/routes_v3.py] [--jumpers K] [--span S] [--seconds T] --out FILE
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortools.sat.python import cp_model
from cpsat_route import geometry, ROWS, cells_of, corners, PRIM, SEC, MAX_WORKERS

LNETS = ("OUT L+", "OUT L-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--routes", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "routes_v3.py"))
    ap.add_argument("--jumpers", type=int, default=1); ap.add_argument("--span", type=int, default=6)
    ap.add_argument("--seconds", type=float, default=90); ap.add_argument("--out", required=True)
    ap.add_argument("--keep-prefix", default="", help="keep each OUT L leg as in the routes file up to a hole, e.g. 'OUT L-=22,1;OUT L+=21,0'")
    a = ap.parse_args()
    ns = {}; exec(open(a.routes).read(), ns); C = ns["CONFIG"]
    g = geometry(C["in_rot"], C["out_rot"], C["m1"], C["m2"], {k: C[k] for k in ("cols", "t1", "t2", "trow", "in_col", "out_col", "hrow")})
    cols = g["cols"]; reserved = g["pins"] | set(g["im"]) | set(g["om"])
    # The loop closes along T1's secondary pin column (pin 7 up to pin 12 and back to pin 11). A leg or a
    # jumper through the gaps in that column would make the loop self-intersect, and signed area would
    # cancel instead of measuring the loop (first attempt: signed 0, filled 222). Keep them out, so the
    # loop is a simple curve and signed area = filled area.
    sc_col = g["T"]["T1"][1]; tr0 = C["trow"]
    reserved = reserved | {(sc_col, r) for r in range(SEC[12] + tr0, SEC[7] + tr0 + 1)}
    others, keep, prefix = {}, [], {}
    stop = {k: tuple(map(int, v.split(","))) for k, v in (kv.split("=") for kv in a.keep_prefix.split(";") if kv)}
    for label, col, pts, j in ns["routes"]:
        h = cells_of(pts)
        net = next((n for n, (s, t) in g["nets"].items() if {h[0], h[-1]} == {s, t}), None)
        if net in LNETS:
            h = h if h[0] == g["nets"][net][0] else h[::-1]
            prefix[net] = h[:h.index(stop[net]) + 1] if net in stop else h[:1]
            continue
        keep.append((label, col, pts, j))
        for c in h: others[c] = label
    onb = lambda c: 0 <= c[0] < cols and 0 <= c[1] < ROWS
    m = cp_model.CpModel(); one = m.NewBoolVar("one"); m.Add(one == 1)
    x, arcs, jumps = {}, {}, []
    taken = {c for p in prefix.values() for c in p[:-1]}
    for n in LNETS:
        t = g["nets"][n][1]; s = prefix[n][-1]
        allowed = {(c, r) for c in range(cols) for r in range(ROWS) if (c, r) not in others and (c, r) not in reserved and (c, r) not in taken} | {s, t}
        idx = {c: i for i, c in enumerate(sorted(allowed))}; lits = []
        for c in allowed:
            if c == s: x[n, c] = one; continue
            x[n, c] = m.NewBoolVar(""); lits.append((idx[c], idx[c], x[n, c].Not()))
        for p in allowed:
            if p == t: continue
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (p[0] + d[0], p[1] + d[1])
                if q in allowed and q != s:
                    v = arcs[n, p, q] = m.NewBoolVar(""); lits.append((idx[p], idx[q], v))
                for span in range(2, a.span + 1):
                    q = (p[0] + d[0] * span, p[1] + d[1] * span)
                    inner = [(p[0] + d[0] * k, p[1] + d[1] * k) for k in range(1, span)]
                    if not onb(q) or any(c in reserved for c in inner): break
                    if q not in allowed or q == s or not any(c in others for c in inner): continue
                    v = arcs[n, p, q] = m.NewBoolVar(""); lits.append((idx[p], idx[q], v)); jumps.append((n, p, q, v, inner))
        m.Add(x[n, t] == 1); lits.append((idx[t], idx[s], one))
        m.AddCircuit(lits)
    for c in {c for (_, c) in x}:
        vs = [x[n, c] for n in LNETS if (n, c) in x]
        if len(vs) == 2: m.Add(sum(vs) <= 1)
    for n, p, q, v, inner in jumps:
        for c in inner:
            for n2 in LNETS:
                if (n2, c) in x: m.AddImplication(v, x[n2, c].Not())
    m.Add(sum(j[3] for j in jumps) <= a.jumpers)
    # OUT L loop area, as in cpsat_route.py: header -> pin-7 leg -> pin column -> pin-11 leg -> header
    t1 = "T1"; tr = C["trow"]; pc, sc = g["T"][t1]
    tp = lambda pn: (pc, PRIM[pn] + tr) if pn in PRIM else (sc, SEC[pn] + tr)
    a0, a1, b0, b1 = tp(7), tp(8), tp(12), tp(11)
    cross = lambda u, w: u[0] * w[1] - w[0] * u[1]
    hot = next(n for n in LNETS if a0 in g["nets"][n]); cold = next(n for n in LNETS if b1 in g["nets"][n])
    hh = next(c for c in g["nets"][hot] if c != a0); hc = next(c for c in g["nets"][cold] if c != b1)
    const = cross(a0, a1) + cross(a1, b0) + cross(b0, b1) + cross(hc, hh)
    for n in LNETS:   # the kept prefixes are fixed parts of the loop
        sign = (1 if g["nets"][hot][0] == hh else -1) if n == hot else (1 if g["nets"][cold][0] == b1 else -1)
        const += sum(sign * cross(p, q) for p, q in zip(prefix[n], prefix[n][1:]))
    terms = []
    for (n, p, q), v in arcs.items():
        sign = (1 if g["nets"][hot][0] == hh else -1) if n == hot else (1 if g["nets"][cold][0] == b1 else -1)
        terms.append(sign * cross(p, q) * v)
    area2 = m.NewIntVar(0, 20000, "area2"); m.Add(area2 >= sum(terms) + const); m.Add(area2 >= -(sum(terms) + const))
    length = [v for (n, c), v in x.items() if v is not one]
    orig = {}
    for label, col, pts, j in ns["routes"]:
        h = cells_of(pts); net = next((n for n, (s0, t0) in g["nets"].items() if {h[0], h[-1]} == {s0, t0}), None)
        if net in LNETS:
            h = h if h[0] == g["nets"][net][0] else h[::-1]; h = h[h.index(prefix[net][-1]):]
            for p, q in zip(h, h[1:]): orig[net, p, q] = 1
    if all((k in arcs) for k in orig):
        for k, v in arcs.items(): m.AddHint(v, orig.get(k, 0))
    # two phases: CP-SAT finds a first routing fast without the objective, much more slowly with it
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = a.seconds / 3; s.parameters.num_workers = MAX_WORKERS
    t0 = time.time(); st = s.Solve(m)
    print(f"jumpers <= {a.jumpers}, span <= {a.span}: feasibility {s.StatusName(st)} in {time.time() - t0:.0f}s", flush=True)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return
    m.ClearHints()
    for v in list(arcs.values()) + [v for v in x.values() if v is not one] + [area2]: m.AddHint(v, s.Value(v))
    m.Minimize(50 * area2 + sum(length))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = a.seconds; s.parameters.num_workers = MAX_WORKERS
    t0 = time.time(); st = s.Solve(m)
    print(f"  optimise: {s.StatusName(st)} in {time.time() - t0:.0f}s", flush=True)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return
    print(f"  OUT L loop area {s.Value(area2) / 2:g} square pitches (lower bound {s.BestObjectiveBound() / 100:.0f})")
    succ = {}; used_j = []
    for (n, p, q), v in arcs.items():
        if s.Value(v): succ[n, p] = q
    for n, p, q, v, inner in jumps:
        if s.Value(v): used_j.append((n, p, q, inner))
    paths = {}
    for n in LNETS:
        t = g["nets"][n][1]; path = list(prefix[n])
        while path[-1] != t:
            q = succ[n, path[-1]]; path += cells_of([path[-1], q])[1:]
        paths[n] = path
    for n, p, q, inner in used_j:
        print(f"  jumper on {n}: {p} -> {q}, {len(inner) + 1} pitches long, over {[(c, others[c]) for c in inner if c in others]}")
    labels = {"OUT L+": "L+ : T1 pin 11 -> OUT (mirrored)", "OUT L-": "L- : T1 pin 7 -> OUT (mirrored)"}
    with open(a.out, "w") as fh:
        fh.write(f"# jumper_probe.py on {os.path.basename(a.routes)}: OUT L rerouted, jumpers <= {a.jumpers}. NOT a build.\n")
        for n, p, q, inner in used_j: fh.write(f"# JUMPER on {n}: {p} -> {q} over {[c for c in inner if c in others]}\n")
        fh.write(f"CONFIG = {C!r}\n")
        for k in ("IN_C", "OUT_C", "BR_C", "SH_C"): fh.write(f"{k} = {ns[k]!r}\n")
        fh.write(f"IN_MAP = {ns['IN_MAP']!r}\nOUT_MAP = {ns['OUT_MAP']!r}\nroutes = [\n")
        for label, col, pts, j in keep:
            fh.write(f" ({label!r}, {'OUT_C' if col == ns['OUT_C'] else 'IN_C' if col == ns['IN_C'] else 'SH_C' if col == ns['SH_C'] else 'BR_C'}, {pts!r}, {j}),\n")
        for n in LNETS: fh.write(f" ({labels[n]!r}, OUT_C, {corners(paths[n])!r}, False),\n")
        fh.write("]\n")


if __name__ == "__main__":
    main()
