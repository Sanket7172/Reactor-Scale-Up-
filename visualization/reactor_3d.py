import math
import numpy as np
import plotly.graph_objects as go

def create_reactor_figure(D,H,liquid_height,stages,baffles=4):
    R=D/2; fig=go.Figure()
    a=np.linspace(0,2*math.pi,100)
    for z in np.linspace(0,H,10):fig.add_trace(go.Scatter3d(x=R*np.cos(a),y=R*np.sin(a),z=np.full_like(a,z),mode='lines',showlegend=False,line=dict(width=2)))
    # liquid cylinder surface
    z=liquid_height; x=np.r_[0,R*.98*np.cos(a)]; y=np.r_[0,R*.98*np.sin(a)]; zz=np.full_like(x,z)
    fig.add_trace(go.Scatter3d(x=x,y=y,z=zz,mode='lines',name='Liquid level',line=dict(width=5)))
    # baffles
    for i in range(baffles):
        th=2*math.pi*i/baffles; rr=np.linspace(.86*R,.98*R,20)
        fig.add_trace(go.Scatter3d(x=rr*np.cos(th),y=rr*np.sin(th),z=np.linspace(0,H,20),mode='lines',showlegend=False,line=dict(width=7)))
    fig.add_trace(go.Scatter3d(x=[0,0],y=[0,0],z=[0,H],mode='lines',name='Shaft',line=dict(width=8)))
    for i,s in enumerate(stages,1):
        d=s['impeller_diameter_m']; z=s['elevation_m']; fig.add_trace(go.Scatter3d(x=d/2*np.cos(a),y=d/2*np.sin(a),z=np.full_like(a,z),mode='lines',name=f'Stage {i}',line=dict(width=9)))
        # conceptual circulation paths
        for phase in np.linspace(0,2*math.pi,8,endpoint=False):
            t=np.linspace(0,2*math.pi,100); rad=.55*d*(.7+.25*np.sin(t)**2)
            fig.add_trace(go.Scatter3d(x=rad*np.cos(t+phase),y=rad*np.sin(t+phase),z=np.clip(z+.15*D*np.sin(2*t+phase),0,liquid_height),mode='lines',showlegend=False,line=dict(width=2)))
    fig.update_layout(title='3D Reactor & Mixing — CFD-inspired visualization',margin=dict(l=0,r=0,t=45,b=0),scene=dict(aspectmode='data',xaxis_title='X (m)',yaxis_title='Y (m)',zaxis_title='Elevation (m)'))
    return fig
