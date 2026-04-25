# Shopify Store Health Monitor

A Python CLI tool that checks a Shopify store for common product, inventory and configuration issues using the Shopify Admin REST API.

Shopify Store Health Monitor is a Python CLI tool for running basic health checks on a Shopify store catalogue.

I built it because e-commerce operations teams often have to manually check for small issues that can affect sales or customer experience, such as missing SKUs, products without prices, inventory problems, or products that may not be purchasable.

The tool connects to the Shopify Admin REST API, fetches product data, runs a set of validation checks, and produces text and JSON reports.

## Why I Built This

I wanted to build a practical operations tool using Python rather than a purely academic project. Shopify store operations involve a lot of small checks that are easy to miss when a catalogue changes often.

This project gave me a way to practise API integration, data validation, CLI tooling, report generation and unit testing around a realistic e-commerce operations problem.

## What It Does

The script reads Shopify API credentials from a local config file, fetches products from the Shopify Admin REST API, converts the API response into simple Python models, and runs health checks against each product and variant.

It then prints a summary in the terminal and saves reports in text and JSON formats.

## Tech Stack

- Python 3.11 recommended
- Shopify Admin REST API
- `requests` for HTTP requests
- `PyYAML` for configuration
- `unittest` for tests

Dependencies are listed in [requirements.txt](requirements.txt).

## Key Features

- Fetches Shopify products with REST API pagination.
- Checks for missing titles, handles, variants, SKUs and prices.
- Flags zero-price or invalid-price variants.
- Flags active published products with no inventory.
- Flags variants that allow overselling when inventory is zero or below.
- Uses rule-based cartability checks for inactive, unpublished, out-of-stock or unpriced variants.
- Flags likely subscription products based on configured tag or product type keywords.
- Flags products with configured merchant policy tags.
- Generates text and JSON reports.

## Setup

Clone the repository and install the dependencies:

```bash
git clone <repository-url>
cd Shopify-operations
pip install -r requirements.txt
```

## Configuration

Copy the example config file:

```bash
cp config.yaml.example config.yaml
```

On Windows PowerShell:

```powershell
Copy-Item config.yaml.example config.yaml
```

Edit `config.yaml` with your own Shopify development store details:

```yaml
store_domain: example.myshopify.com
admin_api_version: 2024-04
admin_access_token: replace_with_shopify_admin_access_token
google_merchant_product_tag: google_merchant_disapproved
report_output_dir: reports
dry_run: true
max_products: 250
timeout_seconds: 15
subscription_tag_keywords:
  - subscription
  - subscribe
  - recurring
```

The token can also be provided through an environment variable:

```bash
export SHOPIFY_ADMIN_ACCESS_TOKEN=replace_with_shopify_admin_access_token
```

On Windows PowerShell:

```powershell
$env:SHOPIFY_ADMIN_ACCESS_TOKEN = "replace_with_shopify_admin_access_token"
```

The access token should have read-only scopes for product and inventory data, such as `read_products`, `read_inventory` and `read_locations`.

Do not commit `config.yaml`, `.env`, access tokens or generated reports. These files are ignored because they can contain private store data.

## Running The Tool

Run the CLI:

```bash
python run.py
```

Use a different config path:

```bash
python run.py --config path/to/config.yaml
```

The script will:

- load `config.yaml`
- fetch products from the Shopify Admin REST API
- run the configured checks
- print a summary
- save reports in the configured `reports/` directory

Run tests:

```bash
python -m unittest discover tests
```

## Example Output

Example reports using fake data are included here:

- [examples/sample_report.txt](examples/sample_report.txt)
- [examples/sample_report.json](examples/sample_report.json)

Short example:

```text
HEALTH CHECK SUMMARY
================================================================================
Total Issues Found: 5
  Critical: 2
  Warning:  1
  Info:     2

Issues by Check:
  cartability_check: 1
  inventory_check: 1
  merchant_policy_check: 1
  product_integrity_check: 2
================================================================================
```

## Project Structure

```text
Shopify-operations/
|-- checks/
|   |-- cartability_check.py
|   |-- inventory_check.py
|   |-- merchant_policy_check.py
|   |-- product_integrity_check.py
|   `-- subscription_check.py
|-- examples/
|   |-- sample_report.json
|   `-- sample_report.txt
|-- tests/
|   |-- test_checks.py
|   `-- test_report.py
|-- config.yaml.example
|-- models.py
|-- report.py
|-- requirements.txt
|-- run.py
`-- shopify_client.py
```

## What I Learned

- How to structure a small Python CLI project.
- How to work with a real external REST API and handle pagination.
- How to keep local configuration separate from committed code.
- How to turn API responses into simpler internal models.
- How to write checks that produce readable operational reports.
- How to test report output and validation logic with fake data.

## Current Limitations

- Cartability checks are rule based and do not simulate a real checkout.
- The tool currently runs locally as a CLI script.
- It does not include a database or scheduled monitoring.
- For very large stores, performance may need improvement.
- Some checks depend on what data the Shopify API returns and what permissions the token has.
- Subscription checks only identify likely subscription products from tags or product types because selling plan data is not included in the basic product response used here.
- Merchant policy checks are tag based and do not connect directly to Google Merchant Center.

## Next Steps

- Expand the GitHub Actions workflow if the project adds linting or coverage checks.
- Add more unit tests for checks and report generation.
- Add more fake sample data for testing edge cases.
- Consider async fetching for large catalogues.
- Optionally add Slack or email alerts later.
