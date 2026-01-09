import streamlit as st
import pandas as pd

from ui.state import get_report, sort_findings
from models import Finding, normalize_severity, SEVERITY_ORDER
from parsers.nessus import parse_nessus
from parsers.openvas import parse_openvas
from parsers.nmap import parse_nmap


def render():
    report = get_report()

    st.header("Import Findings")

    import_sev = st.multiselect(
        "Import only these severities",
        SEVERITY_ORDER,
        default=SEVERITY_ORDER,
        key="import_sev",
    )

    uploaded = st.file_uploader(
        "Upload Nessus / OpenVAS / Nmap files",
        type=["nessus", "xml"],
        accept_multiple_files=True,
    )

    @st.cache_data(show_spinner=False)
    def parse_files(file_specs):
        imported = []
        for name, content in file_specs:
            if name.endswith(".nessus"):
                imported += parse_nessus(content)
            elif "nmap" in name:
                imported += parse_nmap(content)
            else:
                try:
                    imported += parse_openvas(content)
                except Exception:
                    imported += parse_nmap(content)

        for f in imported:
            f.severity = normalize_severity(f.severity)
        return imported

    imported_all: list[Finding] = []
    imported_filtered: list[Finding] = []

    if uploaded:
        file_specs = [(f.name.lower(), f.getvalue()) for f in uploaded]

        with st.spinner("Parsing files..."):
            imported_all = parse_files(file_specs)

        # --- stats all ---
        counts_all = {s: 0 for s in SEVERITY_ORDER}
        for f in imported_all:
            counts_all[normalize_severity(f.severity)] += 1

        st.subheader("Parsed findings (all)")
        cols = st.columns(6)
        cols[0].metric("Total", len(imported_all))
        for i, sev in enumerate(SEVERITY_ORDER):
            cols[i if i < 5 else 5].metric(sev, counts_all[sev])

        # --- filter ---
        imported_filtered = [
            f for f in imported_all if normalize_severity(f.severity) in import_sev
        ]

        counts_f = {s: 0 for s in SEVERITY_ORDER}
        for f in imported_filtered:
            counts_f[normalize_severity(f.severity)] += 1

        st.subheader("Will be imported (after severity filter)")
        cols2 = st.columns(6)
        cols2[0].metric("Total", len(imported_filtered))
        for i, sev in enumerate(SEVERITY_ORDER):
            cols2[i if i < 5 else 5].metric(sev, counts_f[sev])

        show_preview = st.checkbox("Show preview table (can be slow)", value=False)
        if show_preview:
            df = pd.DataFrame(
                [
                    {
                        "Severity": normalize_severity(f.severity),
                        "Title": f.title,
                        "Host": f.host,
                        "CVSS": f.cvss,
                        "CVE": ", ".join(f.cve),
                        "Source": f.source,
                    }
                    for f in imported_filtered
                ]
            )
            st.dataframe(df.head(200), use_container_width=True)

        colA, colB = st.columns(2)
        with colA:
            if st.button("✅ Import filtered into report"):
                report.findings.extend(imported_filtered)
                sort_findings(report)
                st.success(f"Imported {len(imported_filtered)} findings.")
                st.rerun()

        with colB:
            if st.button("➕ Add empty finding"):
                report.findings.append(Finding(severity="Info", title="New Finding", source="manual"))
                sort_findings(report)
                st.rerun()

    else:
        st.info("Upload one or more files to see preview and import options.")

    # ---- existing findings (bulk delete) ----
    st.markdown("---")
    st.subheader("Current Report Findings")

    if not report.findings:
        st.info("No findings in report yet.")
        return

    df_report = pd.DataFrame(
        [
            {
                "ID": f.id,
                "Select": False,
                "Severity": normalize_severity(f.severity),
                "Title": f.title,
                "Host": f.host,
                "CVSS": f.cvss,
                "Source": f.source,
            }
            for f in report.findings
        ]
    ).set_index("ID")

    sev_filter = st.multiselect(
        "Filter by severity",
        SEVERITY_ORDER,
        default=SEVERITY_ORDER,
        key="import_view_sev",
    )

    df_view = df_report[df_report["Severity"].isin(sev_filter)]

    edited = st.data_editor(
        df_view,
        use_container_width=True,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
    )

    if st.button("🗑️ Delete selected"):
        ids = set(edited.loc[edited["Select"] == True].index.tolist())
        report.findings = [f for f in report.findings if f.id not in ids]
        sort_findings(report)
        st.success(f"Deleted {len(ids)} findings.")
        st.rerun()
