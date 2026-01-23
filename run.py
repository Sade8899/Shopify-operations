#!/usr/bin/env python3
"""
Shopify Store Health and Automation Monitor

Main entry point for running health checks against a Shopify store.
"""
import os
import sys
import yaml
from typing import List

from shopify_client import ShopifyClient, ShopifyAPIError
from models import parse_product, ProductSummary, HealthIssue
from report import save_reports
import checks


def load_config(config_path: str = 'config.yaml') -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Override token with environment variable if set
    env_token = os.getenv('SHOPIFY_ADMIN_ACCESS_TOKEN')
    if env_token:
        config['admin_access_token'] = env_token
        print("Using access token from SHOPIFY_ADMIN_ACCESS_TOKEN environment variable")

    # Validate required fields
    required_fields = ['store_domain', 'admin_api_version', 'admin_access_token']
    missing_fields = [field for field in required_fields if not config.get(field)]

    if missing_fields:
        raise ValueError(f"Missing required config fields: {', '.join(missing_fields)}")

    return config


def fetch_products(client: ShopifyClient, max_products: int) -> List[ProductSummary]:
    """
    Fetch and parse products from Shopify.

    Args:
        client: ShopifyClient instance
        max_products: Maximum number of products to fetch

    Returns:
        List of ProductSummary objects
    """
    print(f"Fetching up to {max_products} products from Shopify...")

    try:
        raw_products = client.get_products(limit=max_products)
        print(f"Retrieved {len(raw_products)} products")

        products = []
        for raw_product in raw_products:
            try:
                product = parse_product(raw_product)
                products.append(product)
            except Exception as e:
                print(f"Warning: Failed to parse product {raw_product.get('id')}: {e}")

        print(f"Successfully parsed {len(products)} products")
        return products

    except ShopifyAPIError as e:
        print(f"Error fetching products: {e}")
        raise


def run_health_checks(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """
    Run all health checks against products.

    Args:
        products: List of ProductSummary objects
        config: Configuration dictionary

    Returns:
        Combined list of all health issues found
    """
    all_issues = []

    print(f"\nRunning {len(checks.ALL_CHECKS)} health checks...")

    for check_module in checks.ALL_CHECKS:
        check_name = check_module.__name__.split('.')[-1]
        print(f"  Running {check_name}...", end=' ')

        try:
            issues = check_module.run(products, config)
            all_issues.extend(issues)
            print(f"found {len(issues)} issue(s)")

        except Exception as e:
            print(f"ERROR: {e}")
            # Create a system issue for the failed check
            all_issues.append(HealthIssue(
                check_name='system',
                severity='warning',
                title=f'Health check failed: {check_name}',
                details=f'Exception: {str(e)}',
                recommended_fix='Review check implementation and error logs'
            ))

    return all_issues


def print_summary(issues: List[HealthIssue]):
    """
    Print a concise summary to console.

    Args:
        issues: List of HealthIssue objects
    """
    from collections import defaultdict

    print("\n" + "=" * 80)
    print("HEALTH CHECK SUMMARY")
    print("=" * 80)

    # Count by severity
    severity_counts = defaultdict(int)
    for issue in issues:
        severity_counts[issue.severity] += 1

    print(f"Total Issues Found: {len(issues)}")
    print(f"  🔴 Critical: {severity_counts['critical']}")
    print(f"  🟡 Warning:  {severity_counts['warning']}")
    print(f"  🔵 Info:     {severity_counts['info']}")

    # Count by check
    check_counts = defaultdict(int)
    for issue in issues:
        check_counts[issue.check_name] += 1

    if check_counts:
        print("\nIssues by Check:")
        for check_name in sorted(check_counts.keys()):
            print(f"  {check_name}: {check_counts[check_name]}")

    print("=" * 80)


def main():
    """Main entry point."""
    print("Shopify Store Health and Automation Monitor")
    print("=" * 80)

    try:
        # Load configuration
        print("\nLoading configuration...")
        config = load_config()
        print(f"Configuration loaded for store: {config['store_domain']}")

        if config.get('dry_run', False):
            print("⚠️  DRY RUN MODE ENABLED - Review config.yaml to disable")

        # Initialize Shopify client
        print("\nInitializing Shopify API client...")
        client = ShopifyClient(
            store_domain=config['store_domain'],
            api_version=config['admin_api_version'],
            access_token=config['admin_access_token'],
            timeout=config.get('timeout_seconds', 30)
        )

        # Fetch products
        max_products = config.get('max_products', 250)
        products = fetch_products(client, max_products)

        if not products:
            print("\n⚠️  No products found in store. Nothing to check.")
            return 0

        # Run health checks
        issues = run_health_checks(products, config)

        # Save reports
        output_dir = config.get('report_output_dir', 'reports')
        print(f"\nSaving reports to {output_dir}/...")
        text_path, json_path = save_reports(issues, config['store_domain'], output_dir)

        print(f"  Text report: {text_path}")
        print(f"  JSON report: {json_path}")

        # Print summary
        print_summary(issues)

        # Return exit code based on critical issues
        critical_count = sum(1 for issue in issues if issue.severity == 'critical')
        if critical_count > 0:
            print(f"\n⚠️  {critical_count} critical issue(s) require immediate attention!")
            return 1

        print("\n✅ Health check complete!")
        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print("Make sure config.yaml exists in the current directory.", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"\n❌ Configuration error: {e}", file=sys.stderr)
        return 1

    except ShopifyAPIError as e:
        print(f"\n❌ Shopify API error: {e}", file=sys.stderr)
        print("Check your store domain and access token.", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        return 130

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
