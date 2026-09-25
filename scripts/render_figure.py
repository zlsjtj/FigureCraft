"""Render a Studio JSON scene to editable SVG, vector PDF, and optional PNG."""
from pathlib import Path
import argparse,json,subprocess,shutil
from figure_core import fonts,export_scene,sha
from palette_tools import CVD
from check_figure import check

def qa_views(png,out):
    import numpy as np
    from PIL import Image
    im=Image.open(png).convert('RGB');im.thumbnail((1400,1400))
    a=np.asarray(im).astype(float)/255
    v=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    for name,b in [('grayscale',np.repeat((v@np.array([.2126,.7152,.0722]))[...,None],3,axis=2)),('deuteranopia',v@np.array(CVD).T)]:
        b=np.clip(b,0,1);b=np.where(b<=.0031308,12.92*b,1.055*np.power(b,1/2.4)-.055)
        Image.fromarray(np.rint(b*255).astype('uint8')).save(out/f'qa-{name}.png')
    return {'method':'grayscale: linear-sRGB relative luminance; CVD: Machado 2009 deuteranomaly severity 100, clipped to sRGB','status':'GENERATED_REVIEW_REQUIRED','preview_max_px':1400,'not_all_color_vision_conditions':True}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True);p.add_argument('--cjk-font',type=Path);p.add_argument('--pdftoppm',type=Path)
    p.add_argument('--placement-width-mm',type=float,help='Final document placement width; scaled typography is checked separately')
    p.add_argument('--dpi',type=int,default=300);p.add_argument('--qa-views',action='store_true');p.add_argument('--view',choices=['normal','grayscale','deuteranopia'],default='normal')
    p.add_argument('--library',type=Path,default=Path(__file__).resolve().parents[1]/'assets/reference_palettes.json');a=p.parse_args()
    try:
        if a.out.exists():raise ValueError('Output directory exists; use a new revision directory')
        if not 72<=a.dpi<=1200:raise ValueError('DPI must be 72..1200')
        spec=json.loads(a.spec.read_text(encoding='utf-8'));loaded=fonts(a.font,a.cjk_font)
        if a.placement_width_mm is not None:spec['output']['placement_width_mm']=a.placement_width_mm
        # Data reference validation runs before creation; never trust an unbound data table.
        if spec.get('data_source'):
            data_path=(a.spec.parent/spec['data_source']).resolve()
            if not data_path.is_file() or sha(data_path)!=spec['data_sha256']:raise ValueError('Source-data file absent or hash differs; rebuild the scene from verified data')
        a.out.mkdir(parents=True);m=export_scene(spec,a.out,loaded,json.loads(a.library.read_text(encoding='utf-8')),a.view)
        m['input_spec_file_sha256']=sha(a.spec);m['source_spec_path']=str(a.spec.resolve())
        raster={'status':'NOT_RUN','reason':'No explicit pdftoppm path; SVG/PDF still produced'}
        if a.pdftoppm:
            if not a.pdftoppm.is_file():raster={'status':'NOT_RUN','reason':'Specified pdftoppm is missing'}
            else:
                cmd=[str(a.pdftoppm),'-png','-singlefile','-r',str(a.dpi),str(a.out/'figure.pdf'),str(a.out/'figure')]
                run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
                raster={'status':'PASS' if run.returncode==0 and (a.out/'figure.png').is_file() else 'FAIL','command':cmd,'exit_code':run.returncode,'stderr':run.stderr}
                if raster['status']=='PASS':
                    from PIL import Image
                    im=Image.open(a.out/'figure.png');raster.update(pixel_size=list(im.size),dpi=a.dpi)
                    im.thumbnail((1400,1400));im.save(a.out/'preview.png')
                    if a.qa_views:m['color_vision_previews']=qa_views(a.out/'figure.png',a.out)
        m['raster']=raster
        for file in a.out.glob('*.png'):m['files'][file.name]=sha(file)
        m['files']['figure_spec.json']=sha(a.out/'figure_spec.json')
        if spec.get('data_source'):
            shutil.copy2(data_path,a.out/data_path.name);m['files'][data_path.name]=sha(a.out/data_path.name)
        (a.out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
        qa=check(a.out);(a.out/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'output':str(a.out),'geometry_checks':qa['status'],'technical_status':qa['technical_status'],
            'scientific_review_status':qa.get('scientific_review_status','REVIEW_REQUIRED'),'overall_status':qa['overall_status'],
            'placement':qa.get('placement'),'raster':raster['status'],'visual_review':'NOT_RUN'},ensure_ascii=False))
        return 1 if qa['status']=='FAIL' or raster['status']=='FAIL' else 0
    except (ValueError,OSError,KeyError,subprocess.TimeoutExpired) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
