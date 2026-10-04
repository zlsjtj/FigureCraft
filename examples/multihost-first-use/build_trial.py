"""从公开的 T5 教学材料生成同一记录、两个独立输出的示意；不是测量图。"""
from pathlib import Path
import argparse
import hashlib
import json
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skill', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('输出必须是新目录。')
    sys.path.insert(0, str(args.skill.resolve() / 'scripts'))
    from make_examples import Scene
    from relation_components import relation_path
    s = Scene('paired_translation_first_use', 'A and B read one immutable placement record and are resampled into separate mosaics.', height=500)
    s.s['output'].update(width_mm=160, view_width=800, view_height=500, placement_width_mm=160)
    s.s['items'][0].update(w=800, h=500)
    s.s['layout'].update(archetype='paired_object_rows_shared_record', reading_order='left-to-right within each channel; central record serves both')
    s.s['role_map']={'A':{'base':'#286383'},'B':{'base':'#975426'},'record':{'base':'#596C78'},'neutral':{'base':'#CED7DE'}}
    s.s['depth']['mode']='D0'
    for entity,role,desc in [('tileA','A','T5 channel A acquired plane'),('tileB','B','T5 channel B acquired plane'),('outputA','A','Independent A mosaic; one representative T5 placement'),('outputB','B','Independent B mosaic; same T5 placement'),('mapA','neutral','Resampling operation for channel A'),('mapB','neutral','Resampling operation for channel B'),('record','record','One immutable translation selected for T5')]:
        s.entity(entity,role,desc)
    s.text('heading','One placement, two mosaics',34,39,24)
    s.text('demo','CONSTRUCTED DEMO',766,38,15,align='right',fill='#596771')
    s.text('left-head','Paired input planes',85,79,19)
    s.text('right-head','Separate output mosaics',495,79,19)
    # Frames are local coordinate views, not instruments or adjacent physical cameras.
    for k,(ch,y,color,fill) in enumerate([('A',112,'#286383','#E8F2F7'),('B',320,'#975426','#FCF1E8')]):
        inp='tile'+ch; dst='output'+ch; op='map'+ch
        s.text(ch+'-label',ch,40,y+48,22,fill=color)
        s.add(ch+'-plane','rect',x=88,y=y,w=96,h=96,fill=fill,stroke=color,stroke_width=1.8,entity=inp,role=ch)
        s.text(ch+'-id','T5',168,y+82,16,align='right',fill=color,background=fill,entity=inp)
        s.add(ch+'-fiducial','circle',x=98,y=y+18,r=3.8,fill=color,background=fill,entity=inp)
        s.add(ch+'-frame','rect',x=498,y=y-3,w=238,h=116,fill='#FBFCFD',stroke='#B9C7D0',stroke_width=1.3,entity=dst)
        # Given example: translation (84,3), same unit scale in both coordinate views.
        ox,oy=498+84,y-3+3
        s.add(ch+'-placed','rect',x=ox,y=oy,w=96,h=96,fill=fill,stroke=color,stroke_width=1.8,entity=dst,role=ch)
        s.text(ch+'-placed-id','T5',ox+80,oy+82,16,align='right',fill=color,background=fill,entity=dst)
        s.add(ch+'-placed-fiducial','circle',x=ox+10,y=oy+18,r=3.8,fill=color,background=fill,entity=dst)
        relation=relation_path(ch+'-mapping',semantics='value_mapping',points=[[203,y+48],[472,y+48]],source_entity=inp,target_entity=dst,meaning='Apply the shared translation during separate resampling; no physical motion',color=color,width=1.7,head=8)
        s.s['items']+=relation['items'];s.s['relations']+=relation['relations']
        s.text(ch+'-resample','Resample '+ch,344,y+(31 if ch=='A' else 78),18,align='center',fill=color,entity=op)
        s.add(ch+'-operation-point','circle',x=344,y=y+48,r=3.5,fill=color,entity=op)
    # Short undirected links terminate on the operation, not on the image contents.
    s.add('record-face','rect',x=258,y=230,w=172,h=64,radius=5,fill='#EDF2F5',stroke='#6D8290',stroke_width=1.4,entity='record')
    s.text('record-title','T5 placement',344,254,18,align='center',entity='record')
    s.text('record-value','(84, 3) px',344,279,20,align='center',entity='record')
    for label,points,target in [('A',[[344,230],[344,160]],'mapA'),('B',[[344,294],[344,368]],'mapB')]:
        relation=relation_path('shared-'+label,semantics='common_reference',points=points,source_entity='record',target_entity=target,meaning='This resampling operation reads the same immutable T5 record',color='#778B99',width=1.6)
        # Draw links behind the labels and colored operation markers.
        s.s['items'][1:1]=relation['items'];s.s['relations']+=relation['relations']
    s.text('source-size','96 × 96 px per plane',88,449,17,fill='#596771')
    s.text('shared-note','Shared record; separate resampling',498,449,17,fill='#596771')
    s.s['locked_values']={'tile_id':'T5','plane_size_px':[96,96],'translation_px':[84,3], 'input_fiducial':[10,18],'output_fiducial':[94,21],'score_gate':0.8}
    s.s['forbidden_implications']=['No claim of identical channel intensity or measured specimen appearance','No rotation correction','No correction of residual channel-specific shifts','Shared placement need not be globally correct','Mosaic frames are coordinate views, not physical positions']
    s.s['source_refs']=[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(args.input.iterdir()) if p.is_file()]
    s.s['caption']='CONSTRUCTED DEMO. One T5 example is shown in two coordinate views. A selected translation of (84, 3) pixels is read by both channel resamplers (plain links); arrows denote application of that mapping, not physical motion. A local fiducial at (10, 18) maps to (94, 21) in each output. The planes have different stain intensities; only a representative paired fiducial is drawn. The record comes from A registration if its fixed score is at least 0.8, otherwise from stage metadata; B is not independently registered after fallback. Separate resampling also transforms the masks. Common placement does not correct residual channel-specific shifts or guarantee correct global placement. Frames show coordinate extents for this illustration, not a measured full mosaic boundary.'
    args.out.mkdir(parents=True)
    s.finish(args.out/'figure_spec.json')
    (args.out/'caption.txt').write_text(s.s['caption']+'\n',encoding='utf-8')
    (args.out/'design.md').write_text('图把同一记录放在两路重采样之间，以无箭头短线说明共同读取；横向箭头只表示坐标映射。两幅输出保留同一局部标记，避免把不同通道画成相同强度图像。采纳材料允许的 T5 例子，不显示实验结果表。该任务已知且由维护模型执行，不能作为独立迁移测试。\n',encoding='utf-8')


if __name__=='__main__':
    main()
