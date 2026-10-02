"""Real ReportLab filter-chain regression and conservative failure semantics."""
import base64
import importlib.util
import io
import sys
import unittest
import zlib
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("figurecraft_pdf_filter_audit", ROOT / "vendor/nature-figure/audit_pdf_text.py")
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


def fixture(payload, filters=b""):
    return b"%PDF-1.4\n1 0 obj\n<< /Length " + str(len(payload)).encode() + filters + b" >>\nstream\n" + payload + b"\nendstream\nendobj\n%%EOF"


class PDFFilterChainTests(unittest.TestCase):
    def assert_rejected(self, data):
        result = audit.audit_pdf(data, 8)
        self.assertFalse(result["auditable"])
        self.assertFalse(result["decoding_complete"])
        self.assertTrue(result["warnings"])
        return result

    def test_real_reportlab_ordered_filters_and_small_text(self):
        from reportlab import rl_config
        from reportlab.pdfgen import canvas
        for size in (10, 5):
            with self.subTest(size=size), patch.object(rl_config, "useA85", 1):
                target = io.BytesIO()
                c = canvas.Canvas(target, pageCompression=1)
                c.setFont("Helvetica", size)
                c.drawString(20, 20, "Measured text")
                c.save()
                data = target.getvalue()
                self.assertIn(b"/ASCII85Decode /FlateDecode", data)
                result = audit.audit_pdf(data, 8)
                self.assertTrue(result["auditable"], result)
                self.assertEqual(result["minimum_found_pt"], size)
                self.assertEqual(bool(result["below_minimum_count"]), size < 8)
                self.assertFalse(result["warnings"])

    def test_plain_and_single_filters_preserve_behavior(self):
        text = b"BT /F1 9 Tf (plain) Tj ET"
        cases = [(text, b""), (zlib.compress(text), b" /Filter /FlateDecode"),
                 (base64.a85encode(text, adobe=True), b" /Filter /ASCII85Decode"),
                 (base64.a85encode(zlib.compress(text), adobe=True), b" /Filter [/A85 /Fl]")]
        for payload, filters in cases:
            with self.subTest(filters=filters):
                result = audit.audit_pdf(fixture(payload, filters), 8)
                self.assertTrue(result["auditable"], result)
                self.assertEqual(result["minimum_found_pt"], 9)

    def test_order_is_applied_as_declared(self):
        encoded = base64.a85encode(zlib.compress(b"/F1 9 Tf"), adobe=True)
        self.assert_rejected(fixture(encoded, b" /Filter [/FlateDecode /ASCII85Decode]"))

    def test_unknown_and_partial_chain_cannot_pass(self):
        good = fixture(b"/F1 10 Tf")
        for filters in (b" /Filter /LZWDecode", b" /Filter [/ASCII85Decode /LZWDecode]",
                        b" /Filter [/Unknown /FlateDecode]"):
            with self.subTest(filters=filters):
                result = self.assert_rejected(good + fixture(b"/F1 3 Tf", filters))
                self.assertTrue(result["partial_text_found"])
                self.assertEqual(result["minimum_found_pt"], 10)
                self.assertNotIn("verdict: PASS", audit.render_text(Path("partial.pdf"), result))

    def test_missing_malformed_indirect_filter_values(self):
        for filters in (b" /Filter", b" /Filter 4 0 R", b" /Filter []",
                        b" /Filter [/ASCII85Decode /FlateDecode", b" /Filter [/FlateDecode 123]",
                        b" /Filter /FlateDecode /Filter /ASCII85Decode", b" /Filter /FlateDecode#20"):
            with self.subTest(filters=filters):
                self.assert_rejected(fixture(b"/F1 9 Tf", filters))

    def test_malformed_or_truncated_filter_payloads(self):
        for payload, filters in ((b"invalid~>", b" /Filter /ASCII85Decode"),
                                 (b"87cURDZ", b" /Filter /ASCII85Decode"),
                                 (b"not zlib", b" /Filter /FlateDecode"),
                                 (zlib.compress(b"/F1 9 Tf")[:-2], b" /Filter /FlateDecode")):
            with self.subTest(payload=payload):
                self.assert_rejected(fixture(payload, filters))

    def test_missing_dictionary_or_endstream_is_incomplete(self):
        self.assert_rejected(b"%PDF-1.4\nstream\n/F1 9 Tf\nendstream")
        self.assert_rejected(b"%PDF-1.4\n<< /Length 9 >>\nstream\n/F1 9 Tf")

    def test_unhandled_parameters_and_object_streams_are_refused(self):
        for fields in (b" /Type /ObjStm", b" /Type /XRef", b" /Filter /FlateDecode /DecodeParms 2 0 R",
                       b" /Filter /FlateDecode /DecodeParms << /Predictor 12 >>"):
            with self.subTest(fields=fields):
                self.assert_rejected(fixture(zlib.compress(b"/F1 9 Tf"), fields))

    def test_encrypted_and_escaped_filter_names_are_refused(self):
        self.assert_rejected(fixture(b"/F1 9 Tf") + b"\ntrailer << /Encrypt 4 0 R >>")
        self.assert_rejected(fixture(b"/F1 9 Tf", b" /F#69lter /Unknown"))

    def test_cli_nonzero_for_partial_decoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.pdf"
            path.write_bytes(fixture(b"/F1 10 Tf") + fixture(b"/F1 3 Tf", b" /Filter /Unknown"))
            with redirect_stdout(io.StringIO()) as output:
                code = audit.main([str(path), "--min-pt", "8", "--json"])
            self.assertEqual(code, 2)
            self.assertIn('"auditable": false', output.getvalue())


if __name__ == "__main__":
    unittest.main()
