"""
Unit tests for report generation.
"""
import unittest
import json
from models import HealthIssue
from report import render_text, render_json


class TestReportGeneration(unittest.TestCase):
    """Test report rendering functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_issues = [
            HealthIssue(
                check_name='inventory_check',
                severity='critical',
                title='Out of stock product',
                details='Product has zero inventory',
                recommended_fix='Restock inventory',
                product_id=12345,
                variant_id=67890,
                sku='TEST-SKU-001'
            ),
            HealthIssue(
                check_name='inventory_check',
                severity='warning',
                title='Low stock warning',
                details='Product has low inventory',
                recommended_fix='Consider restocking',
                product_id=12346
            ),
            HealthIssue(
                check_name='product_integrity_check',
                severity='info',
                title='Missing SKU',
                details='Variant has no SKU',
                recommended_fix='Add SKU for tracking',
                product_id=12347,
                variant_id=67891
            )
        ]

    def test_render_text_includes_severity_counts(self):
        """Test that text report includes severity counts."""
        report = render_text(self.test_issues, 'test.myshopify.com')

        # Check that severity counts are present
        self.assertIn('Critical: 1', report)
        self.assertIn('Warning:  1', report)
        self.assertIn('Info:     1', report)
        self.assertIn('Total Issues: 3', report)

    def test_render_text_includes_all_issues(self):
        """Test that text report includes all issue titles."""
        report = render_text(self.test_issues, 'test.myshopify.com')

        # Check that all issue titles are present
        self.assertIn('Out of stock product', report)
        self.assertIn('Low stock warning', report)
        self.assertIn('Missing SKU', report)

    def test_render_text_includes_product_ids(self):
        """Test that text report includes product IDs."""
        report = render_text(self.test_issues, 'test.myshopify.com')

        self.assertIn('Product ID: 12345', report)
        self.assertIn('Product ID: 12346', report)
        self.assertIn('Product ID: 12347', report)

    def test_render_text_empty_issues(self):
        """Test text report with no issues."""
        report = render_text([], 'test.myshopify.com')

        self.assertIn('No issues found', report)
        self.assertIn('Total Issues: 0', report)

    def test_render_json_structure(self):
        """Test that JSON report has correct structure."""
        report_data = render_json(self.test_issues, 'test.myshopify.com')

        # Check top-level keys
        self.assertIn('store_domain', report_data)
        self.assertIn('generated_at', report_data)
        self.assertIn('summary', report_data)
        self.assertIn('issues', report_data)

        # Check store domain
        self.assertEqual(report_data['store_domain'], 'test.myshopify.com')

        # Check summary counts
        summary = report_data['summary']
        self.assertEqual(summary['total_issues'], 3)
        self.assertEqual(summary['critical'], 1)
        self.assertEqual(summary['warning'], 1)
        self.assertEqual(summary['info'], 1)

        # Check issues array
        self.assertEqual(len(report_data['issues']), 3)

    def test_render_json_issue_fields(self):
        """Test that JSON issues contain all required fields."""
        report_data = render_json(self.test_issues, 'test.myshopify.com')

        issue = report_data['issues'][0]
        required_fields = [
            'check_name', 'severity', 'title', 'details',
            'recommended_fix', 'product_id', 'variant_id', 'sku'
        ]

        for field in required_fields:
            self.assertIn(field, issue)

    def test_render_json_serializable(self):
        """Test that JSON report can be serialized."""
        report_data = render_json(self.test_issues, 'test.myshopify.com')

        # Should not raise exception
        json_str = json.dumps(report_data)
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 0)


class TestInventoryCheck(unittest.TestCase):
    """Test inventory check with mock data."""

    def test_inventory_check_flags_out_of_stock(self):
        """Test that inventory check flags out of stock products."""
        from models import ProductSummary, VariantSummary
        from checks.inventory_check import run

        # Create mock product that is out of stock
        variant = VariantSummary(
            variant_id=1,
            title='Default',
            sku='TEST-001',
            price='10.00',
            available=False,
            inventory_item_id=100,
            inventory_quantity=0,
            inventory_management='shopify',
            inventory_policy='deny'
        )

        product = ProductSummary(
            product_id=1,
            title='Test Product',
            handle='test-product',
            status='active',
            published_at='2024-01-01T00:00:00Z',
            tags='',
            variant_count=1,
            variants=[variant]
        )

        config = {}
        issues = run([product], config)

        # Should flag as out of stock
        self.assertGreater(len(issues), 0)
        self.assertTrue(any('out of stock' in issue.title.lower() for issue in issues))

    def test_inventory_check_flags_overselling(self):
        """Test that inventory check flags overselling variants."""
        from models import ProductSummary, VariantSummary
        from checks.inventory_check import run

        # Create variant that allows overselling
        variant = VariantSummary(
            variant_id=1,
            title='Default',
            sku='TEST-002',
            price='10.00',
            available=True,
            inventory_item_id=100,
            inventory_quantity=0,
            inventory_management='shopify',
            inventory_policy='continue'  # Allows overselling!
        )

        product = ProductSummary(
            product_id=2,
            title='Overselling Product',
            handle='overselling-product',
            status='active',
            published_at='2024-01-01T00:00:00Z',
            tags='',
            variant_count=1,
            variants=[variant]
        )

        config = {}
        issues = run([product], config)

        # Should flag as critical overselling issue
        critical_issues = [i for i in issues if i.severity == 'critical']
        self.assertGreater(len(critical_issues), 0)
        self.assertTrue(any('overselling' in issue.title.lower() for issue in critical_issues))


if __name__ == '__main__':
    unittest.main()
