import streamlit as st
import pandas as pd

def crud_list(
    title: str,
    items: list[dict],
    fields: list[tuple[str, str]],   # (key, label)
    add_defaults: dict,
    key_prefix: str,
    field_widgets: dict | None = None,  # optional custom widgets per field
):
    """
    Generic CRUD list:
      - shows dataframe
      - select row
      - add form
      - edit/save/delete selected
    """
    st.subheader(title)
    field_widgets = field_widgets or {}

    if items:
        df = pd.DataFrame(items)
        df.index = range(1, len(items) + 1)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No items yet.")

    options = ["(none)"] + [str(i) for i in range(1, len(items) + 1)]
    sel = st.selectbox("Select row to edit/delete", options, index=0, key=f"{key_prefix}_row_select")
    idx = int(sel) - 1 if sel != "(none)" else None

    # ---- ADD ----
    with st.form(f"{key_prefix}_add_form", clear_on_submit=True):
        values = {}
        for k, label in fields:
            if k in field_widgets:
                values[k] = field_widgets[k](label, add_defaults.get(k, ""), key=f"{key_prefix}_add_{k}")
            else:
                values[k] = st.text_input(label, add_defaults.get(k, ""), key=f"{key_prefix}_add_{k}")
        add = st.form_submit_button("➕ Add")

    if add:
        items.append({k: values[k] for k, _ in fields})
        st.success("Added.")
        st.rerun()

    # ---- EDIT/DELETE ----
    if idx is not None and 0 <= idx < len(items):
        st.markdown("### Edit selected")

        current = items[idx]
        with st.form(f"{key_prefix}_edit_form"):
            edited = {}
            for k, label in fields:
                val = current.get(k, "")
                if k in field_widgets:
                    edited[k] = field_widgets[k](label, val, key=f"{key_prefix}_edit_{k}")
                else:
                    edited[k] = st.text_input(label, val, key=f"{key_prefix}_edit_{k}")
            save = st.form_submit_button("💾 Save changes")

        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("🗑️ Delete selected", key=f"{key_prefix}_delete"):
                del items[idx]
                st.success("Deleted.")
                st.rerun()

        if save:
            items[idx] = {k: edited[k] for k, _ in fields}
            st.success("Updated.")
            st.rerun()
