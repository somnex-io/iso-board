#!/usr/bin/env python3
"""Exact CP-SAT router for the FOH iso board (see docs/DESIGN-SPEC.md).

Model (v3, replaces the unvalidated v1 flow model):
- Every point-to-point net is one AddCircuit over the holes it may use: a used hole is on
  the circuit, an unused hole takes its self-loop, and a fixed closing arc t -> s turns the
  circuit into a single simple path s -> t. No stray loops are possible.
- Shield: two such paths, SH1 from T1 pin 9 and SH2 from T2 pin 9, each ending at either
  OUT GND pin. SH1 and SH2 may share holes (same net), so SH2 running into SH1 and following
  it to GND is "T2's shield joins T1's wire"; every valid shield tree decomposes this way.
- At most one net per hole (the two shield paths count as one net). Pin and header holes are
  usable only by the net that terminates there; IN GND and centre taps 2 and 5 by nobody.

The status printed is the solver's own: INFEASIBLE is a proof, UNKNOWN means a time or
memory limit hit first. (v1 printed INFEASIBLE for both; its two logged INFEASIBLE results
were really UNKNOWN.)

Resource limits (13 Sept: uncapped runs with 12+ workers OOM-killed the Mac):
at most 4 workers, one solver process at a time, and always run under solver/memguard.py.
max_memory_in_mb is set but is NOT enforced on macOS (tested: a 150 MB cap ran to 887 MB),
and macOS rejects ulimit -v, so memguard is the real limit.

usage: cpsat_route.py IN_ROT OUT_ROT M1 M2 [seconds] [options]
"""
import argparse, json, sys, time
from ortools.sat.python import cp_model

ROWS = 17
PRIM = {6: 3, 5: 5, 4: 7, 3: 9, 2: 11, 1: 13}
SEC = {12: 3, 11: 5, 9: 9, 8: 11, 7: 13}
MAX_WORKERS = 4
DEFAULT_MEM_MB = 4000
# Default placement: board columns, T1/T2 primary pin column, transformer row offset,
# IN/OUT header left column, header top row.
DEFAULT_PLACE = dict(cols=48, t1=6, t2=27, trow=0, in_col=1, out_col=45, hrow=7)


def hdr_vertical(c0, r0, rot):
    """2x3 header, GND/L/R rows. rot 1 = mounted 180 degrees."""
    rows = [r0, r0 + 1, r0 + 2]; pairs = [("G1", "G2"), ("L+", "L-"), ("R+", "R-")]
    if rot: rows = rows[::-1]; pairs = [(b, a) for a, b in pairs]
    m = {}
    for r, (a, b) in zip(rows, pairs): m[(c0, r)] = a; m[(c0 + 1, r)] = b
    return m


def check_place(P):
    """Physical sanity of a placement, in hole units (body 18.5 x 13.4, centred on its pins)."""
    t1s, t2s = P["t1"] + 14, P["t2"] + 14
    assert P["in_col"] >= 1 and P["out_col"] + 1 <= P["cols"] - 2, "headers need a free column at the board end"
    assert P["t1"] - 2.25 >= P["in_col"] + 2.75, "T1 body over the IN header"
    assert t2s + 2.25 <= P["out_col"] - 0.75, "T2 body over the OUT header"
    assert P["t2"] - 2.25 >= t1s + 2.25 + 1, "T1 and T2 bodies closer than one hole"
    assert -1 <= P["trow"] <= 1, "transformer body off the 17-row board"
    assert 0 <= P["hrow"] and P["hrow"] + 2 < ROWS


def geometry(in_rot, out_rot, m1, m2, place=None):
    P = dict(DEFAULT_PLACE, **(place or {}))
    check_place(P)
    T = {"T1": (P["t1"], P["t1"] + 14), "T2": (P["t2"], P["t2"] + 14)}
    def pin(t, p):
        pc, sc = T[t]
        return (pc, PRIM[p] + P["trow"]) if p in PRIM else (sc, SEC[p] + P["trow"])
    im, om = hdr_vertical(P["in_col"], P["hrow"], in_rot), hdr_vertical(P["out_col"], P["hrow"], out_rot)
    ii = {v: k for k, v in im.items()}; oo = {v: k for k, v in om.items()}
    hot1, cold1 = (1, 4) if not m1 else (4, 1); oh1, oc1 = (7, 11) if not m1 else (11, 7)
    hot2, cold2 = (1, 4) if not m2 else (4, 1); oh2, oc2 = (7, 11) if not m2 else (11, 7)
    nets = {
        "T1 3-6": (pin("T1", 3), pin("T1", 6)), "T1 8-12": (pin("T1", 8), pin("T1", 12)),
        "T2 3-6": (pin("T2", 3), pin("T2", 6)), "T2 8-12": (pin("T2", 8), pin("T2", 12)),
        "IN L+": (ii["L+"], pin("T1", hot1)), "IN L-": (ii["L-"], pin("T1", cold1)),
        "IN R+": (ii["R+"], pin("T2", hot2)), "IN R-": (ii["R-"], pin("T2", cold2)),
        "OUT L+": (pin("T1", oh1), oo["L+"]), "OUT L-": (pin("T1", oc1), oo["L-"]),
        "OUT R+": (pin("T2", oh2), oo["R+"]), "OUT R-": (pin("T2", oc2), oo["R-"]),
    }
    # holes under each body (hole centres inside the 18.5 x 13.4 outline)
    bodies = {t: {(c, r) for c in range(pc - 2, sc + 3) for r in range(2 + P["trow"], 15 + P["trow"])} for t, (pc, sc) in T.items()}
    return dict(cols=P["cols"], T=T, im=im, om=om, nets=nets, bodies=bodies,
                pins={pin(t, p) for t in T for p in [*PRIM, *SEC]},
                sh_src=[pin("T1", 9), pin("T2", 9)], sh_snk=[oo["G1"], oo["G2"]],
                cfg=dict(in_rot=in_rot, out_rot=out_rot, m1=m1, m2=m2, **P))


PAIRS = [("IN L+", "IN L-"), ("IN R+", "IN R-"), ("OUT L+", "OUT L-"), ("OUT R+", "OUT R-")]
# soft preference weights, shared with check_routes.score (kept in sync by hand)
W_CELL, W_BEND, W_UNPAIRED, W_UNDER_IN, W_UNDER_OUT = 1, 2, 3, 2, 1


def build(g, relax=(), fixed=None, hint=None, objective=False):
    """fixed/hint: {net: [cells s..t]} with nets incl. SH1/SH2. relax: holes allowed two nets."""
    cols = g["cols"]
    cells = [(c, r) for c in range(cols) for r in range(ROWS)]
    nb = {(c, r): [(c + dc, r + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))
                   if 0 <= c + dc < cols and 0 <= r + dr < ROWS] for c, r in cells}
    reserved = g["pins"] | set(g["im"]) | set(g["om"])
    free = [c for c in cells if c not in reserved]
    m = cp_model.CpModel()
    one = m.NewBoolVar("one"); m.Add(one == 1)
    x, arc = {}, {}
    ends = {n: (s, {t}) for n, (s, t) in g["nets"].items()}
    ends["SH1"] = (g["sh_src"][0], set(g["sh_snk"])); ends["SH2"] = (g["sh_src"][1], set(g["sh_snk"]))
    for n, (s, sinks) in ends.items():
        allowed = set(free) | {s} | sinks | (set(g["sh_src"]) if n.startswith("SH") else set())
        idx = {c: i for i, c in enumerate(sorted(allowed))}
        lits = []
        for c in allowed:
            if c == s: x[n, c] = one; continue
            x[n, c] = m.NewBoolVar(f"x[{n}]{c}")
            lits.append((idx[c], idx[c], x[n, c].Not()))
        for a in allowed:
            if a in sinks: continue                       # a path stops at its first sink
            for b in nb[a]:
                if b in allowed and b != s:
                    arc[n, a, b] = v = m.NewBoolVar(f"a[{n}]{a}{b}")
                    lits.append((idx[a], idx[b], v))
        if len(sinks) == 1:
            (t,) = sinks; m.Add(x[n, t] == 1); lits.append((idx[t], idx[s], one))
        else:
            for k in sinks: lits.append((idx[k], idx[s], x[n, k]))
        m.AddCircuit(lits)
    p2p = list(g["nets"])
    for c in cells:
        base = [x[n, c] for n in p2p if (n, c) in x]
        cap = 2 if c in relax else 1
        for k in ("SH1", "SH2"):
            if (k, c) in x: m.Add(sum(base) + x[k, c] <= cap)
        if len(base) > 1: m.Add(sum(base) <= cap)
    for src, is_fix in ((fixed, True), (hint, False)):
        if not src: continue
        want = {(n, a, b) for n, p in src.items() for a, b in zip(p, p[1:])}
        missing = [k for k in want if k not in arc]
        if missing: return None, f"route uses arcs the model forbids: {sorted(missing)[:4]}"
        for k, v in arc.items():
            if is_fix: m.Add(v == int(k in want))
            else: m.AddHint(v, int(k in want))
    if objective:
        obj = []
        u = {}
        for c in cells:
            if ("SH1", c) in x:
                u[c] = m.NewBoolVar(""); m.AddImplication(x["SH1", c], u[c]); m.AddImplication(x["SH2", c], u[c])
        obj += [W_CELL * x[n, c] for n in p2p for c in cells if (n, c) in x] + [W_CELL * v for v in u.values()]
        for n in p2p + ["SH1", "SH2"]:
            for c in cells:
                if (n, c) not in x: continue
                hin = [arc[k] for k in ((n, d, c) for d in nb[c] if d[1] == c[1]) if k in arc]
                vin = [arc[k] for k in ((n, d, c) for d in nb[c] if d[0] == c[0]) if k in arc]
                hout = [arc[k] for k in ((n, c, d) for d in nb[c] if d[1] == c[1]) if k in arc]
                vout = [arc[k] for k in ((n, c, d) for d in nb[c] if d[0] == c[0]) if k in arc]
                if (hin and vout) or (vin and hout):
                    b = m.NewBoolVar("")
                    if hin and vout: m.Add(b >= sum(hin) + sum(vout) - 1)
                    if vin and hout: m.Add(b >= sum(vin) + sum(hout) - 1)
                    obj.append(W_BEND * b)
        for p, q in PAIRS:
            for a, bnet in ((p, q), (q, p)):
                for c in cells:
                    if (a, c) not in x: continue
                    near = [x[bnet, d] for d in nb[c] if (bnet, d) in x]
                    lone = m.NewBoolVar("")          # a's hole with no b hole beside it
                    if near:
                        adj = m.NewBoolVar(""); m.Add(adj <= sum(near)); m.Add(lone >= x[a, c] - adj)
                    else:
                        m.Add(lone >= x[a, c])
                    obj.append(W_UNPAIRED * lone)
        other = {"T1": "R", "T2": "L"}               # the channel that does not belong under this body
        for t, body in g["bodies"].items():
            ch = other[t]
            for n in p2p:
                if n.endswith(("3-6", "8-12")) or n.split()[1][0] != ch: continue
                w = W_UNDER_IN if n.startswith("IN") else W_UNDER_OUT
                obj += [w * x[n, c] for c in body if (n, c) in x]
        m.Minimize(sum(obj))
    return m, (x, arc, ends)


def extract(g, solver, vars_):
    x, arc, ends = vars_
    succ = {}
    for (n, a, b), v in arc.items():
        if solver.Value(v): succ[n, a] = b
    paths = {}
    for n, (s, sinks) in ends.items():
        p = [s]
        while p[-1] not in sinks: p.append(succ[n, p[-1]])
        paths[n] = p
    return paths


def shield_pieces(paths):
    """SH1/SH2 cell paths -> physical wires: SH1 whole, SH2 up to where it first meets SH1."""
    p1, p2 = paths["SH1"], paths["SH2"]
    on1 = set(p1)
    cut = next(i for i, c in enumerate(p2) if c in on1 or i == len(p2) - 1)
    return p1, p2[:cut + 1]


def corners(path):
    pts = [path[0]]
    for a, b, c in zip(path, path[1:], path[2:]):
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]): pts.append(b)
    pts.append(path[-1]); return pts


def cells_of(pts):
    out = [tuple(pts[0])]
    for (a, b), (c, d) in zip(pts, pts[1:]):
        step = ((c > a) - (c < a), (d > b) - (d < b))
        while out[-1] != (c, d): out.append((out[-1][0] + step[0], out[-1][1] + step[1]))
    return out


def load_routes(path, g):
    """Read a routes_v2.py-style file -> {net: [cells s..t]}, nets found by their endpoints."""
    ns = {}; exec(open(path).read(), ns)
    res, adj = {}, {}
    for label, _col, pts, _jumper in ns["routes"]:
        h = cells_of(pts)
        net = next((n for n, (s, t) in g["nets"].items() if {h[0], h[-1]} == {s, t}), None)
        if net:
            res[net] = h if h[0] == g["nets"][net][0] else h[::-1]
        else:
            for a, b in zip(h, h[1:]): adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    for k, s in (("SH1", g["sh_src"][0]), ("SH2", g["sh_src"][1])):
        prev, q = {s: None}, [s]
        for u in q:
            if u in g["sh_snk"]: break
            for w in sorted(adj.get(u, ())):
                if w not in prev: prev[w] = u; q.append(w)
        p = [u]
        while prev[p[-1]] is not None: p.append(prev[p[-1]])
        res[k] = p[::-1]
    return res


def write_routes(g, paths, path, note=""):
    """Write {net: [cells]} (with SH1/SH2) as a routes_v2.py-style file."""
    cfg = g["cfg"]
    im = {k: ("GND\nn.c." if v[0] == "G" else v) for k, v in g["im"].items()}
    om = {k: ("GND" if v[0] == "G" else v) for k, v in g["om"].items()}
    def pinname(cell):
        t = "T1" if cell[0] in g["T"]["T1"] else "T2"
        col = PRIM if cell[0] == g["T"][t][0] else SEC
        return t, next(p for p, r in col.items() if r + cfg["trow"] == cell[1])
    L = []
    for n in ["IN L+", "IN L-", "IN R+", "IN R-"]:
        tt, p = pinname(g["nets"][n][1]); mir = cfg["m1" if tt == "T1" else "m2"]
        L.append((f"{n[3:]} : IN -> {tt} pin {p}{' (mirrored)' if mir else ''}", "IN_C", paths[n]))
    for n in ["T1 3-6", "T1 8-12", "T2 3-6", "T2 8-12"]:
        L.append((f"{n[:2]} bridge {n[3:]}", "BR_C", paths[n]))
    for n in ["OUT L+", "OUT L-", "OUT R+", "OUT R-"]:
        tt, p = pinname(g["nets"][n][0]); mir = cfg["m1" if tt == "T1" else "m2"]
        L.append((f"{n[4:]} : {tt} pin {p} -> OUT{' (mirrored)' if mir else ''}", "OUT_C", paths[n]))
    p1, p2 = shield_pieces(paths)
    L.append(("shield T1 pin 9 -> OUT GND", "SH_C", p1))
    L.append((f"shield T2 pin 9 -> {'OUT GND' if p2[-1] in g['sh_snk'] else 'joins T1 shield'}", "SH_C", p2))
    with open(path, "w") as fh:
        fh.write(f"# Routing generated by solver ({note})\n")
        fh.write(f"CONFIG = {cfg!r}\n")
        fh.write('IN_C, OUT_C, BR_C, SH_C = "#1F6FB2", "#D9541E", "#7A7A7A", "#2E8B57"\n')
        fh.write(f"IN_MAP  = {im!r}\nOUT_MAP = {om!r}\n# (label, colour, points, is_jumper)\nroutes = [\n")
        for label, col, cells in L: fh.write(f" ({label!r}, {col}, {corners(cells)!r}, False),\n")
        fh.write("]\n")


def solve(g, seconds, workers=MAX_WORKERS, mem_mb=DEFAULT_MEM_MB, relax=(), fixed=None, hint=None, objective=False, log=False):
    t0 = time.time()
    m, vars_ = build(g, relax, fixed, hint, objective)
    if m is None: return dict(status="REJECTED", why=vars_, build_s=time.time() - t0)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = seconds
    s.parameters.num_workers = min(workers, MAX_WORKERS)
    s.parameters.max_memory_in_mb = mem_mb
    s.parameters.log_search_progress = log
    st = s.Solve(m)
    res = dict(status=s.StatusName(st), build_s=round(time.time() - t0 - s.WallTime(), 1), solve_s=round(s.WallTime(), 1),
               limit_s=seconds, workers=s.parameters.num_workers, mem_mb=mem_mb, info=s.SolutionInfo())
    if objective and st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        res.update(obj=s.ObjectiveValue(), bound=s.BestObjectiveBound())
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        res["paths"] = extract(g, s, vars_)
    return res


def parse_place(txt):
    return {k: int(v) for k, v in (kv.split("=") for kv in txt.split(",") if kv)} if txt else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("in_rot", type=int); ap.add_argument("out_rot", type=int)
    ap.add_argument("m1", type=int); ap.add_argument("m2", type=int)
    ap.add_argument("seconds", type=float, nargs="?", default=60)
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    ap.add_argument("--mem-mb", type=int, default=DEFAULT_MEM_MB)
    ap.add_argument("--place", default="", help="e.g. cols=49,out_col=45 (keys: %s)" % ",".join(DEFAULT_PLACE))
    ap.add_argument("--relax", default="", help="holes that may hold two nets, e.g. '43,6;44,6'")
    ap.add_argument("--fix", help="routes file whose wires are forced into the model")
    ap.add_argument("--hint", help="routes file used as a solution hint")
    ap.add_argument("--opt", action="store_true", help="minimise length, bends and the soft preferences")
    ap.add_argument("--routes-out", help="write the solution as a routes file")
    ap.add_argument("--append", help="append a one-line JSON result here (checkpoint)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--log", action="store_true")
    a = ap.parse_args()
    g = geometry(a.in_rot, a.out_rot, a.m1, a.m2, parse_place(a.place))
    relax = {tuple(map(int, p.split(","))) for p in a.relax.split(";") if p}
    res = solve(g, a.seconds, a.workers, a.mem_mb, relax,
                load_routes(a.fix, g) if a.fix else None, load_routes(a.hint, g) if a.hint else None, a.opt, a.log)
    head = {k: v for k, v in res.items() if k != "paths"}
    print(f"{a.tag} cfg {g['cfg']} relax {len(relax)} fix {a.fix} hint {a.hint} -> {head}", flush=True)
    if "paths" in res:
        for k, v in res["paths"].items(): print(f"  {k:8s} {corners(v)}")
        if a.routes_out: write_routes(g, res["paths"], a.routes_out, f"cpsat {res['status']}")
    if a.append:
        with open(a.append, "a") as fh:
            fh.write(json.dumps(dict(tag=a.tag, cfg=g["cfg"], relax=sorted(relax), fix=a.fix, hint=a.hint, opt=a.opt, **head,
                                     paths={k: corners(v) for k, v in res.get("paths", {}).items()}, at=time.strftime("%F %T"))) + "\n")


if __name__ == "__main__":
    main()
