def validate_design(g,stages):
    checks=[]; T=g['tank_diameter_m']; fill=100*g['working_volume_m3']/g['total_volume_m3'] if g['total_volume_m3'] else 0
    def add(n,ok,m):checks.append((n,bool(ok),m))
    add('Working fill',20<=fill<=85,f'{fill:.1f}%')
    add('Liquid H/T',g['liquid_height_m']/T>=.5,f"H/T={g['liquid_height_m']/T:.2f}")
    add('Baffles',g['baffles']>=4 or g['froude']<.05,f"{g['baffles']} baffles; Fr={g['froude']:.3g}")
    for i,s in enumerate(stages,1):
        add(f'Stage {i} D/T',.2<=s['impeller_diameter_m']/T<=.9,f"D/T={s['impeller_diameter_m']/T:.2f}")
        add(f'Stage {i} C/T',.02<=s['clearance_m']/T<=.5,f"C/T={s['clearance_m']/T:.2f}")
        add(f'Stage {i} RPM',s['rpm']>0,f"RPM={s['rpm']:.0f}")
    return checks

def recommendations(process_type,train):
    p=process_type.lower()
    if 'solid' in p or 'crystall' in p: base='Verify suspension using system-specific Njs and maintain an experimentally justified N/Njs margin.'
    elif 'gas' in p: base='Verify gas dispersion, superficial gas velocity and kLa using process-specific correlations or pilot data.'
    elif 'viscos' in p: base='Check torque, motor loading, wall clearance and heat-transfer limitations before finalizing RPM.'
    elif 'heat' in p: base='Verify U·A·ΔT against heat release and utility limits; mixing alone does not establish thermal adequacy.'
    else: base='Use blend time or Q/V as primary scale-up evidence; P/V, tip speed and Re are secondary checks.'
    return [base,f"Calculated train P/V = {train['power_per_volume_W_m3']:.1f} W/m³; compare with validated pilot/reference data."]
