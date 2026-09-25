"""Original DEMO scenes; exact counts/data, editable primitives, no research claims."""
from pathlib import Path
import argparse,copy,csv,json,math,hashlib,sys
from palette_tools import digest,derive,gamut,to_oklab
from figure_core import fonts,wrap_text

ROOT=Path(__file__).resolve().parents[1]
INK='#24323B';MUTED='#4A5861';WHITE='#FFFFFF'
class Scene:
    def __init__(self,id,message,height=530):
        self.s={'schema_version':1,'figure_id':id,'mode':'new_schematic','demo':True,
          'scientific_message':message,'evidence_status':'DEMO_constructed_description_not_research',
          'source_refs':['Original teaching specification in this example; no scientific measurements'],
          'forbidden_implications':['No measured performance, transport rate, material effectiveness or journal endorsement'],
          'entities':[],'relations':[],'exact_labels':[],'locked_values':{},
          'reference_palette':'blue_gold_coral','role_map':{'input':{'swatch':'sky_blue'},'blocked':{'swatch':'gold'},'structure':{'swatch':'coral_pink'},'neutral':{'base':'#D8DFE3'}},
          'layout':{'archetype':'spatial_boundary','reading_order':'left_to_right'},
          'depth':{'mode':'D0','affects_quantitative_encoding':False},
          'output':{'width_mm':180,'view_width':900,'view_height':height,'font_profile':'generic_readable_draft'},
          'publication':{'target_journal':None,'eligibility':'unverified'},'items':[]}
        self.add('canvas','rect',x=0,y=0,w=900,h=height,fill=WHITE)
    def entity(self,id,role,description):self.s['entities'].append({'id':id,'semantic_role':role,'description':description})
    def relation(self,id,src,dst,kind,meaning):self.s['relations'].append({'id':id,'from':src,'to':dst,'kind':kind,'meaning':meaning})
    def add(self,id,type,**kw):self.s['items'].append(dict(id=id,type=type,**kw));return self.s['items'][-1]
    def text(self,id,text,x,y,size=18,align='left',fill=INK,**kw):
        return self.add(id,'text',text=text,x=x,y=y,size=size,align=align,fill=fill,**kw)
    def line(self,id,points,stroke=INK,stroke_width=1.7,**kw):return self.add(id,'line',points=points,stroke=stroke,stroke_width=stroke_width,**kw)
    def arrow(self,id,points,relation,color=INK,head='flow'):
        self.line(id,points,color,relation=relation)
        x,y=points[-1];px,py=points[-2];a=math.atan2(y-py,x-px);v=(math.cos(a),math.sin(a));n=(-v[1],v[0])
        if head=='inhibition':self.line(id+'-stop',[[x+n[0]*9,y+n[1]*9],[x-n[0]*9,y-n[1]*9]],color,relation=relation)
        else:self.add(id+'-head','polygon',points=[[x,y],[x-v[0]*10+n[0]*4.5,y-v[1]*10+n[1]*4.5],[x-v[0]*10-n[0]*4.5,y-v[1]*10-n[1]*4.5]],fill=color,relation=relation)
    def sphere(self,id,x,y,r,role,entity,depth=False):
        self.add(id,'circle',x=x,y=y,r=r,fill=f'@{role}.fill',stroke=f'@{role}.stroke',stroke_width=1.5,role=role,entity=entity)
        if depth:
            # Nested opaque vector disks, aligned toward a consistent upper-left light.
            self.add(id+'-shade','circle',x=x+2,y=y+2,r=r*.82,fill=f'@{role}.fill',role=role,entity=entity,decorative_depth=True)
            self.add(id+'-light','ellipse',x=x-r*.23,y=y-r*.26,rx=r*.42,ry=r*.28,fill=f'@{role}.highlight',role=role,entity=entity,decorative_depth=True)
    def finish(self,path):
        self.s['exact_labels']=[p['text'] for p in self.s['items'] if p['type']=='text']
        self.s['alt_text']=self.s['scientific_message']+' '+self.s.get('caption','')
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():raise ValueError('Example source exists: '+str(path))
        path.write_text(json.dumps(self.s,ensure_ascii=False,indent=2),encoding='utf-8')
        return self.s

def mechanism(variant):
    s=Scene('mechanism_'+variant,'A hypothetical boundary passes round probes and stops triangular probes.')
    for id,role,desc in [('feed','neutral','Feed-side region'),('boundary','structure','Barrier with one open pore'),('receiver','neutral','Receiving region'),('round','input','Six visible round probes'),('triangle','blocked','Three visible triangular probes')]:s.entity(id,role,desc)
    s.relation('pass','round','receiver','flow','Round probes traverse the pore')
    s.relation('stop','triangle','boundary','inhibition','Triangular probes do not cross this hypothetical boundary')
    s.s['locked_values']={'round_probes':6,'triangular_probes':3,'pore_count':1}
    s.s['count_constraints']=[{'name':'round_probes','expected':6,'item_ids':['round-'+str(i) for i in range(6)]},{'name':'triangular_probes','expected':3,'item_ids':['triangle-'+str(i) for i in range(3)]}]
    s.s['caption']='DEMO. Shape-based selectivity is stipulated for drawing tests, not inferred from a material or experiment.'
    s.text('title','Selective transfer at a boundary',36,48,26)
    s.text('subtitle','DEMO  /  specified relations, no measured transport',36,78,16)
    final=variant=='D';depth=variant in ('C','D');gx=438 if final else 414;gw=94 if final else 66
    ytop=135;gap0=218;gap1=255;bottom=382
    s.text('feed-name','Feed side',115 if final else 185,122,21)
    s.text('boundary-name','Open pore',gx+gw/2,122,21,align='center')
    s.text('receiver-name','Receiving side',650 if final else 665,122,21,align='center')
    # Chamber walls and one interrupted plate: the objects are spatial geometry, not process cards.
    s.line('top-wall',[[66,145],[820,145]],'#76848C',entity='feed')
    s.line('bottom-wall',[[66,380],[820,380]],'#76848C',entity='receiver')
    for index,(yy,hh) in enumerate([(ytop,gap0-ytop),(gap1,bottom-gap1)]):
        if depth:
            s.add(f'plate-side-{index}','polygon',points=[[gx+gw,yy],[gx+gw+13,yy-9],[gx+gw+13,yy+hh-9],[gx+gw,yy+hh]],fill='@structure.shadow',entity='boundary',role='structure',decorative_depth=True)
            s.add(f'plate-top-{index}','polygon',points=[[gx,yy],[gx+13,yy-9],[gx+gw+13,yy-9],[gx+gw,yy]],fill='@structure.highlight',entity='boundary',role='structure',decorative_depth=True)
        s.add(f'plate-face-{index}','rect',x=gx,y=yy,w=gw,h=hh,fill='@structure.fill',stroke='@structure.stroke',stroke_width=1.7,entity='boundary',role='structure')
    rounds=[(145,236),(216,190),(229,333),(650,237),(719,194),(725,331)] if final else [(150,185),(220,236),(155,333),(664,187),(725,236),(664,330)]
    for i,(x,y) in enumerate(rounds):s.sphere('round-'+str(i),x,y,14,'input','round',depth)
    triangles=[(115,305),(278,287),(354,326)] if final else [(250,184),(247,325),(346,311)]
    for i,(x,y) in enumerate(triangles):
        s.add('triangle-'+str(i),'polygon',points=[[x,y-15],[x-15,y+12],[x+15,y+12]],fill='@blocked.fill',stroke='@blocked.stroke',stroke_width=1.7,entity='triangle',role='blocked')
    s.arrow('pore-flow',[[250,236],[620,236]],'pass','@input.stroke')
    s.arrow('blocked-path',[[365,310],[gx-10,310]],'stop','@blocked.stroke',head='inhibition')
    s.text('flow-label','Pass',575 if final else 564,215,18)
    s.text('stop-label','Blocked',gx-25,353,18,align='right')
    s.sphere('legend-round',85,430,10,'input','round',False)
    s.text('legend-round-label','Round probe',105,436,18)
    s.add('legend-triangle','polygon',points=[[314,418],[302,439],[326,439]],fill='@blocked.fill',stroke='@blocked.stroke',entity='triangle',role='blocked')
    s.text('legend-triangle-label','Triangular probe',342,436,18)
    s.text('footer','Symbol shape and direct labels retain meaning without color.',36,494,16)
    s.s['depth']['mode']='D1_shallow_2_5d' if depth else 'D0'
    s.s['layout']['hierarchy']='enlarged pore and shortened object-to-label travel' if final else 'balanced boundary view'
    if variant=='A':s.s['role_map']={r:{'base':'#CFD5DA'} for r in s.s['role_map']}
    return s

def hardware():
    s=Scene('register_capacity','Three teaching snapshots show occupancy, with fixed capacity of 32 cells.',520)
    s.s['layout']['archetype']='same_capacity_snapshots';s.s['depth']['mode']='D1_shallow_2_5d'
    s.s['role_map']['input']={'swatch':'sky_blue'};s.s['locked_values']={'cells_per_snapshot':32,'occupied':[19,7,28],'groups_final':4,'cells_per_group':7}
    s.text('title','Fixed capacity, changing occupancy',36,46,26)
    s.text('subtitle','DEMO  /  each panel contains exactly 32 register cells',36,77,17)
    xstarts=[88,371,654];counts=[19,7,28];names=['Initial live set','After release','Four groups fit']
    s.s['count_constraints']=[{'name':'snapshot-'+str(k),'expected':32,'item_ids':[f'cell-{k}-{col}-{row}' for col in range(4) for row in range(8)]} for k in range(3)]
    for k,(x,count,name) in enumerate(zip(xstarts,counts,names)):
        ent='snapshot-'+str(k);s.entity(ent,'input',f'32 cells; {count} occupied; illustrative occupancy only')
        s.text('panel-'+str(k),f'{chr(97+k)}  {name}',x-8,125,20)
        # 4 columns × 8 rows, column-major order; final groups have seven live cells each.
        for col in range(4):
            for row in range(8):
                live=(col*8+row<count) if k<2 else row<7
                xx=x+col*38;yy=159+row*25
                s.add(f'cell-{k}-{col}-{row}-side','polygon',points=[[xx+30,yy],[xx+34,yy-3],[xx+34,yy+18],[xx+30,yy+21]],fill='@neutral.shadow',entity=ent,decorative_depth=True)
                s.add(f'cell-{k}-{col}-{row}','rect',x=xx,y=yy,w=30,h=21,fill='@input.fill' if live else WHITE,stroke='@input.stroke' if live else '#78858D',stroke_width=1,entity=ent,role='input' if live else 'neutral',occupied=live,cell_index=col*8+row)
                if not live:s.line(f'empty-{k}-{col}-{row}',[[xx+11,yy+10],[xx+19,yy+10]],'#9EA8AE',entity=ent)
        s.text('count-'+str(k),f'{count} / 32 occupied',x+69,382,22,align='center')
        if k==2:
            for col in range(4):s.text(f'group-{col}',f'G{col+1}',x+col*38+15,148,16,align='center')
    s.relation('release','snapshot-0','snapshot-1','dependency','Illustrative release transition')
    s.relation('pack','snapshot-1','snapshot-2','dependency','Four independent seven-cell groups in fixed capacity')
    s.arrow('release-arrow',[[267,245],[338,245]],'release');s.arrow('pack-arrow',[[551,245],[620,245]],'pack')
    s.text('group-equation','4 groups × 7 cells = 28 cells; 4 cells remain free.',36,446,20)
    s.text('footer','Capacity illustration only. No 4× speedup or measured runtime is implied.',36,484,16)
    s.s['caption']='DEMO: 19 → 7 → 28 are occupied cell counts, not performance. Fourfold group capacity is conditional on seven cells per group and no additional reserved cells.'
    return s

def material():
    s=Scene('coated_particles','A constructed layered composite shows coated cores on a substrate and a section of one core.',560)
    s.s['reference_palette']='yellow_blue_sage'
    s.s['role_map']={'core':{'swatch':'yellow'},'coating':{'swatch':'blue'},'base':{'swatch':'sage'},'support':{'swatch':'lilac'},'neutral':{'base':'#D8DFE3'}}
    s.s['layout']['archetype']='cutaway_with_detail';s.s['depth']['mode']='D1_vector_2_5d_not_3D_scene'
    s.s['locked_values']={'cores_in_overview':6,'detail_views':1,'layers':2}
    s.s['count_constraints']=[{'name':'overview_cores','expected':6,'item_ids':['core-'+str(i) for i in range(6)]}]
    for id,role,desc in [('substrate','base','Lower structural slab'),('layer','support','Upper support layer'),('coating','coating','Blue shells around each core'),('core','core','Six yellow cores; right section is a repeated view of a core')]:s.entity(id,role,desc)
    s.relation('shell-contains','coating','core','containment','Shell surrounds core; no mechanistic efficacy claimed')
    s.relation('zoom','core','core','detail','Right cross-section repeats the front-right particle')
    s.text('title','Coating, core and supporting layers',36,47,26)
    s.text('subtitle','DEMO  /  vector 2.5D schematic, not to scale',36,78,17)
    # Parallel projection: rear objects first, front objects later; consistent down-right depth.
    s.add('substrate-front','polygon',points=[[60,340],[366,340],[366,372],[60,372]],fill='@base.shadow',stroke='@base.stroke',entity='substrate',role='base')
    s.add('substrate-side','polygon',points=[[366,340],[491,250],[491,282],[366,372]],fill='@base.fill',stroke='@base.stroke',entity='substrate',role='base')
    s.add('substrate-top','polygon',points=[[60,340],[185,250],[491,250],[366,340]],fill='@base.highlight',stroke='@base.stroke',entity='substrate',role='base')
    s.add('support-front','polygon',points=[[60,322],[366,322],[366,340],[60,340]],fill='@support.shadow',stroke='@support.stroke',entity='layer',role='support')
    s.add('support-side','polygon',points=[[366,322],[491,232],[491,250],[366,340]],fill='@support.fill',stroke='@support.stroke',entity='layer',role='support')
    s.add('support-top','polygon',points=[[60,322],[185,232],[491,232],[366,322]],fill='@support.highlight',stroke='@support.stroke',entity='layer',role='support')
    positions=[(219,225),(299,225),(379,225),(148,285),(228,285),(308,285)]
    for i,(x,y) in enumerate(positions):
        s.sphere('shell-'+str(i),x,y-29,36,'coating','coating',True)
        # Exposed front core section is a schematic cut, not a literal transparency.
        s.sphere('core-'+str(i),x+1,y-24,25,'core','core',True)
    s.text('overview-label','Layered composite',86,144,20)
    s.line('zoom-leader',[[345,270],[503,195],[574,195]],'#65747F',relation='zoom',dash=[5,4])
    s.text('section-title','Local section',638,145,20,align='center')
    s.add('section-shell','circle',x=659,y=262,r=76,fill='@coating.fill',stroke='@coating.stroke',stroke_width=2,entity='coating',role='coating')
    s.add('section-core','circle',x=659,y=262,r=55,fill='@core.fill',stroke='@core.stroke',stroke_width=1.5,entity='core',role='core')
    s.text('core-label','Core',659,268,19,align='center',background='@core.fill')
    s.line('coating-leader',[[723,225],[761,203]],'#536571',entity='coating')
    s.text('coating-label','Coating',758,188,19,align='center')
    s.line('layer-leader',[[224,331],[224,402]],'#536571',entity='layer')
    s.text('layer-label','Support layer',224,429,18,align='center')
    s.line('substrate-leader',[[85,359],[69,444]],'#536571',entity='substrate')
    s.text('substrate-label','Substrate',79,469,18,align='center')
    s.text('shell-note','Section repeats one particle;',560,388,17)
    s.text('shell-note-2','it is not an additional core.',560,411,17)
    s.text('footer','Six cores in the overview. Depth explains layers; it does not encode measured values.',36,528,16)
    s.s['caption']='Original DEMO: six coated cores over two slabs, with a repeated local section. Core cut faces are exposed schematically. No microscopy, transport physics, 3D mesh or calibrated size is claimed.'
    return s

def quantitative(data_path):
    rows=list(csv.DictReader(data_path.open(encoding='utf-8',newline='')))
    if not rows or len(rows)>12:raise ValueError('This paired-time builder supports 1..12 rows; adapt layout for more')
    seen=set();data=[]
    for r in rows:
        if r['case'] in seen:raise ValueError('Duplicate case; define replicate structure rather than silently aggregate')
        seen.add(r['case']);control=float(r['control_ms']);candidate=float(r['candidate_ms'])
        if not all(math.isfinite(v) and v>0 for v in (control,candidate)):raise ValueError('Positive finite times required; zero denominators/missing rows need an explicit alternate design')
        data.append({'case':r['case'],'control_ms':control,'candidate_ms':candidate,'ratio':control/candidate,'change_percent':100*(candidate/control-1)})
    s=Scene('paired_times','Paired DEMO times retain an improvement, a tie and a regression.',440+max(0,len(rows)-3)*85)
    s.s['mode']='quantitative';s.s['data']=data;s.s['data_source']=data_path.name;s.s['data_sha256']=hashlib.sha256(data_path.read_bytes()).hexdigest()
    s.s['layout']['archetype']='paired_position_plot';s.s['locked_values']={'rows':len(data),'time_unit':'ms','ratio':'control / candidate','uncertainty':'none; no replicate records'}
    s.text('title','All outcomes remain visible',36,46,26)
    s.text('subtitle','DEMO  /  paired illustrative times; no uncertainty estimates',36,77,17)
    s.entity('control','input','Control time, circular symbol');s.entity('candidate','blocked','Candidate time, diamond symbol')
    s.sphere('legend-control',520,111,6,'input','control',False);s.text('control-key','Control',536,117,16)
    s.add('legend-candidate','polygon',points=[[687,103],[695,111],[687,119],[679,111]],fill='@blocked.fill',stroke='@blocked.stroke',entity='candidate');s.text('candidate-key','Candidate',706,117,16)
    xmax=math.ceil(max(max(r['control_ms'],r['candidate_ms']) for r in data)/4)*4+4
    x=lambda v:156+v/xmax*486
    for tick in range(0,xmax+1,4):
        s.line('grid-'+str(tick),[[x(tick),145],[x(tick),145+85*len(rows)]],'#DCE2E6')
        s.text('tick-'+str(tick),str(tick),x(tick),170+85*len(rows),16,align='center')
    s.text('effect-heading','Time change',730,143,16,align='center')
    for i,r in enumerate(data):
        y=188+i*85;c=r['control_ms'];q=r['candidate_ms'];case=r['case']
        s.text('case-'+str(i),case,80,y+6,20,align='center')
        s.line('pair-'+str(i),[[x(c),y],[x(q),y]],'#73838F')
        s.add('control-'+str(i),'circle',x=x(c),y=y,r=7,fill='@input.fill',stroke='@input.stroke',stroke_width=2,entity='control',role='input',data_value=c,data_case=case)
        s.add('candidate-'+str(i),'polygon',points=[[x(q),y-9],[x(q)+9,y],[x(q),y+9],[x(q)-9,y]],fill='@blocked.fill',stroke='@blocked.stroke',stroke_width=2,entity='candidate',role='blocked',data_value=q,data_case=case)
        # When equal, place one mark above and below a shared x position, with a short paired segment.
        if c==q:
            s.s['items'][-2]['y']=y-7;s.s['items'][-1]['points']=[[a,b+8] for a,b in s.s['items'][-1]['points']]
        s.text('control-value-'+str(i),f'{c:g}',x(c),y-22,16,align='center')
        s.text('candidate-value-'+str(i),f'{q:g}',x(q),y+35,16,align='center')
        change=r['change_percent'];label=f'{change:+.0f}%' if abs(change)>1e-8 else '0%'
        s.text('change-'+str(i),label,730,y+6,21,align='center')
    bottom=145+85*len(rows)
    s.text('x-axis','Time (ms) — lower is faster',393,bottom+57,18,align='center')
    s.text('footer','DEMO values only. Both methods and all cases are retained.',36,s.s['output']['view_height']-17,16)
    # Ensure sufficient height for the x-axis and footer even on the smallest dataset.
    new_h=max(s.s['output']['view_height'],bottom+115);s.s['output']['view_height']=new_h;s.s['items'][0]['h']=new_h;s.s['items'][-1]['y']=new_h-18
    s.s['caption']='DEMO: supplied single illustrative values, not empirical measurements or replicate statistics. Relative changes use (candidate / control − 1) × 100. There are no fabricated error bars. Equal times use a small vertical separation at the same x value; vertical position does not encode time.'
    # Palette keys name scientific roles, independent of whether a value improves or regresses.
    rename={'input':'control','blocked':'candidate'}
    s.s['role_map']={rename.get(k,k):v for k,v in s.s['role_map'].items()}
    for e in s.s['entities']:e['semantic_role']=rename.get(e['semantic_role'],e['semantic_role'])
    for item in s.s['items']:
        if item.get('role') in rename:item['role']=rename[item['role']]
        for field in ('fill','stroke'):
            if field in item:
                for old,new in rename.items():item[field]=item[field].replace('@'+old+'.','@'+new+'.')
    return s

def labels(loaded,crowded=False):
    s=Scene('labels_'+('crowded' if crowded else 'repaired'),'A Chinese-label stress test preserves two near-color roles with redundant symbols.',470)
    s.s['reference_palette']='aqua_lilac_peach';s.s['role_map']={'round':{'base':'#C4D8EA'},'square':{'base':'#CED6EC'},'neutral':{'base':'#D8DFE3'}}
    s.entity('kept','round','Retained old input, circle');s.entity('updated','square','Updated value, square')
    s.relation('dependency','kept','updated','dependency','Old input is retained until dependent update completes')
    s.text('title','长标签与近色对象：保持非颜色线索',36,47,25)
    s.text('subtitle','DEMO  /  中文、英文与上下标；字号不随拥挤缩小',36,82,17)
    s.sphere('kept-symbol',170,190,45,'round','kept',False)
    s.add('updated-symbol','rect',x=571,y=145,w=90,h=90,fill='@square.fill',stroke='@square.stroke',stroke_width=2,entity='updated',role='square')
    s.arrow('dependency-arrow',[[235,190],[540,190]],'dependency')
    left='保留旧输入，直到所有依赖它的局部更新完成后再执行写回'
    right='新值写回对应位置，同时保留其他尚未完成更新所需的数据'
    for id,text,x in [('label-left',left,170),('label-right',right,616)]:
        rendered=text if crowded else wrap_text(text,305,20,loaded)
        s.text(id,rendered,x,280,20,align='center',max_width=305,leading=29)
    s.text('math-left','旧输入  x₀, x₁',170,387,19,align='center')
    s.text('math-right','新值  y₂  /  V²',616,387,19,align='center')
    s.text('footer','形状 + 文字区分角色；浅色只用于填充，文字保持深色。',36,441,17)
    s.s['caption']='DEMO only. Repaired version wraps at measured glyph widths without reducing the 20-unit label size. Circle/square and direct labels remain usable in grayscale.'
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--cjk-font',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('Examples destination must be new')
    loaded=fonts(a.font,a.cjk_font);a.out.mkdir(parents=True)
    for v in 'ABCD':mechanism(v).finish(a.out/'mechanism'/f'{v}.json')
    theme={'reference_palette':'blue_teal_peach','role_map':{'input':{'swatch':'sky_blue'},'blocked':{'swatch':'peach'},'structure':{'swatch':'deep_blue'},'neutral':{'base':'#D8DFE3'}}}
    (a.out/'mechanism/I4-theme.json').write_text(json.dumps(theme,indent=2),encoding='utf-8')
    hardware().finish(a.out/'hardware/registers.json');material().finish(a.out/'material/section.json')
    qdir=a.out/'quantitative';qdir.mkdir()
    data_path=qdir/'DEMO_times.csv';data_path.write_text('case,control_ms,candidate_ms\nA,10,8\nB,10,10\nC,10,12\n',encoding='utf-8')
    quantitative(data_path).finish(qdir/'paired.json')
    labels(loaded,True).finish(a.out/'labels/crowded.json');labels(loaded,False).finish(a.out/'labels/repaired.json')
    print('Created nine original scene specs, one recolor theme and one DEMO CSV.')
if __name__=='__main__':main()
