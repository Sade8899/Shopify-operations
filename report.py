"""Report generation for Shopify Store Health Monitor."""
import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from io import StringIO
from typing import Dict, List

from models import HealthIssue


def render_text(issues: List[HealthIssue], store_domain: str) -> str:
    """Render health issues as a formatted text report."""
    lines = []

    lines.append("=" * 80)
    lines.append("SHOPIFY STORE HEALTH REPORT")
    lines.append("=" * 80)
    lines.append(f"Store: {store_domain}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    severity_counts = defaultdict(int)
    for issue in issues:
        severity_counts[issue.severity] += 1

    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Total Issues: {len(issues)}")
    lines.append(f"  Critical: {severity_counts['critical']}")
    lines.append(f"  Warning:  {severity_counts['warning']}")
    lines.append(f"  Info:     {severity_counts['info']}")
    lines.append("")

    if not issues:
        lines.append("No issues found.")
        lines.append("=" * 80)
        return "\n".join(lines)

    issues_by_check = defaultdict(lambda: defaultdict(list))
    for issue in issues:
        issues_by_check[issue.check_name][issue.severity].append(issue)

    for check_name in sorted(issues_by_check.keys()):
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"CHECK: {check_name.replace('_', ' ').upper()}")
        lines.append("=" * 80)

        for severity in ['critical', 'warning', 'info']:
            if severity not in issues_by_check[check_name]:
                continue

            severity_issues = issues_by_check[check_name][severity]
            lines.append("")
            lines.append(f"[{severity.upper()}] - {len(severity_issues)} issue(s)")
            lines.append("-" * 80)

            for issue in severity_issues:
                issue_parts = []

                if issue.product_id:
                    issue_parts.append(f"Product ID: {issue.product_id}")

                if issue.variant_id:
                    issue_parts.append(f"Variant ID: {issue.variant_id}")

                if issue.sku:
                    issue_parts.append(f"SKU: {issue.sku}")

                lines.append(f"  - {issue.title}")
                if issue_parts:
                    lines.append(f"    {' | '.join(issue_parts)}")
                lines.append(f"    Details: {issue.details}")
                lines.append(f"    Fix: {issue.recommended_fix}")
                lines.append("")

    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    return "\n".join(lines)


def render_json(issues: List[HealthIssue], store_domain: str) -> Dict:
    """Render health issues as a JSON-serializable dictionary."""
    severity_counts = defaultdict(int)
    for issue in issues:
        severity_counts[issue.severity] += 1

    issues_data = []
    for issue in issues:
        issues_data.append({
            'check_name': issue.check_name,
            'severity': issue.severity,
            'title': issue.title,
            'details': issue.details,
            'recommended_fix': issue.recommended_fix,
            'product_id': issue.product_id,
            'variant_id': issue.variant_id,
            'sku': issue.sku
        })

    return {
        'store_domain': store_domain,
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_issues': len(issues),
            'critical': severity_counts['critical'],
            'warning': severity_counts['warning'],
            'info': severity_counts['info']
        },
        'issues': issues_data
    }


def render_csv(issues: List[HealthIssue], store_domain: str) -> str:
    """Render health issues as CSV for spreadsheet review."""
    output = StringIO()
    fieldnames = [
        'store_domain',
        'check_name',
        'severity',
        'title',
        'details',
        'recommended_fix',
        'product_id',
        'variant_id',
        'sku'
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for issue in issues:
        writer.writerow({
            'store_domain': store_domain,
            'check_name': issue.check_name,
            'severity': issue.severity,
            'title': issue.title,
            'details': issue.details,
            'recommended_fix': issue.recommended_fix,
            'product_id': issue.product_id or '',
            'variant_id': issue.variant_id or '',
            'sku': issue.sku or ''
        })

    return output.getvalue()


def save_reports(issues: List[HealthIssue], store_domain: str, output_dir: str = 'reports') -> tuple:
    """Save text, JSON and CSV reports to disk with timestamped filenames."""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    text_report = render_text(issues, store_domain)
    json_data = render_json(issues, store_domain)
    csv_report = render_csv(issues, store_domain)

    text_path = os.path.join(output_dir, f'report_{timestamp}.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text_report)

    json_path = os.path.join(output_dir, f'report_{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    csv_path = os.path.join(output_dir, f'report_{timestamp}.csv')
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        f.write(csv_report)

    return text_path, json_path, csv_path
