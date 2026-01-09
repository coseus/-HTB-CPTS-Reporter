import os
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.nav import sidebar_nav

import ui.pages.report_info as report_info
import ui.pages.import_findings as import_findings
import ui.pages.findings_editor as findings_editor
import ui.pages.walkthrough_editor as walkthrough_editor
import ui.pages.appendix_data as appendix_data
import ui.pages.preview_export as preview_export

st.set_page_config(page_title="HTB CPTS Reporter", layout="wide")
st.title("🛡️ HTB CPTS Reporter")

page = sidebar_nav()

if page == "Report Info":
    report_info.render()
elif page == "Import Findings":
    import_findings.render()
elif page == "Findings Editor":
    findings_editor.render()
elif page == "Walkthrough Editor":
    walkthrough_editor.render()
elif page == "Appendix Data":
    appendix_data.render()
else:
    preview_export.render()
