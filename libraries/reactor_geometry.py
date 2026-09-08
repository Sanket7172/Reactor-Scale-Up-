import math
HEADS={'Flat Bottom':0,'2:1 Ellipsoidal':.25,'10% Torispherical':.10,'6% Torispherical':.06,'Hemispherical':.50,'Conical':.25}
def calculate_total_volume(D,H,bottom,top):
    r=D/2; area=math.pi*r*r; db=HEADS[bottom]*D; dt=HEADS[top]*D
    def hv(d,t):
        if t=='Flat Bottom':return 0
        if t=='Hemispherical':return 2*math.pi*r**3/3
        if t=='Conical':return area*d/3
        return .5*area*d
    return area*H+hv(db,bottom)+hv(dt,top)
def liquid_height_from_volume(V,D,H,bottom,top):
    total=calculate_total_volume(D,H,bottom,top); V=min(max(V,0),total); lo=0; hi=HEADS[bottom]*D+H+HEADS[top]*D
    # numerical bisection using approximate head profile
    def partial(h):
        db=HEADS[bottom]*D; area=math.pi*(D/2)**2
        if h<=0:return 0
        if db and h<db:return area*db*(h/db)**2/2
        base=(area*db/2 if db else 0)
        hc=min(max(h-db,0),H); val=base+area*hc
        if h>db+H:
            d=min(h-db-H,HEADS[top]*D); val+=area*d/2
        return val
    for _ in range(80):
        mid=(lo+hi)/2
        if partial(mid)<V:lo=mid
        else:hi=mid
    return (lo+hi)/2
