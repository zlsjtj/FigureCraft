"""Report declared SVG text load; never infer readability or artistic quality."""
from pathlib import Path
import argparse,collections,json,re,xml.etree.ElementTree as ET
from compare_designs import inspect,placement_info,positive_mm

def measure(path,width_mm):
    source=inspect(path);root=ET.fromstring(source['raw'])
    labels=[''.join(e.itertext()).strip() for e in root.iter() if e.tag.rsplit('}',1)[-1]=='text']
    labels=[s for s in labels if s]
    def counts(s):
        return {'latin_tokens':len(re.findall(r"[A-Za-z]+(?:[-’'][A-Za-z]+)*",s)),
                'cjk_characters':len(re.findall(r'[\u3400-\u9fff]',s)),
                'numeric_tokens':len(re.findall(r'(?<![\w.])[+-]?\d+(?:\.\d+)?',s))}
    entries=[{'text':s,**counts(s)} for s in labels]
    sizing=placement_info(source,positive_mm(width_mm))
    totals={k:sum(e[k] for e in entries) for k in ('latin_tokens','cjk_characters','numeric_tokens')}
    return {'source_sha256':source['sha256'],'declared_text_elements':len(labels),**totals,
            'labels':entries,'repeated_labels':{s:n for s,n in collections.Counter(labels).items() if n>1},
            'sizing':sizing,'effectiveness':'REVIEW_REQUIRED',
            'scope':'Lexical counts of declared text nodes, not rendered ink or visibility. Latin identifiers are included, tspan content counted once. Styles, hidden nodes, clones, clipping and raster labels may change visible load. Numeric tokens are lexical, not scientific values. No density threshold proves readability. Human/agent interpretation and actual-size viewing remain separate.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('svg',type=Path);ap.add_argument('--width-mm',type=positive_mm,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise FileExistsError('Refusing existing output')
    result=measure(a.svg,a.width_mm);a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('declared_text_elements','latin_tokens','cjk_characters','numeric_tokens','effectiveness')}))
if __name__=='__main__':main()
