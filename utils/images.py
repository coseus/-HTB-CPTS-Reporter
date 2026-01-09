import base64, io
from PIL import Image

def b64_from_upload(uploaded_file) -> tuple[str,str,str]:
    data = uploaded_file.getvalue()
    b64 = base64.b64encode(data).decode("ascii")
    return uploaded_file.name, (uploaded_file.type or "application/octet-stream"), b64

def resize_image_b64(b64: str, max_w: int = 1100, max_h: int = 800, fmt: str = "PNG") -> str:
    raw = base64.b64decode(b64)
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB","RGBA"):
        img = img.convert("RGBA")
    w,h = img.size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    out = io.BytesIO()
    save_fmt = "PNG" if fmt.upper() == "PNG" else "JPEG"
    if save_fmt == "JPEG" and img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(out, format=save_fmt, optimize=True, quality=85)
    return base64.b64encode(out.getvalue()).decode("ascii")
