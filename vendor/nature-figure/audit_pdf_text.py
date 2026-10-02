#!/usr/bin/env python3
"""Audit text font sizes used by PDF content-stream ``Tf`` operators.

This dependency-free check catches reduced mathtext superscripts/subscripts and
other glyph runs that can fall below a journal font-size floor even when the
parent matplotlib ``fontsize`` is compliant. It supports plain streams and
ordered ASCII85Decode/FlateDecode filter chains, including ReportLab output.

This is a bounded regular-expression check, not a general PDF parser. It does
not resolve indirect filter definitions, object streams, predictors, encrypted
streams, or arbitrary transforms; incomplete decoding cannot produce a PASS.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path


STREAM_START = re.compile(rb"\bstream\r?\n")
PDF_SPACE = b"\x00\t\n\x0c\r "
FILTER_KEY = re.compile(rb"/Filter\b")
FILTER_NAME = re.compile(rb"/([A-Za-z0-9]+)")
SUPPORTED_FILTERS = {b"ASCII85Decode", b"A85", b"FlateDecode", b"Fl"}
TF_OPERATOR = re.compile(
    rb"/([^\s/<>]+)\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)\s+Tf\b"
)


@dataclass(frozen=True)
class TextRun:
    stream: int
    font: str
    size_pt: float


def stream_dictionary(data: bytes, start: int) -> bytes:
    """Read a direct, flat dictionary immediately preceding a stream.

    Nested dictionaries and strings are deliberately refused: extracting a
    filter from either with a name regex could silently select the wrong key.
    Stream delimiting remains regex-based, rather than resolving /Length.
    """
    header = data[:start].rstrip(PDF_SPACE)
    if not header.endswith(b">>"):
        raise ValueError("missing direct stream dictionary")
    tokens = list(re.finditer(rb"<<|>>", header))
    depth = 0
    for token in reversed(tokens):
        depth += 1 if token.group() == b">>" else -1
        if depth == 0:
            dictionary = header[token.start():]
            if (dictionary.count(b"<<") != 1 or b"(" in dictionary
                    or b"%" in dictionary or b"#" in dictionary):
                raise ValueError("nested/string/comment/escaped-name stream dictionaries are unsupported")
            return dictionary
    raise ValueError("malformed stream dictionary")


def filter_chain(dictionary: bytes) -> list[bytes]:
    """Accept a direct name or complete array of supported filter names."""
    if re.search(rb"/Type\s*/(?:ObjStm|XRef)\b", dictionary):
        raise ValueError("object/xref streams are unsupported")
    if re.search(rb"/DecodeParms\b", dictionary):
        # Predictor dictionaries and indirect parameters need a real PDF parser.
        if not re.search(rb"/DecodeParms\s+null(?=\s|/|>>)", dictionary):
            raise ValueError("non-null or indirect DecodeParms are unsupported")
    keys = list(FILTER_KEY.finditer(dictionary))
    if not keys:
        return []
    if len(keys) != 1:
        raise ValueError("duplicate Filter entries")
    value = dictionary[keys[0].end():].lstrip(PDF_SPACE)
    if value.startswith(b"["):
        end = value.find(b"]")
        if end < 0:
            raise ValueError("unterminated Filter array")
        body = value[1:end]
        names = FILTER_NAME.findall(body)
        if not names or FILTER_NAME.sub(b"", body).strip(PDF_SPACE):
            raise ValueError("malformed Filter array")
    else:
        match = FILTER_NAME.match(value)
        if not match or (value[match.end():match.end()+1] not in (b"", b">", b"/")
                         and value[match.end()] not in PDF_SPACE):
            raise ValueError("missing, malformed or indirect Filter value")
        names = [match.group(1)]
    unknown = [name.decode("ascii", errors="replace") for name in names if name not in SUPPORTED_FILTERS]
    if unknown:
        raise ValueError("unsupported PDF filter chain: " + ", ".join(unknown))
    return names


def decode_payload(payload: bytes, filters: list[bytes]) -> bytes:
    for name in filters:
        try:
            if name in (b"ASCII85Decode", b"A85"):
                # PDF ASCII85 requires ~>; ReportLab omits the optional <~.
                payload = base64.a85decode(payload.strip(PDF_SPACE), adobe=True,
                                          ignorechars=PDF_SPACE)
            else:
                decoder = zlib.decompressobj()
                decoded = decoder.decompress(payload) + decoder.flush()
                if not decoder.eof or decoder.unused_data.strip(PDF_SPACE):
                    raise ValueError("incomplete Flate stream or non-whitespace trailing data")
                payload = decoded
        except (ValueError, zlib.error) as exc:
            raise ValueError(f"{name.decode('ascii')} failed: {exc}") from exc
    return payload


def decoded_streams(data: bytes) -> tuple[list[bytes], list[str]]:
    streams: list[bytes] = []
    warnings: list[str] = []
    if re.search(rb"/Encrypt\b", data):
        return [], ["encrypted PDFs are unsupported"]
    cursor = 0
    stream_number = 0
    while True:
        match = STREAM_START.search(data, cursor)
        if not match:
            break
        stream_number += 1
        end = data.find(b"endstream", match.end())
        if end < 0:
            warnings.append(f"stream {stream_number} has no endstream marker")
            break
        # Keep the raw stream bytes. zlib accepts PDF's trailing line break,
        # while stripping could accidentally remove a legitimate compressed
        # byte that happens to equal CR or LF.
        payload = data[match.end() : end]
        try:
            dictionary = stream_dictionary(data, match.start())
            payload = decode_payload(payload, filter_chain(dictionary))
        except ValueError as exc:
            warnings.append(f"stream {stream_number} {exc}")
            cursor = end + len(b"endstream")
            continue
        streams.append(payload)
        cursor = end + len(b"endstream")
    return streams, warnings


def audit_pdf(data: bytes, minimum_pt: float = 5.0) -> dict[str, object]:
    streams, warnings = decoded_streams(data)
    runs: list[TextRun] = []
    for stream_index, stream in enumerate(streams, 1):
        for match in TF_OPERATOR.finditer(stream):
            try:
                font = match.group(1).decode("ascii", errors="replace")
                size = float(match.group(2))
            except ValueError:
                continue
            if size > 0:
                runs.append(TextRun(stream=stream_index, font=font, size_pt=size))
    below = [run for run in runs if run.size_pt < minimum_pt]
    return {
        "auditable": bool(runs) and not warnings,
        "decoding_complete": not warnings,
        "partial_text_found": bool(runs) and bool(warnings),
        "minimum_required_pt": minimum_pt,
        "minimum_found_pt": min((run.size_pt for run in runs), default=None),
        "text_run_count": len(runs),
        "below_minimum_count": len(below),
        "below_minimum": [asdict(run) for run in below],
        "warnings": warnings,
    }


def render_text(path: Path, result: dict[str, object]) -> str:
    lines = [
        "Nature Figure PDF Text Audit",
        f"pdf: {path}",
        f"minimum required: {result['minimum_required_pt']:g} pt",
    ]
    if not result["auditable"]:
        reason = ("stream decoding is incomplete; partial text cannot establish a pass"
                  if result["warnings"] else "no supported Tf text operators were found")
        lines.append(f"verdict: NOT AUDITABLE — {reason}")
    else:
        lines.extend(
            [
                f"minimum found: {result['minimum_found_pt']:g} pt",
                f"text runs: {result['text_run_count']}",
                f"below minimum: {result['below_minimum_count']}",
                f"verdict: {'FAIL' if result['below_minimum_count'] else 'PASS'}",
            ]
        )
    for run in result["below_minimum"]:
        lines.append(f"  - stream {run['stream']}: /{run['font']} {run['size_pt']:g} Tf")
    for warning in result["warnings"]:
        lines.append(f"warning: {warning}")
    lines.append("note: regex Tf scanning is not a general PDF parser; indirect filters, object streams, "
                 "encryption and predictors are unsupported. Stream markers are not resolved by /Length. "
                 "Final-size inspection and arbitrary PDF transforms remain outside this check.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="exported PDF figure")
    parser.add_argument("--min-pt", type=float, default=5.0, help="minimum allowed Tf font size in points")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.min_pt <= 0:
        print("error: --min-pt must be positive", file=sys.stderr)
        return 2
    try:
        data = args.pdf.read_bytes()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not data.startswith(b"%PDF-"):
        print(f"error: not a PDF file: {args.pdf}", file=sys.stderr)
        return 2
    result = audit_pdf(data, minimum_pt=args.min_pt)
    if args.json:
        print(json.dumps({"pdf": str(args.pdf), **result}, indent=2, ensure_ascii=False))
    else:
        print(render_text(args.pdf, result))
    if not result["auditable"]:
        return 2
    return 1 if result["below_minimum_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
