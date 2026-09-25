"""Bounded comparison tests: a label/color edit must not masquerade as new geometry."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cmp',ROOT/'scripts/compare_designs.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
BASE='<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="80mm" viewBox="0 0 400 200"><rect x="20" y="50" width="80" height="50" fill="#FF0000"/><text x="30" y="80" font-size="20">Input</text></svg>'
def run(out):
 out.mkdir(parents=True,exist_ok=False);results=[]
 def artifact(name,text):p=out/(name+'.svg');p.write_text(text,encoding='utf-8');return p
 before=artifact('before',BASE)
 def case(name,fn):
  try:fn();results.append({'case':name,'status':'PASS'})
  except Exception as e:results.append({'case':name,'status':'FAIL','error':repr(e)})
 def expect(s,category):
  p=artifact(category+str(len(results)),s);r=C.compare(C.inspect(before),C.inspect(p));assert r['classification']==category;assert r['effectiveness']=='REVIEW_REQUIRED'
 case('identical_is_not_improvement',lambda:expect(BASE,'IDENTICAL_BYTES'))
 case('label_only_not_new_layout',lambda:expect(BASE.replace('Input','Updated explanation'),'LABEL_STYLE_OR_METADATA_ONLY'))
 case('recolor_only_not_new_layout',lambda:expect(BASE.replace('#FF0000','#0000FF'),'LABEL_STYLE_OR_METADATA_ONLY'))
 case('text_move_separate_from_object_layout',lambda:expect(BASE.replace('x="30"','x="120"'),'TEXT_PLACEMENT_CHANGED'))
 case('object_relocation_still_requires_effect_review',lambda:expect(BASE.replace('x="20"','x="180"'),'OBJECT_GEOMETRY_CHANGED'))
 def missing():
  try:C.run(before,[out/'absent.svg'],out/'missing-result')
  except FileNotFoundError:assert not (out/'missing-result').exists();return
  raise AssertionError('Missing candidate accepted')
 case('missing_candidate_no_false_gallery',missing)
 def reject_existing():
  target=out/'existing';target.mkdir();(target/'keep.txt').write_text('retain')
  try:C.run(before,[before],target)
  except FileExistsError:assert (target/'keep.txt').read_text()=='retain';return
  raise AssertionError('Output overwritten')
 case('existing_output_protected',reject_existing)
 def gallery():
  dest=out/'gallery';r=C.run(before,[before],dest)
  assert (dest/'comparison.html').is_file() and 'data:image/svg+xml;base64,' in (dest/'comparison.html').read_text()
  assert r['status']=='COMPARISON_CREATED_REVIEW_REQUIRED'
 case('actual_portable_gallery_not_quality_pass',gallery)
 def pair(name,a,b,category):
  r=C.compare(C.inspect(artifact(name+'-before',a)),C.inspect(artifact(name+'-after',b)))
  assert r['classification']==category,r
  assert r['scientific_review']==r['effectiveness']=='REVIEW_REQUIRED'
  return r
 line='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><line x1="10" y1="10" x2="90" y2="10" stroke="black"/></svg>'
 case('line_horizontal_to_vertical',lambda:pair('line-turn',line,line.replace('x2="90" y2="10"','x2="10" y2="90"'),'OBJECT_GEOMETRY_CHANGED'))
 case('line_start_moved',lambda:pair('line-start',line,line.replace('x1="10"','x1="30"'),'OBJECT_GEOMETRY_CHANGED'))
 case('line_end_reversed',lambda:pair('line-reverse',line,line.replace('x1="10"','x1="90"').replace('x2="90"','x2="10"'),'OBJECT_GEOMETRY_CHANGED'))
 case('line_recolor_stays_style',lambda:pair('line-color',line,line.replace('black','blue'),'LABEL_STYLE_OR_METADATA_ONLY'))
 grouped=line.replace('<line','<g transform="translate(0 0)"><line').replace('</svg>','</g></svg>')
 case('line_ancestor_transform',lambda:pair('line-transform',grouped,grouped.replace('translate(0 0)','translate(10 20)'),'OBJECT_GEOMETRY_CHANGED'))
 case('physical_output_size_reported',lambda:expect(BASE.replace('160mm','80mm'),'OUTPUT_SIZE_CHANGED'))
 use='<svg xmlns="http://www.w3.org/2000/svg"><use href="#a" x="10"/></svg>'
 def partial():
  r=pair('use',use,use.replace('x="10"','x="30"'),'UNCLASSIFIED_RENDER_CHANGE')
  assert r['geometry_coverage']=='PARTIAL' and 'use' in r['uninspected_features']
 case('unsupported_use_not_false_style_only',partial)
 styled=BASE.replace('fill="#FF0000"','style="fill:red;x:20px"')
 case('css_geometry_change_pending',lambda:pair('css',styled,styled.replace('x:20px','x:90px'),'UNCLASSIFIED_RENDER_CHANGE'))
 def bad_xml():
  p=artifact('malformed','<svg>');target=out/'malformed-gallery'
  p1=subprocess.run([sys.executable,str(ROOT/'scripts/compare_designs.py'),'--baseline',str(before),'--candidate',str(p),'--out',str(target)],capture_output=True,text=True)
  assert p1.returncode!=0 and not target.exists()
 case('malformed_cli_nonzero_without_output',bad_xml)
 def real_cli():
  a=artifact('cli-line-before',line);b=artifact('cli-line-after',line.replace('x2="90" y2="10"','x2="10" y2="90"'));target=out/'cli-gallery'
  p1=subprocess.run([sys.executable,str(ROOT/'scripts/compare_designs.py'),'--baseline',str(a),'--candidate',str(b),'--out',str(target)],capture_output=True,text=True)
  assert p1.returncode==0,(p1.stdout,p1.stderr)
  r=json.loads((target/'comparison.json').read_text(encoding='utf-8'))
  assert r['candidates'][0]['comparison']['object_geometry_changed'] and (target/'comparison.html').is_file()
 case('actual_cli_reports_line_change',real_cli)
 result={'passed':sum(r['status']=='PASS' for r in results),'total':len(results),'results':results}
 (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));return result['passed']==result['total']
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();raise SystemExit(0 if run(a.out) else 1)
