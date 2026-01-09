import streamlit as st
import pandas as pd
import json

from ui.state import get_report, sort_findings
from models import (
    ReportData,
    Finding,
    WalkthroughStep,
    CodeBlock,
    EvidenceImage,
    normalize_severity,
    SEVERITY_ORDER,
)
from report.pdf import build_pdf


def render():
    report = get_report()

    st.header("Preview & Export")

    st.subheader("Web Preview: Summary of Findings")
    if report.findings:
        df_sum = pd.DataFrame(
            [
                {
                    "Severity": normalize_severity(f.severity),
                    "Title": f.title,
                    "Host": f.host,
                    "CVSS": f.cvss,
                    "CVE": ", ".join(f.cve),
                    "Source": f.source,
                }
                for f in report.findings
            ]
        )

        sev_filter = st.multiselect("Filter", SEVERITY_ORDER, default=SEVERITY_ORDER, key="prev_sev")
        df_sum = df_sum[df_sum["Severity"].isin(sev_filter)]
        st.dataframe(df_sum, use_container_width=True)
    else:
        st.info("No findings yet.")

    st.markdown("---")
    st.subheader("Backup / Restore")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download report.json",
            json.dumps(report.to_dict(), indent=2),
            file_name="report.json",
            mime="application/json",
        )

    with col2:
        up_json = st.file_uploader("Load JSON backup", type=["json"])
        if up_json and st.button("Load JSON"):
            data = json.loads(up_json.getvalue().decode("utf-8"))

            r = ReportData(
                candidate_name=data.get("candidate_name", ""),
                candidate_title=data.get("candidate_title", ""),
                candidate_email=data.get("candidate_email", ""),
                customer_name=data.get("customer_name", ""),
                version=data.get("version", "1.0"),
                dates=data.get("dates", ""),
                approach=data.get("approach", "Black Box"),
                engagement_contacts=data.get("engagement_contacts", []) or [],
                scope=data.get("scope", []) or [],
                executive_summary=data.get("executive_summary", ""),
                remediation_short=data.get("remediation_short", ""),
                remediation_medium=data.get("remediation_medium", ""),
                remediation_long=data.get("remediation_long", ""),

                # ✅ Appendix (8.2 - 8.7) - keep compatibility with older JSON backups
                appendix_host_service=data.get("appendix_host_service", []) or [],
                appendix_subdomains=data.get("appendix_subdomains", []) or [],
                appendix_exploited_hosts=data.get("appendix_exploited_hosts", []) or [],
                appendix_compromised_users=data.get("appendix_compromised_users", []) or [],
                appendix_cleanup=data.get("appendix_cleanup", []) or [],
                appendix_flags=data.get("appendix_flags", []) or [],
            )

            # Findings
            for f in data.get("findings", []) or []:
                ff = Finding(
                    id=f.get("id", ""),
                    severity=f.get("severity", "Info"),
                    title=f.get("title", ""),
                    host=f.get("host", ""),
                    port=f.get("port", ""),
                    service=f.get("service", ""),
                    cvss=f.get("cvss", None),
                    cve=f.get("cve", []) or [],
                    description=f.get("description", ""),
                    impact=f.get("impact", ""),
                    recommendation=f.get("recommendation", ""),
                    references=f.get("references", []) or [],
                    source=f.get("source", "manual"),
                    raw=f.get("raw", {}) or {},
                )

                for img in f.get("evidence_images", []) or []:
                    ff.evidence_images.append(EvidenceImage(**img))
                for cb in f.get("code_blocks", []) or []:
                    ff.code_blocks.append(CodeBlock(**cb))

                r.findings.append(ff)

            # Walkthrough
            for s in data.get("walkthrough", []) or []:
                ws = WalkthroughStep(
                    id=s.get("id", ""),
                    name=s.get("name", ""),
                    description=s.get("description", ""),
                )
                for img in s.get("images", []) or []:
                    ws.images.append(EvidenceImage(**img))
                for cb in s.get("code_blocks", []) or []:
                    ws.code_blocks.append(CodeBlock(**cb))
                r.walkthrough.append(ws)

            st.session_state.report = r
            sort_findings(r)
            st.success("Loaded.")
            st.rerun()

    st.markdown("---")
    st.subheader("Generate PDF (HTB-style)")
    if st.button("Build PDF"):
        pdf_bytes = build_pdf(report)
        st.download_button(
            "⬇️ Download HTB-CPTS-Report.pdf",
            pdf_bytes,
            file_name="HTB-CPTS-Report.pdf",
            mime="application/pdf",
        )