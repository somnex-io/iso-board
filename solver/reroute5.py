import os
import itertools, json
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reroute3.py")).read().split("best=None")[0])
im=hmap(1,2,7,0)
BR=bridges(7,28)
def attempt(om, bare_names, ins_names):
    hdr=set(im)|set(om); inv_in={v:k for k,v in im.items()}; inv_out={v:k for k,v in om.items()}
    nets={"IN L+":(inv_in["L+"],{(6,13)}),"IN L-":(inv_in["L-"],{(6,7)}),"IN R+":(inv_in["R+"],{(27,13)}),"IN R-":(inv_in["R-"],{(27,7)}),
          "OUT L-":((20,5),{inv_out["L-"]}),"OUT L+":((20,13),{inv_out["L+"]}),"OUT sh1":((20,9),{inv_out["G1"],inv_out["G2"]}),
          "OUT R+":((41,13),{inv_out["R+"]}),"OUT R-":((41,5),{inv_out["R-"]}),"OUT sh2":((41,9),{inv_out["G1"],inv_out["G2"]})}
    base={}
    for k,v in BR.items():
        for h in holes(v): base[h]=k
    best=None
    for oo in itertools.permutations(bare_names):
        occ=dict(base); sol={}; fail=False; total=0
        for name in oo:
            s,gs=nets[name]
            if name=="OUT sh2" and "OUT sh1" in sol: gs=gs|set(holes(sol["OUT sh1"]))
            if name=="OUT sh1" and "OUT sh2" in sol: gs=gs|set(holes(sol["OUT sh2"]))
            blocked=set(occ)|(hdr-({s}|gs))
            if name.startswith("IN"): blocked|={(c,r) for c in range(COLS) for r in (0,1,2)}; cost=IN_COST
            else: blocked|={(c,r) for c in range(COLS) for r in (14,15,16)}; cost=OUT_COST
            r=route(s,gs,blocked,cost)
            if r is None: fail=True; break
            for h in r[0]: occ[h]=name
            sol[name]=compress(r[0]); total+=r[1]
        if fail: continue
        endpoints={p for v in sol.values() for p in (v[0],v[-1])}|{p for v in BR.values() for p in (v[0],v[-1])}
        barecells=set(occ)
        isol={}; ok=True; occ2={}
        for name in ins_names:
            s,gs=nets[name]
            if name=="OUT sh1" and "OUT sh2" in sol: gs=gs|set(holes(sol["OUT sh2"]))
            iends={p for v in isol.values() for p in (v[0],v[-1])}
            blocked=(hdr-({s}|gs))|endpoints|iends
            if name.startswith("IN"): blocked|={(c,r) for c in range(COLS) for r in (0,1,2)}; lane=lambda n: 1 if n[1]>=14 else 3
            else: blocked|={(c,r) for c in range(COLS) for r in (14,15,16)}; lane=lambda n: 1 if n[1]<=2 else 3
            cost=lambda n: lane(n) + (4 if n in barecells else 0) + (4 if n in occ2 else 0)
            r=route(s,gs,blocked,cost)
            if r is None: ok=False; break
            for h in r[0]: occ2[h]=name
            isol[name]=compress(r[0]); total+=r[1]
        if ok and (best is None or total<best[0]): best=(total,sol,isol)
    return best
results=[]
base_ins=["IN R+","IN R-","OUT L+","OUT L-","OUT sh1"]
for out_cols,out_rot in (((45,46),0),((45,46),1),((44,45),0),((44,45),1)):
    om=hmap(out_cols[0],out_cols[1],7,out_rot)
    allnames=["IN L+","IN L-","IN R+","IN R-","OUT L-","OUT L+","OUT sh1","OUT R+","OUT R-","OUT sh2"]
    for extra in ([],["OUT R+"],["OUT R-"],["OUT sh2"]):
        ins=base_ins+extra; bare=[n for n in allnames if n not in ins]
        r=attempt(om,bare,ins)
        if r:
            print("OK cols",out_cols,"rot",out_rot,"insulated",ins,"cost %.1f"%r[0])
            results.append((len(ins),r[0],out_cols,out_rot,r[1],r[2]))
            break
        else: print("fail cols",out_cols,"rot",out_rot,"extra",extra)
results.sort(key=lambda x:(x[0],x[1]))
if results:
    n,cost,out_cols,out_rot,sol,isol=results[0]
    print("\nCHOSEN cols",out_cols,"rot",out_rot)
    for k,v in sol.items(): print("  bare ",k,v)
    for k,v in isol.items(): print("  INSUL",k,v)
    json.dump(dict(out_cols=out_cols,out_rot=out_rot,sol=sol,isol=isol),open('best_route.json','w'))
