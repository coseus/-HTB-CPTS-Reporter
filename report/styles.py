from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER

HTB_BG = colors.HexColor("#0B1220")
HTB_FG = colors.white
HTB_GREEN = colors.HexColor("#7CFF00")
HTB_GREY = colors.HexColor("#B7C0D0")
HTB_CODE_BG = colors.HexColor("#111A2B")

HTB_TABLE_HDR = colors.HexColor("#7CFF00")
HTB_TABLE_HDR_TXT = colors.black
HTB_TABLE_ROW = colors.HexColor("#C9D2E3")
HTB_TABLE_ROW2 = colors.HexColor("#BFC9DC")

def build_styles():
    s = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("htb_title", parent=s["Title"], fontName="Helvetica-Bold",
                                fontSize=26, textColor=HTB_FG, alignment=TA_LEFT, leading=30),
        "h1": ParagraphStyle("htb_h1", parent=s["Heading1"], fontName="Helvetica-Bold",
                             fontSize=18, textColor=HTB_GREEN, leading=22, spaceBefore=10, spaceAfter=8),
        "h2": ParagraphStyle("htb_h2", parent=s["Heading2"], fontName="Helvetica-Bold",
                             fontSize=13, textColor=HTB_GREEN, leading=16, spaceBefore=8, spaceAfter=6),
        "p": ParagraphStyle("htb_p", parent=s["BodyText"], fontName="Helvetica",
                            fontSize=10.5, textColor=HTB_FG, leading=14),
        "muted": ParagraphStyle("htb_muted", parent=s["BodyText"], fontName="Helvetica",
                                fontSize=9.5, textColor=HTB_GREY, leading=12),
        "center": ParagraphStyle("htb_center", parent=s["BodyText"], fontName="Helvetica-Bold",
                                 fontSize=10, textColor=HTB_FG, alignment=TA_CENTER),
        "code": ParagraphStyle("htb_code", parent=s["BodyText"], fontName="Courier",
                               fontSize=9.2, textColor=HTB_FG, leading=11.5,
                               backColor=HTB_CODE_BG, leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=6),
    }
