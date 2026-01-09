import streamlit as st
import pandas as pd

from ui.state import get_report


def _show_table(rows: list[dict], columns: list[str], headers: dict[str, str] | None = None):
    headers = headers or {}
    if not rows:
        st.info("No entries yet.")
        return
    df = pd.DataFrame(rows)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    df = df[columns].copy()
    df.rename(columns={c: headers.get(c, c) for c in columns}, inplace=True)
    df.index = range(1, len(df) + 1)
    st.dataframe(df, use_container_width=True)


def _crud_table(
    *,
    key_prefix: str,
    rows: list[dict],
    columns: list[str],
    labels: dict[str, str],
    add_defaults: dict[str, str] | None = None,
):
    """
    CRUD list:
      - Select row
      - Add row (form)
      - Edit selected row (form)
      - Delete selected row
    IMPORTANT:
      - No st.rerun() inside; commit changes directly to rows (reference list).
      - Edit widget keys include idx so they refresh when selection changes.
    """
    add_defaults = add_defaults or {}

    # current table
    _show_table(rows, columns, labels)

    # selection state
    sel_key = f"{key_prefix}_sel_idx"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = None

    # select row
    options = ["(none)"] + [str(i) for i in range(1, len(rows) + 1)]
    current_idx = st.session_state[sel_key]
    # map current_idx -> selectbox index
    selectbox_index = 0
    if isinstance(current_idx, int) and 0 <= current_idx < len(rows):
        selectbox_index = current_idx + 1

    sel = st.selectbox(
        "Select row to edit/delete",
        options,
        index=selectbox_index,
        key=f"{key_prefix}_selbox",
    )
    idx = int(sel) - 1 if sel != "(none)" else None
    st.session_state[sel_key] = idx

    # ADD
    st.markdown("**Add**")
    with st.form(f"{key_prefix}_add_form", clear_on_submit=True):
        new_vals = {}
        for c in columns:
            new_vals[c] = st.text_input(
                labels.get(c, c),
                value=str(add_defaults.get(c, "")),
                key=f"{key_prefix}_add_{c}",
            )
        add_btn = st.form_submit_button("➕ Add")

    if add_btn:
        rows.append({c: new_vals[c] for c in columns})
        st.success("Added.")
        # keep selection on new row
        st.session_state[sel_key] = len(rows) - 1

    # EDIT / DELETE
    if idx is not None and 0 <= idx < len(rows):
        st.markdown("**Edit selected**")
        cur = rows[idx]

        with st.form(f"{key_prefix}_edit_form"):
            edited = {}
            for c in columns:
                edited[c] = st.text_input(
                    labels.get(c, c),
                    value=str(cur.get(c, "")),
                    key=f"{key_prefix}_edit_{c}_{idx}",  # ✅ include idx
                )
            save_btn = st.form_submit_button("💾 Save changes")

        col1, col2 = st.columns([1, 3])
        with col1:
            del_btn = st.button("🗑️ Delete selected", key=f"{key_prefix}_delete_{idx}")

        if save_btn:
            rows[idx] = {c: edited[c] for c in columns}
            st.success("Updated.")

        if del_btn:
            del rows[idx]
            st.success("Deleted.")
            st.session_state[sel_key] = None


def render():
    report = get_report()

    st.header("Report Info")

    # --- Main report info
    with st.form("report_info_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            candidate_name = st.text_input("Candidate Name", report.candidate_name)
            candidate_title = st.text_input("Candidate Title", report.candidate_title)
            candidate_email = st.text_input("Candidate Email", report.candidate_email)
        with c2:
            customer_name = st.text_input("Customer Name", report.customer_name)
            version = st.text_input("Report Version", report.version)
            dates = st.text_input("Testing Dates (free text)", report.dates)
        with c3:
            approach = st.selectbox(
                "Approach",
                ["Black Box", "Gray Box", "White Box"],
                index=["Black Box", "Gray Box", "White Box"].index(
                    report.approach if report.approach in ["Black Box", "Gray Box", "White Box"] else "Black Box"
                ),
            )

        st.subheader("Executive Summary")
        exec_sum = st.text_area("Executive Summary", report.executive_summary, height=200)

        st.subheader("Remediation Summary")
        rem_s = st.text_area("6.1 Short Term", report.remediation_short, height=120)
        rem_m = st.text_area("6.2 Medium Term", report.remediation_medium, height=120)
        rem_l = st.text_area("6.3 Long Term", report.remediation_long, height=120)

        saved = st.form_submit_button("💾 Save Report Info")

    if saved:
        report.candidate_name = candidate_name
        report.candidate_title = candidate_title
        report.candidate_email = candidate_email
        report.customer_name = customer_name
        report.version = version
        report.dates = dates
        report.approach = approach
        report.executive_summary = exec_sum
        report.remediation_short = rem_s
        report.remediation_medium = rem_m
        report.remediation_long = rem_l
        st.success("Saved.")

    st.markdown("---")
    st.info("Statement of Confidentiality este inclus automat în PDF conform template-ului HTB CPTS.")

    # --- Engagement Contacts (two tables)
    st.markdown("---")
    st.header("Engagement Contacts")

    all_contacts = list(report.engagement_contacts or [])
    cust = [r for r in all_contacts if r.get("type") == "Customer"]
    assess = [r for r in all_contacts if r.get("type") == "Assessor"]

    # Ensure at least one row exists (so user can edit)
    if not cust:
        cust = [{"type": "Customer", "name": "", "title": "", "email": ""}]
    if not assess:
        assess = [{"type": "Assessor", "name": "", "title": "", "email": ""}]

    st.subheader("Customer Contacts")
    _crud_table(
        key_prefix="cust_contacts",
        rows=cust,
        columns=["name", "title", "email"],
        labels={"name": "Name", "title": "Title", "email": "Email"},
        add_defaults={"name": report.customer_name or "", "title": "", "email": ""},
    )

    st.subheader("Assessor Contacts")
    _crud_table(
        key_prefix="assessor_contacts",
        rows=assess,
        columns=["name", "title", "email"],
        labels={"name": "Name", "title": "Title", "email": "Email"},
        add_defaults={
            "name": report.candidate_name or "",
            "title": report.candidate_title or "",
            "email": report.candidate_email or "",
        },
    )

    # Commit back to report.engagement_contacts with proper type + fallbacks
    out = []
    for r in cust:
        out.append({
            "type": "Customer",
            "name": (r.get("name", "") or report.customer_name or "").strip(),
            "title": (r.get("title", "") or "").strip(),
            "email": (r.get("email", "") or "").strip(),
        })

    for r in assess:
        out.append({
            "type": "Assessor",
            "name": (r.get("name", "") or report.candidate_name or "Assessor Name").strip(),
            "title": (r.get("title", "") or report.candidate_title or "").strip(),
            "email": (r.get("email", "") or report.candidate_email or "").strip(),
        })

    report.engagement_contacts = out

    # --- Scope (assets)
    st.markdown("---")
    st.header("Scope (In Scope Assets)")

    if report.scope is None:
        report.scope = []
    if not report.scope:
        # keep empty; user can add
        pass

    _crud_table(
        key_prefix="scope_assets",
        rows=report.scope,  # ✅ use report list directly (no copy)
        columns=["asset", "description"],
        labels={"asset": "Host/URL/IP Address", "description": "Description"},
        add_defaults={"asset": "", "description": ""},
    )
