# -*- coding: utf-8 -*-
"""Extract the body text of an academic PDF (excluding the references section).

Purpose: prepare clean source text for paper translation.

Behavior (improvements over naive page-header matching):
- References detection: a page is treated as the start of the references only
  when a *standalone header line* matches (e.g. "References", "REFERENCES",
  "Bibliography"). Trailing punctuation and a leading section number are
  tolerated, but a keyword appearing mid-sentence does NOT count.
- Scan order: the second half of the document is scanned first, then the first
  half, to reduce false positives on table-of-contents pages and on
  "References" mentions inside the body.
- Page numbering: PyMuPDF page indices are 0-based. The JSON output reports
  ``ref_start_page`` as a 0-based index and also includes
  ``ref_start_page_1based`` for humans.
- Scanned PDFs: if almost no text is extracted, the script exits with a clear
  message suggesting OCR, because scanned PDFs have no extractable text layer.
- Output directory: created automatically if missing.
- Errors: clear messages and a non-zero exit code (file not found, unreadable
  PDF, missing dependency).

Usage:
    python extract_pdf_body.py <pdf_path> [--out <out.txt>] [--ref-keywords ...]
    python extract_pdf_body.py --json <pdf_path>   # print only metadata as JSON

Notes (avoid repeated failures):
- Pass PDF paths that contain quotes/apostrophes in DOUBLE quotes, e.g.
  r"D:\\path\\with 'apostrophe'.pdf" -- single quotes break Python.
- Run this file directly (python script.py); do NOT inline multi-line Python
  via `python -c "..."` in PowerShell -- it fails with ScriptBlock errors.
"""
import argparse
import json
import os
import sys

# Keywords are normalized to lowercase for comparison.
DEFAULT_REF_KEYWORDS = ["references", "bibliography"]

MIN_BODY_CHARS = 100  # below this, the PDF is likely scanned/images-only


def normalize_header(line):
    """Strip whitespace, trailing punctuation and a leading section number.

    Examples:
        "References"          -> "references"
        "References."         -> "references"
        "7. References"       -> "references"
        "5.1 Bibliography:"   -> "bibliography"
    """
    line = line.strip().rstrip(".:\u3002\uff1a")
    if not line:
        return ""
    parts = line.split(None, 1)
    if parts and parts[0].rstrip(".").isdigit():
        line = parts[1].strip() if len(parts) > 1 else ""
    return line.rstrip(".:\u3002\uff1a").lower()


def is_ref_header(line, keywords):
    """True only for a standalone reference header line."""
    return normalize_header(line) in keywords


def find_ref_page(doc, keywords):
    """Return the 0-based page index where references start, or None.

    Scans the second half of the document first, then the first half.
    """
    n = doc.page_count
    if n == 0:
        return None
    scan_order = list(range(n // 2, n)) + list(range(0, n // 2))
    for i in scan_order:
        text = doc[i].get_text("text", sort=True)
        for raw in text.splitlines():
            if is_ref_header(raw, keywords):
                return i
    return None


def extract_body(pdf_path, out_path=None, ref_keywords=None):
    import pymupdf  # PyMuPDF; dependency declared in requirements.txt

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError("PDF file not found: %s" % pdf_path)

    ref_keywords = ref_keywords or DEFAULT_REF_KEYWORDS
    ref_keywords = [k.lower() for k in ref_keywords]

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        raise ValueError("Cannot open PDF (corrupt, encrypted, or not a PDF): %s" % exc)

    with doc:
        n_pages = doc.page_count
        ref_page = find_ref_page(doc, ref_keywords)
        if ref_page is None:
            ref_page = n_pages  # no refs detected -> treat all pages as body

        pages_text = []
        body_chars = 0
        for i in range(0, min(ref_page, n_pages)):
            text = doc[i].get_text("text", sort=True)
            pages_text.append("===== [PAGE %d] =====\n" % (i + 1) + text)
            body_chars += len(text)
        body = "\n".join(pages_text)

        if out_path:
            out_dir = os.path.dirname(os.path.abspath(out_path))
            os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(body)

        return {
            "pdf": pdf_path,
            "pages": n_pages,
            "ref_start_page": ref_page,          # 0-based PyMuPDF index
            "ref_start_page_1based": ref_page + 1,  # human-readable page number
            "refs_found": ref_page < n_pages,
            "body_chars": body_chars,
            "out": out_path,
            "scan_warning": (
                "Almost no text extracted; this may be a scanned PDF "
                "requiring OCR." if body_chars < MIN_BODY_CHARS else None
            ),
        }


def main():
    parser = argparse.ArgumentParser(description="Extract PDF body text before references.")
    parser.add_argument("pdf_path")
    parser.add_argument("--out", default=None, help="Output txt path (default: <pdfname>_body.txt next to input)")
    parser.add_argument("--json", action="store_true", help="Print only metadata JSON, skip body output")
    parser.add_argument("--ref-keywords", nargs="+", default=None, help="Reference section header keywords")
    args = parser.parse_args()

    try:
        out_path = args.out
        if not args.json and not out_path:
            out_path = os.path.splitext(args.pdf_path)[0] + "_body.txt"
        info = extract_body(args.pdf_path, out_path=out_path, ref_keywords=args.ref_keywords)
    except Exception as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(1)

    print(json.dumps(info, ensure_ascii=False))
    if info.get("scan_warning"):
        print("Warning: %s" % info["scan_warning"], file=sys.stderr)
    if not args.json and info.get("out"):
        print("Body written to: %s" % info["out"])


if __name__ == "__main__":
    main()
