import streamlit as st
import pandas as pd

from ui.state import get_report


SCOPE_OPTIONS = ["In", "Out"]


def _show_table(rows: list[dict], columns: list[str], headers: dict[str, str]):
    if not rows:
        st.info("No rows yet.")
        return
    df = pd.DataFrame(rows)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    df = df[columns].copy()
    df.rename(columns={c: headers.get(c, c) for c in columns}, inplace=True)
    df.index = range(1, len(df) + 1)
    st.dataframe(df, use_container_width=True)


def _next_flag_no(rows: list[dict]) -> str:
    nums = []
    for r in rows or []:
        v = str(r.get("flag_no", "")).strip()
        if v.isdigit():
            nums.append(int(v))
    return str((max(nums) + 1) if nums else 1)


def _crud_rows(
    title: str,
    rows: list[dict],
    columns: list[str],
    labels: dict[str, str],
    key_prefix: str,
    add_defaults: dict | None = None,
    dropdown_fields: dict[str, list[str]] | None = None,
    autonumber_field: str | None = None,
    autonumber_func=None,
):
    """
    Generic CRUD:
      - view table
      - select row
      - add row (form, only saved on Add)
      - edit selected row (form, saved on Save)
      - delete selected row
    Extras:
      - dropdown_fields: {"scope": ["In","Out"], ...}
      - autonumber_field: e.g. "flag_no" with autonumber_func(rows)->str used as default in Add
    """
    add_defaults = add_defaults or {}
    dropdown_fields = dropdown_fields or {}

    st.subheader(title)

    _show_table(rows, columns, labels)

    # ----- select row -----
    options = ["(none)"] + [str(i) for i in range(1, len(rows) + 1)]
    sel = st.selectbox("Select row to edit/delete", options, index=0, key=f"{key_prefix}_sel")
    idx = int(sel) - 1 if sel != "(none)" else None

    # ----- add row (form) -----
    st.markdown("**Add row**")
    with st.form(f"{key_prefix}_add_form", clear_on_submit=True):
        vals = {}

        # prefill autonumber if requested
        auto_default = None
        if autonumber_field and autonumber_func:
            auto_default = autonumber_func(rows)

        for c in columns:
            label = labels.get(c, c)
            default = add_defaults.get(c, "")

            if autonumber_field == c and auto_default is not None:
                default = auto_default

            if c in dropdown_fields:
                opts = dropdown_fields[c]
                cur = str(default) if str(default) in opts else opts[0]
                vals[c] = st.selectbox(label, opts, index=opts.index(cur), key=f"{key_prefix}_add_{c}")
            else:
                vals[c] = st.text_input(label, value=str(default), key=f"{key_prefix}_add_{c}")

        add_btn = st.form_submit_button("➕ Add")

    if add_btn:
        rows.append({c: vals[c] for c in columns})
        st.success("Row added.")
        st.rerun()

    # ----- edit/delete selected -----
    if idx is not None and 0 <= idx < len(rows):
        st.markdown("**Edit selected row**")
        cur = rows[idx]

        with st.form(f"{key_prefix}_edit_form"):
            edited = {}
            for c in columns:
                label = labels.get(c, c)
                cur_val = cur.get(c, "")

                if c in dropdown_fields:
                    opts = dropdown_fields[c]
                    cur_s = str(cur_val)
                    if cur_s not in opts:
                        cur_s = opts[0]
                    edited[c] = st.selectbox(label, opts, index=opts.index(cur_s), key=f"{key_prefix}_edit_{c}")
                else:
                    edited[c] = st.text_input(label, value=str(cur_val), key=f"{key_prefix}_edit_{c}")

            save_btn = st.form_submit_button("💾 Save changes")

        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("🗑️ Delete selected", key=f"{key_prefix}_del"):
                del rows[idx]
                st.success("Deleted.")
                st.rerun()

        if save_btn:
            rows[idx] = {c: edited[c] for c in columns}
            st.success("Updated.")
            st.rerun()


def render():
    report = get_report()
    st.header("Appendix Data")

    st.info("Completează tabelele pentru Appendix (8.2–8.7). Rândurile se adaugă DOAR cu butonul Add.")

    # Ensure attributes exist even for older ReportData objects
    if not hasattr(report, "appendix_host_service"):
        report.appendix_host_service = []
    if not hasattr(report, "appendix_subdomains"):
        report.appendix_subdomains = []
    if not hasattr(report, "appendix_exploited_hosts"):
        report.appendix_exploited_hosts = []
    if not hasattr(report, "appendix_compromised_users"):
        report.appendix_compromised_users = []
    if not hasattr(report, "appendix_cleanup"):
        report.appendix_cleanup = []
    if not hasattr(report, "appendix_flags"):
        report.appendix_flags = []

    # 8.2 Host & Service Discovery
    _crud_rows(
        "8.2 Host & Service Discovery",
        report.appendix_host_service,
        columns=["ip", "port", "service", "notes"],
        labels={"ip": "IP Address", "port": "Port", "service": "Service", "notes": "Notes"},
        key_prefix="app_hs",
    )

    st.markdown("---")

    # 8.3 Subdomain Discovery
    _crud_rows(
        "8.3 Subdomain Discovery",
        report.appendix_subdomains,
        columns=["url", "description", "method"],
        labels={"url": "URL", "description": "Description", "method": "Discovery Method"},
        key_prefix="app_sub",
    )

    st.markdown("---")

    # 8.4 Exploited Hosts (auto from findings + manual edits)
    st.subheader("8.4 Exploited Hosts")

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("🔄 Refresh from findings hosts", key="app_expl_refresh"):
            hosts = sorted({(f.host or "").strip() for f in (report.findings or []) if (f.host or "").strip()})
            existing = {r.get("host", "").strip() for r in report.appendix_exploited_hosts}
            added = 0
            for h in hosts:
                if h not in existing:
                    report.appendix_exploited_hosts.append({"host": h, "scope": "In", "method": "", "notes": ""})
                    added += 1
            st.success(f"Merged hosts. Added {added} new.")
            st.rerun()
    with c2:
        st.caption("Adaugă host-urile din findings (nu șterge ce ai completat). Scope este dropdown (In/Out).")

    _crud_rows(
        "8.4 Exploited Hosts (edit)",
        report.appendix_exploited_hosts,
        columns=["host", "scope", "method", "notes"],
        labels={"host": "Host", "scope": "Scope", "method": "Method", "notes": "Notes"},
        key_prefix="app_expl",
        dropdown_fields={"scope": SCOPE_OPTIONS},   # ✅ dropdown
        add_defaults={"scope": "In"},
    )

    st.markdown("---")

    # 8.5 Compromised Users
    _crud_rows(
        "8.5 Compromised Users",
        report.appendix_compromised_users,
        columns=["username", "type", "method", "notes"],
        labels={"username": "Username", "type": "Type", "method": "Method", "notes": "Notes"},
        key_prefix="app_users",
    )

    st.markdown("---")

    # 8.6 Changes/Host Cleanup (Scope dropdown also useful here)
    _crud_rows(
        "8.6 Changes/Host Cleanup",
        report.appendix_cleanup,
        columns=["host", "scope", "change"],
        labels={"host": "Host", "scope": "Scope", "change": "Change/Cleanup Needed"},
        key_prefix="app_clean",
        dropdown_fields={"scope": SCOPE_OPTIONS},
        add_defaults={"scope": "In"},
    )

    st.markdown("---")

    # 8.7 Flags Discovered (auto-number Flag#)
    _crud_rows(
        "8.7 Flags Discovered",
        report.appendix_flags,
        columns=["flag_no", "host", "flag_value", "flag_location", "method"],
        labels={
            "flag_no": "Flag#",
            "host": "Host",
            "flag_value": "Flag Value",
            "flag_location": "Flag Location",
            "method": "Method Used",
        },
        key_prefix="app_flags",
        autonumber_field="flag_no",
        autonumber_func=_next_flag_no,   # ✅ auto-number default
    )
