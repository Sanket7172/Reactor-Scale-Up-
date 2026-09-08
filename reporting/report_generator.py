from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet

def build_pdf(data):
    b=BytesIO(); doc=SimpleDocTemplate(b,pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=15*mm,bottomMargin=15*mm); s=getSampleStyleSheet(); story=[Paragraph('Reactor Scale-Up Engineering Report',s['Title']),Spacer(1,8)]
    g=data['geometry']; t=data['train']; story.append(Paragraph('Design Basis',s['Heading2']))
    story.append(_tbl([['Parameter','Value'],['Process',data['process_type']],['Working volume',f"{g['working_volume_m3']:.3f} m³"],['Total volume',f"{g['total_volume_m3']:.3f} m³"],['Liquid height',f"{g['liquid_height_m']:.3f} m"],['Fill',f"{100*g['working_volume_m3']/g['total_volume_m3']:.1f}%"]]))
    story += [Spacer(1,8),Paragraph('Independent Agitator Train',s['Heading2'])]
    rows=[['Stage','Agitator','D m','RPM','Power kW','Q m³/h','Tip m/s','Re']]
    for i,x in enumerate(data['stages'],1):rows.append([i,x['agitator'],f"{x['impeller_diameter_m']:.3f}",f"{x['rpm']:.0f}",f"{x['power_kw'] or 0:.2f}",f"{x['Q_m3_h'] or 0:.2f}",f"{x['tip_speed_m_s']:.2f}",f"{x['Re']:.2g}"])
    story += [_tbl(rows),Spacer(1,8),Paragraph('Train Performance',s['Heading2']),_tbl([['Metric','Value'],['Total power',f"{t['total_power_kw']:.2f} kW"],['Total Q',f"{t['total_Q_m3_h']:.2f} m³/h"],['P/V',f"{t['power_per_volume_W_m3']:.2f} W/m³"],['Q/V',f"{t['Q_per_volume_1_s']:.4f} s⁻¹"],['Turnover',f"{t['turnover_time_min']:.2f} min" if t['turnover_time_min'] else 'N/A']]),Spacer(1,8),Paragraph('Validation & Recommendation',s['Heading2'])]
    for n,ok,m in data['checks']:story.append(Paragraph(('PASS' if ok else 'REVIEW')+' — '+n+': '+m,s['BodyText']))
    for r in data['recommendations']:story.append(Paragraph('• '+r,s['BodyText']))
    story.append(Spacer(1,8)); story.append(Paragraph('Engineering limitation: Np/Nq are screening coefficients. RCI/vendor-specific data, Njs, kLa, heat transfer and final mechanical design require validated correlations/vendor data and process evidence.',s['BodyText']))
    doc.build(story); b.seek(0); return b.getvalue()
def _tbl(rows):
    t=Table(rows,repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17233c')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.4,colors.grey),('FONTSIZE',(0,0),(-1,-1),8)])); return t
