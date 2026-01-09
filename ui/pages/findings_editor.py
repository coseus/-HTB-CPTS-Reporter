import streamlit as st
import pandas as pd

from ui.state import get_report, sort_findings
from models import Finding, CodeBlock, EvidenceImage, normalize_severity, SEVERITY_ORDER
from utils.images import b64_from_upload, resize_image_b64

CODE_LANGS = [
    "text", "bash", "powershell", "cmd",
    "python", "php", "javascript", "sql",
    "http", "curl", "nmap", "json", "xml",
]

def render():
    report = get_report()

    st.header("Findings Editor (Fast)")

    # ---- Add Finding (Form) ----
    st.subheader("Add Finding")
    with st.form("add_finding_form", clear_on_submit=True):
        r1c1, r1c2, r1c3 = st.columns([2, 1, 1])
        with r1c1:
            nf_title = st.text_input("Title *")
        with r1c2:
            nf_sev = st.selectbox("Severity", SEVERITY_ORDER, index=SEVERITY_ORDER.index("Info"))
        with r1c3:
            nf_cvss = st.number_input("CVSS", min_value=0.0, max_value=10.0, value=0.0, step=0.1)

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            nf_host = st.text_input("Host")
        with r2c2:
            nf_port = st.text_input("Port")
        with r2c3:
            nf_service = st.text_input("Service")

        nf_cves = st.text_input("CVE (comma-separated)")
        nf_desc = st.text_area("Description / Root Cause", height=110)
        nf_impact = st.text_area("Impact", height=90)
        nf_reco = st.text_area("Recommendation", height=90)

        submit = st.form_submit_button("➕ Create Finding")

    if submit:
        f = Finding(
            severity=nf_sev,
            title=(nf_title.strip() or "New Finding"),
            host=nf_host.strip(),
            port=nf_port.strip(),
            service=nf_service.strip(),
            cvss=(nf_cvss if nf_cvss > 0 else None),
            cve=[x.strip() for x in nf_cves.split(",") if x.strip()],
            description=nf_desc,
            impact=nf_impact,
            recommendation=nf_reco,
            source="manual",
        )
        report.findings.append(f)
        sort_findings(report)
        st.session_state["selected_finding_id"] = f.id  # auto-select
        st.success("Finding created.")
        st.rerun()

    st.markdown("---")

    if not report.findings:
        st.info("No findings yet.")
        return

    # ---- Filters ----
    cA, cB, cC = st.columns([2, 2, 1])
    with cA:
        sev_filter = st.multiselect("Filter by severity", SEVERITY_ORDER, default=SEVERITY_ORDER, key="fe_sev")
    with cB:
        search = st.text_input("Search (title/host/cve)", "", key="fe_search")
    with cC:
        if st.button("Normalize + sort"):
            for f in report.findings:
                f.severity = normalize_severity(f.severity)
            sort_findings(report)
            st.rerun()

    def match(f: Finding):
        if normalize_severity(f.severity) not in sev_filter:
            return False
        hay = f"{f.title} {f.host} {' '.join(f.cve)}".lower()
        return search.lower().strip() in hay

    filtered = [f for f in report.findings if match(f)]

    # ---- Pagination ----
    p1, p2 = st.columns([1, 2])
    with p1:
        page_size = st.selectbox("Page size", [10, 20, 50], index=1, key="fe_page_size")
    total = len(filtered)
    pages = max(1, (total + page_size - 1) // page_size)
    with p2:
        page_no = st.number_input("Page", min_value=1, max_value=pages, value=1, step=1, key="fe_page_no")

    start = (page_no - 1) * page_size
    end = min(start + page_size, total)
    page_items = filtered[start:end]
    st.caption(f"Showing {start+1}-{end} of {total} (page {page_no}/{pages})")

    # ---- List table (fast) ----
    df_list = pd.DataFrame([{
        "ID": f.id,
        "Severity": normalize_severity(f.severity),
        "Title": f.title,
        "Host": f.host,
        "CVSS": f.cvss,
        "CVE": ", ".join(f.cve),
    } for f in page_items]).set_index("ID")

    st.dataframe(df_list, use_container_width=True, hide_index=True)

    # ---- Select one finding to edit ----
    def fmt(fid: str):
        x = next((z for z in page_items if z.id == fid), None)
        if not x:
            return fid
        return f"{normalize_severity(x.severity)} | {x.title} | {x.host}"

    options = [f.id for f in page_items]
    if not options:
        st.info("No findings match the filters.")
        return

    selected_id = st.selectbox(
        "Select a finding to edit",
        options=options,
        format_func=fmt,
        key="selected_finding_id",
    )

    sel = next((x for x in report.findings if x.id == selected_id), None)
    if not sel:
        st.warning("Selected finding not found.")
        return

    st.markdown("## Edit Finding")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        sel.title = st.text_input("Title", sel.title, key=f"{sel.id}_title_one")
        sel.description = st.text_area("Description / Root Cause", sel.description, height=140, key=f"{sel.id}_desc_one")
        sel.impact = st.text_area("Impact", sel.impact, height=120, key=f"{sel.id}_impact_one")
        sel.recommendation = st.text_area("Recommendation", sel.recommendation, height=120, key=f"{sel.id}_reco_one")
    with c2:
        sel.severity = st.selectbox(
            "Severity",
            SEVERITY_ORDER,
            index=SEVERITY_ORDER.index(normalize_severity(sel.severity)),
            key=f"{sel.id}_sev_one",
        )
        sel.host = st.text_input("Host", sel.host, key=f"{sel.id}_host_one")
        sel.port = st.text_input("Port", sel.port, key=f"{sel.id}_port_one")
        sel.service = st.text_input("Service", sel.service, key=f"{sel.id}_svc_one")
        cvss_val = float(sel.cvss) if sel.cvss is not None else 0.0
        cvss_val = st.number_input("CVSS", 0.0, 10.0, cvss_val, 0.1, key=f"{sel.id}_cvss_one")
        sel.cvss = cvss_val if cvss_val > 0 else None
    with c3:
        cves = st.text_area("CVE (comma-separated)", ", ".join(sel.cve), height=70, key=f"{sel.id}_cves_one")
        sel.cve = [x.strip() for x in cves.split(",") if x.strip()]
        if st.button("Delete Finding", key=f"{sel.id}_del_one"):
            report.findings = [x for x in report.findings if x.id != sel.id]
            sort_findings(report)
            st.rerun()

    if st.button("💾 Save & re-sort", key=f"{sel.id}_save_one"):
        sort_findings(report)
        st.toast("Saved & sorted.")
        st.rerun()

    # ---- Evidence Images ----
    st.markdown("### Evidence Images")
    show_imgs = st.checkbox("Show image previews", value=False, key=f"{sel.id}_show_imgs")

    img_up = st.file_uploader(
        "Upload image(s) (then click Attach)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key=f"{sel.id}_imgup",
    )
    if st.button("📎 Attach uploaded images", key=f"{sel.id}_attach_imgs") and img_up:
        for u in img_up:
            name, mime, b64 = b64_from_upload(u)
            b64 = resize_image_b64(b64, max_w=1100, max_h=800)
            sel.evidence_images.append(EvidenceImage(name=name, mime=mime, b64=b64))
        st.rerun()

    for img in list(sel.evidence_images):
        cols = st.columns([2, 2, 1])
        with cols[0]:
            if show_imgs:
                st.image(f"data:{img.mime};base64,{img.b64}", caption=img.name, use_container_width=True)
            else:
                st.write(img.name)
        with cols[1]:
            img.caption = st.text_input("Caption", img.caption, key=f"{sel.id}_{img.id}_cap")
        with cols[2]:
            if st.button("Remove", key=f"{sel.id}_{img.id}_rm"):
                sel.evidence_images = [x for x in sel.evidence_images if x.id != img.id]
                st.rerun()

    # ---- Code Blocks ----
    st.markdown("### Code Blocks")
    if st.button("Add Code Block", key=f"{sel.id}_addcb"):
        sel.code_blocks.append(CodeBlock(language="text", code=""))
        st.rerun()

    for cb in list(sel.code_blocks):
        ccb1, ccb2 = st.columns([1, 4])
        with ccb1:
            cb.language = st.selectbox(
                "Language",
                CODE_LANGS,
                index=CODE_LANGS.index(cb.language) if cb.language in CODE_LANGS else 0,
                key=f"{sel.id}_{cb.id}_lang",
            )
            if st.button("Remove Block", key=f"{sel.id}_{cb.id}_rmcb"):
                sel.code_blocks = [x for x in sel.code_blocks if x.id != cb.id]
                st.rerun()
        with ccb2:
            cb.code = st.text_area(
                "Code (paste here; whitespace preserved in PDF)",
                cb.code,
                height=160,
                key=f"{sel.id}_{cb.id}_code",
            )
            if cb.code.strip():
                st.code(cb.code, language=cb.language or "text")
