import math
G=9.80665

def calculate_stage(stage):
    D=float(stage['impeller_diameter_m']); rpm=float(stage['rpm']); n=max(1,int(stage.get('number_impellers',1)))
    rho=float(stage['density_kg_m3']); mu=max(float(stage['viscosity_pa_s']),1e-12); N=rpm/60
    Np=stage.get('Np'); Nq=stage.get('Nq')
    P=float(Np)*rho*N**3*D**5*n if Np is not None else None
    Q=float(Nq)*N*D**3*n if Nq is not None else None
    return {**stage,'N_s':N,'Re':rho*N*D**2/mu,'Fr':N**2*D/G,'tip_speed_m_s':math.pi*D*N,
            'power_w':P,'power_kw':P/1000 if P is not None else None,'Q_m3_s':Q,'Q_m3_h':Q*3600 if Q is not None else None,
            'torque_Nm':P/(2*math.pi*N) if P is not None and N>0 else None}

def calculate_train(stages,volume_m3):
    results=[calculate_stage(s) for s in stages]
    P=sum(x['power_w'] or 0 for x in results); Q=sum(x['Q_m3_s'] or 0 for x in results)
    return results,{'total_power_kw':P/1000,'total_Q_m3_h':Q*3600,'power_per_volume_W_m3':P/volume_m3 if volume_m3 else None,
                    'Q_per_volume_1_s':Q/volume_m3 if volume_m3 else None,'turnover_time_min':volume_m3/Q/60 if Q>0 else None}

def zwietering_njs(stage,solids_wt_pct,particle_d_m,solid_density,liquid_density,S=5.0):
    X=float(solids_wt_pct)/100; dp=float(particle_d_m); dr=float(solid_density)-float(liquid_density)
    if X<=0 or dp<=0 or dr<=0:return None
    nu=float(stage['viscosity_pa_s'])/float(liquid_density); D=float(stage['impeller_diameter_m'])
    return S*nu**0.1*G**0.45*X**0.13*dp**0.2*dr**0.45*D**-0.85*float(liquid_density)**-0.45
