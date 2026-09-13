import itertools, heapq, json, sys, time
COLS, ROWS = 48, 17
PRIM = {6:3,5:5,4:7,3:9,2:11,1:13}; SEC = {12:3,11:5,9:9,8:11,7:13}
PINS = {(c,r) for c in (6,27) for r in PRIM.values()} | {(c,r) for c in (20,41) for r in SEC.values()}
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
            if n not in goals and (n in blocked or n in PINS): continue
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
# header geometries: list of (pos,label) for the 3 pairs in order GND, L, R
def hdr_vertical(c0,r0,rot):
    rows=[r0,r0+1,r0+2]; pairs=[("G1","G2"),("L+","L-"),("R+","R-")]
    if rot: rows=rows[::-1]; pairs=[(b,a) for a,b in pairs]
    m={}
    for r,(a,b) in zip(rows,pairs): m[(c0,r)]=a; m[(c0+1,r)]=b
    return m
def hdr_horizontal(c0,r0,rot):
    cols=[c0,c0+1,c0+2]; pairs=[("G1","G2"),("L+","L-"),("R+","R-")]
    if rot: cols=cols[::-1]; pairs=[(b,a) for a,b in pairs]
    m={}
    for c,(a,b) in zip(cols,pairs): m[(c,r0)]=a; m[(c,r0+1)]=b
    return m
IN_COST  = lambda n: 1 if n[1]>=14 else (2 if n[0]<=5 or 23<=n[0]<=29 else 6)
OUT_COST = lambda n: 1 if n[1]<=2 else (2 if n[0]>=20 else 6)
def run(im, om, br, t1m, t2m):
    hdr=set(im)|set(om); inv_in={v:k for k,v in im.items()}; inv_out={v:k for k,v in om.items()}
    base={}
    for k,v in br.items():
        for h in holes(v): base[h]=k
    t1p=( (6,13),(6,7) ) if not t1m else ((6,7),(6,13))   # (hot target, cold target)
    t1s=( (20,13),(20,5) ) if not t1m else ((20,5),(20,13))
    t2p=( (27,13),(27,7) ) if not t2m else ((27,7),(27,13))
    t2s=( (41,13),(41,5) ) if not t2m else ((41,5),(41,13))
    innets={"IN L+":(inv_in["L+"],{t1p[0]}),"IN L-":(inv_in["L-"],{t1p[1]}),"IN R+":(inv_in["R+"],{t2p[0]}),"IN R-":(inv_in["R-"],{t2p[1]})}
    outnets={"OUT L+":(t1s[0],{inv_out["L+"]}),"OUT L-":(t1s[1],{inv_out["L-"]}),"OUT sh1":((20,9),{inv_out["G1"],inv_out["G2"]}),
             "OUT R+":(t2s[0],{inv_out["R+"]}),"OUT R-":(t2s[1],{inv_out["R-"]}),"OUT sh2":((41,9),{inv_out["G1"],inv_out["G2"]})}
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
t0=time.time(); found=[]
import os
log=open("nojump.log","a")
in_opts=[("V",hdr_vertical(1,7,0)),("Vr",hdr_vertical(1,7,1)),("H",hdr_horizontal(1,7,0)),("Hr",hdr_horizontal(1,7,1)),("H8",hdr_horizontal(1,8,0)),("H8r",hdr_horizontal(1,8,1))]
out_opts=[("V",hdr_vertical(45,7,0)),("Vr",hdr_vertical(45,7,1)),("H",hdr_horizontal(44,7,0)),("Hr",hdr_horizontal(44,7,1)),("H8",hdr_horizontal(44,8,0)),("H8r",hdr_horizontal(44,8,1))]
for (iname,im) in in_opts:
  for (oname,om) in out_opts:
    for t1m in (0,1):
      for t2m in (0,1):
        for b2a in (26,28):
          for b2b in (40,42):
            br={"T1 3-6":[(6,9),(7,9),(7,3),(6,3)],"T1 8-12":[(20,11),(19,11),(19,3),(20,3)],
                "T2 3-6":[(27,9),(b2a,9),(b2a,3),(27,3)],"T2 8-12":[(41,11),(b2b,11),(b2b,3),(41,3)]}
            r=run(im,om,br,t1m,t2m)
            if r:
                log.write("FOUND %s %s %d %d %d %d %.1f %s\n"%(iname,oname,t1m,t2m,b2a,b2b,r[0],json.dumps(r[1]))); log.flush()
                found.append((r[0],iname,oname,t1m,t2m,b2a,b2b,r[1],im,om))
print("elapsed",time.time()-t0)
found.sort(key=lambda x:x[0])
if found:
    c,iname,oname,t1m,t2m,b2a,b2b,sol,im,om=found[0]
    print("BEST",iname,oname,t1m,t2m,b2a,b2b)
    print("IN",im); print("OUT",om)
    for k,v in sol.items(): print(" ",k,v)
    json.dump(dict(iname=iname,oname=oname,t1m=t1m,t2m=t2m,b2a=b2a,b2b=b2b,sol=sol,im={str(k):v for k,v in im.items()},om={str(k):v for k,v in om.items()}),open('nojump.json','w'))
else: print("none")
