#!/usr/bin/env python3
"""Command-line entry point for Shopify Store Health Monitor."""
import argparse
import os
import sys
from typing import List

import yaml

import checks
from models import HealthIssue, ProductSummary, parse_product
from report import save_reports
from shopify_client import ShopifyAPIError, ShopifyClient, SHOPIFY_MAX_PAGE_SIZE


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from a YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    env_token = os.getenv('SHOPIFY_ADMIN_ACCESS_TOKEN')
    if env_token:
        config['admin_access_token'] = env_token
        print("Using access token from SHOPIFY_ADMIN_ACCESS_TOKEN environment variable")

    required_fields = ['store_domain', 'admin_api_version', 'admin_access_token']
    missing_fields = [field for field in required_fields if not config.get(field)]

    if missing_fields:
        raise ValueError(f"Missing required config fields: {', '.join(missing_fields)}")

    return config


def fetch_products(client: ShopifyClient, max_products: int) -> List[ProductSummary]:
    """Fetch products from the Shopify Admin API and parse them."""
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
    """Run all configured health checks."""
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
            all_issues.append(HealthIssue(
                check_name='system',
                severity='warning',
                title=f'Health check failed: {check_name}',
                details=f'Exception: {str(e)}',
                recommended_fix='Review check implementation and error logs'
            ))

    return all_issues


def print_summary(issues: List[HealthIssue]):
    """Print a concise summary to the console."""
    from collections import defaultdict

    print("\n" + "=" * 80)
    print("HEALTH CHECK SUMMARY")
    print("=" * 80)

    severity_counts = defaultdict(int)
    for issue in issues:
        severity_counts[issue.severity] += 1

    print(f"Total Issues Found: {len(issues)}")
    print(f"  Critical: {severity_counts['critical']}")
    print(f"  Warning:  {severity_counts['warning']}")
    print(f"  Info:     {severity_counts['info']}")

    check_counts = defaultdict(int)
    for issue in issues:
        check_counts[issue.check_name] += 1

    if check_counts:
        print("\nIssues by Check:")
        for check_name in sorted(check_counts.keys()):
            print(f"  {check_name}: {check_counts[check_name]}")

    print("=" * 80)


def parse_args(argv=None):
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description='Run Shopify product, inventory and configuration health checks.'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to the YAML config file. Defaults to config.yaml.'
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Run the CLI."""
    args = parse_args(argv)

    print("Shopify Store Health Monitor")
    print("=" * 80)

    try:
        print("\nLoading configuration...")
        config = load_config(args.config)
        print(f"Configuration loaded for store: {config['store_domain']}")

        if config.get('dry_run', False):
            print("DRY RUN MODE ENABLED - Review config.yaml to disable")

        print("\nInitializing Shopify API client...")
        client = ShopifyClient(
            store_domain=config['store_domain'],
            api_version=config['admin_api_version'],
            access_token=config['admin_access_token'],
            timeout=config.get('timeout_seconds', 30)
        )

        max_products = config.get('max_products', SHOPIFY_MAX_PAGE_SIZE)
        products = fetch_products(client, max_products)

        if not products:
            print("\nNo products found in store. Nothing to check.")
            return 0

        issues = run_health_checks(products, config)

        output_dir = config.get('report_output_dir', 'reports')
        print(f"\nSaving reports to {output_dir}/...")
        text_path, json_path, csv_path = save_reports(issues, config['store_domain'], output_dir)

        print(f"  Text report: {text_path}")
        print(f"  JSON report: {json_path}")
        print(f"  CSV report: {csv_path}")

        print_summary(issues)

        critical_count = sum(1 for issue in issues if issue.severity == 'critical')
        if critical_count > 0:
            print(f"\n{critical_count} critical issue(s) found.")
            return 1

        print("\nHealth check complete.")
        return 0

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("Make sure config.yaml exists in the current directory.", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"\nConfiguration error: {e}", file=sys.stderr)
        return 1

    except ShopifyAPIError as e:
        print(f"\nShopify API error: {e}", file=sys.stderr)
        print("Check your store domain and access token.", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130

    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
