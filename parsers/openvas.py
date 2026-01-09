import xml.etree.ElementTree as ET
from typing import List
from models import Finding
from utils.severity import cvss_to_severity
from utils.text import extract_cves

def parse_openvas(file_bytes: bytes) -> List[Finding]:
    root = ET.fromstring(file_bytes)
    findings: List[Finding] = []
    for res in root.findall(".//result"):
        host = (res.findtext("host") or "").strip()
        port = (res.findtext("port") or "").strip()
        name = (res.findtext("name") or res.findtext("nvt/name") or "Untitled Finding").strip()
        sev_txt = (res.findtext("severity") or "").strip()
        cvss = None
        if sev_txt:
            try:
                cvss = float(sev_txt)
            except:
                cvss = None

        nvt_desc = (res.findtext("nvt/description") or "").strip()
        tags = (res.findtext("nvt/tags") or "").strip()

        impact = ""
        recommendation = ""
        if tags:
            parts = tags.split("|")
            kv = {}
            for p in parts:
                if "=" in p:
                    k,v = p.split("=",1)
                    kv[k.strip().lower()] = v.strip()
            impact = kv.get("impact","")
            recommendation = kv.get("solution","")

        cves = extract_cves(nvt_desc + "\n" + tags)
        sev = cvss_to_severity(cvss)

        findings.append(Finding(
            severity=sev,
            title=name,
            host=host,
            port=port,
            cvss=cvss,
            cve=cves,
            description=nvt_desc or "",
            impact=impact,
            recommendation=recommendation,
            source="openvas",
            raw={"tags": tags}
        ))
    return findings
