import itertools, heapq, json
COLS, ROWS = 48, 17
PRIM = {6:3,5:5,4:7,3:9,2:11,1:13}; SEC = {12:3,11:5,9:9,8:11,7:13}
T1pc,T1sc,T2pc,T2sc = 6,20,27,41
PINSET = {(c,r) for c in (T1pc,T2pc) for r in PRIM.values()} | {(c,r) for c in (T1sc,T2sc) for r in SEC.values()}
def holes(pts):
    s=[]
    for (a,b),(c,d) in zip(pts,pts[1:]):
        if a==c: s += [(a,r) for r in range(min(b,d),max(b,d)+1)]
        else:    s += [(k,b) for k in range(min(a,c),max(a,c)+1)]
    return s
def route(start, goals, blocked, cost):
    dist={start:0}; prev={start:None}; pq=[(0,start)]; found=None
    while pq:
        d,u=heapq.heappop(pq)
        if u in goals: found=u; break
        if d>dist[u]: continue
        c,r=u
        for dc,dr in ((1,0),(-1,0),(0,1),(0,-1)):
            n=(c+dc,r+dr)
            if not(0<=n[0]<COLS and 0<=n[1]<ROWS): continue
            if n not in goals and (n in blocked or n in PINSET): continue
            bend = 0.4 if prev[u] is not None and (n[0]-c,n[1]-r)!=(c-prev[u][0],r-prev[u][1]) else 0
            nd=d+cost(n)+bend
            if nd<dist.get(n,1e9): dist[n]=nd; prev[n]=u; heapq.heappush(pq,(nd,n))
    if found is None: return None
    p=[]; x=found
    while x is not None: p.append(x); x=prev[x]
    return p[::-1], dist[found]
def compress(path):
    out=[path[0]]
    for a,b,c in zip(path,path[1:],path[2:]):
        if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]): out.append(b)
    out.append(path[-1]); return out
def hmap(c0,c1,r0,rot):
    A={(c0,r0):"G1",(c1,r0):"G2",(c0,r0+1):"L+",(c1,r0+1):"L-",(c0,r0+2):"R+",(c1,r0+2):"R-"}
    if rot: A={(c0,r0):"R-",(c1,r0):"R+",(c0,r0+1):"L-",(c1,r0+1):"L+",(c0,r0+2):"G2",(c1,r0+2):"G1"}
    return A
def bridges(b1,b2):
    return {"T1 3-6":[(6,9),(b1,9),(b1,3),(6,3)],"T1 8-12":[(20,11),(19,11),(19,3),(20,3)],
            "T2 3-6":[(27,9),(b2,9),(b2,3),(27,3)],"T2 8-12":[(41,11),(40,11),(40,3),(41,3)]}
IN_COST  = lambda n: 1 if n[1]>=14 else (2 if n[0]<=5 or 23<=n[0]<=28 else 6)
OUT_COST = lambda n: 1 if n[1]<=2 else (2 if n[0]>=20 else 6)
def run(im, om, br):
    hdr=set(im)|set(om)
    inv_in={v:k for k,v in im.items()}; inv_out={v:k for k,v in om.items()}
    base={}
    for k,v in br.items():
        for h in holes(v): base[h]=k
    innets={"IN L+":(inv_in["L+"],{(6,13)}),"IN L-":(inv_in["L-"],{(6,7)}),"IN R+":(inv_in["R+"],{(27,13)}),"IN R-":(inv_in["R-"],{(27,7)})}
    outnets={"OUT L-":((20,5),{inv_out["L-"]}),"OUT L+":((20,13),{inv_out["L+"]}),"OUT sh1":((20,9),{inv_out["G1"],inv_out["G2"]}),
             "OUT R+":((41,13),{inv_out["R+"]}),"OUT R-":((41,5),{inv_out["R-"]}),"OUT sh2":((41,9),{inv_out["G1"],inv_out["G2"]})}
    def solve(nets, order, occ, cost, rows_block, sol):
        occ=dict(occ); sol=dict(sol); total=0
        for name in order:
            s,gs=nets[name]
            if name=="OUT sh2" and "OUT sh1" in sol: gs=gs|set(holes(sol["OUT sh1"]))
            if name=="OUT sh1" and "OUT sh2" in sol: gs=gs|set(holes(sol["OUT sh2"]))
            blocked=set(occ)|(hdr-({s}|gs))|{(c,r) for c in range(COLS) for r in rows_block}
            r=route(s,gs,blocked,cost)
            if r is None: return None
            p,d=r; total+=d
            for h in p: occ[h]=name
            sol[name]=compress(p)
        return total,occ,sol
    bestin=None
    for io in itertools.permutations(innets):
        r=solve(innets,io,base,IN_COST,(0,1,2),{})
        if r and (bestin is None or r[0]<bestin[0]): bestin=r
    if not bestin: return None
    bestout=None
    for oo in itertools.permutations(outnets):
        r=solve(outnets,oo,bestin[1],OUT_COST,(15,16),bestin[2])
        if r and (bestout is None or r[0]<bestout[0]): bestout=r
    if not bestout: return None
    return bestin[0]+bestout[0], bestout[2]
best=None
for in_cols in ((1,2),(2,3)):
 for in_rot in (0,1):
  for out_cols in ((45,46),(44,45)):
   for out_rot in (0,1):
    for b1 in (7,5):
     for b2 in (28,26):
      im=hmap(in_cols[0],in_cols[1],7,in_rot); om=hmap(out_cols[0],out_cols[1],7,out_rot)
      r=run(im,om,bridges(b1,b2))
      if r:
        cost,sol=r
        print("OK cost %.1f in%s rot%d out%s rot%d b1=%d b2=%d"%(cost,in_cols,in_rot,out_cols,out_rot,b1,b2))
        if best is None or cost<best[0]: best=(cost,in_cols,in_rot,out_cols,out_rot,b1,b2,sol,im,om)
if best:
    cost,in_cols,in_rot,out_cols,out_rot,b1,b2,sol,im,om=best
    print("\nBEST cost %.1f in%s rot%d out%s rot%d b1=%d b2=%d"%(cost,in_cols,in_rot,out_cols,out_rot,b1,b2))
    print("IN map",im); print("OUT map",om)
    for k,v in sol.items(): print(" ",k,v)
    json.dump(dict(cost=cost,in_cols=in_cols,in_rot=in_rot,out_cols=out_cols,out_rot=out_rot,b1=b1,b2=b2,
                   sol={k:v for k,v in sol.items()},im={str(k):v for k,v in im.items()},om={str(k):v for k,v in om.items()}),open('best_route.json','w'))
else: print("none")
