import xml.etree.ElementTree as ET
from typing import List
from models import Finding
from utils.severity import nessus_risk_to_severity, cvss_to_severity
from utils.text import extract_cves

def parse_nessus(file_bytes: bytes) -> List[Finding]:
    root = ET.fromstring(file_bytes)
    findings: List[Finding] = []
    for report_host in root.findall(".//ReportHost"):
        host = report_host.get("name","")
        for item in report_host.findall("./ReportItem"):
            title = (item.get("pluginName","") or "").strip()
            risk = item.get("risk_factor","")
            sev = nessus_risk_to_severity(risk)
            port = item.get("port","") or ""
            svc = item.get("svc_name","") or ""

            desc = (item.findtext("description") or "").strip()
            sol = (item.findtext("solution") or "").strip()
            syn = (item.findtext("synopsis") or "").strip()
            plugin_output = (item.findtext("plugin_output") or "").strip()

            cvss = None
            for tag in ["cvss3_base_score","cvss_base_score"]:
                t = item.findtext(tag)
                if t:
                    try:
                        cvss = float(t)
                        break
                    except:
                        pass

            cves = []
            cve_text = (item.findtext("cve") or "")
            if cve_text:
                cves += [c.strip() for c in cve_text.split(",") if c.strip()]
            cves += extract_cves(desc + "\n" + plugin_output)
            cves = sorted(set(cves))

            if sev == "Info" and cvss is not None:
                sev = cvss_to_severity(cvss)

            findings.append(Finding(
                severity=sev,
                title=title or "Untitled Finding",
                host=host,
                port=str(port),
                service=svc,
                cvss=cvss,
                cve=cves,
                description=syn or desc,
                impact=desc if syn else "",
                recommendation=sol,
                source="nessus",
                raw={"pluginID": item.get("pluginID",""), "plugin_output": plugin_output}
            ))
    return findings
