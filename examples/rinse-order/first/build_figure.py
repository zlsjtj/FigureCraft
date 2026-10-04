"""Rebuild the constructed collector DEMO using editable FigureCraft primitives.

All geometry is topology-only, not a measured shape or dimension.
Native flow relations are used: the relation_path API's data_flow semantic
specifies data transmission, whereas these links transport rinse/sample liquid.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build(source):
    s = dict(schema_version=1, figure_id='collector_rinse_order_demo',
        mode='new_schematic', demo=True,
        scientific_message='P bypasses the single holder before rinsing it; Q reverses the same two volumes.',
        evidence_status='Constructed DEMO; no physical experiments or mechanism validation',
        source_refs=[{'path':str(p.resolve()),'sha256':sha(p)} for p in source],
        forbidden_implications=['No simultaneous branch operation','No physical dimensions or assembly geometry',
            'No second holder','No waste recirculation','No sensor-based contamination or seal certification',
            'No validated washing or adsorption mechanism','No real benchmark or product evidence'],
        entities=[], relations=[], exact_labels=[],
        locked_values={'holder_count':1,'disc_count':1,'seal_count':2,'selector_count':2,'pump_count':1,
            'source_reservoir_count':2,'waste_reservoir_count':1,'feed_nominal_dead_volume_ml':2.0,
            'P_order':['bypass','holder'],'P_volume_ml':[4.0,8.0],
            'Q_order':['holder','bypass'],'Q_volume_ml':[8.0,4.0],
            'threshold_pct':0.50,'P_Q_total_ml':12.0,'P_Q_total_s':43.0},
        reference_palette='blue_gold_coral',
        role_map={'hardware':{'base':'#87979F'},'rinse':{'base':'#376D9D'},
                  'bypass':{'base':'#C08032'},'holder_route':{'base':'#287E7B'},
                  'sample':{'base':'#A99A85'},'waste':{'base':'#75828B'}},
        layout={'archetype':'single_topology_with_order_comparison','reading_order':'topology then P and Q'},
        depth={'mode':'D0','affects_quantitative_encoding':False},
        edit_scope={'allowed':['layout','labels','palette'],'protected':['topology','count','volumes','protocol_order']},
        output={'width_mm':160,'placement_width_mm':160,'view_width':900,'view_height':562.5,'font_profile':'Arial'},
        publication={'target_journal':None,'eligibility':'unverified'},items=[],count_constraints=[])
    ink='#243741'; muted='#586A75'; white='#FFFFFF'
    def add(id,t,**kw):
        s['items'].append(dict(id=id,type=t,**kw));return s['items'][-1]
    def text(id,t,x,y,size=20,align='left',**kw):
        return add(id,'text',text=t,x=x,y=y,size=size,align=align,fill=ink,background=white,**kw)
    def obj(id,t,ent,role,**kw):
        return add(id,t,entity=ent,role=role,logical_id=ent,object_part='primary',**kw)
    def flow(id,a,b,pts,role='hardware'):
        import math
        color='@'+role+'.stroke';head=9
        add(id+'-line','line',points=pts,stroke=color,stroke_width=2.8,relation=id,role=role)
        x,y=pts[-1];px,py=pts[-2];d=math.hypot(x-px,y-py);ux=(x-px)/d;uy=(y-py)/d
        base=[x-head*ux,y-head*uy]
        add(id+'-head','polygon',points=[[x,y],[base[0]-head*.4*uy,base[1]+head*.4*ux],
            [base[0]+head*.4*uy,base[1]-head*.4*ux]],fill=color,stroke=color,stroke_width=0,relation=id,role=role)
        s['relations'].append({'id':id,'from':a,'to':b,'kind':'flow',
            'meaning':'Liquid flow from '+a+' to '+b+' when this route is selected',
            'geometry':{'item_id':id+'-line','from':pts[0],'to':pts[-1],
              'arrow':{'item_id':id+'-head','tip':[x,y],'base':base}}})
    ents=[('sample','sample','Separate Sample source reservoir'),('rinse','rinse','Separate Rinse source reservoir'),
        ('V1','hardware','Three-port source selector'),('pump','hardware','One conventional pump'),
        ('feed','hardware','Feed segment between pump outlet and V2'),('V2','hardware','Three-port destination selector'),
        ('holder','holder_route','The one holder, containing one porous disc between two seals'),
        ('seat','hardware','Holder inlet seat sensor; presence only'),('waste','waste','One shared Waste reservoir')]
    for id,role,desc in ents:s['entities'].append({'id':id,'semantic_role':role,'description':desc})
    add('canvas','rect',x=0,y=0,w=900,h=562.5,fill=white)
    text('demo','CONSTRUCTED DEMO',32,35,18)
    text('topology-label','Liquid routes',32,72,23)
    text('not-scale','Topology only',867,35,18,align='right')
    # Minimal reservoir silhouettes identify reservoirs without specifying capacity.
    def reservoir(ent,x,y,w,h,role,label):
        obj(ent+'-body','path',ent,role,commands=[['M',x,y],['L',x,y+h-8],
            ['C',x,y+h+4,x+w,y+h+4,x+w,y+h-8],['L',x+w,y],['Z']],
            fill='@'+role+'.fill',stroke='@'+role+'.stroke',stroke_width=2)
        add(ent+'-rim','ellipse',x=x+w/2,y=y,rx=w/2,ry=6,
            fill=white,stroke='@'+role+'.stroke',stroke_width=2,entity=ent,role=role,
            logical_id=ent,object_part='decoration')
        text(ent+'-label',label,x+w/2,y+h+29,20,align='center')
    reservoir('sample',38,109,74,43,'sample','Sample')
    reservoir('rinse',38,250,74,43,'rinse','Rinse')
    reservoir('waste',793,255,74,52,'waste','Waste')
    flow('sample-to-v1','sample','V1',[[112,132],[180,132],[180,184]],'sample')
    flow('rinse-to-v1','rinse','V1',[[112,275],[180,275],[180,236]],'rinse')
    flow('v1-to-pump','V1','pump',[[206,210],[259,210]])
    flow('pump-to-feed','pump','feed',[[311,210],[371,210]])
    flow('feed-to-v2','feed','V2',[[371,210],[454,210]])
    flow('v2-to-holder','V2','holder',[[480,184],[480,122],[611,122]],'holder_route')
    flow('holder-to-waste','holder','waste',[[711,122],[830,122],[830,249]],'holder_route')
    flow('bypass-to-waste','V2','waste',[[480,236],[480,285],[787,285]],'bypass')
    for id,x in [('V1',180),('V2',480)]:
        obj(id+'-body','circle',id,'hardware',x=x,y=210,r=26,fill='@hardware.fill',stroke='@hardware.stroke',stroke_width=2)
        text(id+'-name',id,x,216,20,align='center')
    obj('pump-body','circle','pump','hardware',x=285,y=210,r=26,fill=white,stroke='@hardware.stroke',stroke_width=2.4)
    add('pump-direction','polygon',points=[[276,198],[298,210],[276,222]],fill='@hardware.stroke',
        entity='pump',role='hardware',logical_id='pump',object_part='decoration')
    text('pump-name','Pump',285,265,20,align='center')
    text('feed-label','Feed segment',381,154,20,align='center')
    text('feed-value','2.0 mL nominal',381,179,19,align='center')
    # Holder is a schematic symbol, with no unprovided assembly detail.
    obj('holder-body','rect','holder','holder_route',x=611,y=92,w=100,h=60,radius=10,
        fill='@holder_route.fill',stroke='@holder_route.stroke',stroke_width=2.2)
    text('holder-name','Holder',661,128,21,align='center')
    obj('seat-sensor','rect','seat','hardware',x=564,y=112,w=17,h=20,
        fill=white,stroke='@hardware.stroke',stroke_width=2)
    text('seat-label','Seat sensor',552,78,18,align='center')
    add('seat-leader','line',points=[[552,85],[572,109]],stroke=muted,stroke_width=1.2)
    text('holder-route-label','Through holder',673,188,20,align='center')
    text('bypass-label','Bypass',632,271,20,align='center')
    add('separator','line',points=[[32,356],[868,356]],stroke='#D8E0E4',stroke_width=1)
    text('sequence-title','Rinse order',32,389,23)
    text('p-label','P',42,445,24)
    text('q-label','Q',42,517,24)
    def phase(id,label,x,y,w,role):
        add(id,'rect',x=x,y=y,w=w,h=43,radius=5,fill='@'+role+'.fill',stroke='@'+role+'.stroke',stroke_width=1.5,role=role)
        text(id+'-label',label,x+w/2,y+28,20,align='center')
    phase('p-bypass','4.0 mL bypass',84,415,230,'bypass')
    phase('p-holder','8.0 mL holder',372,415,230,'holder_route')
    phase('q-holder','8.0 mL holder',84,487,230,'holder_route')
    phase('q-bypass','4.0 mL bypass',372,487,230,'bypass')
    # These chevrons are typographic order separators, not hydraulic links.
    text('p-next','→',343,445,25,align='center')
    text('q-next','→',343,517,25,align='center')
    text('p-outcome','Then sample',645,444,20)
    text('q-outcome','Diagnostic control',645,516,20)
    for ent in ['sample','rinse','waste','V1','V2','pump','holder','seat']:
        s['count_constraints'].append({'name':ent,'expected':1,'scope':{'entity':ent},'expected_logical_ids':[ent]})
    s['exact_labels']=[i['text'] for i in s['items'] if i['type']=='text']
    s['caption']='Figure 1. Constructed DEMO of the rinse topology and order comparison. V1 selects Sample or Rinse for one pump. The feed segment between the pump outlet and V2 has a nominal dead volume of 2.0 mL. V2 selects either the single holder or the bypass; both discharge to the same Waste reservoir. Arrows show permitted liquid-flow direction, not simultaneous operation. P delivers 4.0 mL through the bypass before 8.0 mL through the holder. Q reverses those quantities and is a diagnostic control. The holder-seat sensor reports presence, not cleanliness or seal integrity. The holder symbol represents one porous disc clamped between two seals; no internal geometry is specified. Shapes, distances and tubing lengths are schematic and have no physical scale.'
    s['alt_text']='One hydraulic topology has separate Sample and Rinse reservoirs entering selector V1, then a pump and a feed segment labelled 2.0 mL nominal. Selector V2 routes liquid either through one holder or along a bypass. Both routes end at one Waste reservoir. A seat sensor is located at the holder inlet. Below, P reads 4.0 mL bypass, then 8.0 mL holder, then sample. Q reads 8.0 mL holder, then 4.0 mL bypass, and is labelled diagnostic control.'
    return s

def main():
    p=argparse.ArgumentParser();p.add_argument('--skill-root',type=Path,required=True)
    p.add_argument('--input-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise SystemExit('Refusing to overwrite '+str(a.out))
    source=[a.input_dir/n for n in ['task.md','materials.md','results.csv']]
    s=build(source);a.out.mkdir(parents=True)
    spec=a.out/'figure_spec.json';spec.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    cmd=[sys.executable,str(a.skill_root/'scripts/render_figure.py'),str(spec),'--out',str(a.out/'exports'),
         '--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--qa-views','--placement-width-mm','160']
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (a.out/'rebuild-log.json').write_text(json.dumps({'command':cmd,'exit_code':run.returncode,
          'stdout':run.stdout,'stderr':run.stderr},indent=2),encoding='utf-8')
    print(run.stdout);print(run.stderr);return run.returncode
if __name__=='__main__':raise SystemExit(main())
