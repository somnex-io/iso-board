#!/usr/bin/env python3
"""Negotiated-congestion router (PathFinder style) for the iso board.

Each round every net is ripped up and rerouted by cheapest path; holes wanted by more
than one net get more expensive (present + history cost) until nobody shares a hole.
Net order does not matter, unlike the old greedy scripts. It is a heuristic: a routing it
finds is real (and is re-checked by check_routes.py); failing to find one proves nothing.

Single process, runs configs one after another, appends one JSON line per run.

usage: negotiate.py [--configs all|IN,OUT,M1,M2;...] [--place k=v,...] [--seeds K] [--rounds N]
"""
import argparse, heapq, itertools, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cpsat_route import geometry, write_routes, parse_place, ROWS, PAIRS, IN_SIDE
import check_routes


INF = float("inf")
HIST_STEP, PRES_GROWTH, PRES_MAX = 0.5, 1.05, 20
# soft preferences as cost multipliers (1 = neutral): beside the pair partner, under the other
# channel's transformer (IN pair / OUT pair), next to a wire from the other side of the isolation
F_PARTNER, F_UNDER_IN, F_UNDER_OUT, F_DOMAIN = 0.35, 1.6, 1.3, 1.5


def route(g, rounds, seed, trace=False, prefs=True):
    cols = g["cols"]; rng = random.Random(seed)
    reserved = g["pins"] | set(g["im"]) | set(g["om"])
    nb = {(c, r): [(c + dc, r + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if 0 <= c + dc < cols and 0 <= r + dr < ROWS] for c in range(cols) for r in range(ROWS)}
    snk = set(g["sh_snk"])
    names = list(g["nets"]) + ["SH"]
    hist, occ, paths = {}, {}, {}
    noise = {}
    partner = {**{p: q for p, q in PAIRS}, **{q: p for p, q in PAIRS}}
    wrong_body = {}
    for t, ch in (("T1", "R"), ("T2", "L")):
        for side, f in (("IN", F_UNDER_IN), ("OUT", F_UNDER_OUT)):
            for n in (f"{side} {ch}+", f"{side} {ch}-"): wrong_body[n] = (g["bodies"][t], f)
    occ_in, occ_out = {}, {}                          # holes held by IN-side / tile-side wires

    def sp(start, goals, pres, n):
        near = {d for c in (set().union(*paths[partner[n]].values()) if prefs and partner.get(n) in paths else ()) for d in nb[c]}
        body, fb = wrong_body.get(n, ((), 1)) if prefs else ((), 1)
        other_side = (occ_out if n in IN_SIDE else occ_in) if prefs else {}
        dist = {start: 0.0}; prev = {start: None}; pq = [(0.0, start)]
        while pq:
            d, u = heapq.heappop(pq)
            if u in goals and u != start: break
            if d > dist[u]: continue
            for w in nb[u]:
                if w in reserved and w not in goals: continue
                f = (F_PARTNER if w in near else 1) * (fb if w in body else 1)
                if other_side and any(other_side.get(e) for e in nb[w]): f *= F_DOMAIN
                nd = d + (1 + hist.get(w, 0)) * (1 + pres * occ.get(w, 0)) * f + noise[w]
                if nd < dist.get(w, INF): dist[w] = nd; prev[w] = u; heapq.heappush(pq, (nd, w))
        else:
            return None
        p = [u]
        while prev[p[-1]] is not None: p.append(prev[p[-1]])
        return p[::-1]

    pres = 0.5
    for it in range(rounds):
        order = names[:]; rng.shuffle(order)
        noise = {c: rng.random() * 0.2 for c in nb}
        for n in order:
            side = occ_in if n in IN_SIDE else occ_out
            for c in {c for p in paths.pop(n, {}).values() for c in p}: occ[c] -= 1; side[c] -= 1
            if n == "SH":
                p1 = sp(g["sh_src"][0], snk, pres, n)
                p2 = sp(g["sh_src"][1], snk | set(p1), pres, n) if p1 else None
                new = {"SH1": p1, "SH2": p2}
            else:
                s, t = g["nets"][n]; new = {n: sp(s, {t}, pres, n)}
            if any(p is None for p in new.values()): return dict(rounds=it + 1, fail="unroutable net " + n)
            paths[n] = new
            for c in {c for p in new.values() for c in p}: occ[c] = occ.get(c, 0) + 1; side[c] = side.get(c, 0) + 1
        over = [c for c, k in occ.items() if k > 1]
        if not over:
            flat = {k: p for d in paths.values() for k, p in d.items()}
            return dict(rounds=it + 1, paths=flat)
        for c in over: hist[c] = hist.get(c, 0) + HIST_STEP * (occ[c] - 1)
        pres = min(pres * PRES_GROWTH, PRES_MAX)
        if trace: print(f"  round {it + 1}: {len(over)} shared holes", flush=True)
    who = {c: sorted(k for k, d in paths.items() if c in {x for p in d.values() for x in p}) for c in over}
    return dict(rounds=rounds, fail=f"{len(over)} holes still shared: " + "; ".join(f"{c} {'/'.join(v)}" for c, v in sorted(who.items())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="all")
    ap.add_argument("--place", default="")
    ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--rounds", type=int, default=200)
    ap.add_argument("--out", default="solver/results")
    ap.add_argument("--stop-on-success", action="store_true", help="next config after the first valid routing")
    ap.add_argument("--no-prefs", action="store_true", help="plain congestion costs, ignore the soft preferences")
    a = ap.parse_args()
    cfgs = list(itertools.product((0, 1), repeat=4)) if a.configs == "all" else \
        [tuple(map(int, c.split(","))) for c in a.configs.split(";")]
    place = parse_place(a.place)
    os.makedirs(os.path.join(a.out, "negotiated"), exist_ok=True)
    log = os.path.join(a.out, "negotiate.jsonl")
    for cfg in cfgs:
        g = geometry(*cfg, place)
        P = g["cfg"]
        tag = "r%d%d_m%d%d_c%d_t%d-%d_tr%d_o%d_h%d" % (*cfg, P["cols"], P["t1"], P["t2"], P["trow"], P["out_col"], P["hrow"])
        for seed in range(a.seeds):
            t0 = time.time()
            res = route(g, a.rounds, seed, prefs=not a.no_prefs)
            rec = dict(tag=tag, cfg=P, seed=seed, prefs=not a.no_prefs, rounds=res["rounds"], secs=round(time.time() - t0, 1), at=time.strftime("%F %T"))
            if "paths" in res:
                fn = os.path.join(a.out, "negotiated", f"{tag}_s{seed}{'' if a.no_prefs else '_p'}.py")
                write_routes(g, res["paths"], fn, f"negotiated router, seed {seed}")
                ns = {}; exec(open(fn).read(), ns)
                errs, notes = check_routes.check(ns["routes"], cfg, P["cols"], {k: P[k] for k in ("t1", "t2", "trow", "in_col", "out_col", "hrow")})
                rec.update(result="VALID" if not errs else "CHECKER REJECTED", errors=errs, file=fn,
                           score=next((n for n in notes if n.startswith("score")), ""))
            else:
                rec.update(result="no routing", why=res["fail"])
            with open(log, "a") as fh: fh.write(json.dumps(rec) + "\n")
            print(f"{tag} seed {seed}: {rec['result']} after {rec['rounds']} rounds, {rec['secs']}s "
                  f"{rec.get('why', '')}{rec.get('score', '')}{' ' + str(rec['errors'][:3]) if rec.get('errors') else ''}", flush=True)
            if a.stop_on_success and rec["result"] == "VALID": break


if __name__ == "__main__":
    main()
