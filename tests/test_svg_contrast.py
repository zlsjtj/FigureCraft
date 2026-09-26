import sys,unittest,xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from svg_text_contrast import screen
LABEL={'id':'t','text':'Value','bounds':[20,20,60,32]}
def run(body,canvas='#FFFFFF'):
 return screen(E.fromstring('<svg>'+body+'</svg>'),[LABEL],canvas)
def text(fill='#000000'):return f'<text id="t" fill="{fill}">Value</text>'
class Contrast(unittest.TestCase):
 def test_black_on_white(self):self.assertAlmostEqual(run(text())['labels'][0]['ratio'],21)
 def test_no_implicit_canvas(self):self.assertEqual(run(text(),None)['status'],'NOT_RUN')
 def test_small_gold_text_below_threshold(self):self.assertEqual(run(text('#9C773F'))['status'],'FAIL')
 def test_darkened_hue_passes(self):self.assertEqual(run(text('#88632F'))['status'],'PASS')
 def test_actual_dark_panel_not_declared_white(self):
  r=run('<rect x="0" y="0" width="100" height="50" fill="#000000"/>'+text('#FFFFFF'))
  self.assertEqual(r['status'],'PASS');self.assertEqual(r['labels'][0]['background'],'#000000')
 def test_partial_background_is_review(self):self.assertEqual(run('<rect width="40" height="50" fill="#000000"/>'+text())['status'],'REVIEW_REQUIRED')
 def test_transparency_is_review(self):self.assertEqual(run('<rect width="100" height="50" opacity="0.5"/>'+text())['status'],'REVIEW_REQUIRED')
 def test_later_cover_is_review(self):self.assertEqual(run(text()+'<rect width="100" height="50"/>')['status'],'REVIEW_REQUIRED')
 def test_inherited_fill(self):self.assertEqual(run('<g fill="#9C773F"><text id="t">Value</text></g>')['status'],'FAIL')
 def test_distant_shape_does_not_poison(self):self.assertEqual(run('<circle cx="120" cy="100" r="10"/>'+text())['status'],'PASS')
 def test_nearer_opaque_panel_resolves_prior_unknown(self):self.assertEqual(run('<path d="M0 0 L100 50"/><rect width="100" height="50" fill="white"/>'+text())['status'],'PASS')
 def test_unsupported_text_paint_review(self):self.assertEqual(run('<text id="t" fill="url(#gradient)">Value</text>')['status'],'REVIEW_REQUIRED')
 def test_missing_id_cannot_pass_partial_coverage(self):self.assertEqual(run('<text>Value</text>')['status'],'REVIEW_REQUIRED')
 def test_nonfinite_paint_cannot_pass(self):self.assertEqual(run('<rect width="nan" height="50"/>'+text())['status'],'REVIEW_REQUIRED')
 def test_duplicate_id_requires_review(self):self.assertEqual(run(text()+text('#FFFFFF'))['status'],'REVIEW_REQUIRED')
if __name__=='__main__':unittest.main()
