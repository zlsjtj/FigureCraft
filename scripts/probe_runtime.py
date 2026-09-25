"""Read-only capability discovery. Availability is not an execution PASS."""
import argparse,importlib.util,importlib.metadata,json,platform,shutil,sys
from pathlib import Path
def probe(font=None,cjk_font=None,pdftoppm=None):
    modules={}
    for name,distribution in [('reportlab','reportlab'),('pypdf','pypdf'),('PIL','Pillow'),('numpy','numpy'),('matplotlib','matplotlib'),('fitz','PyMuPDF'),('colorspacious','colorspacious')]:
        available=importlib.util.find_spec(name) is not None
        try:version=importlib.metadata.version(distribution) if available else None
        except importlib.metadata.PackageNotFoundError:version='unknown'
        modules[name]={'available':available,'version':version,'execution':'NOT_RUN'}
    native={name:{'path':shutil.which(name),'execution':'NOT_RUN'} for name in ('blender','Rscript','inkscape')}
    core=all(modules[n]['available'] for n in ('reportlab','pypdf'))
    raster=bool(pdftoppm and Path(pdftoppm).is_file())
    return {'python':sys.executable,'python_version':platform.python_version(),'platform':platform.platform(),'modules':modules,
      'native':native,'font_paths':{k:{'path':str(v) if v else None,'exists':bool(v and Path(v).is_file())} for k,v in [('latin',font),('cjk',cjk_font)]},
      'core_svg_pdf_available':core,'pdftoppm':{'path':str(pdftoppm) if pdftoppm else None,'available':raster,'execution':'NOT_RUN'},
      'optional_3d':{'status':'NOT_RUN','reason':'No implemented or tested D2 backend in this package'},
      'image_API':{'status':'NOT_RUN','reason':'No external image API used or required'},'journal_rules':'UNVERIFIED'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--font',type=Path);p.add_argument('--cjk-font',type=Path);p.add_argument('--pdftoppm',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    result=probe(a.font,a.cjk_font,a.pdftoppm)
    if a.out:
        if a.out.exists():p.error('Output exists')
        a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['core_svg_pdf_available'] else 2
if __name__=='__main__':raise SystemExit(main())
