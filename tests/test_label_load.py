import tempfile,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from measure_label_load import measure

class Labels(unittest.TestCase):
    def run_svg(self,body):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.svg';p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="80mm" viewBox="0 0 160 80">'+body+'</svg>',encoding='utf-8');return measure(p,160)
    def test_tspan_once(self):
        r=self.run_svg('<text font-size="4">Shared <tspan>offsets</tspan></text>');self.assertEqual((r['declared_text_elements'],r['latin_tokens']),(1,2))
    def test_numbers_separate(self):
        r=self.run_svg('<text font-size="4">Base 4096 0 8 32 40</text>');self.assertEqual((r['latin_tokens'],r['numeric_tokens']),(1,5))
    def test_repeat_not_error(self):
        r=self.run_svg('<text>A</text><text>A</text>');self.assertEqual(r['repeated_labels'],{'A':2});self.assertEqual(r['effectiveness'],'REVIEW_REQUIRED')
    def test_cjk(self):
        r=self.run_svg('<text>共享偏移 32</text>');self.assertEqual((r['cjk_characters'],r['numeric_tokens']),(4,1))
    def test_hidden_stays_bounded(self):
        r=self.run_svg('<text style="display:none">Hidden text</text>');self.assertEqual(r['latin_tokens'],2);self.assertEqual(r['sizing']['font_scaling']['status'],'PARTIAL_OR_UNKNOWN')
    def test_no_text_not_success(self):
        r=self.run_svg('<rect width="10" height="10"/>');self.assertEqual(r['latin_tokens'],0);self.assertEqual(r['effectiveness'],'REVIEW_REQUIRED')
if __name__=='__main__':unittest.main()
