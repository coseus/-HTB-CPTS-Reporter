from io import BytesIO
from copy import deepcopy
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, Preformatted
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas as rl_canvas
import base64, io
from PIL import Image as PILImage

from report.styles import (
    build_styles, HTB_BG, HTB_GREEN, HTB_TABLE_HDR, HTB_TABLE_HDR_TXT,
    HTB_TABLE_ROW, HTB_TABLE_ROW2
)
from models import ReportData, SEVERITY_ORDER, normalize_severity

CONF_TEXT_1 = (
    "This penetration testing report contains confidential information intended solely "
    "for the client organization. Unauthorized access, distribution, disclosure, or copying "
    "of this document or any information contained herein is strictly prohibited. "
    "All findings, methodologies, and artifacts are the intellectual property of the "
    "security testing provider unless otherwise stated."
)
CONF_TEXT_2 = (
    "Findings are provided for informational purposes only and represent the system state at the time of testing only. "
    "The client is solely responsible for implementing and verifying any remediation actions. "
    "The testing team disclaims all liability for any damages resulting from the use of this report or the authorized testing activities. "
    "This penetration test was conducted exclusively in accordance with the Rules of Engagement and Statement of Work signed by the Client. "
    "No warranties of any kind, express or implied, are provided. "
    "The Testing Team and its personnel shall not be held liable for any direct, indirect, incidental, "
    "consequential, or punitive damages arising from the use or misuse of this report, its findings, or any actions taken as a result thereof. "
    "The report is delivered “as is”."
)

def _bg_header_footer(c: rl_canvas.Canvas, doc):
    w, h = A4
    c.saveState()
    c.setFillColor(HTB_BG)
    c.rect(0, 0, w, h, stroke=0, fill=1)

    # top dotted line
    c.setStrokeColor(HTB_GREEN)
    c.setLineWidth(1)
    c.setDash(1, 3)
    c.line(20*mm, h-22*mm, w-20*mm, h-22*mm)
    c.setDash()

    # footer
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(20*mm, 12*mm, "CONFIDENTIAL")
    c.setFont("Helvetica", 9)
    c.drawCentredString(w/2, 12*mm, "HTB CPTS")
    c.drawRightString(w-20*mm, 12*mm, str(doc.page))
    c.restoreState()

class Doc(BaseDocTemplate):
    def __init__(self, buff, **kw):
        super().__init__(buff, pagesize=A4, **kw)
        frame = Frame(
            20*mm, 18*mm, A4[0]-40*mm, A4[1]-50*mm,
            leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0
        )
        tpl = PageTemplate(id="htb", frames=[frame], onPage=_bg_header_footer)
        self.addPageTemplates([tpl])
        self._heading_count = 0

    # IMPORTANT: reset per multiBuild pass so TOC keys stay stable
    def beforeDocument(self):
        self._heading_count = 0

    def afterFlowable(self, flowable):
        # Register headings for TOC + create bookmarks so TOC can resolve
        if isinstance(flowable, Paragraph):
            style = getattr(flowable, "style", None)
            name = getattr(style, "name", "")
            text = flowable.getPlainText()

            # Only these styles go into TOC
            if name == "htb_h1":
                level = 0
            elif name == "htb_h2":
                level = 1
            else:
                return

            key = f"toc_{self._heading_count}"
            self._heading_count += 1

            self.canv.bookmarkPage(key)
            try:
                self.canv.addOutlineEntry(text, key, level=level, closed=False)
            except Exception:
                pass

            self.notify("TOCEntry", (level, text, self.page, key))

def _severity_counts(findings_dicts):
    counts = {k: 0 for k in SEVERITY_ORDER}
    for f in findings_dicts:
        sev = normalize_severity(f.get("severity", "Info"))
        counts[sev] = counts.get(sev, 0) + 1
    return counts

def _table(data, col_widths=None):
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HTB_TABLE_HDR),
        ("TEXTCOLOR", (0, 0), (-1, 0), HTB_TABLE_HDR_TXT),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#1A2438")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])
    for r in range(1, len(data)):
        style.add("BACKGROUND", (0, r), (-1, r), HTB_TABLE_ROW if r % 2 == 1 else HTB_TABLE_ROW2)
    t.setStyle(style)
    return t

def _img_from_b64(b64: str, max_w_pt: float):
    raw = base64.b64decode(b64)
    pil = PILImage.open(io.BytesIO(raw))
    w, h = pil.size
    scale = min(max_w_pt / w, 1.0)
    out = io.BytesIO()
    pil.save(out, format="PNG", optimize=True)
    out.seek(0)
    img = Image(out)
    img.drawWidth = w * scale
    img.drawHeight = h * scale
    return img

def _shorten(s: str, max_len: int = 70) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"

def _safe_br(s: str) -> str:
    return (s or "").replace("\n", "<br/>")

def build_pdf(report: ReportData) -> bytes:
    styles = build_styles()
    buff = BytesIO()
    doc = Doc(buff)

    # Cover styles (centered)
    cover_title = deepcopy(styles["title"])
    cover_p = deepcopy(styles["p"])
    cover_muted = deepcopy(styles["muted"])
    cover_title.alignment = TA_CENTER
    cover_p.alignment = TA_CENTER
    cover_muted.alignment = TA_CENTER

    # TOC styles
    toc1 = deepcopy(styles["p"])
    toc2 = deepcopy(styles["muted"])
    toc1.fontSize = 10
    toc2.fontSize = 9

    # Walkthrough step heading style (indented visually, but still name=htb_h2 so it appears in TOC)
    step_h2 = deepcopy(styles["h2"])
    step_h2.leftIndent = 6 * mm
    step_h2.spaceBefore = 6
    step_h2.spaceAfter = 2

    story = []

    # ---------------- Cover (centered, do NOT use htb_h1/htb_h2)
    story.append(Spacer(1, 55*mm))
    story.append(Paragraph("HACKTHEBOX", cover_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Penetration Test", cover_p))
    story.append(Paragraph("Report of Findings", cover_p))
    story.append(Spacer(1, 8))
    story.append(Paragraph("HTB Certified Penetration Testing Specialist (CPTS) Exam Report", cover_muted))
    story.append(Spacer(1, 22))

    story.append(Paragraph(f"<b>Candidate Name:</b> {report.candidate_name or 'TODO Candidate Name'}", cover_p))
    story.append(Paragraph(f"<b>Customer:</b> {report.customer_name or 'TODO Customer Ltd.'}", cover_p))
    story.append(Paragraph(f"<b>Version:</b> {report.version or '1.0'}", cover_p))
    if report.dates:
        story.append(Paragraph(f"<b>Dates:</b> {report.dates}", cover_p))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>CONFIDENTIAL</b>", cover_p))
    story.append(PageBreak())

    # ---------------- TOC
    story.append(Paragraph("Table of Contents", styles["h1"]))
    toc = TableOfContents()
    toc.levelStyles = [toc1, toc2]
    story.append(toc)
    story.append(PageBreak())

    # 1 Statement of Confidentiality
    story.append(Paragraph("1 Statement of Confidentiality", styles["h1"]))
    story.append(Paragraph(CONF_TEXT_1, styles["p"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(CONF_TEXT_2, styles["p"]))
    story.append(PageBreak())

    # 2 Engagement Contacts (two tables)
    story.append(Paragraph("2 Engagement Contacts", styles["h1"]))

    all_rows = report.engagement_contacts or []
    customer_rows = [r for r in all_rows if r.get("type") == "Customer"]
    assessor_rows = [r for r in all_rows if r.get("type") == "Assessor"]

    # 2.1 Customer Contacts
    story.append(Paragraph("2.1 Customer Contacts", styles["h2"]))
    cust_tbl = [["Name", "Title", "Email"]]
    if customer_rows:
        for r in customer_rows:
            name = r.get("name", "") or (report.customer_name or "TODO Customer Contact")
            cust_tbl.append([name, r.get("title", "") or "", r.get("email", "") or ""])
    else:
        cust_tbl.append([report.customer_name or "TODO Customer Contact", "", ""])
    story.append(_table(cust_tbl, col_widths=[65*mm, 55*mm, 60*mm]))
    story.append(Spacer(1, 10))

    # 2.2 Assessor Contacts
    story.append(Paragraph("2.2 Assessor Contacts", styles["h2"]))
    as_tbl = [["Name", "Title", "Email"]]
    if assessor_rows:
        for r in assessor_rows:
            name = r.get("name") or (report.candidate_name or "Assessor Name")
            title = r.get("title") or (getattr(report, "candidate_title", "") or "")
            email = r.get("email") or (getattr(report, "candidate_email", "") or "")
            as_tbl.append([name, title, email])
    else:
        as_tbl.append([
            report.candidate_name or "Assessor Name",
            getattr(report, "candidate_title", "") or "",
            getattr(report, "candidate_email", "") or "",
        ])
    story.append(_table(as_tbl, col_widths=[65*mm, 55*mm, 60*mm]))
    story.append(PageBreak())

    # 3 Executive Summary
    story.append(Paragraph("3 Executive Summary", styles["h1"]))
    story.append(Paragraph(
        f"{report.customer_name or 'TODO Customer Ltd.'} (“Customer” herein) contracted {report.candidate_name or 'TODO Candidate Name'} "
        "to perform a Network Penetration Test to identify security weaknesses, determine the impact, "
        "document findings, and provide remediation recommendations.",
        styles["p"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.1 Approach", styles["h2"]))
    story.append(Paragraph(
        f"{report.candidate_name or 'TODO Candidate Name'} performed testing under a “{report.approach or 'Black Box'}” approach. "
        f"{report.dates or ''}".strip(),
        styles["p"]
    ))

    story.append(Paragraph("3.2 Scope", styles["h2"]))
    if report.scope:
        scope_tbl = [["Host/URL/IP Address", "Description"]] + [[r.get("asset",""), r.get("description","")] for r in report.scope]
        story.append(_table(scope_tbl, col_widths=[70*mm, 110*mm]))
    else:
        story.append(Paragraph("TODO: Fill in scope assets (IPs, ranges, domains).", styles["p"]))

    story.append(Paragraph("3.3 Assessment Overview and Recommendations", styles["h2"]))
    f_dicts = [f.to_dict() for f in (report.findings or [])]
    counts = _severity_counts(f_dicts)
    total = sum(counts.values())
    story.append(Paragraph(
        f"During the penetration test, {report.candidate_name or 'the assessor'} identified {total} findings. "
        f"Critical: {counts['Critical']}, High: {counts['High']}, Medium: {counts['Medium']}, "
        f"Low: {counts['Low']}, Info: {counts['Info']}.",
        styles["p"]
    ))
    if (report.executive_summary or "").strip():
        story.append(Spacer(1, 6))
        story.append(Paragraph(_safe_br(report.executive_summary), styles["p"]))
    story.append(PageBreak())

    # 4 Assessment Summary
    story.append(Paragraph("4 Network Penetration Test Assessment Summary", styles["h1"]))
    story.append(Paragraph("4.1 Summary of Findings", styles["h2"]))

    ordered = sorted(
        f_dicts,
        key=lambda x: (SEVERITY_ORDER.index(normalize_severity(x.get("severity","Info"))), (x.get("host","") or ""), (x.get("title","") or ""))
    )

    summary_tbl = [["#", "Severity", "Finding Name", "Host"]]
    for i, f in enumerate(ordered, start=1):
        summary_tbl.append([
            str(i),
            normalize_severity(f.get("severity","Info")),
            _shorten(f.get("title",""), 70),
            f.get("host","")
        ])
    story.append(_table(summary_tbl, col_widths=[10*mm, 25*mm, 110*mm, 35*mm]))
    story.append(Spacer(1, 10))

    by_host = {}
    for f in ordered:
        by_host.setdefault(f.get("host","unknown") or "unknown", []).append(f)

    story.append(Paragraph("4.2 Summary of Findings per host", styles["h2"]))
    per_host_tbl = [["Host", "Critical", "High", "Medium", "Low", "Info", "Total"]]
    for host, flist in sorted(by_host.items(), key=lambda kv: kv[0]):
        c = _severity_counts(flist)
        per_host_tbl.append([host, c["Critical"], c["High"], c["Medium"], c["Low"], c["Info"], sum(c.values())])
    story.append(_table(per_host_tbl, col_widths=[55*mm, 18*mm, 18*mm, 18*mm, 18*mm, 18*mm, 18*mm]))
    story.append(PageBreak())

    # 5 Walkthrough (hierarchical numbering + indented steps)
    story.append(Paragraph("5 Internal Network Compromise Walkthrough", styles["h1"]))
    story.append(Paragraph("5.1 Detailed Walkthrough", styles["h2"]))
    story.append(Spacer(1, 6))

    if not report.walkthrough:
        story.append(Paragraph("TODO: Add walkthrough steps (name, description, code blocks, screenshots).", styles["p"]))
    else:
        for idx, step in enumerate(report.walkthrough, start=1):
            # 5.1.1, 5.1.2, ...
            story.append(Paragraph(f"5.1.{idx} {step.name or 'Step'}", step_h2))

            if (step.description or "").strip():
                story.append(Paragraph(_safe_br(step.description), styles["p"]))

            for cb in (step.code_blocks or []):
                if (cb.code or "").strip():
                    story.append(Preformatted(cb.code, styles["code"]))

            for img in (step.images or []):
                if (img.b64 or "").strip():
                    story.append(Spacer(1, 6))
                    story.append(_img_from_b64(img.b64, max_w_pt=A4[0]-40*mm))
                    if (img.caption or "").strip():
                        story.append(Paragraph(img.caption, styles["muted"]))

            story.append(Spacer(1, 10))

    story.append(PageBreak())

    # 6 Remediation Summary
    story.append(Paragraph("6 Remediation Summary", styles["h1"]))
    story.append(Paragraph("6.1 Short Term", styles["h2"]))
    story.append(Paragraph(_safe_br(report.remediation_short or "TODO SHORT TERM REMEDIATION"), styles["p"]))
    story.append(Paragraph("6.2 Medium Term", styles["h2"]))
    story.append(Paragraph(_safe_br(report.remediation_medium or "TODO MEDIUM TERM REMEDIATION"), styles["p"]))
    story.append(Paragraph("6.3 Long Term", styles["h2"]))
    story.append(Paragraph(_safe_br(report.remediation_long or "TODO LONG TERM REMEDIATION"), styles["p"]))
    story.append(PageBreak())

    # 7 Technical Findings Details
    story.append(Paragraph("7 Technical Findings Details", styles["h1"]))
    for idx, f in enumerate(ordered, start=1):
        story.append(Paragraph(
            f"7.{idx} {f.get('title','Untitled')} - {normalize_severity(f.get('severity','Info'))}",
            styles["h2"]
        ))

        meta = []
        if f.get("cvss") is not None:
            meta.append(f"CVSS 3.1: {f.get('cvss')}")
        if f.get("cve"):
            meta.append("CVE: " + ", ".join(f.get("cve")))
        if meta:
            story.append(Paragraph("<br/>".join(meta), styles["muted"]))

        if f.get("description"):
            story.append(Paragraph(f"<b>Description / Root Cause</b><br/>{_safe_br(f.get('description',''))}", styles["p"]))
        if f.get("impact"):
            story.append(Paragraph(f"<b>Impact</b><br/>{_safe_br(f.get('impact',''))}", styles["p"]))
        if f.get("recommendation"):
            story.append(Paragraph(f"<b>Recommendation</b><br/>{_safe_br(f.get('recommendation',''))}", styles["p"]))

        for cb in (f.get("code_blocks") or []):
            code = cb.get("code","")
            if code.strip():
                story.append(Preformatted(code, styles["code"]))

        for img in (f.get("evidence_images") or []):
            b64 = img.get("b64","")
            if b64.strip():
                story.append(Spacer(1, 6))
                story.append(_img_from_b64(b64, max_w_pt=A4[0]-40*mm))
                cap = img.get("caption","")
                if cap.strip():
                    story.append(Paragraph(cap, styles["muted"]))

        story.append(PageBreak())

    # 8 Appendix
    story.append(Paragraph("8 Appendix", styles["h1"]))

    story.append(Paragraph("8.1 Finding Severities", styles["h2"]))
    sev_tbl = [
        ["Rating", "CVSS Score Range"],
        ["Critical", "9.0 - 10.0"],
        ["High", "7.0 - 8.9"],
        ["Medium", "4.0 - 6.9"],
        ["Low", "0.1 - 3.9"],
        ["Info", "0.0"],
    ]
    story.append(_table(sev_tbl, col_widths=[60*mm, 60*mm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Severity ratings are assigned based on CVSS score guidance and the tester’s contextual risk assessment.",
        styles["p"]
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8.2 Host & Service Discovery", styles["h2"]))
    hs = getattr(report, "appendix_host_service", []) or []
    hs_tbl = [["IP Address", "Port", "Service", "Notes"]] + [
        [r.get("ip",""), r.get("port",""), r.get("service",""), r.get("notes","")] for r in hs
    ]
    if len(hs_tbl) == 1:
        hs_tbl.append(["", "", "", ""])
    story.append(_table(hs_tbl, col_widths=[45*mm, 18*mm, 35*mm, 82*mm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8.3 Subdomain Discovery", styles["h2"]))
    subs = getattr(report, "appendix_subdomains", []) or []
    subs_tbl = [["URL", "Description", "Discovery Method"]] + [
        [r.get("url",""), r.get("description",""), r.get("method","")] for r in subs
    ]
    if len(subs_tbl) == 1:
        subs_tbl.append(["", "", ""])
    story.append(_table(subs_tbl, col_widths=[65*mm, 70*mm, 45*mm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8.4 Exploited Hosts", styles["h2"]))
    expl = getattr(report, "appendix_exploited_hosts", []) or []
    if not expl:
        hosts = sorted({(f.get("host","") or "").strip() for f in ordered if (f.get("host","") or "").strip()})
        expl = [{"host": h, "scope": "", "method": "", "notes": ""} for h in hosts] or [{"host":"","scope":"","method":"","notes":""}]
    expl_tbl = [["Host", "Scope", "Method", "Notes"]] + [
        [r.get("host",""), r.get("scope",""), r.get("method",""), r.get("notes","")] for r in expl
    ]
    story.append(_table(expl_tbl, col_widths=[55*mm, 30*mm, 35*mm, 60*mm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8.5 Compromised Users", styles["h2"]))
    users = getattr(report, "appendix_compromised_users", []) or []
    users_tbl = [["Username", "Type", "Method", "Notes"]] + [
        [r.get("username",""), r.get("type",""), r.get("method",""), r.get("notes","")] for r in users
    ]
    if len(users_tbl) == 1:
        users_tbl.append(["", "", "", ""])
    story.append(_table(users_tbl, col_widths=[50*mm, 30*mm, 45*mm, 55*mm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8.6 Changes/Host Cleanup", styles["h2"]))
    clean = getattr(report, "appendix_cleanup", []) or []
    clean_tbl = [["Host", "Scope", "Change/Cleanup Needed"]] + [
        [r.get("host",""), r.get("scope",""), r.get("change","")] for r in clean
    ]
    if len(clean_tbl) == 1:
        clean_tbl.append(["", "", ""])
    story.append(_table(clean_tbl, col_widths=[55*mm, 35*mm, 90*mm]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8.7 Flags Discovered", styles["h2"]))
    flags = getattr(report, "appendix_flags", []) or []
    flags_tbl = [["Flag#", "Host", "Flag Value", "Flag Location", "Method Used"]] + [
        [r.get("flag_no",""), r.get("host",""), r.get("flag_value",""), r.get("flag_location",""), r.get("method","")] for r in flags
    ]
    if len(flags_tbl) == 1:
        flags_tbl.append(["", "", "", "", ""])
    story.append(_table(flags_tbl, col_widths=[15*mm, 35*mm, 55*mm, 45*mm, 30*mm]))

    doc.multiBuild(story, maxPasses=20)
    buff.seek(0)
    return buff.getvalue()