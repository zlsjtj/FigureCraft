"""Source inventory regressions: prevent false resolution/vector/source claims."""
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from PIL import Image

MODULE = Path(__file__).resolve().parents[1]/'scripts/inspect_figure_sources.py'
spec = importlib.util.spec_from_file_location('inspect_figure_sources', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SourceInventoryTests(unittest.TestCase):
    def test_metadata_dpi_cannot_inflate_physical_resolution(self):
        stream=BytesIO()
        Image.new('RGB',(320,200),'white').save(stream,format='JPEG',dpi=(1200,1200))
        rep=m.representation(stream.getvalue(),'.jpg')
        self.assertEqual(rep['pixels'],[320,200])
        self.assertEqual(m.effective_dpi(rep['pixels'],80,50),[101.6,101.6])

    def test_svg_wrapper_is_not_called_full_vector(self):
        rep=m.representation(b'<svg xmlns="http://www.w3.org/2000/svg"><image href="a.png"/><text>x</text></svg>','.svg')
        self.assertEqual(rep['representation'],'mixed-svg')
        self.assertEqual(rep['raster_nodes'],1)
        self.assertEqual(rep['vector_nodes']['text'],1)

    def test_cropped_pixels_and_invalid_extent(self):
        self.assertEqual(m.effective_dpi([1000,1000],50.8,50.8,{'l':25000,'r':25000}),[250,500])
        with self.assertRaises(ValueError):m.effective_dpi([1000,1000],0,50)
        with self.assertRaises(ValueError):m.effective_dpi([1000,1000],50,50,{'l':100000})

    def fixture(self, folder):
        image=folder/'actual.jpg'
        Image.new('RGB',(200,100),'white').save(image)
        docx=folder/'test.docx'
        xml='''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:body><w:p><w:r><w:drawing><wp:inline><wp:extent cx="1800000" cy="900000"/><a:blip r:embed="rId1"/></wp:inline></w:drawing></w:r></w:p></w:body></w:document>'''
        rel='''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="media/embedded.jpg" Type="image"/></Relationships>'''
        with zipfile.ZipFile(docx,'w') as z:
            z.writestr('word/document.xml',xml)
            z.writestr('word/_rels/document.xml.rels',rel)
            z.writestr('word/media/embedded.jpg',image.read_bytes())
        return image,docx

    def test_exact_source_matching_and_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);image,docx=self.fixture(root)
            inv=m.inspect_sources(docx,root,{'drawings':[{'drawing_index':1,'source_file':'actual.jpg'}]})
            d=inv['document']['drawings'][0]
            self.assertEqual(d['byte_identical_sources'],['actual.jpg'])
            self.assertEqual(d['source_identity_status'],'BYTE_MATCH')
            self.assertEqual(d['effective_dpi'],[101.6,101.6])
            self.assertEqual(inv['overall_status'],'REVIEW_REQUIRED')
            with self.assertRaisesRegex(ValueError,'missing'):
                m.inspect_sources(docx,root,{'drawings':[{'drawing_index':1,'source_file':'invented.csv'}]})

    def test_same_filename_cannot_establish_matching_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);image,docx=self.fixture(root)
            Image.new('RGB',(200,100),'black').save(image)
            inv=m.inspect_sources(docx,root,{'drawings':[{'drawing_index':1,'source_file':'actual.jpg'}]})
            d=inv['document']['drawings'][0]
            self.assertEqual(d['byte_identical_sources'],[])
            self.assertEqual(d['pixel_identical_sources'],[])
            self.assertEqual(d['source_identity_status'],'DECLARED_NOT_BYTE_MATCH_REVIEW_REQUIRED')

    def test_same_decoded_pixels_with_different_container_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);image,docx=self.fixture(root)
            original=image.read_bytes()
            # JPEG comment marker changes container bytes without recompression.
            image.write_bytes(original[:2]+b'\xff\xfe\x00\x06test'+original[2:])
            inv=m.inspect_sources(docx,root,{'drawings':[{'drawing_index':1,'source_file':'actual.jpg'}]})
            d=inv['document']['drawings'][0]
            self.assertEqual(d['source_identity_status'],'PIXEL_MATCH_DIFFERENT_BYTES')
            self.assertEqual(d['source_resolution_relation'],'SAME_PIXEL_DIMENSIONS')

    def test_larger_pixel_dimensions_do_not_claim_source_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);image,docx=self.fixture(root)
            Image.new('RGB',(400,200),'red').save(image)
            inv=m.inspect_sources(docx,root,{'drawings':[{'drawing_index':1,'source_file':'actual.jpg'}]})
            d=inv['document']['drawings'][0]
            self.assertEqual(d['source_resolution_relation'],'LARGER_PIXEL_DIMENSIONS')
            self.assertEqual(d['source_identity_status'],'DECLARED_NOT_BYTE_MATCH_REVIEW_REQUIRED')


if __name__=='__main__':unittest.main()
