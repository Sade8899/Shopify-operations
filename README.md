# Shopify Store Health and Automation Monitor

A command-line tool for Shopify operations teams to run automated health checks against a Shopify store and generate actionable reports for stakeholders.

## Problem Statement

E-commerce operations teams face constant challenges keeping Shopify stores healthy:
- Products go out of stock without alerting stakeholders
- Product data integrity issues (missing prices, SKUs, or variants) can block sales
- Inventory policies misconfigured leading to overselling or underselling
- Subscription products may lack proper selling plan configurations
- Google Merchant Center disapprovals may go unnoticed

This tool automates discovery of these issues and generates clear, actionable reports that both technical and non-technical stakeholders can understand.

## Features

### Health Checks

1. **Inventory Check** - Identifies out-of-stock products and inventory policy misconfigurations
2. **Product Integrity Check** - Finds products with missing variants, prices, or SKUs
3. **Cartability Check** - Flags products that likely cannot be added to cart
4. **Subscription Check** - Detects subscription products and flags configuration issues
5. **Merchant Policy Check** - Identifies products tagged for Google Merchant Center issues

### Reporting

- **Text Reports**: Human-readable summaries with issue counts by severity
- **JSON Reports**: Machine-readable data for integration with other tools
- **Timestamped Output**: All reports saved with timestamps for historical tracking
- **Severity Levels**: Issues categorized as Critical, Warning, or Info

## Requirements

- Python 3.11+
- Shopify Admin API access token
- Internet connection

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Shopify-operations
```

2. Install dependencies:
```bash
pip install requests pyyaml
```

## Configuration

### 1. Get a Shopify Admin API Access Token

You need an Admin API access token with the following permissions:
- `read_products`
- `read_inventory`
- `read_locations`

To create one:
1. Log in to your Shopify admin panel
2. Navigate to Settings > Apps and sales channels > Develop apps
3. Create a new app or select an existing one
4. Configure Admin API scopes (read_products, read_inventory, read_locations)
5. Install the app and copy the Admin API access token

### 2. Configure config.yaml

Edit `config.yaml` with your store details:

```yaml
# Your Shopify store domain (without https://)
store_domain: your-store.myshopify.com

# Shopify Admin API version
admin_api_version: 2024-04

# Admin API access token
admin_access_token: shpat_your_token_here

# Tag used to identify products disapproved by Google Merchant Center
google_merchant_product_tag: google_merchant_disapproved

# Directory where reports will be saved
report_output_dir: reports

# Dry run mode - set to false when ready for live checks
dry_run: false

# Maximum number of products to fetch and analyze
max_products: 250

# API request timeout in seconds
timeout_seconds: 15

# Keywords to detect subscription products
subscription_tag_keywords:
  - subscription
  - subscribe
  - recurring
```

### 3. Environment Variable Override (Optional)

For security, you can set the access token via environment variable:

```bash
export SHOPIFY_ADMIN_ACCESS_TOKEN=shpat_your_token_here
```

This overrides the `admin_access_token` in config.yaml.

## Usage

Run the health monitor:

```bash
python run.py
```

### Example Output

```
Shopify Store Health and Automation Monitor
================================================================================

Loading configuration...
Configuration loaded for store: your-store.myshopify.com

Initializing Shopify API client...

Fetching up to 250 products from Shopify...
Retrieved 150 products
Successfully parsed 150 products

Running 5 health checks...
  Running inventory_check... found 8 issue(s)
  Running product_integrity_check... found 3 issue(s)
  Running cartability_check... found 5 issue(s)
  Running subscription_check... found 2 issue(s)
  Running merchant_policy_check... found 1 issue(s)

Saving reports to reports/...
  Text report: reports/report_20240115_143022.txt
  JSON report: reports/report_20240115_143022.json

================================================================================
HEALTH CHECK SUMMARY
================================================================================
Total Issues Found: 19
  🔴 Critical: 6
  🟡 Warning:  8
  🔵 Info:     5

Issues by Check:
  cartability_check: 5
  inventory_check: 8
  merchant_policy_check: 1
  product_integrity_check: 3
  subscription_check: 2
================================================================================

⚠️  6 critical issue(s) require immediate attention!
```

### Sample Report Excerpt

```
================================================================================
CHECK: INVENTORY CHECK
================================================================================

[CRITICAL] - 2 issue(s)
--------------------------------------------------------------------------------
  • Variant allows overselling when out of stock: Winter Jacket - Medium
    Product ID: 7891011 | Variant ID: 41234567 | SKU: WJ-M-BLK
    Details: Variant ID 41234567 has inventory 0 but policy is "continue"
    Fix: Change inventory policy to "deny" or restock inventory

[WARNING] - 3 issue(s)
--------------------------------------------------------------------------------
  • Published product out of stock: Summer T-Shirt
    Product ID: 7891012
    Details: Product ID 7891012 is published and active but has total inventory of 0
    Fix: Restock inventory or unpublish product to avoid customer disappointment
```

## Extending with New Checks

To add a new health check:

1. Create a new file in `checks/` directory (e.g., `checks/my_custom_check.py`)

2. Implement a `run()` function:

```python
from typing import List
from models import ProductSummary, HealthIssue

def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """
    Your check description.

    Args:
        products: List of ProductSummary objects
        config: Configuration dictionary

    Returns:
        List of HealthIssue objects
    """
    issues = []

    for product in products:
        # Your check logic here
        if some_condition:
            issues.append(HealthIssue(
                check_name='my_custom_check',
                severity='warning',  # 'critical', 'warning', or 'info'
                title='Issue title',
                details='Detailed description',
                recommended_fix='How to fix this',
                product_id=product.product_id
            ))

    return issues
```

3. Import your check in `checks/__init__.py`:

```python
from . import my_custom_check

ALL_CHECKS = [
    # ... existing checks ...
    my_custom_check
]
```

## Testing

Run unit tests:

```bash
python -m unittest discover tests
```

Run specific test file:

```bash
python -m unittest tests.test_report
```

## Security Notes

- **Never commit your access token** to version control
- Use environment variables for tokens in CI/CD environments
- Tokens should have minimal required permissions (read-only)
- Rotate tokens regularly following your security policy
- The `reports/` directory may contain sensitive product data - add to `.gitignore`

## Limitations

### Known Limitations

1. **Cartability is Heuristic**: The tool cannot actually test adding products to cart via API. It uses configuration-based heuristics to predict cartability issues.

2. **Subscription Checks are Informational**: Selling plan data is not available in basic REST API product responses. Subscription checks identify potential subscription products but cannot verify selling plan configuration without integration to specific subscription apps (Recharge, Seal Subscriptions, etc.).

3. **No Metafield Access**: Product metafields (like GTIN, MPN, brand) are not easily accessible without additional API calls. The merchant policy check uses tag-based heuristics instead.

4. **Rate Limiting**: The tool respects Shopify API rate limits with automatic retries, but very large stores (1000+ products) may take several minutes to analyze.

5. **Read-Only**: This tool only reads data and generates reports. It does not modify your store.

## Performance Optimization

- Set `max_products` to limit analysis scope for large stores
- API calls are batched where possible (e.g., inventory levels)
- Products are fetched once and reused across all checks
- Pagination is handled automatically

## Troubleshooting

### "Configuration file not found"
Make sure `config.yaml` exists in the directory where you run the script.

### "Client error 401"
Your access token is invalid or expired. Generate a new one.

### "Client error 403"
Your access token lacks required permissions. Ensure it has read_products, read_inventory, and read_locations scopes.

### "Rate limit exceeded"
The tool already implements retry logic. If this persists, reduce `max_products` or wait before running again.

## Project Structure

```
Shopify-operations/
├── run.py                          # Main entry point
├── config.yaml                     # Configuration file
├── shopify_client.py              # Shopify API client
├── models.py                       # Data models
├── report.py                       # Report generation
├── checks/                         # Health check modules
│   ├── __init__.py
│   ├── inventory_check.py
│   ├── product_integrity_check.py
│   ├── cartability_check.py
│   ├── subscription_check.py
│   └── merchant_policy_check.py
├── tests/                          # Unit tests
│   ├── __init__.py
│   └── test_report.py
├── reports/                        # Generated reports (created at runtime)
└── README.md                       # This file
```

## Contributing

Contributions are welcome! Areas for improvement:
- Additional health checks (SEO, image optimization, etc.)
- Integration with alerting systems (Slack, email)
- Historical trend analysis
- GraphQL API support for better performance
- Metafield analysis

## License

This is a portfolio project. Use freely for learning and professional development.

## Author

Built as a portfolio project for Shopify operations roles, demonstrating:
- Shopify Admin API integration
- Python best practices
- Clean architecture and extensibility
- Production-ready error handling
- Documentation for non-technical stakeholders
