import streamlit as st

PAGES = [
    "Report Info",
    "Import Findings",
    "Findings Editor",
    "Walkthrough Editor",
    "Appendix Data",
    "Preview & Export",
]

def sidebar_nav() -> str:
    st.sidebar.title("HTB CPTS Reporter")
    return st.sidebar.radio("Navigate", PAGES, index=0)
