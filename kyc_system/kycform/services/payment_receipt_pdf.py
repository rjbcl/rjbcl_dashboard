from datetime import datetime


def _escape_pdf_text(value):
    text = str(value or "")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_lines(text, max_chars=68):
    text = str(text or "")
    if not text:
        return [""]
    lines = []
    for paragraph in text.splitlines() or [""]:
        chunk = paragraph.strip()
        if not chunk:
            lines.append("")
            continue
        while len(chunk) > max_chars:
            split_at = chunk.rfind(" ", 0, max_chars)
            if split_at <= 0:
                split_at = max_chars
            lines.append(chunk[:split_at].strip())
            chunk = chunk[split_at:].strip()
        lines.append(chunk)
    return lines or [""]


def _build_pdf_stream(lines):
    content = ["BT", "/F1 12 Tf", "50 792 Td"]
    first = True
    for line in lines:
        safe_line = _escape_pdf_text(line)
        if first:
            content.append(f"({safe_line}) Tj")
            first = False
        else:
            content.append("T*")
            content.append(f"({safe_line}) Tj")
    content.append("ET")
    return "\n".join(content).encode("latin-1", errors="ignore")


def build_payment_receipt_pdf(context):
    lines = [
        "RJBCL Payment Receipt",
        f"Policy No: {context.get('policy_no', '-')}",
        f"Client Name: {context.get('client_name', '-')}",
        f"Receipt Date: {context.get('paid_date', '-')}",
        f"Receipt Type: {context.get('installment_type', '-')}",
        f"Paid Amount: NPR {context.get('paid_amount', 0):,.2f}",
        f"Premium: NPR {context.get('premium', 0):,.2f}",
        f"Plan Name: {context.get('plan_name', '-')}",
        f"Term: {context.get('term', '-')}",
        f"Frequency: {context.get('policy_premium_frequency', '-')}",
        f"FUP: {context.get('fup', '-')}",
        "",
        "This receipt is generated from the policy payment history view.",
        f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(_wrap_lines(line))

    stream = _build_pdf_stream(wrapped_lines)
    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        (
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ).encode("latin-1")
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        (
            f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1")
            + stream
            + b"\nendstream endobj\n"
        )
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        (
            "trailer << /Size {size} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
        ).format(size=len(offsets), xref=xref_pos).encode("latin-1")
    )
    return bytes(pdf)
