import xml.etree.ElementTree as ET
from typing import List
from models import Finding

def parse_nmap(file_bytes: bytes) -> List[Finding]:
    root = ET.fromstring(file_bytes)
    findings: List[Finding] = []
    for host in root.findall(".//host"):
        addr_el = host.find("./address[@addrtype='ipv4']") or host.find("./address")
        host_ip = addr_el.get("addr","") if addr_el is not None else ""
        for port in host.findall(".//ports/port"):
            portid = port.get("portid","")
            proto = port.get("protocol","")
            service_el = port.find("service")
            service = service_el.get("name","") if service_el is not None else ""
            product = service_el.get("product","") if service_el is not None else ""
            version = service_el.get("version","") if service_el is not None else ""
            title = f"Open Port: {portid}/{proto} ({service})".strip()
            desc = f"Host {host_ip} has {portid}/{proto} open. Service: {service}. {product} {version}".strip()
            findings.append(Finding(
                severity="Info",
                title=title,
                host=host_ip,
                port=f"{portid}/{proto}",
                service=service,
                description=desc,
                recommendation="Review exposure; restrict access with firewall/ACLs; keep service patched.",
                source="nmap",
                raw={"product": product, "version": version}
            ))
    return findings
