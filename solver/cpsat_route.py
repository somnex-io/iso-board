#!/usr/bin/env python3
import sys, json, itertools, time
from ortools.sat.python import cp_model

COLS, ROWS = 48, 17
PRIM = {6:3,5:5,4:7,3:9,2:11,1:13}; SEC = {12:3,11:5,9:9,8:11,7:13}
T = {"T1": dict(pc=6, sc=20), "T2": dict(pc=27, sc=41)}
def pin(t, p):
    d = T[t]
    return (d["pc"], PRIM[p]) if p in PRIM else (d["sc"], SEC[p])
ALLPINS = {pin(t, p) for t in T for p in list(PRIM) + list(SEC)}

def hdr_vertical(c0, r0, rot):
    rows = [r0, r0+1, r0+2]; pairs = [("G1","G2"), ("L+","L-"), ("R+","R-")]
    if rot: rows = rows[::-1]; pairs = [(b, a) for a, b in pairs]
    m = {}
    for r, (a, b) in zip(rows, pairs): m[(c0, r)] = a; m[(c0+1, r)] = b
    return m

def solve(in_map, out_map, m1, m2, time_limit=60, in_rows_pen=(0,1,2), out_rows_pen=(14,15,16)):
    inv_in = {v: k for k, v in in_map.items()}; inv_out = {v: k for k, v in out_map.items()}
    hot1, cold1 = (1, 4) if not m1 else (4, 1); shot1, scold1 = (7, 11) if not m1 else (11, 7)
    hot2, cold2 = (1, 4) if not m2 else (4, 1); shot2, scold2 = (7, 11) if not m2 else (11, 7)
    nets = {
        "T1 3-6":  (pin("T1",3), pin("T1",6)), "T1 8-12": (pin("T1",8), pin("T1",12)),
        "T2 3-6":  (pin("T2",3), pin("T2",6)), "T2 8-12": (pin("T2",8), pin("T2",12)),
        "IN L+": (inv_in["L+"], pin("T1",hot1)), "IN L-": (inv_in["L-"], pin("T1",cold1)),
        "IN R+": (inv_in["R+"], pin("T2",hot2)), "IN R-": (inv_in["R-"], pin("T2",cold2)),
        "OUT L+": (pin("T1",shot1), inv_out["L+"]), "OUT L-": (pin("T1",scold1), inv_out["L-"]),
        "OUT R+": (pin("T2",shot2), inv_out["R+"]), "OUT R-": (pin("T2",scold2), inv_out["R-"]),
    }
    sh_sources = [pin("T1",9), pin("T2",9)]; sh_sinks = [inv_out["G1"], inv_out["G2"]]
    hdr_cells = set(in_map) | set(out_map)
    terminals = {}
    for n, (a, b) in nets.items(): terminals.setdefault(a, set()).add(n); terminals.setdefault(b, set()).add(n)
    for c in sh_sources + sh_sinks: terminals.setdefault(c, set()).add("SH")
    reserved = ALLPINS | hdr_cells            # only usable as a terminal of the owning net
    cells = [(c, r) for c in range(COLS) for r in range(ROWS)]
    def nbrs(c):
        x, y = c
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n = (x+dx, y+dy)
            if 0 <= n[0] < COLS and 0 <= n[1] < ROWS: yield n
    arcs = [(a, b) for a in cells for b in nbrs(a)]
    m = cp_model.CpModel()
    y = {}      # y[net, cell]
    f = {}      # f[net, arc]
    netnames = list(nets) + ["SH"]
    for n in netnames:
        cap = 2 if n == "SH" else 1
        for c in cells:
            if c in reserved and n not in terminals.get(c, set()):
                continue
            y[n, c] = m.NewBoolVar(f"y_{n}_{c}")
        for a in arcs:
            if (n, a[0]) in y and (n, a[1]) in y:
                f[n, a] = m.NewIntVar(0, cap, f"f_{n}_{a}")
    # one net per cell
    for c in cells:
        vs = [y[n, c] for n in netnames if (n, c) in y]
        if vs: m.Add(sum(vs) <= 1)
    # flow conservation
    for n in netnames:
        for c in cells:
            if (n, c) not in y: continue
            fin = [f[n, a] for a in arcs if a[1] == c and (n, a) in f]
            fout = [f[n, a] for a in arcs if a[0] == c and (n, a) in f]
            if n == "SH":
                if c in sh_sources:
                    m.Add(sum(fout) - sum(fin) == 1); m.Add(y[n, c] == 1)
                elif c in sh_sinks:
                    # sink may absorb 0..2 units
                    absorb = m.NewIntVar(0, 2, f"abs_{c}")
                    m.Add(sum(fin) - sum(fout) == absorb)
                    m.Add(y[n, c] <= sum(fin))
                    m.Add(sum(fin) <= 2 * y[n, c])
                else:
                    m.Add(sum(fin) == sum(fout))
                    m.Add(sum(fin) <= 2 * y[n, c]); m.Add(y[n, c] <= sum(fin))
                    m.Add(sum(fin) >= 1).OnlyEnforceIf(y[n, c])
            else:
                a, b = nets[n]
                if c == a:
                    m.Add(sum(fout) == 1); m.Add(sum(fin) == 0); m.Add(y[n, c] == 1)
                elif c == b:
                    m.Add(sum(fin) == 1); m.Add(sum(fout) == 0); m.Add(y[n, c] == 1)
                else:
                    m.Add(sum(fin) == sum(fout)); m.Add(sum(fin) == y[n, c])
    # total shield flow into sinks == 2
    m.Add(sum(f["SH", a] for a in arcs if a[1] in sh_sinks and ("SH", a) in f)
          - sum(f["SH", a] for a in arcs if a[0] in sh_sinks and ("SH", a) in f) == 2)
    # objective: cells used + domain tidiness penalties
    obj = []
    for (n, c), v in y.items():
        w = 1
        if n.startswith("IN") and c[1] in in_rows_pen: w += 3
        if (n.startswith("OUT") or n == "SH") and c[1] in out_rows_pen: w += 3
        obj.append(w * v)
    m.Minimize(sum(obj))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = time_limit; s.parameters.num_workers = 8
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return None
    # extract paths
    out = {}
    for n in netnames:
        used = {c for (nn, c), v in y.items() if nn == n and s.Value(v)}
        arcs_used = [(a, s.Value(f[nn, a])) for (nn, a) in f if nn == n and s.Value(f[nn, a]) > 0]
        out[n] = dict(cells=sorted(used), arcs=[(a, v) for a, v in arcs_used])
    return dict(status=s.StatusName(st), obj=s.ObjectiveValue(), nets=out, terms={k: v for k, v in nets.items()},
                sh=dict(sources=sh_sources, sinks=sh_sinks))

if __name__ == "__main__":
    in_rot = int(sys.argv[1]); out_rot = int(sys.argv[2]); m1 = int(sys.argv[3]); m2 = int(sys.argv[4])
    tl = float(sys.argv[5]) if len(sys.argv) > 5 else 60
    im = hdr_vertical(1, 7, in_rot); om = hdr_vertical(45, 7, out_rot)
    t0 = time.time()
    r = solve(im, om, m1, m2, tl)
    print("in_rot", in_rot, "out_rot", out_rot, "m1", m1, "m2", m2, "->", (r["status"], r["obj"]) if r else "INFEASIBLE", "%.0fs" % (time.time() - t0))
    if r:
        r["im"] = {str(k): v for k, v in im.items()}; r["om"] = {str(k): v for k, v in om.items()}
        r["cfg"] = dict(in_rot=in_rot, out_rot=out_rot, m1=m1, m2=m2)
        json.dump(r, open(f"cpsat_{in_rot}{out_rot}{m1}{m2}.json", "w"), default=str)
