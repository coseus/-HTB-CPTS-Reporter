import streamlit as st
from models import ReportData, normalize_severity, SEVERITY_ORDER

def get_report() -> ReportData:
    if "report" not in st.session_state:
        st.session_state.report = ReportData()
    return st.session_state.report

def sort_findings(report: ReportData):
    report.findings.sort(
        key=lambda x: (
            SEVERITY_ORDER.index(normalize_severity(x.severity)),
            (x.host or "").lower(),
            (x.title or "").lower(),
        )
    )
