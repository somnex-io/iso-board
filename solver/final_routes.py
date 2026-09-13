# Final routing for the confirmed header maps (both: G G / L+ L- / R+ R-, viewed from the top, GND row toward row 0)
COLS, ROWS = 48, 17
PRIM = {6:3,5:5,4:7,3:9,2:11,1:13}; SEC = {12:3,11:5,9:9,8:11,7:13}
PINS = {(c,r) for c in (6,27) for r in PRIM.values()} | {(c,r) for c in (20,41) for r in SEC.values()}
IN_MAP  = {(1,7):"GND",(2,7):"GND",(1,8):"L+",(2,8):"L-",(1,9):"R+",(2,9):"R-"}
OUT_MAP = {(45,7):"GND",(46,7):"GND",(45,8):"L+",(46,8):"L-",(45,9):"R+",(46,9):"R-"}
HDR = set(IN_MAP)|set(OUT_MAP)
BARE = {
 "T1 bridge 3-6":  [(6,9),(7,9),(7,3),(6,3)],
 "T1 bridge 8-12": [(20,11),(19,11),(19,3),(20,3)],
 "T2 bridge 3-6":  [(27,9),(28,9),(28,3),(27,3)],
 "T2 bridge 8-12": [(41,11),(40,11),(40,3),(41,3)],
 "IN L- -> T1 pin 4":   [(2,8),(5,8),(5,7),(6,7)],
 "IN L+ -> T1 pin 1":   [(1,8),(0,8),(0,14),(6,14),(6,13)],
 "T1 pin 11 -> OUT L-": [(20,5),(21,5),(21,0),(47,0),(47,8),(46,8)],
 "T2 pin 7 -> OUT R+":  [(41,13),(45,13),(45,9)],
 "T2 pin 9 -> OUT GND (left)": [(41,9),(41,7),(45,7)],
}
INSUL = {
 "IN R+ -> T2 pin 1":   [(1,9),(1,16),(27,16),(27,13)],
 "IN R- -> T2 pin 4":   [(2,9),(2,15),(25,15),(25,7),(27,7)],
 "T1 pin 7 -> OUT L+":  [(20,13),(20,12),(22,12),(22,2),(44,2),(44,8),(45,8)],
 "T1 pin 9 -> OUT GND (right)": [(20,9),(20,6),(24,6),(24,4),(46,4),(46,7)],
 "T2 pin 11 -> OUT R-": [(41,5),(42,5),(42,12),(46,12),(46,9)],
}
import sys
if len(sys.argv) > 1:  # final_routes.py ROUTES.py: the same checks on a routes file, pads from its CONFIG and header maps
    _ns = {}; exec(open(sys.argv[1]).read(), _ns); _c = _ns["CONFIG"]
    PINS = {(t + dc, r + _c["trow"]) for t in (_c["t1"], _c["t2"]) for dc, rs in ((0, PRIM), (14, SEC)) for r in rs.values()}
    HDR = set(_ns["IN_MAP"]) | set(_ns["OUT_MAP"])
    BARE = {k: p for k, _, p, j in _ns["routes"] if not j}; INSUL = {k: p for k, _, p, j in _ns["routes"] if j}
def holes(pts):
    s=[]
    for (a,b),(c,d) in zip(pts,pts[1:]):
        if a==c: s += [(a,r) for r in range(min(b,d),max(b,d)+1)]
        else:    s += [(k,b) for k in range(min(a,c),max(a,c)+1)]
    return s
if __name__=="__main__":
    import itertools
    bad=False
    B={k:holes(v) for k,v in BARE.items()}; I={k:holes(v) for k,v in INSUL.items()}
    for (k1,h1),(k2,h2) in itertools.combinations(B.items(),2):
        x=set(h1)&set(h2)
        if x and k1.startswith("shield") and k2.startswith("shield") and x <= {BARE[k1][0],BARE[k1][-1]} & {BARE[k2][0],BARE[k2][-1]}:
            print("  shield joint (same net)",k1,"|",k2,sorted(x)); continue
        if x: print("BARE CROSS",k1,"|",k2,sorted(x)); bad=True
    allends={v[0] for v in BARE.values()}|{v[-1] for v in BARE.values()}|{v[0] for v in INSUL.values()}|{v[-1] for v in INSUL.values()}
    for k,v in list(BARE.items())+list(INSUL.items()):
        inner=set(holes(v))-{v[0],v[-1]}
        hit=inner&(PINS|HDR)
        if hit: print("THROUGH A PAD",k,sorted(hit)); bad=True
        hit2=inner&allends
        if hit2: print("OVER A SOLDER JOINT",k,sorted(hit2)); bad=True
    for k,v in INSUL.items():
        for k2,v2 in list(BARE.items())+list(INSUL.items()):
            if k2==k: continue
            ov=[h for h in holes(v) if h in set(holes(v2))]
            if len(ov)>1:
                # parallel overlap check: consecutive shared holes
                s2=set(holes(v2)); run=0; mx=0
                for h in holes(v):
                    run = run+1 if h in s2 else 0; mx=max(mx,run)
                if mx>1: print("PARALLEL OVERLAP",k,"|",k2,ov); bad=True
    print("clean" if not bad else "PROBLEMS")
    for k,v in INSUL.items():
        xs=[h for h in holes(v)[1:-1] if any(h in set(holes(b)) for b in BARE.values())]
        print(f"  {k}: crosses bare at {xs}")
