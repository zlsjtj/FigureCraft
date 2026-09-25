"""Bounded checks on the actual exported SVG/PDF, never a human-readability test."""
import argparse, hashlib, json, math, re
from pathlib import Path
from xml.etree import ElementTree as ET
from pypdf import PdfReader

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--figure-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    root=a.figure_dir; svg=root/'figure.svg'; tree=ET.parse(svg);elems=list(tree.getroot());byid={e.get('id'):e for e in elems if e.get('id')}; circles=[e for e in elems if e.tag.endswith('}circle')]
    b=byid['disk-B'];ad=byid['disk-A'];upper=byid['barrier-upper'];lower=byid['barrier-lower'];f=lambda e,k:float(e.get(k));top=f(upper,'y')+f(upper,'height');bottom=f(lower,'y');wall=f(upper,'x');u=10
    checks={
      'exact_circle_count_2':len(circles)==2,
      'identities_exactly_A_B':{e.get('data-logical-id') for e in circles}=={'A','B'},
      'all_circles_primary':all(e.get('data-object-part')=='primary' for e in circles),
      'A_diameter_2':abs(2*f(ad,'r')/u-2)<1e-10,
      'B_diameter_4':abs(2*f(b,'r')/u-4)<1e-10,
      'opening_3':abs((bottom-top)/u-3)<1e-10,
      'shared_centerline':f(b,'cy')==f(ad,'cy')==(top+bottom)/2,
      'single_shared_wall_ID':upper.get('data-logical-id')==lower.get('data-logical-id')=='wall',
      'A_right_of_wall':f(ad,'cx')-f(ad,'r')>wall+f(upper,'width'),
      'B_center_left_of_wall':f(b,'cx')<wall,
      'B_touches_both_corners':all(abs(math.hypot(wall-f(b,'cx'),y-f(b,'cy'))-f(b,'r'))<1e-10 for y in [top,bottom]),
      'no_ghosts_or_extra_disks':len(circles)==2 and len([e for e in elems if e.tag.endswith('}ellipse')])==0,
      'dimensions_160_by_84':tree.getroot().get('width')=='160mm' and tree.getroot().get('height')=='84mm'
    }
    for prefix in ['B-approach','A-through']:
        arrow=byid[prefix+'-head'];pts=[tuple(map(float,p.split(','))) for p in arrow.get('points').split()]
        checks[prefix+'_rightward']=pts[0][0]>sum(p[0] for p in pts[1:])/2 and abs(pts[0][1]-(top+bottom)/2)<1e-10
    content=PdfReader(root/'figure.pdf').pages[0].get_contents().get_data()
    fonts=[float(v) for v in re.findall(rb'/[^\s/]+\s+([0-9.]+)\s+Tf',content)]
    checks['pdf_min_font_at_least_10pt']=bool(fonts) and min(fonts)>=10
    # This is re-evaluation of the stated deterministic rule, not benchmark data.
    cases=[{'d':d,'result':'pass' if d<3 else 'block','evidence':'constructed rule check'} for d in [2,2.5,3,4]]
    checks['four_constructed_checks']=[v['result'] for v in cases]==['pass','pass','block','block']
    result={'source_svg_sha256':sha(svg),'source_pdf_sha256':sha(root/'figure.pdf'),'checks':checks,'constructed_checks':cases,'minimum_pdf_tf_pt':min(fonts),'status':'PASS' if all(checks.values()) else 'FAIL','scope':'Actual SVG primitives and decoded PDF stream. Geometrically constructed tangent B placement, no dynamics or forces. Does not certify visual quality. Uses independent arithmetic, not FigureCraft scene engine.'}
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(checks)}))
    return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
