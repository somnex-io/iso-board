#!/usr/bin/env python3
"""Per-pair loop and crosstalk geometry for a routes file.

For each balanced pair (IN L, IN R, OUT L, OUT R): the loop polygon (hot wire, straight down the pin
column through the windings and bridge, cold wire, across the header), its signed area and its
filled (even-odd) area, how far apart the two legs run, and which other conductors have holes inside
the loop. Then the longest runs where an L-channel conductor runs alongside an R-channel conductor.

usage: analyse_pairs.py [ROUTES_FILE]   (default solver/routes_v3.py)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_routes import spec, holes

PITCH_MM = 2.54


def load(path):
    ns = {}; exec(open(path).read(), ns)
    c = ns["CONFIG"]
    place = {k: c[k] for k in ("t1", "t2", "trow", "in_col", "out_col", "hrow")}
    nets, pads, sh_src, out_gnd, in_gnd, bodies, windings = spec(c["in_rot"], c["out_rot"], c["m1"], c["m2"], **place)
    paths = {}
    for label, _c, pts, _j in ns["routes"]:
        h = holes(pts)
        name = next((n for n, t in nets.items() if {h[0], h[-1]} == t), None)
        if name is None: name = "T1 shield" if h[0] == sh_src[0] else "T2 shield"
        paths[name] = h
    return paths, windings


def winding(poly, x, y):
    w = 0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if y0 <= y < y1 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) > 0: w += 1
        elif y1 <= y < y0 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) < 0: w -= 1
    return w


def loop(paths, pair, wnd):
    a0, a1, b0, b1 = wnd
    legs = [paths[f"{pair}+"], paths[f"{pair}-"]]
    hot = next(p for p in legs if a0 in (p[0], p[-1])); cold = next(p for p in legs if b1 in (p[0], p[-1]))
    hot = hot if hot[-1] == a0 else hot[::-1]; cold = cold if cold[0] == b1 else cold[::-1]
    name = lambda p: next(n for n in (f"{pair}+", f"{pair}-") if paths[n] in (p, p[::-1]))
    return hot + [a1, b0] + cold, hot, cold, name(hot), name(cold)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "routes_v3.py")
    paths, windings = load(path)
    chan = lambda n: "L" if (" L" in n or n.startswith("T1")) else "R"
    print(f"{path}\n")
    print("1. Loop area per pair (square hole pitches; 1 = 6.45 mm^2)")
    rows = []
    for pair, wnd in windings.items():
        poly, hot, cold, hn, cn = loop(paths, pair, wnd)
        signed = abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))) / 2
        step = 0.1
        xs = [x for x, _ in poly]; ys = [y for _, y in poly]
        filled = sum(step * step for i in range(int(min(xs) / step), int(max(xs) / step) + 1)
                     for j in range(int(min(ys) / step), int(max(ys) / step) + 1)
                     if winding(poly, i * step + 0.013, j * step + 0.017) % 2)
        cold_set = set(cold); hot_set = set(hot)
        near = lambda c, other: min(abs(c[0] - o[0]) + abs(c[1] - o[1]) for o in other)
        gaps = [near(c, cold_set) for c in hot]
        beside = sum(1 for g in gaps if g == 1)
        together, cur = [], []
        for c, g in zip(hot, gaps):
            if g == 1: cur.append(c)
            elif cur: together.append(cur); cur = []
        if cur: together.append(cur)
        together = "; ".join(f"{t[0]}..{t[-1]}" for t in together if len(t) >= 3) or "nowhere for 3+ holes"
        inside = {}
        on_loop = set(poly)
        for n, p in paths.items():
            if n in (f"{pair}+", f"{pair}-"): continue
            k = [c for c in p if c not in on_loop and winding(poly, c[0] + 0.013, c[1] + 0.017) != 0]
            if k: inside[n] = len(k)
        rows.append((pair, signed, filled, len(hot), len(cold), beside, max(gaps), inside, hn, cn, together))
    tot = sum(r[1] for r in rows)
    for pair, signed, filled, lh, lc, beside, gmax, inside, hn, cn, together in rows:
        print(f"   {pair:6s} signed {signed:5.0f}  filled {filled:5.0f}  ({100 * signed / tot:4.0f}% of total {tot:.0f})")
        print(f"          {hn} {lh} holes, {cn} {lc} holes; {beside} holes of {hn} have {cn} beside them; widest gap {gmax} pitches")
        print(f"          side by side (listed from the header end): {together}")
    print("\n2. Conductors with holes inside each pair's loop")
    for pair, _s, _f, _lh, _lc, _b, _g, inside, *_ in rows:
        other = "R" if pair.endswith("L") else "L"
        desc = ", ".join(f"{n} {k}{' <- other channel' if chan(n) == other and 'shield' not in n else ''}" for n, k in sorted(inside.items())) or "none"
        print(f"   {pair:6s}: {desc}")
    t1, t2 = set(paths["T1 shield"]), set(paths["T2 shield"])
    print(f"\n3. Shield: T1 wire {len(paths['T1 shield'])} holes, T2 wire {len(paths['T2 shield'])} holes, holes in common {sorted(t1 & t2)}"
          f" -> {'a tree (no loop)' if len(t1 & t2) <= 1 else 'CHECK: shared run or loop'}")
    print("\n4. Longest side-by-side runs, L-channel vs R-channel conductors (shields excluded)")
    runs = []
    for ln, lp in paths.items():
        if "shield" in ln or chan(ln) != "L": continue
        for rn, rp in paths.items():
            if "shield" in rn or chan(rn) != "R": continue
            rs = set(rp)
            for gap in (1, 2):
                best = cur = 0; best_end = None
                for i, c in enumerate(lp):
                    d = (lp[i + 1][0] - c[0], lp[i + 1][1] - c[1]) if i + 1 < len(lp) else (c[0] - lp[i - 1][0], c[1] - lp[i - 1][1])
                    perp = [(d[1] * gap, d[0] * gap), (-d[1] * gap, -d[0] * gap)]
                    hit = any((c[0] + p[0], c[1] + p[1]) in rs for p in perp)
                    cur = cur + 1 if hit else 0
                    if cur > best: best, best_end = cur, c
                if best >= 3: runs.append((best, gap, ln, rn, best_end))
    for best, gap, ln, rn, end in sorted(runs, reverse=True)[:8]:
        print(f"   {best:2d} holes (~{(best - 1) * PITCH_MM:3.0f} mm) at {gap * PITCH_MM:.2f} mm spacing: {ln} beside {rn}, ending at {end}")


if __name__ == "__main__":
    main()
