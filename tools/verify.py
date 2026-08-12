# tools/verify.py  (new file)
import re

DATE_PATTERN = re.compile(r"\(([A-Z][a-zA-Z]+),\s*\d{4}\)")  # e.g. (Salesforce, 2022)
QUOTE_PATTERN = re.compile(r'"([^"]{15,})"')  # quoted spans of 15+ chars

def find_ungrounded_claims(report_text: str, research_results: list[dict]) -> list[str]:
    source_text = " ".join(r.get("answer", "") for r in research_results)

    issues = []

    for match in DATE_PATTERN.finditer(report_text):
        issues.append(f"Fabricated citation/date not in research: {match.group(0)}")

    for match in QUOTE_PATTERN.finditer(report_text):
        quote = match.group(1)
        if quote not in source_text:
            issues.append(f"Unverified quote not found in research: \"{quote[:60]}...\"")

    return issues