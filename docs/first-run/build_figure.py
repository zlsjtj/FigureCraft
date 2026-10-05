"""公开首次使用材料的本次新构图；需要 FigureCraft 的已发布脚本。"""
import argparse, hashlib, json, pathlib, sys
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--skill',type=pathlib.Path,required=True)
    p.add_argument('--input',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args()
    if a.out.exists(): raise ValueError('Output must be new')
    sys.path.insert(0,str(a.skill/'scripts'))
    from relation_components import relation_branch,relation_path
    ink='#263D49'; grey='#5A6D76'; teal='#087E8B'; coral='#BD493D'
    s={'schema_version':1,'figure_id':'first_use_shared_placement','mode':'new_schematic','demo':True,
       'scientific_message':'The two planes of a tile read one selected translation record and are resampled into separate mosaics.',
       'evidence_status':'constructed_teaching_material_not_research',
       'source_refs':[{'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(a.input.iterdir())],
       'forbidden_implications':['A and B are not the same stain intensity map.','Shared placement does not correct residual optical shift or erroneous stage coordinates.','Canvas extents and marker appearance are schematic; no measured imaging texture is shown.'],
       'entities':[],'relations':[],'exact_labels':[],
       'locked_values':{'tile_id':'T5','selected_translation_px':[84,3],'tile_side_px':96,'illustrative_fiducial_local_px':[10,18],'illustrative_fiducial_output_px':[94,21],'score_gate':0.8},
       'reference_palette':'blue_gold_coral','role_map':{'channel_A':{'base':teal},'channel_B':{'base':coral},'shared_record':{'base':'#A47921'}},
       'layout':{'archetype':'shared_record_and_paired_images','reading_order':'record then paired rows then outputs'},
       'depth':{'mode':'D0','affects_quantitative_encoding':False},
       'edit_scope':{'allowed':['new schematic'],'protected':['scientific content']},
       'publication':{'target_journal':None,'eligibility':'unverified'},
       'output':{'width_mm':160,'placement_width_mm':160,'view_width':800,'view_height':500,'font_profile':'explicit_Arial'},'items':[]}
    def item(id,type,**kw): s['items'].append(dict(id=id,type=type,**kw))
    def text(id,t,x,y,size=19,**kw): item(id,'text',text=t,x=x,y=y,size=size,fill=ink,**kw)
    def rect(id,x,y,w,h,fill,stroke=ink,**kw): item(id,'rect',x=x,y=y,w=w,h=h,fill=fill,stroke=stroke,stroke_width=1.5,**kw)
    def line(id,pts,color=ink,**kw): item(id,'line',points=pts,stroke=color,stroke_width=1.6,**kw)
    for id,role,desc in [('record','shared_record','One immutable selected translation for tile T5'),('A','channel_A','Acquired plane A'),('B','channel_B','Acquired plane B'),('outA','channel_A','A resampled into output mosaic A'),('outB','channel_B','B resampled into output mosaic B')]:
        s['entities'].append({'id':id,'semantic_role':role,'description':desc})
    rect('canvas',0,0,800,500,'#FFFFFF','#FFFFFF')
    text('title','One placement, two channels',26,37,26)
    item('demo','text',text='DEMO',x=774,y=37,size=16,align='right',fill=grey)
    text('record-head','One record',26,97,21)
    text('pair-head','Tile T5',379,97,21,align='center')
    text('outputs-head','Two mosaics',658,97,21,align='center')
    # File-shaped record is one data object, not a physical component.
    item('record-shape','polygon',points=[[26,220],[189,220],[211,242],[211,294],[26,294]],fill='#FCF4DF',stroke='#987128',stroke_width=1.5,entity='record',role='shared_record')
    line('record-fold',[[189,220],[189,242],[211,242]],'#987128',entity='record')
    text('record-id','T5',43,246,20,entity='record')
    text('delta','Δ = (84, 3) px',43,276,20,entity='record')
    text('selection','From A, else stage',26,207,17)
    # Reference is undirected. Image resampling has a separate directed edge.
    shared=relation_branch('shared',semantics='common_reference',source=[211,258],targets=[[327,181],[327,375]],junction_x=282,source_entity='record',target_entities=['A','B'],meaning='Both planes look up the same immutable tile record',color='#987128',width=1.8)
    s['items']+=shared['items'];s['relations']+=shared['relations']
    for channel,color,y in [('A',teal,137),('B',coral,331)]:
        pale='#E8F3F3' if channel=='A' else '#FAEEEB'
        text(channel+'-name',channel,335,y-12,21,entity=channel)
        rect(channel+'-tile',335,y,88,88,pale,color,entity=channel,role='channel_'+channel)
        # A cross is an illustrative known paired fiducial, not invented stain texture.
        fx=335+10*88/96;fy=y+18*88/96
        line(channel+'-cross-h',[[fx-4,fy],[fx+4,fy]],color,entity=channel)
        line(channel+'-cross-v',[[fx,fy-4],[fx,fy+4]],color,entity=channel)
        text(channel+'-out-name',channel+' mosaic',550,y-12,21,entity='out'+channel)
        rect(channel+'-canvas',550,y,216,118,'#FFFFFF','#AAB7BD',entity='out'+channel)
        # The same diagram scale is used for input tile and placed tile.
        tx=550+84*88/96;ty=y+3*88/96
        rect(channel+'-placed-tile',tx,ty,88,88,pale,color,entity='out'+channel,role='channel_'+channel)
        ox=tx+10*88/96;oy=ty+18*88/96
        line(channel+'-out-cross-h',[[ox-4,oy],[ox+4,oy]],color,entity='out'+channel)
        line(channel+'-out-cross-v',[[ox,oy-4],[ox,oy+4]],color,entity='out'+channel)
        s['locked_values'][channel+'_geometry']={'input_origin':[335,y],'output_origin':[550,y],'scale':88/96,'placed_tile_origin':[tx,ty],'fiducial':[ox,oy]}
        rel=relation_path('resample-'+channel,semantics='data_flow',points=[[434,y+44],[536,y+44]],source_entity=channel,target_entity='out'+channel,meaning='Separate bilinear resampling into this channel mosaic',color=color,width=2,head=8)
        s['items']+=rel['items'];s['relations']+=rel['relations']
    text('size','96 × 96 px each',379,461,17,align='center')
    text('flow-label','Separate resampling',658,480,18,align='center')
    caption=('DEMO. MosaicPair selects one translation for each tile from channel A when the inherited quality score is at least 0.8; otherwise it uses the stage-grid translation. '
             'The undirected branches denote common lookup of the immutable T5 record, while arrows denote separate resampling of A and B into their respective mosaics. '
             'The example uses Δ = (84, 3) pixels: the marked local fiducial (10, 18) appears at (94, 21) in both output coordinate systems. '
             'Image fields are schematic crops; crosses denote paired fiducials, not stain intensity. Masks use the same record, and export refuses missing pairs. '
             'Shared placement cannot correct a residual channel-specific shift or an incorrect stage location.')
    s['caption']=caption;s['alt_text']='One translation record at left connects without arrowheads to a pair of image planes. Separate arrows place each plane in its own mosaic using the same displacement.'
    s['exact_labels']=[i['text'] for i in s['items'] if i['type']=='text']
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    a.out.with_suffix('.caption.txt').write_text(caption,encoding='utf-8')
if __name__=='__main__': main()
