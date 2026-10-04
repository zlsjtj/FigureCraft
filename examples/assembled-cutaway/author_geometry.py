"""Editable DEMO geometry; two information designs, no measured dimensions."""
from pathlib import Path
import argparse, json, sys, subprocess, copy, hashlib

def build(skill, output, variant):
    sys.path.insert(0,str(skill/'scripts'))
    from make_examples import Scene
    s=Scene('pressure_fixture_'+variant,'Three isolated samples face one continuous reference cavity across closed diaphragms.',531.25)
    s.s['output'].update(width_mm=160,view_width=1000,view_height=531.25,placement_width_mm=160)
    s.s['items'][0]['w']=1000
    s.s['role_map']={'sample':{'base':'#80BDD6'},'reference':{'base':'#85BBAA'},'seal':{'base':'#D9A85F'},'housing':{'base':'#9FAEB4'},'membrane':{'base':'#354B56'}}
    s.s['depth']={'mode':'D1_shallow_2_5d','affects_quantitative_encoding':False,'meaning':'Illustrative cutaway with consistent oblique depth; not measured CAD geometry.'}
    s.s['locked_values']={'samples':3,'sensors':3,'diaphragms':3,'pins':2,'gaskets':1,'connected_reference_volumes':1,'dimensions':'unspecified','module_positions_fixed':True}
    s.s['forbidden_implications']=['No flow through a diaphragm','No sample-to-sample connection','No invented pin socket or fit','Illustrative shapes are not measured geometry','No new sensing function; predecessor also shares reference pressure']
    for ent,role,desc in [('base','housing','One removable reference base'),('reference','reference','One connected reference cavity'),('gasket','seal','One piece sealing all three reference ports')]:s.entity(ent,role,desc)
    for i in range(1,4):
        s.entity('S'+str(i),'sample','Isolated sample chamber')
        s.entity('sensor'+str(i),'housing','Sensor body, schematic outer profile')
        s.entity('diaphragm'+str(i),'membrane','Closed separating membrane')
        s.relation('reference'+str(i),'reference','sensor'+str(i),'reference','Sensor faces the same continuous reference cavity; no flow implied')
    for i in range(1,3):s.entity('pin'+str(i),'housing','Alignment pin; mating detail unspecified')
    H='#E5EBEE'; HS='#B6C4CC'; EDGE='#718792'; BLUE='#D9EEF6'; GREEN='#CCE6DC'; TEAL='#438675'; GOLD='#DCB372'; INK='#243B47'
    def poly(id,p,fill,ent,stroke='none',sw=1.7,**extra):s.add(id,'polygon',points=p,fill=fill,stroke=stroke,stroke_width=sw,entity=ent,**extra)
    def rect(id,x,y,w,h,fill,ent,stroke='none',sw=1.7,**extra):s.add(id,'rect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,stroke_width=sw,entity=ent,**extra)
    def line(id,p,ent,stroke=EDGE,sw=1.4,**extra):s.line(id,p,stroke,sw,entity=ent,**extra)
    def ell(id,x,y,rx,ry,fill,ent,stroke='none',**extra):s.add(id,'ellipse',x=x,y=y,rx=rx,ry=ry,fill=fill,stroke=stroke,stroke_width=1.5,entity=ent,**extra)
    def text(id,t,x,y,size=23,align='left',**kw):s.text(id,t,x,y,size,align,INK,**kw)
    text('title','Three isolated samples, one reference',30,39,26)
    text('demo','DEMO',969,38,21,'right')
    # Same shallow projection for every physical layer: rear is (+55,-34).
    rear=(55,-34); cx=[280,480,680]; basey=348
    # Full envelope and right side remain opaque; the front wall is cut away.
    poly('base-top',[[118,348],[173,314],[873,314],[818,348]],H,'base',EDGE)
    poly('base-right',[[818,348],[873,314],[873,406],[818,440]],HS,'base',EDGE)
    rect('base-section',118,348,700,92,H,'base',EDGE)
    # One connected volume: a continuous front section plus connected port necks.
    path=[['M',140,370]]
    for c in cx:path += [['L',c-42,370],['L',c-42,276],['L',c+42,276],['L',c+42,370]]
    path += [['L',796,370],['L',796,421],['L',140,421],['Z']]
    s.add('reference-cut-space','path',commands=path,fill=GREEN,stroke=TEAL,stroke_width=1.8,entity='reference',role='reference')
    # Rear roof is kept in place; no transparent surface invents a route between samples.
    # A gasket back rail and front lip are connected on the right-hand return.
    gy=348 if variant=='assembled' else 298
    poly('gasket-plane',[[126,gy],[181,gy-34],[859,gy-34],[804,gy]],GOLD,'gasket','#B58A46')
    poly('gasket-right-return',[[804,gy],[859,gy-34],[859,gy-28],[804,gy+6]],'#BD8F47','gasket')
    rect('gasket-front-edge',126,gy,678,6,'#C69A54','gasket')
    # Apertures are illustrations of three known ports, not their measured profile.
    for n,c in enumerate(cx,1):
        poly('gasket-opening'+str(n),[[c-43,gy],[c+12,gy-34],[c+96,gy-34],[c+41,gy]],GREEN,'reference',TEAL,1.2)
        if variant=='exploded':
            line('opening-guide-left'+str(n),[[c-42,gy+9],[c-42,346]],'gasket','#A6AAA8',1.2,dash=[4,4])
            line('opening-guide-right'+str(n),[[c+42,gy+9],[c+42,346]],'gasket','#A6AAA8',1.2,dash=[4,4])
    # Module fronts and their cut-away sensor skirt expose sealed interfaces.
    module_shift=-36 if variant=='exploded' else 0
    for n,c in enumerate(cx,1):
        top=142+module_shift; bottom=276+module_shift
        # Back half-shell and front section share one object identity.
        # The rear half shell is rounded; it is not a box with a decorative wing.
        s.add('sensor-side'+str(n),'path',commands=[['M',c-55,top+4],['C',c-19,top-26,c+77,top-32,c+77,top+4],['L',c+77,bottom+40],['C',c+77,bottom+55,c+65,bottom+65,c+55,bottom+72],['L',c-55,bottom+72],['Z']],fill=HS,stroke=EDGE,stroke_width=1.4,entity='sensor'+str(n))
        rect('sensor-left-wall'+str(n),c-55,top+4,13,bottom+68-top,H,'sensor'+str(n),EDGE)
        rect('sensor-right-wall'+str(n),c+42,top+4,13,bottom+68-top,H,'sensor'+str(n),EDGE)
        rect('reference-front-neck'+str(n),c-42,bottom+4,84,356-(bottom+4),GREEN,'reference')
        line('reference-front-left'+str(n),[[c-42,bottom+4],[c-42,356]],'reference',TEAL,1.7)
        line('reference-front-right'+str(n),[[c+42,bottom+4],[c+42,356]],'reference',TEAL,1.7)
        # Sample chamber silhouette is rounded; only its front longitudinal half is shown.
        s.add('chamber-'+str(n),'path',commands=[['M',c-42,top+4],['L',c+42,top+4],['L',c+42,bottom],['L',c-42,bottom],['Z']],fill=BLUE,stroke='#558DA6',stroke_width=1.7,entity='S'+str(n),logical_id='S'+str(n),object_part='primary')
        s.add('chamber-back-rim'+str(n),'path',commands=[['M',c-42,top+4],['C',c-12,top-18,c+64,top-18,c+65,top+4],['L',c+42,top+4],['Z']],fill='#EAF6FA',stroke='#558DA6',stroke_width=1.3,entity='S'+str(n),logical_id='S'+str(n),object_part='decoration',surface_meaning='same chamber rear boundary')
        if variant=='exploded':rect('open-reference-stub'+str(n),c-42,bottom+5,84,42,GREEN,'reference',TEAL)
        # Continuous line is the closed membrane. It must never turn into a gap.
        rect('membrane-'+str(n),c-43,bottom-1,86,6,'#354B56','diaphragm'+str(n))
        text('sample-name'+str(n),'S'+str(n),c,top+66,25,'center')
    # Two actual pins, deliberately no invented mating holes.
    for n,x in enumerate([160,777],1):
        rect('pin-shaft'+str(n),x-6,286,12,64,'#A6B7BF','pin'+str(n),EDGE)
        ell('pin-cap'+str(n),x,286,6,3,'#DCE5E9','pin'+str(n),EDGE)
    # Reference continuity is visible, so the label is short and centered in the space.
    text('reference-label','Common reference cavity',470,406,23,'center')
    # Short object-bound leaders stay separate from material boundaries.
    text('diaphragms-label','Diaphragms',975,228,23,'right')
    line('diaphragm-leader',[[852,236],[800,236],[723,275+module_shift]],'diaphragm3',INK,1.4)
    text('pins-label','Alignment pins',42,255,22)
    line('pin-label-left',[[157,265],[160,282]],'pin1',INK)
    text('gasket-label','One-piece gasket',972,288 if variant=='assembled' else 320,22,'right')
    line('gasket-leader',[[876,298 if variant=='assembled' else 328],[832,331 if variant=='assembled' else 301]],'gasket',INK)
    text('base-label','Removable base',470,485,23,'center')
    line('base-leader',[[470,459],[470,442]],'base',INK)
    text('scale','Illustrative cutaway; not to scale',30,520,20)
    s.s['count_constraints']=[{'name':'samples','expected':3,'scope':{'id_prefix':'chamber-'},'expected_logical_ids':['S1','S2','S3']}]
    s.s['caption']=('DEMO. Three isolated sample chambers face the same connected reference cavity through closed diaphragms. '
        'The one-piece gasket seals three reference ports; two pins align the removable base while sample modules stay in place. '
        'Cutaway shapes and depths are illustrative, not mechanical dimensions or a pin-fit design. Depressurize before opening. '
        +('The gasket and modules are separated vertically only to show their correspondence; this is a maintenance view, not operation.' if variant=='exploded' else 'The front wall is cut away to show the connected cavity; solid side walls remain opaque.'))
    s.s['alt_text']='Three blue chambers end in separate closed dark diaphragms. Three green reference necks join one green cavity in a grey removable base. A gold gasket wraps the three ports; two grey pins are visible. No flow arrows.'
    s.s['layout']={'archetype':'assembled_cutaway' if variant=='assembled' else 'exploded_interface','reading_order':'three samples to closed membranes to common cavity','primary_message':'Shared reference does not connect the samples'}
    s.finish(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skill',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--variant',choices=['assembled','exploded'],required=True);a=p.parse_args()
    build(a.skill,a.out,a.variant)
