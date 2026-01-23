# Project Summary: Shopify Store Health and Automation Monitor

## Overview
A production-ready Python CLI tool for automated Shopify store health monitoring, built as a portfolio project for Shopify operations roles.

## Complete File Structure

```
Shopify-operations/
├── run.py                          # Main entry point - run with `python run.py`
├── config.yaml                     # Active configuration (gitignored)
├── config.yaml.example             # Example configuration template
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── README.md                       # Comprehensive documentation
│
├── shopify_client.py              # Shopify Admin API client
│   ├── ShopifyClient class
│   ├── Retry logic for 429 and 5xx errors
│   ├── Pagination support
│   └── Error handling
│
├── models.py                       # Data models
│   ├── ProductSummary dataclass
│   ├── VariantSummary dataclass
│   ├── HealthIssue dataclass
│   └── parse_product() helper
│
├── report.py                       # Report generation
│   ├── render_text() - Human-readable reports
│   ├── render_json() - Machine-readable reports
│   └── save_reports() - File output with timestamps
│
├── checks/                         # Health check modules
│   ├── __init__.py                # Check registry
│   ├── inventory_check.py         # Out of stock & inventory issues
│   ├── product_integrity_check.py # Missing data validation
│   ├── cartability_check.py       # Cart addition blockers
│   ├── subscription_check.py      # Subscription product detection
│   └── merchant_policy_check.py   # Google Merchant issues
│
├── tests/                          # Unit tests
│   ├── __init__.py
│   └── test_report.py             # Report and check tests (9 tests)
│
└── reports/                        # Generated reports directory (created at runtime)

```

## Key Features Implemented

### ✅ Core Functionality
- Shopify Admin API integration with proper authentication
- Product and inventory data fetching with pagination
- 5 comprehensive health check modules
- Text and JSON report generation
- Timestamped report files
- Console output with severity indicators

### ✅ Production Quality
- Comprehensive error handling
- API retry logic for rate limits and server errors
- Environment variable configuration support
- Configurable timeouts and limits
- Clean separation of concerns
- Type hints throughout

### ✅ Developer Experience
- Modular architecture for easy extension
- Well-documented code
- Unit tests with 100% pass rate
- Example configuration files
- Comprehensive README with usage examples

### ✅ Security
- Gitignore for sensitive files
- Environment variable support for tokens
- No hardcoded credentials
- Read-only API operations

## Technical Highlights

### API Client (shopify_client.py)
- Automatic retry with exponential backoff
- Rate limit handling (429 responses)
- Link header pagination support
- Batched inventory level queries (50 per batch)
- Proper timeout handling

### Health Checks
1. **Inventory Check**: Identifies overselling configurations and out-of-stock published products
2. **Product Integrity**: Validates product data completeness (variants, prices, SKUs)
3. **Cartability**: Heuristic checks for cart addition blockers
4. **Subscription**: Detects subscription products by tags/type
5. **Merchant Policy**: Flags Google Merchant Center issues

### Report System
- Severity-based categorization (Critical, Warning, Info)
- Grouped by check and severity
- Includes product IDs, variant IDs, and SKUs
- Clear recommended fixes for each issue
- Both human and machine-readable formats

## Test Coverage

All 9 unit tests passing:
- Text report rendering
- JSON report structure
- Severity counting
- Issue serialization
- Inventory check logic
- Out-of-stock detection
- Overselling detection

## How to Use

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your store:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your store details
   ```

3. Run health checks:
   ```bash
   python run.py
   ```

4. Review reports in `reports/` directory

## Extensibility

Adding new checks is straightforward:
1. Create new file in `checks/` directory
2. Implement `run(products, config)` function returning list of HealthIssue
3. Register in `checks/__init__.py`

## Business Value

This tool demonstrates:
- **Operations Excellence**: Automates manual store audits
- **Stakeholder Communication**: Clear reports for non-technical teams
- **Proactive Monitoring**: Catches issues before they impact sales
- **Scalability**: Handles stores with hundreds of products efficiently
- **Maintainability**: Clean architecture for ongoing development

## Portfolio Strengths

1. **Real-world application** solving actual e-commerce operations problems
2. **Production-ready code** with error handling, testing, and documentation
3. **API integration** with authentication, pagination, and rate limiting
4. **Clean architecture** demonstrating software engineering best practices
5. **Stakeholder focus** with clear, actionable output for non-technical users

---

Built with Python 3.11+ | Uses Shopify Admin API 2024-04 | Ready for GitHub
