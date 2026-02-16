from __future__ import annotations

from datetime import datetime
from typing import List, Dict


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_audit_pdf(title: str, entries: List[Dict[str, str]]) -> bytes:
    """
    Minimal single-page PDF generator without external dependencies.
    """
    lines = [f"{title} - {datetime.utcnow().isoformat()}", ""]
    for entry in entries:
        line = f"[{entry.get('created_at','')}] {entry.get('event_type','')}: {entry.get('message','')}"
        lines.append(line[:120])
    if not lines:
        lines = [title, "No audit events found."]

    content_lines = []
    y = 760
    for line in lines:
        content_lines.append(f"1 0 0 1 50 {y} Tm ({_escape_pdf_text(line)}) Tj")
        y -= 16
        if y < 60:
            break

    content = "\n".join(["BT", "/F1 12 Tf"] + content_lines + ["ET"])

    objects = []
    objects.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj")
    objects.append("2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj")
    objects.append(
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj"
    )
    objects.append("4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj")
    objects.append(
        f"5 0 obj << /Length {len(content.encode('utf-8'))} >> stream\n{content}\nendstream endobj"
    )

    xref_positions = []
    pdf = ["%PDF-1.4"]
    offset = len("%PDF-1.4\n")
    for obj in objects:
        xref_positions.append(offset)
        pdf.append(obj)
        offset += len(obj.encode("utf-8")) + 1

    xref_start = offset
    xref = ["xref", f"0 {len(objects) + 1}", "0000000000 65535 f "]
    for pos in xref_positions:
        xref.append(f"{pos:010d} 00000 n ")

    trailer = [
        "trailer",
        f"<< /Size {len(objects) + 1} /Root 1 0 R >>",
        "startxref",
        str(xref_start),
        "%%EOF",
    ]

    pdf_data = "\n".join(pdf + xref + trailer).encode("utf-8")
    return pdf_data
