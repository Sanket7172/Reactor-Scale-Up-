import streamlit as st
import pandas as pd
from calculations.engine import calculate_train,zwietering_njs
from calculations.scaleup import scale_rpm
from calculations.validation import validate_design,recommendations
from libraries.agitator_geometry import AGITATORS
from libraries.reactor_geometry import calculate_total_volume,liquid_height_from_volume
from visualization.reactor_3d import create_reactor_figure
from reporting.report_generator import build_pdf
st.set_page_config(page_title='Reactor Scale-Up Engineering Studio',page_icon='⚗️',layout='wide')
st.markdown('''<style>.stApp{background:#f5f7fb}.block-container{max-width:1500px;padding-top:1rem}.hero{padding:22px 26px;border-radius:18px;background:linear-gradient(135deg,#111b33,#203a63);color:#fff;margin-bottom:18px}.hero h1{margin:0}.kpi{background:#fff;border:1px solid #e2e7ef;border-radius:14px;padding:14px;min-height:82px}.kpi small{color:#6b778c}.kpi b{display:block;font-size:23px;color:#17233c}.section{font-size:20px;font-weight:700;color:#17233c;margin:12px 0}</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>⚗️ Reactor Scale-Up Engineering Studio</h1><div>Process requirement → mixing mechanism → agitator train → geometry → scale-up → validation → recommendation</div></div>',unsafe_allow_html=True)
with st.sidebar:
    st.header('Study configuration')
    process_type=st.selectbox('Process requirement',['General blending','Liquid–Liquid','Solid–Liquid','Gas–Liquid','Gas–Liquid–Solid','Crystallization','High viscosity','Heat-controlled reaction'])
    basis=st.selectbox('Scale-up basis',['Constant Tip Speed','Constant P/V','Constant Q/V','Constant Froude','Constant Reynolds','Constant RPM'])
    st.caption('Screening tool: validate final design against pilot data, vendor curves and detailed process/mechanical design.')
V,T,H,rho=st.columns(4)
with V: workV=st.number_input('Working volume (m³)',.1,5000.,3.,.1)
with T: tankD=st.number_input('Tank ID (m)',.2,20.,1.5,.01)
with H: straightH=st.number_input('Straight side (m)',.2,30.,2.,.01)
with rho: density=st.number_input('Density (kg/m³)',1.,5000.,1000.,1.)
a,b,c,d=st.columns(4)
with a: visc_cp=st.number_input('Viscosity (cP)',.1,1000000.,10.,.1)
with b: bottom=st.selectbox('Bottom head',['Flat Bottom','2:1 Ellipsoidal','10% Torispherical','6% Torispherical','Hemispherical','Conical'])
with c: top=st.selectbox('Top head',['Flat Bottom','2:1 Ellipsoidal','10% Torispherical','6% Torispherical','Hemispherical','Conical'])
with d: baffles=st.number_input('Baffles',0,12,4,1)
totalV=calculate_total_volume(tankD,straightH,bottom,top); liquidH=liquid_height_from_volume(workV,tankD,straightH,bottom,top); fill=100*workV/totalV if totalV else 0
st.markdown('<div class="section">Reactor geometry</div>',unsafe_allow_html=True); st.info(f'Capacity: **{totalV:.3f} m³** | Liquid height: **{liquidH:.3f} m** | Fill: **{fill:.1f}%**')
st.markdown('<div class="section">Independent agitator train</div>',unsafe_allow_html=True)
nstages=st.number_input('Independent agitator stages',1,3,2,1); stages=[]; cols=st.columns(nstages)
for i,col in enumerate(cols,1):
    with col:
        st.subheader(f'Stage {i}'); name=st.selectbox('Agitator',list(AGITATORS),index=i-1,key=f'ag{i}'); spec=AGITATORS[name]
        ratio=st.number_input('Impeller D/T',.1,.95,spec['D_T'],.01,key=f'dt{i}'); rpm=st.number_input('RPM',1.,1500.,120. if name not in ['Anchor','Helical Ribbon'] else 40.,1.,key=f'rpm{i}')
        nimp=st.number_input('Impellers in stage',1,6,1,1,key=f'ni{i}'); elev=st.number_input('Elevation from bottom (m)',0.,max(straightH,.1),min(.35*straightH,straightH),.01,key=f'el{i}'); clr=st.number_input('Bottom clearance (m)',.01,max(tankD,.2),max(.15*tankD,.02),.01,key=f'cl{i}')
        st.caption(f"Np={spec['Np'] if spec['Np'] is not None else 'Vendor'} | Nq={spec['Nq'] if spec['Nq'] is not None else 'Vendor'} | {spec['flow']}")
        stages.append({'agitator':name,'Np':spec['Np'],'Nq':spec['Nq'],'impeller_diameter_m':tankD*ratio,'rpm':rpm,'number_impellers':nimp,'elevation_m':elev,'clearance_m':clr,'density_kg_m3':density,'viscosity_pa_s':visc_cp/1000})
results,train=calculate_train(stages,workV)
if 'Solid' in process_type or 'Crystallization' in process_type:
    a,b,c,d=st.columns(4)
    with a: solids=st.number_input('Solids wt%',0.,80.,10.,.5)
    with b: dp=st.number_input('Particle d50 (mm)',.001,20.,.5,.01)
    with c: solidrho=st.number_input('Solid density (kg/m³)',1.,10000.,1500.,10.)
    with d: S=st.number_input('Njs S constant',.1,20.,5.,.1)
    for x in results:x['Njs_s_inv']=zwietering_njs(x,solids,dp/1000,solidrho,density,S)
else:
    for x in results:x['Njs_s_inv']=None
geom={'tank_diameter_m':tankD,'working_volume_m3':workV,'total_volume_m3':totalV,'liquid_height_m':liquidH,'baffles':baffles,'froude':max(x['Fr'] for x in results)}
checks=validate_design(geom,results); recs=recommendations(process_type,train)
kpis=[('Working Volume',f'{workV:.2f} m³'),('Fill',f'{fill:.1f}%'),('Total Power',f'{train["total_power_kw"]:.2f} kW'),('P/V',f'{train["power_per_volume_W_m3"]:.1f} W/m³'),('Total Q',f'{train["total_Q_m3_h"]:.1f} m³/h'),('Q/V',f'{train["Q_per_volume_1_s"]:.4f} s⁻¹'),('Turnover',f'{train["turnover_time_min"]:.1f} min' if train['turnover_time_min'] else 'N/A'),('Validation',f'{sum(x[1] for x in checks)}/{len(checks)} PASS')]
for j in range(0,8,4):
    cs=st.columns(4)
    for cc,(lab,val) in zip(cs,kpis[j:j+4]):cc.markdown(f'<div class="kpi"><small>{lab}</small><b>{val}</b></div>',unsafe_allow_html=True)
t1,t2,t3,t4,t5=st.tabs(['Performance','Scale-Up','Validation','3D Mixing','Engineering Report'])
with t1:
    df=pd.DataFrame([{'Stage':i+1,'Agitator':x['agitator'],'D (m)':x['impeller_diameter_m'],'RPM':x['rpm'],'Re':x['Re'],'Fr':x['Fr'],'Tip speed':x['tip_speed_m_s'],'Power kW':x['power_kw'],'Q m³/h':x['Q_m3_h'],'Torque N·m':x['torque_Nm'],'Njs s⁻¹':x['Njs_s_inv'],'N/Njs':x['rpm']/60/x['Njs_s_inv'] if x['Njs_s_inv'] else None} for i,x in enumerate(results)])
    st.dataframe(df,use_container_width=True,hide_index=True)
with t2:
    st.subheader('Reference → target scale-up'); a,b=st.columns(2)
    with a: rv=st.number_input('Reference volume (m³)',.01,5000.,max(workV/10,.1),.1); rd=st.number_input('Reference impeller D (m)',.01,10.,max(results[0]['impeller_diameter_m']*.7,.05),.01); rr=st.number_input('Reference RPM',1.,1500.,results[0]['rpm'],1.)
    with b: td=st.number_input('Target impeller D (m)',.01,10.,results[0]['impeller_diameter_m'],.01); sr=scale_rpm({'rpm':rr,'impeller_diameter_m':rd,'volume_m3':rv},{'impeller_diameter_m':td,'volume_m3':workV},basis); st.success(f'Calculated target RPM: **{sr:.1f} rpm**'); st.caption('Starting-point criterion only; check geometry, P/V, Q/V, N/Njs, blend time and heat transfer.')
with t3:
    for n,ok,m in checks:(st.success if ok else st.warning)(f"{'PASS' if ok else 'REVIEW'} — {n}: {m}")
    for r in recs:st.info(r)
with t4:
    st.plotly_chart(create_reactor_figure(tankD,straightH,liquidH,results,baffles),use_container_width=True); st.caption('CFD-inspired visualization only — not a CFD solver or calculated velocity/species field.')
with t5:
    pdf=build_pdf({'process_type':process_type,'geometry':geom,'stages':results,'train':train,'checks':checks,'recommendations':recs}); st.download_button('Download Engineering PDF',pdf,'reactor_scaleup_engineering_report.pdf','application/pdf',use_container_width=True)
