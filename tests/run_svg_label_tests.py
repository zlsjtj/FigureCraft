"""Existing SVG audit negative cases, without relying on a Studio manifest."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_svg_labels import audit,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    results=[]
    def test(name,body,predicate,width=160,regions=None):
        f=a.out/(name+'.svg');f.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 400">'+body+'</svg>',encoding='utf-8')
        if regions:regions={'svg_sha256':sha(f),'labels':regions}
        r=audit(f,a.font,a.bold_font,width,regions);ok=predicate(r)
        results.append({'name':name,'status':'PASS' if ok else 'FAIL'});(a.out/(name+'.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
    label='<text x="200" y="100" font-family="Arial" font-size="24">Shared offsets</text>'
    clean=lambda r:r['technical_status']=='PASS'
    has=lambda name:lambda r:any(f['check']==name for f in r['findings'])
    test('clear',label,clean)
    test('untyped-guide',label+'<path d="M 210 50 L 210 150" fill="none" stroke="black"/>',has('guide_text_contact'))
    test('dashed-guide',label+'<path d="M 210 50 L 210 150" fill="none" stroke="black" stroke-dasharray="2 4"/>',has('guide_text_contact'))
    test('guide-gap',label+'<path d="M 210 50 L 210 75 M 210 110 L 210 150" fill="none" stroke="black"/>',clean)
    test('placement-shrink',label,has('placement_font_floor_8pt'),80)
    test('transformed', '<g transform="scale(.5)">'+label+'</g>',has('unsupported_svg_feature'))
    test('css',label.replace('font-size="24"','style="font-size:24px"'),has('unsupported_svg_feature'))
    test('curved-guide',label+'<path d="M 0 0 C 10 20 30 40 50 60" fill="none" stroke="black"/>',has('unmeasured_guide'))
    test('missing-font',label.replace('Arial','WrongFont'),has('unmeasured_text'))
    test('outside-canvas',label.replace('x="200"','x="990"'),has('text_outside_view'))
    test('wrong-owner-region',label,has('label_outside_declared_owner_region'),regions=[{'text':'Shared offsets','owner':'held-out','bounds':[700,0,1000,400]}])
    test('correct-owner-region',label,clean,regions=[{'text':'Shared offsets','owner':'table','bounds':[0,0,700,400]}])
    test('nested-inheritance','<g font-family="Arial" font-size="24">'+label.replace(' font-family="Arial" font-size="24"','')+'</g>',clean)
    test('text-overlap',label+label,has('text_text_contact'))
    test('no-text','<path d="M 0 0 L 100 100" fill="none" stroke="black"/>',lambda r:r['technical_status']=='REVIEW_REQUIRED')
    test('science-never-auto-approved',label,lambda r:r['overall_status']=='REVIEW_REQUIRED' and r['scientific_review']=='NOT_RUN')
    prefixed=a.out/'prefixed.svg';prefixed.write_text('<s:svg xmlns:s="http://www.w3.org/2000/svg" viewBox="0 0 1000 400">'+label.replace('<text','<s:text').replace('</text>','</s:text>')+'</s:svg>',encoding='utf-8')
    r=audit(prefixed,a.font,a.bold_font,160);results.append({'name':'prefixed-root-needs-render-review','status':'PASS' if has('prefixed_svg_root_compatibility')(r) else 'FAIL'})
    result={'status':'PASS' if all(x['status']=='PASS' for x in results) else 'FAIL','count':len(results),'tests':results}
    (a.out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));return result['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
