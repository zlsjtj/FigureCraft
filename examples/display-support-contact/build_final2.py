"""Annotation ownership repair only: section direction vs disengagement."""
from pathlib import Path
import argparse,csv,json,shutil,sys
import build_candidates as b
import build_final as f
import native_geometry as g

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--bold-font',type=Path,required=True);ap.add_argument('--pdftoppm',type=Path,required=True);a=ap.parse_args()
    root=Path(__file__).parent;prior=root/'selected'/'candidate-A-final'
    rows=list(csv.DictReader((root/'source-input'/'finite-record.csv').open(encoding='utf-8')))
    sc=f.final_scene(rows)
    for it in sc.items:
        if it.get('s')=='A · S2 section':it['s']='A · S2 section · view +y'
        if it['role']=='final-section-view-direction':
            it.update(s='Lift out',x=133,y=19,anchor='start',role='final2-local-release-label',id='final2-local-release-label')
    checks=b.export(sc,a.out,a)
    old=json.loads((prior/'scene.json').read_text());new=json.loads(json.dumps(sc.items))
    assert [z for z in old if z['kind']!='text']==[z for z in new if z['kind']!='text'],'Non-text geometry changed'
    text_changes=[{'before':x,'after':y} for x,y in zip(old,new) if x!=y]
    assert len(text_changes)==2 and all(z['before']['kind']=='text' for z in text_changes)
    for n in ('caption.md','alt.txt','finite-record.csv'):
        shutil.copy2(prior/n,a.out/n)
    caption=(a.out/'caption.md').read_text(encoding='utf-8').replace('**A · S2 section**','**A · S2 section · view +y**').replace('The orange upward arrow indicates local disengagement only','The orange upward arrow labelled **Lift out** indicates local disengagement only')
    caption+='\n标注归属修复：观察方向 `view +y` 归入截面标题；橙色箭头旁单独写 `Lift out`，避免把向上的抬离箭头误当成观察方向。\n'
    (a.out/'caption.md').write_text(caption,encoding='utf-8')
    alt=(a.out/'alt.txt').read_text(encoding='utf-8').replace('A · S2 section and View +y identify the local view.','The title A · S2 section · view +y identifies the local view and its observation direction.').replace('An orange upward arrow denotes local disengagement.','An orange upward arrow explicitly labelled Lift out denotes local disengagement.')
    (a.out/'alt.txt').write_text(alt,encoding='utf-8')
    spec=json.loads((prior/'figure_spec.json').read_text());spec['selected']='selected/candidate-A-final2';spec['parent_candidate']='selected/candidate-A-final';spec['revision_type']='annotation_ownership_repair_only';spec['local_view']['in_figure_identity']='A · S2 section · view +y title; main short trace A +y';spec['motion_arrow']='Orange upward arrow explicitly labelled Lift out; qualitative local disengagement only';spec['selected_sha256']={n:g.sha(a.out/n) for n in ['figure.svg','figure.pdf','figure.png','caption.md','alt.txt','finite-record.csv']}
    (a.out/'figure_spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    inherited=json.loads((prior/'validation.json').read_text())
    record={'kind':'annotation_ownership_repair_only','command':sys.argv,'prior_svg_sha256':g.sha(prior/'figure.svg'),'all_non_text_scene_items_equal':True,'exactly_two_text_items_changed':text_changes,'physical_mm':checks['physical_mm'],'min_font_pt':checks['minimum_font_pt'],'text_out_of_bounds':checks['text_out_of_bounds'],'scientific_checks':'Unchanged geometry and byte-identical CSV retain the prior geometry checks; no new science claim','csv_byte_equal':g.sha(prior/'finite-record.csv')==g.sha(a.out/'finite-record.csv'),'retained_five_probes':inherited['all_five_probes_match'],'retained_four_state_checks':inherited['all_four_states_pass'],'source_sha256':{p.name:g.sha(p) for p in [Path(__file__),root/'build_final.py',root/'build_candidates.py',root/'native_geometry.py']},'independent_review':'NOT_RUN','author_acceptance':False,'overall_status':'REVIEW_REQUIRED'}
    (a.out/'validation.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps({k:record[k] for k in ['all_non_text_scene_items_equal','physical_mm','min_font_pt','text_out_of_bounds','csv_byte_equal']}))
if __name__=='__main__':main()
