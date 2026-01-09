import re
def extract_cves(text: str):
    if not text:
        return []
    return sorted(set(re.findall(r"CVE-\d{4}-\d{4,7}", text, flags=re.I)))
