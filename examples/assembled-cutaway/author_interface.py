"""Original fixed-source DEMO: make the changed interface visible beside its predecessor."""
from pathlib import Path
import argparse,sys,json

def build(skill,out):
    sys.path.insert(0,str(skill/'scripts'))
    from make_examples import Scene
    s=Scene('reference_interface_replacement','The same three isolated sensing modules retain a common reference; three individual hoses are replaced by one aligned removable base.',531.25)
    s.s['output'].update(width_mm=160,view_width=1000,view_height=531.25,placement_width_mm=160);s.s['items'][0]['w']=1000
    s.s['role_map']={'sample':{'base':'#80BDD6'},'reference':{'base':'#85BBAA'},'seal':{'base':'#D9A85F'},'housing':{'base':'#9FAEB4'},'membrane':{'base':'#354B56'}}
    s.s['depth']={'mode':'D1_shallow_2_5d','affects_quantitative_encoding':False,'meaning':'Front cutaway with retained rear shell; illustrative geometry.'}
    s.s['locked_values']={'physical_samples':3,'physical_sensors':3,'diaphragms_per_state':3,'baseline_hoses':3,'new_bases':1,'new_pins':2,'new_gaskets':1,'reference_volumes_per_state':1,'before_after_views_of_same_samples':True}
    s.s['forbidden_implications']=['No new common-reference function','No sample communication or flow through membranes','No real mechanical dimensions','No pin mating geometry specified','No motion during operation','No performance implied by shorter drawn paths']
    s.s['entities']=[];s.s['relations']=[]
    for n in range(1,4):
        s.entity('S'+str(n),'sample','Same isolated sample repeated across two configurations')
        s.entity('sensor'+str(n),'housing','Same sensing module, unchanged position')
        s.entity('membrane'+str(n),'membrane','Same closed diaphragm')
        s.entity('hose'+str(n),'reference','One individual reference hose in prior configuration')
    for ent,role,desc in [('old_reference','reference','Common reference source in prior configuration'),('new_reference','reference','Common reference cavity in removable base'),('base','housing','One removable base'),('gasket','seal','One gasket around three ports'),('pin1','housing','First alignment pin'),('pin2','housing','Second alignment pin')]:s.entity(ent,role,desc)
    for n in range(1,4):
        s.relation('prior_reference'+str(n),'old_reference','sensor'+str(n),'reference','Individual hose connects each reference side to common source, no flow direction stipulated')
        s.relation('new_reference'+str(n),'new_reference','sensor'+str(n),'reference','Reference side faces same connected reference cavity, no flow arrow')
    s.s['layout']={'archetype':'paired_interface_change','reading_order':'same top modules, different reference interface below','primary_message':'Changed packaging, preserved sensing and isolation'}
    BLUE='#D9EEF6';GREEN='#CCE6DC';TEAL='#438675';GREY='#E5EBEE';EDGE='#718792';SIDE='#B6C4CC';GOLD='#DCB372';INK='#243B47'
    def rect(id,x,y,w,h,fill,entity,stroke='none',sw=1.3,**kw):return s.add(id,'rect',x=x,y=y,w=w,h=h,fill=fill,entity=entity,stroke=stroke,stroke_width=sw,**kw)
    def path(id,c,fill,ent,stroke='none',sw=1.3,**kw):return s.add(id,'path',commands=c,fill=fill,entity=ent,stroke=stroke,stroke_width=sw,**kw)
    def poly(id,p,fill,ent,stroke='none',sw=1.3):return s.add(id,'polygon',points=p,fill=fill,entity=ent,stroke=stroke,stroke_width=sw)
    def text(id,t,x,y,size=23,align='left'):s.text(id,t,x,y,size,align,INK)
    def line(id,p,ent,color=INK,sw=1.2,**kw):s.line(id,p,color,sw,entity=ent,**kw)
    text('title','Replace the interface, retain the sensing',30,40,26)
    text('demo','DEMO',975,39,21,'right')
    text('prior-title','a  Three individual hoses',222,108,24,'center')
    text('base-title','b  One aligned base',769,108,24,'center')
    # Shared reference in prior design is an abstract source, not invented hardware.
    rect('old-source',40,370,375,42,GREEN,'old_reference',TEAL,1.7,radius=6)
    text('prior-reference-label','Common reference',227,398,22,'center')
    oldcs=[90,220,350];newcs=[640,770,900]
    # Three distinct hoses terminate at the same source. They are physical connections,
    # not data-flow arrows and are not drawn to encode lengths or setup times.
    for i,c in enumerate(oldcs,1):
        path('hose-outline'+str(i),[['M',c,291],['C',c,319,c+30,330,c+16,348],['C',c+10,356,c,361,c,370]],'none','hose'+str(i),TEAL,5)
        path('hose-fill'+str(i),[['M',c,291],['C',c,319,c+30,330,c+16,348],['C',c+10,356,c,361,c,370]],'none','hose'+str(i),GREEN,2.5)
    # Connected reference base under the unchanged module coordinates.
    poly('base-top',[[575,300],[610,279],[974,279],[939,300]],GREY,'base',EDGE)
    poly('base-side',[[939,300],[974,279],[974,391],[939,412]],SIDE,'base',EDGE)
    rect('base-cut-face',575,300,364,112,GREY,'base',EDGE)
    cp=[['M',592,337]]
    for c in newcs:cp += [['L',c-25,337],['L',c-25,244],['L',c+25,244],['L',c+25,337]]
    cp += [['L',928,337],['L',928,396],['L',592,396],['Z']]
    path('new-cavity',cp,GREEN,'new_reference',TEAL,1.6)
    # One contiguous sheet, with apertures removed at the three known ports.
    poly('gasket-sheet',[[580,300],[615,279],[969,279],[934,300]],GOLD,'gasket','#B58A46')
    rect('gasket-lip',580,300,354,4,'#C69A54','gasket')
    for n,c in enumerate(newcs,1):poly('port'+str(n),[[c-25,300],[c+10,279],[c+60,279],[c+25,300]],GREEN,'new_reference',TEAL,1)
    # Same module proportions and placement are repeated in both configurations.
    for config,cs,reference in [('prior',oldcs,'old_reference'),('new',newcs,'new_reference')]:
        for n,c in enumerate(cs,1):
            top=158;bottom=244;end=300
            path(config+'-body'+str(n),[['M',c-33,top],['C',c-9,top-20,c+47,top-20,c+47,top],['L',c+47,end-20],['C',c+47,end-10,c+38,end-4,c+33,end],['L',c-33,end],['Z']],SIDE,'sensor'+str(n),EDGE)
            rect(config+'-wall-left'+str(n),c-33,top,8,end-top,GREY,'sensor'+str(n),EDGE)
            rect(config+'-wall-right'+str(n),c+25,top,8,end-top,GREY,'sensor'+str(n),EDGE)
            # The open reference neck is not capped at the shared interface.
            rect(config+'-neck'+str(n),c-25,bottom+4,50,61 if config=='new' else 45,GREEN,reference)
            line(config+'-neck-left'+str(n),[[c-25,bottom+4],[c-25,305 if config=='new' else 291]],reference,TEAL,1.4)
            line(config+'-neck-right'+str(n),[[c+25,bottom+4],[c+25,305 if config=='new' else 291]],reference,TEAL,1.4)
            if config=='prior':
                # A narrowing neck joins its own hose without an impermeable end cap.
                path(config+'-neck-taper'+str(n),[['M',c-25,290],['L',c-3,303],['L',c+3,303],['L',c+25,290]],GREEN,reference,TEAL,1.3)
            rect(config+'-sample'+str(n),c-25,top,50,bottom-top,BLUE,'S'+str(n),'#558DA6',1.4)
            path(config+'-sample-rim'+str(n),[['M',c-25,top],['C',c-5,top-13,c+39,top-13,c+39,top],['L',c+25,top],['Z']],'#EAF6FA','S'+str(n),'#558DA6',1)
            rect(config+'-diaphragm'+str(n),c-26,bottom-1,52,5,'#354B56','membrane'+str(n))
            text(config+'-sample-label'+str(n),'S'+str(n),c,210,22,'center')
    # Two pins drawn with no invented mating holes or mounting bracket.
    for n,(x,y) in enumerate([(590,267),(963,248)],1):
        rect('pin'+str(n),x-4,y,8,38,'#A6B7BF','pin'+str(n),EDGE)
        s.add('pin-cap'+str(n),'ellipse',x=x,y=y,rx=4,ry=2,fill='#DCE5E9',stroke=EDGE,stroke_width=1,entity='pin'+str(n))
    text('new-reference-label','Common reference',755,372,22,'center')
    text('aligned-label','Two pins + one gasket',765,458,22,'center')
    text('scope','Same three modules shown in both configurations',30,514,20)
    s.s['caption']='DEMO. Replacement of the reference interface. (a) Three hoses connect the sensor reference sides to a common source. (b) One removable base supplies the same reference through three sealed ports, aligned by two pins and sealed by one gasket. Both views repeat the same three modules; blue samples remain isolated by the dark closed diaphragms. Pale housings, hose lengths and depths are schematic, not measured geometry or a pin-fit design. No flow direction is implied. Depressurize before opening.'
    s.s['alt_text']='Two aligned configurations repeat the same three sample modules. On the left three distinct hoses descend to a common reference source. On the right the same reference sides meet one connected cavity in a removable base, with one gold gasket and two alignment pins. Closed dark diaphragms separate every blue sample from the reference.'
    s.finish(out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skill',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();build(a.skill,a.out)
