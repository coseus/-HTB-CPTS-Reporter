import streamlit as st

from ui.state import get_report
from models import WalkthroughStep, CodeBlock, EvidenceImage
from utils.images import b64_from_upload, resize_image_b64

CODE_LANGS = [
    "text", "bash", "powershell", "cmd",
    "python", "php", "javascript", "sql",
    "http", "curl", "nmap", "json", "xml",
]

def render():
    report = get_report()

    st.header("Walkthrough Editor")

    if st.button("Add Walkthrough Step"):
        report.walkthrough.append(WalkthroughStep(name="New Step"))
        st.rerun()

    if not report.walkthrough:
        st.info("No walkthrough steps yet.")
        return

    show_imgs = st.checkbox("Show image previews (can be slow)", value=False, key="wt_show_imgs")

    for idx, step in enumerate(report.walkthrough, start=1):
        with st.expander(f"Step {idx}: {step.name}", expanded=False):
            step.name = st.text_input("Name", step.name, key=f"{step.id}_name")
            step.description = st.text_area("Description", step.description, height=120, key=f"{step.id}_desc")

            st.markdown("### Images")
            w_up = st.file_uploader(
                "Upload image(s) (then click Attach)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key=f"{step.id}_imgup",
            )
            if st.button("📎 Attach uploaded images", key=f"{step.id}_attach_imgs") and w_up:
                for u in w_up:
                    name, mime, b64 = b64_from_upload(u)
                    b64 = resize_image_b64(b64, max_w=1100, max_h=800)
                    step.images.append(EvidenceImage(name=name, mime=mime, b64=b64))
                st.rerun()

            for img in list(step.images):
                cols = st.columns([2, 2, 1])
                with cols[0]:
                    if show_imgs:
                        st.image(f"data:{img.mime};base64,{img.b64}", caption=img.name, use_container_width=True)
                    else:
                        st.write(img.name)
                with cols[1]:
                    img.caption = st.text_input("Caption", img.caption, key=f"{step.id}_{img.id}_cap")
                with cols[2]:
                    if st.button("Remove", key=f"{step.id}_{img.id}_rm"):
                        step.images = [x for x in step.images if x.id != img.id]
                        st.rerun()

            st.markdown("### Code Blocks")
            if st.button("Add Code Block", key=f"{step.id}_addcb"):
                step.code_blocks.append(CodeBlock(language="text", code=""))
                st.rerun()

            for cb in list(step.code_blocks):
                ccb1, ccb2 = st.columns([1, 4])
                with ccb1:
                    cb.language = st.selectbox(
                        "Language",
                        CODE_LANGS,
                        index=CODE_LANGS.index(cb.language) if cb.language in CODE_LANGS else 0,
                        key=f"{step.id}_{cb.id}_lang",
                    )
                    if st.button("Remove Block", key=f"{step.id}_{cb.id}_rm"):
                        step.code_blocks = [x for x in step.code_blocks if x.id != cb.id]
                        st.rerun()
                with ccb2:
                    cb.code = st.text_area(
                        "Code (paste here; whitespace preserved in PDF)",
                        cb.code,
                        height=160,
                        key=f"{step.id}_{cb.id}_code",
                    )
                    if cb.code.strip():
                        st.code(cb.code, language=cb.language or "text")

            if st.button("Delete Step", key=f"{step.id}_del"):
                report.walkthrough = [x for x in report.walkthrough if x.id != step.id]
                st.rerun()
