import math

def scale_rpm(reference,target,basis):
    Nr=float(reference['rpm']); Dr=float(reference['impeller_diameter_m']); Dt=float(target['impeller_diameter_m']); Vr=float(reference['volume_m3']); Vt=float(target['volume_m3'])
    if min(Dr,Dt,Vr,Vt)<=0: raise ValueError('Diameter and volume must be positive.')
    b=basis.lower()
    if b=='constant tip speed': return Nr*Dr/Dt
    if b=='constant rpm': return Nr
    if b=='constant froude': return Nr*math.sqrt(Dr/Dt)
    if b=='constant p/v': return Nr*((Dr**5/Vr)/(Dt**5/Vt))**(1/3)
    if b=='constant q/v': return Nr*((Dr**3/Vr)/(Dt**3/Vt))
    if b=='constant reynolds': return Nr*(Dr/Dt)**2
    raise ValueError(basis)
