import sys; sys.path.insert(0,'analysis')
import conditional_numbers as cn, numpy as np
d,c,l,n=cn.load_rows()
rng=np.random.default_rng(5)
opset=np.zeros(n,int)
for b,op in enumerate(cn.OPERATORS): opset[np.unique(d["date"][d["op"]==op])]|=1<<b
def strat_perm():
    p=np.arange(n)
    for v in np.unique(opset):
        ix=np.flatnonzero(opset==v); p[ix]=rng.permutation(ix)
    return p
import collections; print(collections.Counter(opset))
perms=[strat_perm() for _ in range(20)]
yr=d["year"]
scopes={"All operators":np.ones(len(yr),bool),
        "All, Magnum biased eras removed":~((d["op"]=="Magnum")&((yr<1995)|(yr>=2019))),
        "Toto + Da Ma Cai":d["op"]!="Magnum"}
for sname,sel in scopes.items():
  for fs in [("weekday","tithi"),("weekday","lunar_day"),("weekday","day_of_month"),("weekday",),("era_5yr",)]:
    cell,_=cn.cell_codes(sel,d["date"],c,d["prize"],fs)
    out=[]
    for u,(nu,share,_) in cn.UNITS.items():
        ux=d["num"][sel] if u=="number" else cn.GROUP_OF[d["num"][sel]]
        k=cn.once_per_draw(d["date"][sel],ux,nu)
        chi=cn.scan(cell[k],ux[k],nu,share)[0]
        null=[cn.scan(cn.cell_codes(sel,p[d["date"]],c,d["prize"],fs)[0][k],ux[k],nu,share)[0] for p in perms]
        out.append(f"{u} z={(chi-np.mean(null))/np.std(null,ddof=1):+.1f}")
    print(f"{sname:<34} {' x '.join(fs):<24} {'  '.join(out)}")
