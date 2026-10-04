from pathlib import Path
import hashlib,json,shutil,sys
root=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=Path(sys.argv[1])
ref=root/'baseline-reference';ref.mkdir(exist_ok=True)
for name in ['figure.svg','figure.png']:
    shutil.copy2(baseline/name,ref/name)
variants=[('Baseline: four equal profiles','baseline-reference/figure.svg'),('First A: assembly / local contact / released pose','first-candidates/candidate-A/figure.svg'),('First B: shared-datum overlay — rejected','first-candidates/candidate-B/figure.svg'),('SELECTED: A with local release direction and true clearance','selected/candidate-A-refined/figure.svg')]
html='<!doctype html><meta charset="utf-8"><title>Shape development — actual artifacts</title><style>body{font:16px Arial;margin:24px;color:#243b46}section{margin-bottom:35px}img{width:160mm;height:99mm;max-width:none;border:1px solid #ddd}h2{font-size:18px}p{max-width:860px}</style><h1>Shape development</h1><p>All figures use 160 × 99 mm CSS size. Display scaling is not a calibrated ruler. A/B are development candidates, not independent or human acceptance. S1/S3 angles are retained in the selected caption and source CSV; the selected drawing prioritizes contact release.</p>'
for label,src in variants:html+=f'<section><h2>{label}</h2><img src="{src}"></section>'
html+='<p><a href="caption.md">Selected caption</a> · <a href="review-one-page.md">Evidence and trade-offs</a></p>'
(root/'comparison.html').write_text(html,encoding='utf-8')
checks={}
for name in ['figure.svg','figure.pdf','figure.png','figure-grayscale.png','figure-deuteranopia.png','scene.json']:
    checks[name]={'selected_sha256':sha(root/'selected'/'candidate-A-refined'/name),'relocated_sha256':sha(root/'relocated-rebuild'/'candidate-A-refined'/name)}
    checks[name]['identical']=checks[name]['selected_sha256']==checks[name]['relocated_sha256']
(root/'portability-check.json').write_text(json.dumps({'copied_source':'relocated-source','invocation_cwd':str(root.parent.parent),'all_identical':all(z['identical'] for z in checks.values()),'files':checks,'scope':'Fixed-source reconstruction, not fresh generation or independent review.'},indent=2),encoding='utf-8')
v=json.loads((root/'validation.json').read_text());v['relocated_rebuild_all_identical']=all(z['identical'] for z in checks.values());(root/'validation.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
manifest={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.name!='artifact-hashes.json'}
(root/'artifact-hashes.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'artifacts':len(manifest),'relocated_rebuild_all_identical':v['relocated_rebuild_all_identical'],'selected':'selected/candidate-A-refined','overall_status':'REVIEW_REQUIRED'}))
