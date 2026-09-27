"""Development merge after reviewing frozen candidates; NOT an independent trial.

Generate two same-size layouts from the fixed input, then render native vectors.
All positions are information layout, never optical poses or measured paths.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys

HERE=Path(__file__).resolve().parent


def make_scene(skill_dir, source, variant):
    sys.path.insert(0,str(skill_dir/'scripts'))
    from make_examples import Scene
    from relation_components import relation_path, add_component
    s=Scene('common-reference-dev-'+variant,
            'Two fixed cameras observe one passive board and write separate corner-residual records.',506.25)
    s.s['output'].update(width_mm=160,placement_width_mm=160)
    s.s['source_refs']=[{'file':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]
    s.s['evidence_status']='Constructed teaching DEMO; development after inspecting both frozen candidates'
    s.s['forbidden_implications']=['Digital transmission from Board','Camera-to-camera communication',
        'Merged records','Measured optical positions, viewing angles, focal lengths or performance',
        'Stereo reconstruction','Independent validation of this development candidate']
    s.s['role_map']={'camera':{'base':'#C7DEEF'},'record':{'base':'#E1F0EC'},
        'reference':{'base':'#D7DEE3'},'observation':{'base':'#68747F'},'write':{'base':'#2D8278'}}
    s.s['layout']={'archetype':'shared-reference-independent-rows' if variant=='rows' else 'shared-reference-independent-columns',
        'reading_order':'Board to either camera, then that camera to its own record',
        'position_semantics':'Logical grouping only. Front-view camera symbols do not encode physical orientation.'}
    s.s['depth']['mode']='D1_shallow_2_5d'
    s.s['locked_values']={'Board':1,'cameras':['C1','C2'],'records':['L1','L2'],
        'observations':[['C1','Board'],['C2','Board']], 'writes':[['C1','L1'],['C2','L2']],
        'record_content':'Each camera independently computes its own observed corner residuals',
        'physical_layout':'Unknown; not encoded','measurement_data':None}
    for eid,role,description in [('Board','reference','One passive checkerboard'),('C1','camera','Fixed camera 1'),
        ('C2','camera','Fixed camera 2'),('L1','record','Own residual record from C1'),('L2','record','Own residual record from C2')]:
        s.entity(eid,role,description)
    s.s['count_constraints']=[{'name':eid,'expected':1,'scope':{'entity':eid},'expected_logical_ids':[eid]}
        for eid in ['Board','C1','C2','L1','L2']]
    ink='#22313A'; blue='#285673'; green='#286E65'
    def obj(eid,part,typ,**kw):
        return s.add(eid+'-'+part,typ,entity=eid,logical_id=eid,
            object_part='primary' if part=='body' else 'decoration',**kw)
    def label(eid,txt,x,y,**kw):
        return s.text(eid+'-label',txt,x,y,20,align='center',fill=ink,background='#FFFFFF',
                      entity=eid,logical_id=eid,object_part='decoration',**kw)
    def board(x,y):
        # 7 by 5 graphic pattern is schematic, not a calibration target specification.
        obj('Board','top','polygon',points=[[x,y],[x+7,y-7],[x+147,y-7],[x+140,y]],fill='#E4E9ED',stroke='#4B5863',stroke_width=1.5)
        obj('Board','side','polygon',points=[[x+140,y],[x+147,y-7],[x+147,y+110],[x+140,y+117]],fill='#A7B2BC',stroke='#4B5863',stroke_width=1.5)
        obj('Board','body','rect',x=x,y=y,w=140,h=117,fill='#FFFFFF',stroke='#4B5863',stroke_width=1.7)
        for r in range(5):
            for c in range(7):
                if (r+c)%2==0:
                    obj('Board',f'square-{r}-{c}','rect',x=x+7+c*18,y=y+13+r*18,w=18,h=18,fill='#34424C')
        label('Board','Board',x+70,y-22)
    def camera(eid,cx,cy,side_label=False):
        obj(eid,'top','polygon',points=[[cx-60,cy-31],[cx-53,cy-38],[cx+67,cy-38],[cx+60,cy-31]],fill='#E1ECF5',stroke=blue,stroke_width=1.6)
        obj(eid,'side','polygon',points=[[cx+60,cy-31],[cx+67,cy-38],[cx+67,cy+32],[cx+60,cy+39]],fill='#8DB5CD',stroke=blue,stroke_width=1.6)
        obj(eid,'body','rect',x=cx-60,y=cy-31,w=120,h=70,radius=5,fill='#C7DEEF',stroke=blue,stroke_width=1.9)
        # Front circular lens preserves camera recognition without an in-plane optical axis.
        obj(eid,'lens-rim','circle',x=cx+7,y=cy+4,r=27,fill='#88B1CB',stroke=blue,stroke_width=1.8)
        obj(eid,'lens','circle',x=cx+7,y=cy+4,r=19,fill='#30566E',stroke='#244257',stroke_width=1.6)
        obj(eid,'lens-light','circle',x=cx+1,y=cy-2,r=6,fill='#B9D4E7')
        obj(eid,'stand','line',points=[[cx,cy+39],[cx,cy+53],[cx-21,cy+62],[cx+21,cy+62]],stroke=blue,stroke_width=2)
        label(eid,eid,cx-90 if side_label else cx,cy+10 if side_label else cy-54)
    def record(eid,cx,cy):
        x,y=cx-48,cy-39
        obj(eid,'body','polygon',points=[[x,y],[x+76,y],[x+96,y+20],[x+96,y+78],[x,y+78]],fill='#E1F0EC',stroke=green,stroke_width=1.9)
        obj(eid,'fold','polygon',points=[[x+76,y],[x+76,y+20],[x+96,y+20]],fill='#BCD9D1',stroke=green,stroke_width=1.3)
        s.text(eid+'-label',eid,cx,cy+9,20,align='center',fill=ink,background='#E1F0EC',
               entity=eid,logical_id=eid,object_part='decoration')
    def observe(eid,points,segment):
        add_component(s,relation_path('observe-'+eid,semantics='common_reference',points=points,
            source_entity=eid,target_entity='Board',meaning=eid+' observes the same passive Board; logical association, not a ray or signal',
            color='#657580',width=1.8,dash=[6,5],role='observation',
            label={'text':'Observe','segment':segment,'offset':[0,-12],'size':20,'fill':ink}))
    def write(eid,record_id,points,offset,align='center'):
        add_component(s,relation_path('write-'+eid,semantics='data_flow',points=points,
            source_entity=eid,target_entity=record_id,meaning=eid+' writes its own computed corner residuals to '+record_id,
            color=green,width=2.3,head=10,role='write',
            label={'text':'Write corner\nresiduals','segment':0,'offset':offset,'size':20,'leading':24,'align':align,'fill':ink}))
    s.text('title','One shared board, two independent records',450,40,23,align='center',fill=ink,background='#FFFFFF')
    if variant=='rows':
        board(55,206)
        for eid,rid,cy,by in [('C1','L1',160,231),('C2','L2',360,289)]:
            observe(eid,[[347,cy],[259,cy],[259,by],[203,by]],0)
            write(eid,rid,[[489,cy],[706,cy]],[0,-33])
            camera(eid,415,cy);record(rid,770,cy)
    else:
        board(380,98)
        for eid,rid,cx,bx in [('C1','L1',220,372),('C2','L2',680,535)]:
            observe(eid,[[cx,256],[cx,162],[bx,162]],1)
            write(eid,rid,[[cx,367],[cx,415]],[17,-10],'left')
            camera(eid,cx,294,True);record(rid,cx,464)
    s.s['caption']='Teaching schematic. Two fixed cameras observe one passive checkerboard Board. Dashed undirected connectors denote observation associations, not optical rays or digital transmission. Each camera independently computes its own observed corner residuals and writes them to its corresponding record (solid arrows). The cameras do not communicate; records are not merged. Front-view symbols, connector bends, positions, and board pattern organize the explanation and do not specify optical geometry, distances, angles, or performance.'
    s.s['alt_text']='A single Board connects by two dashed undirected observation relations to front-view camera symbols C1 and C2. A separate solid write arrow from each camera leads to its own folded-page record: C1 to L1 and C2 to L2. No line joins the cameras or the records.'
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--skill-dir',type=Path,default=HERE.parents[2])
    p.add_argument('--input',type=Path,default=HERE.parent/'input/figure-task.md')
    p.add_argument('--font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for variant in ('rows','columns'):
        scene=make_scene(a.skill_dir.resolve(),a.input.resolve(),variant)
        spec=a.out/(variant+'.json');scene.finish(spec)
        # Scene.finish supplies generic alt text; preserve the actual spatial alternative.
        data=json.loads(spec.read_text(encoding='utf-8'))
        data['alt_text']='One passive Board is shared by C1 and C2. Separate solid arrows link each camera to only its own residual record, L1 or L2. Dashed elbow connectors denote observation, not rays.'
        spec.write_text(json.dumps(data,indent=2),encoding='utf-8')
        cmd=[sys.executable,'-B','-X','utf8',str(a.skill_dir/'scripts/render_figure.py'),str(spec),
             '--out',str(a.out/variant),'--font',str(a.font),'--pdftoppm',str(a.pdftoppm),'--dpi','300','--qa-views']
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if (a.out/variant).is_dir():
            for key,name in [('caption','caption.txt'),('alt_text','alt-text.txt')]:
                (a.out/variant/name).write_text(data[key],encoding='utf-8')
        receipts.append({'variant':variant,'command':cmd,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    (a.out/'build-receipt.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    print(json.dumps([{'variant':r['variant'],'exit_code':r['exit_code']} for r in receipts]))
    return max(r['exit_code'] for r in receipts)

if __name__=='__main__':raise SystemExit(main())
