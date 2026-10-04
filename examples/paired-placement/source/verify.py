"""Verify exact post-review SVG geometry and a fresh fixed-source reconstruction."""
import argparse,hashlib,json,subprocess,sys,xml.etree.ElementTree as E
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True);p.add_argument('--bold-font',type=Path,required=True);p.add_argument('--pdftoppm',type=Path,required=True)
    p.add_argument('--rendered',type=Path,help='Previously generated output; defaults to selected in the example.')
    p.add_argument('--rebuild-out',type=Path,help='New directory for independent reconstruction.')
    p.add_argument('--receipt',type=Path,help='New receipt file; existing files are never overwritten.')
    a=p.parse_args()
    b=a.root.resolve();r=a.rendered.resolve() if a.rendered else b/'selected'
    rebuilt=a.rebuild_out.resolve() if a.rebuild_out else b/'verification-rebuilt'
    out=a.receipt.resolve() if a.receipt else b/'verification.json'
    if out.exists() or rebuilt.exists():raise FileExistsError('Receipt and reconstruction directory must be new')
    ns={'s':'http://www.w3.org/2000/svg'};svg=E.parse(r/'figure.svg').getroot()
    get=lambda typ,id:svg.find(f"s:{typ}[@id='{id}']",ns)
    record=get('rect','shared-record');checks={};coordinates={}
    checks['one_immutable_record']=len(svg.findall("s:rect[@data-role='single-immutable-record']",ns))==1
    checks['T5_record_value_exact']=record.get('data-record-id')=='T5' and record.get('data-translation-px')=='84,3'
    checks['both_reference_labels_exact']=all(get('text','read-'+ch).text=='read t' for ch in ['A','B'])
    checks['both_reference_links_undirected']=all(get('polygon','reference-'+ch+'-arrow') is None for ch in ['A','B'])
    checks['formula_key_explicit']=get('text','same-map').text=='p → p + t[T5]'
    xs=[float(get('text',id).get('x')) for id in ['same-map','example-input','example-output']]
    checks['example_and_formula_centered_together']=max(xs)-min(xs)<1e-9
    for ch in ['A','B']:
        before=get('rect','input-'+ch);after=get('rect','placed-'+ch);context=get('rect','context-'+ch)
        checks[ch+'_identity_preserved']=before.get('data-logical-id')==after.get('data-logical-id')==ch+'-T5'
        s=float(after.get('width'))/96
        trans=[(float(after.get(k))-float(context.get(k)))/s for k in ['x','y']]
        positions={}
        for state,rect in [('input',before),('placed',after)]:
            pts=[list(map(float,t.split(','))) for t in get('polyline',state+'-'+ch+'-fid-x').get('points').split()]
            center=[(pts[0][0]+pts[1][0])/2,pts[0][1]];unit=float(rect.get('width'))/96
            local=[(center[i]-float(rect.get(k)))/unit for i,k in enumerate(['x','y'])]
            positions[state+'_local']=local
        positions['translation']=trans;positions['output_coordinate']=[trans[i]+positions['placed_local'][i] for i in [0,1]];coordinates[ch]=positions
        checks[ch+'_translation_84_3']=all(abs(v-e)<1e-9 for v,e in zip(trans,[84,3]))
        checks[ch+'_fiducial_input_and_placed_local_10_18']=all(abs(v-e)<1e-9 for k in ['input_local','placed_local'] for v,e in zip(positions[k],[10,18]))
        checks[ch+'_output_94_21']=all(abs(v-e)<1e-9 for v,e in zip(positions['output_coordinate'],[94,21]))
        # Verify each reference endpoint actually meets its own image-processing segment.
        end=list(map(float,get('polyline','reference-'+ch).get('points').split()[-1].split(',')))
        arrow=[list(map(float,t.split(','))) for t in get('polyline','apply-'+ch).get('points').split()]
        checks[ch+'_reference_meets_own_resample']=abs(end[0]-arrow[0][0])<1e-9 and arrow[0][1]<=end[1]<=arrow[-1][1]
    checks['min_font_not_reduced']=min(float(e.get('font-size')) for e in svg.findall('s:text',ns))>=9
    checks['no_mask_geometry_added']=not any('mask' in (e.get('data-role') or '') for e in svg)
    checks['nine_results_rows_preserved']=len((b/'source/inputs/results.csv').read_text(encoding='utf-8').strip().splitlines())==10
    cmd=[sys.executable,'-B',str(b/'source/build.py'),'--out',str(rebuilt),'--variant','vertical','--font',str(a.font.resolve()),'--bold-font',str(a.bold_font.resolve()),'--pdftoppm',str(a.pdftoppm.resolve())]
    run=subprocess.run(cmd,cwd=b.parent.parent,capture_output=True,text=True,encoding='utf-8',errors='replace')
    files=['figure.svg','figure.pdf','figure.png','figure-gray.png','figure-deuteranopia.png','caption.txt','alt_text.txt']
    reconstruction={f:{'rendered':sha(r/f),'rebuilt':sha(rebuilt/f),'equal':sha(r/f)==sha(rebuilt/f)} for f in files} if run.returncode==0 else {}
    status=all(checks.values()) and run.returncode==0 and all(x['equal'] for x in reconstruction.values())
    receipt={'kind':'post-review merge; fixed-source rebuild, not first-round transfer validation','svg_sha256':sha(r/'figure.svg'),'checks':checks,'coordinates_px':coordinates,
      'status':'PASS' if status else 'FAIL','overall_status':'REVIEW_REQUIRED','reviewer':'drawing agent exact-file checks; not human acceptance','reconstruction':reconstruction,
      'command':cmd,'cwd':str(b.parent.parent),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,
      'source_hashes':{str(p.relative_to(b)):sha(p) for p in [b/'README.md',b/'source/build.py',b/'source/verify.py',b/'source/inputs/notes.md',b/'source/inputs/results.csv']}}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps({'status':receipt['status'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'rebuild_files':len(reconstruction)}))
if __name__=='__main__':main()
