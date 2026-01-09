from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import uuid

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Info"]

def normalize_severity(sev: str) -> str:
    if not sev:
        return "Info"
    s = sev.strip().lower()
    m = {
        "critical": "Critical", "crit": "Critical",
        "high": "High",
        "medium": "Medium", "med": "Medium",
        "low": "Low",
        "info": "Info", "informational": "Info", "none": "Info"
    }
    if s in m:
        return m[s]
    t = sev.strip().title()
    return t if t in SEVERITY_ORDER else "Info"

@dataclass
class EvidenceImage:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    mime: str = "image/png"
    b64: str = ""          # base64 (no header)
    caption: str = ""

@dataclass
class CodeBlock:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    language: str = "text"
    code: str = ""

@dataclass
class Finding:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: str = "Info"
    title: str = ""
    host: str = ""
    port: str = ""
    service: str = ""
    cvss: Optional[float] = None
    cve: List[str] = field(default_factory=list)
    description: str = ""
    impact: str = ""
    recommendation: str = ""
    references: List[str] = field(default_factory=list)
    evidence_images: List[EvidenceImage] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    source: str = "manual"   # nessus/openvas/nmap/manual
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class WalkthroughStep:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    code_blocks: List[CodeBlock] = field(default_factory=list)
    images: List[EvidenceImage] = field(default_factory=list)

@dataclass
class ReportData:
    candidate_name: str = ""
    candidate_title: str = ""
    candidate_email: str = ""
    customer_name: str = ""
    version: str = "1.0"
    dates: str = ""
    approach: str = "Black Box"

    engagement_contacts: List[Dict[str, str]] = field(default_factory=lambda: [
        {"type": "Customer", "name": "", "title": "", "email": ""},
        {"type": "Assessor", "name": "", "title": "", "email": ""},
    ])

    scope: List[Dict[str, str]] = field(default_factory=list)  # {"asset":"","description":""}

    executive_summary: str = ""

    remediation_short: str = ""
    remediation_medium: str = ""
    remediation_long: str = ""

    findings: List[Finding] = field(default_factory=list)
    walkthrough: List[WalkthroughStep] = field(default_factory=list)

    # ---------------- Appendix Data (8.2 - 8.7) ----------------
    # 8.2 Host & Service Discovery: ip, port, service, notes
    appendix_host_service: List[Dict[str, str]] = field(default_factory=list)

    # 8.3 Subdomain Discovery: url, description, method
    appendix_subdomains: List[Dict[str, str]] = field(default_factory=list)

    # 8.4 Exploited Hosts: host, scope, method, notes
    appendix_exploited_hosts: List[Dict[str, str]] = field(default_factory=list)

    # 8.5 Compromised Users: username, type, method, notes
    appendix_compromised_users: List[Dict[str, str]] = field(default_factory=list)

    # 8.6 Changes/Host Cleanup: host, scope, change
    appendix_cleanup: List[Dict[str, str]] = field(default_factory=list)

    # 8.7 Flags Discovered: flag_no, host, flag_value, flag_location, method
    appendix_flags: List[Dict[str, str]] = field(default_factory=list)
    # -----------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)