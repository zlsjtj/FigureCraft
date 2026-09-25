"""Bounded comparison tests: a label/color edit must not masquerade as new geometry."""
from pathlib import Path
import argparse,importlib.util,json,math,subprocess,sys
from html.parser import HTMLParser
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
  assert r['display']['mode']=='RESPONSIVE_LEGACY' and 'sizing' not in r['baseline']
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
 def fixed_width_cli():
  # The second source has half the physical width and twice the viewBox width.
  # At equal placement width its height and effective font scale must follow
  # its own viewBox, not the first source or a responsive card width.
  altered=BASE.replace('width="160mm" height="80mm" viewBox="0 0 400 200"','width="80mm" height="60mm" viewBox="0 0 800 600"')
  candidate=artifact('different-size',altered);target=out/'fixed-width-gallery'
  p1=subprocess.run([sys.executable,str(ROOT/'scripts/compare_designs.py'),'--baseline',str(before),'--candidate',str(candidate),'--placement-width-mm','160','--out',str(target)],capture_output=True,text=True)
  assert p1.returncode==0,(p1.stdout,p1.stderr)
  r=json.loads((target/'comparison.json').read_text(encoding='utf-8'));a=r['baseline']['sizing'];b=r['candidates'][0]['artifact']['sizing']
  assert r['display']['mode']=='UNIFORM_CSS_MM_WIDTH' and not r['display']['physical_ruler_verified']
  assert a['placement']['width_mm']==b['placement']['width_mm']==160
  assert a['placement']['height_mm']==80 and b['placement']['height_mm']==120
  assert a['placement']['width_scale_from_declared_source']==1 and b['placement']['width_scale_from_declared_source']==2
  assert math.isclose(a['font_scaling']['minimum_known_font_pt'],20*160/400*72/25.4)
  assert math.isclose(b['font_scaling']['minimum_known_font_pt'],20*160/800*72/25.4)
  class Images(HTMLParser):
   def __init__(self):super().__init__();self.styles=[]
   def handle_starttag(self,tag,attrs):
    if tag=='img':self.styles.append(dict(attrs).get('style',''))
  document=(target/'comparison.html').read_text(encoding='utf-8');parser=Images();parser.feed(document)
  assert len(parser.styles)==2 and all('width:160mm;' in s and 'min-width:160mm;' in s and 'max-width:none' in s for s in parser.styles)
  assert 'height:80mm' in parser.styles[0] and 'height:120mm' in parser.styles[1]
  assert 'overflow-x:auto' in document and 'flex:0 0 auto' in document and 'width:100%' not in document
  assert r['candidates'][0]['comparison']['effectiveness']=='REVIEW_REQUIRED'
 case('equal_css_mm_uses_each_viewbox_and_reports_font_scaling',fixed_width_cli)
 def unknown_dimensions():
  unknown=artifact('unknown-size','<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="auto"><text font-size="20">Unknown viewport</text></svg>')
  r=C.run(before,[unknown],out/'unknown-size-gallery',160);s=r['candidates'][0]['artifact']['sizing']
  assert s['design']['absolute_width_mm'] is None and s['design']['viewBox'] is None
  assert s['placement']['height_mm'] is None and s['placement']['aspect_ratio_basis']=='UNKNOWN'
  assert s['font_scaling']['minimum_known_font_pt'] is None and s['font_scaling']['unknown_font_count']==1
  assert 'height:auto' in (out/'unknown-size-gallery/comparison.html').read_text(encoding='utf-8')
 case('unknown_dimensions_remain_unknown',unknown_dimensions)
 def uncertain_fonts():
  css=artifact('font-css',BASE.replace('<text','<text style="font-size:24px"'))
  transformed=artifact('font-transform',BASE.replace('<text','<g transform="scale(2)"><text').replace('</text>','</text></g>'))
  relative=artifact('font-relative',BASE.replace('font-size="20"','font-size="1.2em"'))
  r=C.run(before,[css,transformed,relative],out/'unknown-font-gallery',80)
  for c in r['candidates']:
   font=c['artifact']['sizing']['font_scaling']
   assert font['status']=='PARTIAL_OR_UNKNOWN' and font['unknown_font_count']==1 and font['minimum_known_font_pt'] is None
   assert font['entries'][0]['limits']
 case('css_transform_and_relative_fonts_never_report_verified_sizes',uncertain_fonts)
 def absolute_without_viewbox():
  svg=artifact('absolute-no-viewbox','<svg xmlns="http://www.w3.org/2000/svg" width="4in" height="2in"><g font-size="12pt"><text>Inherited font</text></g></svg>')
  r=C.run(before,[svg],out/'absolute-size-gallery',50.8);s=r['candidates'][0]['artifact']['sizing']
  assert s['placement']['aspect_ratio_basis']=='absolute_viewport_without_valid_viewBox'
  assert s['placement']['height_mm']==25.4 and math.isclose(s['font_scaling']['minimum_known_font_pt'],6)
  assert s['font_scaling']['entries'][0]['status']=='COMPUTED_NOT_RENDER_VERIFIED'
 case('absolute_viewport_and_inherited_font_have_bounded_scaling',absolute_without_viewbox)
 def invalid_width():
  for i,value in enumerate([0,-1,float('nan'),float('inf'),-float('inf')]):
   target=out/f'invalid-width-api-{i}'
   try:C.run(before,[before],target,value)
   except ValueError:assert not target.exists()
   else:raise AssertionError(f'Invalid API width accepted: {value}')
   target=out/f'invalid-width-cli-{i}'
   p1=subprocess.run([sys.executable,str(ROOT/'scripts/compare_designs.py'),'--baseline',str(before),'--candidate',str(before),f'--placement-width-mm={value}','--out',str(target)],capture_output=True,text=True)
   assert p1.returncode!=0 and not target.exists(),(value,p1.stdout,p1.stderr)
 case('nonpositive_nan_infinite_width_rejected_before_output',invalid_width)
 result={'passed':sum(r['status']=='PASS' for r in results),'total':len(results),'results':results}
 (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));return result['passed']==result['total']
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();raise SystemExit(0 if run(a.out) else 1)
