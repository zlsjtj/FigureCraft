"""Finite analytic ray checks plus finite label and portable-rebuild checks."""
import argparse,hashlib,json,math,shutil,subprocess,sys
from pathlib import Path
import numpy as np
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def analytic_ray(x,y,cam):
    v=np.array(cam['view_toward_observer']);o=x*np.array(cam['right'])-y*np.array(cam['up']);hits=[]
    def retained(p):return abs(math.atan2(p[1],p[0])) >= math.radians(35)-1e-9
    for r,lo,hi,role in [(12,0,30,'sleeve_outer'),(9,0,30,'sleeve_inner'),(5,-3,33,'solid_core')]:
        aa=v[:2]@v[:2];bb=2*(o[:2]@v[:2]);cc=o[:2]@o[:2]-r*r;dis=bb*bb-4*aa*cc
        if dis<0:continue
        for t in [(-bb-math.sqrt(dis))/(2*aa),(-bb+math.sqrt(dis))/(2*aa)]:
            p=o+t*v
            if lo-1e-9<=p[2]<=hi+1e-9 and (r==5 or retained(p)):hits.append((t,role))
    for z,lo,hi,role in [(0,9,12,'sleeve_end_rim'),(30,9,12,'sleeve_end_rim'),(-3,0,5,'core_end'),(33,0,5,'core_end')]:
        t=(z-o[2])/v[2];p=o+t*v;r=np.linalg.norm(p[:2])
        if lo-1e-9<=r<=hi+1e-9 and (hi==5 or retained(p)):hits.append((t,role))
    for theta in [-35,35]:
        theta=math.radians(theta);n=np.array([-math.sin(theta),math.cos(theta),0]);d=np.array([math.cos(theta),math.sin(theta),0])
        t=-(o@n)/(v@n);p=o+t*v;r=p@d
        if 9-1e-9<=r<=12+1e-9 and 0-1e-9<=p[2]<=30+1e-9:hits.append((t,'sleeve_opening_face'))
    return max(hits) if hits else None
def main():
    ap=argparse.ArgumentParser()
    for n in ['root','skill','font','bold-font','pdftoppm']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();qa=a.root/'qa';qa.mkdir(exist_ok=False);runs=[]
    for name in ['first','final']:
        art=a.root/name;spec=json.loads((art/'figure_spec.json').read_text(encoding='utf-8'));record=json.loads((art/'surface_record.json').read_text(encoding='utf-8'));rev={i:r for r,i in record['roles'].items()};rows=[]
        for s in record['visibility_samples']:
            exact=analytic_ray(*s['xy'],spec['camera'])
            rows.append({'role_matches':bool(exact and exact[1]==rev[s['role_id']]),'depth_error':abs(exact[0]-s['depth']) if exact else None})
        dump(qa/(name+'-analytic-rays.json'),{'sample_count':len(rows),'role_match_count':sum(r['role_matches'] for r in rows),'maximum_depth_error':max(r['depth_error'] for r in rows if r['depth_error'] is not None),'mesh_error_units_tolerance':.003,'status':'PASS' if all(r['role_matches'] and r['depth_error']<.003 for r in rows) else 'REVIEW_REQUIRED','scope':'400 visible sampled rays only; exact source-cylinder intersections; does not prove every pixel'})
        cmd=[sys.executable,str(a.skill/'scripts/audit_svg_labels.py'),str(art/'figure.svg'),'--font',str(a.font),'--bold-font',str(a.bold_font),'--placement-width-mm','160','--canvas-background','#FFFFFF','--out',str(qa/(name+'-svg-label-audit.json'))]
        r=subprocess.run(cmd,capture_output=True,text=True);runs.append({'command':cmd,'exit_code':r.returncode});(qa/(name+'-svg-label-audit.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
        cmd=[sys.executable,str(a.skill/'vendor/nature-figure/audit_pdf_text.py'),str(art/'figure.pdf'),'--min-pt','8','--json'];r=subprocess.run(cmd,capture_output=True,text=True);runs.append({'command':cmd,'exit_code':r.returncode});(qa/(name+'-pdf-font-audit.json')).write_text(r.stdout,encoding='utf-8')
    portable=qa/'relocated-source';portable.mkdir();shutil.copy2(a.root/'final/build_figure.py',portable/'build_figure.py');shutil.copy2(a.root/'final/input.md',portable/'input.md')
    cmd=[sys.executable,str(portable/'build_figure.py'),'--skill',str(a.skill),'--input',str(portable/'input.md'),'--out',str(qa/'rebuilt'),'--font',str(a.font),'--bold-font',str(a.bold_font),'--pdftoppm',str(a.pdftoppm),'--revision','final']
    r=subprocess.run(cmd,capture_output=True,text=True,cwd=portable);runs.append({'command':cmd,'cwd':str(portable),'exit_code':r.returncode});(qa/'portable-rebuild.log').write_text(r.stdout+r.stderr,encoding='utf-8')
    compare={f:sha(a.root/'final'/f)==sha(qa/'rebuilt'/f) for f in ['figure.svg','figure.png','surface.png','figure-grayscale.png','figure-deuteranopia-approx.png','caption.txt','alt_text.txt']}
    dump(qa/'portable-rebuild.json',{'status':'PASS' if r.returncode==0 and all(compare.values()) else 'FAIL','artifact_hash_matches':compare,'pdf_binary_comparison':'NOT_APPLICABLE: creation timestamp changes; label and page geometry separately audited','meaning':'Same source rebuild from copied script/input and different working directory; not another independent figure generation'})
    dump(qa/'executions.json',runs)
    files=['scripts/audit_svg_labels.py','vendor/nature-figure/audit_pdf_text.py']
    dump(qa/'additional_loaded_skill_hashes.json',{'skill_root':str(a.skill),'files':[{'path':f,'sha256':sha(a.skill/f)} for f in files]})
    print(json.dumps({'qa':str(qa),'portable_hash_matches':compare,'audit_exit_codes':[r['exit_code'] for r in runs]}))
if __name__=='__main__':main()
