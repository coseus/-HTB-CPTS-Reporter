def cvss_to_severity(cvss: float|None) -> str:
    if cvss is None:
        return "Info"
    if cvss >= 9.0:
        return "Critical"
    if cvss >= 7.0:
        return "High"
    if cvss >= 4.0:
        return "Medium"
    if cvss >= 0.1:
        return "Low"
    return "Info"

def nessus_risk_to_severity(risk: str) -> str:
    if not risk:
        return "Info"
    r = risk.strip().lower()
    mapping = {"critical":"Critical","high":"High","medium":"Medium","low":"Low","none":"Info"}
    return mapping.get(r, "Info")
