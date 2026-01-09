# HTB CPTS Reporter

🛡️ **HTB CPTS Reporter** is a Streamlit-based application designed to help penetration testers create **professional, HTB CPTS–style penetration testing reports**, from vulnerability imports to a fully formatted PDF.

The tool is optimized for the **Hack The Box Certified Penetration Testing Specialist (CPTS)** exam format, but can also be reused for real-world internal network penetration tests.

---

## ✨ Features

### 📥 Import Findings

- Import findings from:
    - **Nessus**
    - **OpenVAS**
    - **Nmap**
- Automatic mapping:
    - Severity
    - Title
    - Host
    - CVSS
    - CVE
    - Description / Impact / Recommendation
- Automatic severity normalization and sorting

---

### ✏️ Findings Editor

- Add findings **manually** (Add → then edit)
- Full CRUD (Add / Edit / Delete)
- Advanced editor per finding:
    - Description, Impact, Recommendation
    - Code blocks with syntax highlighting
    - Evidence images (Base64, auto-resize)
- Automatic renumbering
- Filter by severity
- Sorted automatically by severity

---

### 🧭 Walkthrough Editor

- Step-by-step **Internal Network Compromise Walkthrough**
- Each step supports:
    - Name & description
    - Multiple code blocks
    - Screenshots with captions
- Hierarchical numbering in PDF:
5.1 Detailed Walkthrough
5.1.1 Step 1
5.1.2 Step 2

---

### 📊 Appendix Data (Dedicated Page)

Editable tables with **Add / Edit / Delete** workflow:

- **8.2 Host & Service Discovery**
- **8.3 Subdomain Discovery**
- **8.4 Exploited Hosts**
- Auto-populate from findings
- Scope dropdown: `In / Out`
- **8.5 Compromised Users**
- **8.6 Changes / Host Cleanup**
- **8.7 Flags Discovered**
- Auto-numbered Flag IDs

---

### 📄 PDF Generation (HTB-style)

- Clean, professional layout
- Centered cover page
- Automatic **Table of Contents**
- Correct section numbering:
- 2.1 / 2.2 Engagement Contacts
- 4.2 Summary of Findings per Host
- 5.1 / 5.1.1 Walkthrough hierarchy
- 7.x Technical Findings
- 8.x Appendix
- Includes:
- Statement of Confidentiality
- Executive Summary
- Scope
- Remediation Summary
- Technical Findings
- Appendix tables

---

### 💾 Backup & Restore

- Export full project to `report.json`
- Restore work at any time
- Backward-compatible with older JSON versions

---

## 🧱 Project Structure

htb_cpts_reporter/
│
├── streamlit_app.py # Main entry point
├── [models.py](http://models.py/) # Data models
├── requirements.txt
│
├── ui/
│ ├── [nav.py](http://nav.py/) # Sidebar navigation
│ ├── [state.py](http://state.py/) # Global report state
│ └── pages/
│ ├── report_info.py
│ ├── import_findings.py
│ ├── findings_editor.py
│ ├── walkthrough_editor.py
│ ├── appendix_data.py
│ └── preview_export.py
│
├── parsers/
│ ├── [nessus.py](http://nessus.py/)
│ ├── [openvas.py](http://openvas.py/)
│ └── [nmap.py](http://nmap.py/)
│
├── report/
│ ├── [pdf.py](http://pdf.py/) # PDF generation logic
│ └── [styles.py](http://styles.py/) # ReportLab styles
│
└── utils/
└── [images.py](http://images.py/)

---

## 🚀 Installation

### 1. Clone repository

```bash
git clone <https://github.com/yourusername/htb-cpts-reporter.git>
cd htb-cpts-reporter
```

2. Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate
```

## 📝 Notes

- Designed primarily for **HTB CPTS exam reports**
- Not affiliated with Hack The Box
- Use at your own responsibility for real engagements

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Run the app

```bash
streamlit run streamlit_app.py
```
