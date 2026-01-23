"""
Report generation for Shopify Store Health Monitor.
"""
import json
import os
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
from models import HealthIssue


def render_text(issues: List[HealthIssue], store_domain: str) -> str:
    """
    Render health issues as formatted text report.

    Args:
        issues: List of HealthIssue objects
        store_domain: Shopify store domain

    Returns:
        Formatted text report
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("SHOPIFY STORE HEALTH REPORT")
    lines.append("=" * 80)
    lines.append(f"Store: {store_domain}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Summary counts by severity
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
        lines.append("No issues found! Your store is in great shape.")
        lines.append("=" * 80)
        return "\n".join(lines)

    # Group issues by check name, then by severity
    issues_by_check = defaultdict(lambda: defaultdict(list))
    for issue in issues:
        issues_by_check[issue.check_name][issue.severity].append(issue)

    # Sort check names for consistent output
    check_names = sorted(issues_by_check.keys())

    # Report each check's issues
    for check_name in check_names:
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"CHECK: {check_name.replace('_', ' ').upper()}")
        lines.append("=" * 80)

        # Process in severity order: critical, warning, info
        for severity in ['critical', 'warning', 'info']:
            if severity not in issues_by_check[check_name]:
                continue

            severity_issues = issues_by_check[check_name][severity]
            lines.append("")
            lines.append(f"[{severity.upper()}] - {len(severity_issues)} issue(s)")
            lines.append("-" * 80)

            for issue in severity_issues:
                # Build issue line
                issue_parts = []

                if issue.product_id:
                    issue_parts.append(f"Product ID: {issue.product_id}")

                if issue.variant_id:
                    issue_parts.append(f"Variant ID: {issue.variant_id}")

                if issue.sku:
                    issue_parts.append(f"SKU: {issue.sku}")

                # Format the issue
                lines.append(f"  • {issue.title}")
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
    """
    Render health issues as JSON-serializable dictionary.

    Args:
        issues: List of HealthIssue objects
        store_domain: Shopify store domain

    Returns:
        Dictionary suitable for JSON serialization
    """
    # Count by severity
    severity_counts = defaultdict(int)
    for issue in issues:
        severity_counts[issue.severity] += 1

    # Convert issues to dictionaries
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


def save_reports(issues: List[HealthIssue], store_domain: str, output_dir: str = 'reports') -> tuple:
    """
    Save both text and JSON reports to disk with timestamp.

    Args:
        issues: List of HealthIssue objects
        store_domain: Shopify store domain
        output_dir: Directory to save reports

    Returns:
        Tuple of (text_file_path, json_file_path)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Generate reports
    text_report = render_text(issues, store_domain)
    json_data = render_json(issues, store_domain)

    # Write text report
    text_path = os.path.join(output_dir, f'report_{timestamp}.txt')
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text_report)

    # Write JSON report
    json_path = os.path.join(output_dir, f'report_{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    return text_path, json_path
