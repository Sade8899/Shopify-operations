"""Tests for product and cartability checks."""
import unittest

from checks.cartability_check import run as run_cartability_check
from checks.product_integrity_check import run as run_product_integrity_check
from models import ProductSummary, VariantSummary
from report import render_json


def make_variant(**overrides):
    data = {
        'variant_id': 1,
        'title': 'Default',
        'sku': 'DEMO-001',
        'price': '10.00',
        'available': True,
        'inventory_item_id': 100,
        'inventory_quantity': 5,
        'inventory_management': 'shopify',
        'inventory_policy': 'deny'
    }
    data.update(overrides)
    return VariantSummary(**data)


def make_product(**overrides):
    variant = overrides.pop('variant', make_variant())
    variants = overrides.pop('variants', [variant])
    data = {
        'product_id': 1,
        'title': 'Demo Product',
        'handle': 'demo-product',
        'status': 'active',
        'published_at': '2026-01-01T00:00:00Z',
        'tags': '',
        'variant_count': len(variants),
        'variants': variants,
        'product_type': None
    }
    data.update(overrides)
    return ProductSummary(**data)


class TestProductIntegrityCheck(unittest.TestCase):
    def test_flags_missing_sku(self):
        product = make_product(variant=make_variant(sku=''))

        issues = run_product_integrity_check([product], {})

        self.assertTrue(any('missing SKU' in issue.title for issue in issues))
        self.assertTrue(any(issue.severity == 'info' for issue in issues))

    def test_flags_zero_price(self):
        product = make_product(variant=make_variant(price='0.00'))

        issues = run_product_integrity_check([product], {})

        self.assertTrue(any('zero price' in issue.title for issue in issues))
        self.assertTrue(any(issue.severity == 'critical' for issue in issues))


class TestCartabilityCheck(unittest.TestCase):
    def test_flags_unpublished_product(self):
        product = make_product(published_at=None)

        issues = run_cartability_check([product], {})

        self.assertTrue(any('unpublished product' in issue.title for issue in issues))
        self.assertTrue(any(issue.severity == 'info' for issue in issues))

    def test_sample_issue_data_can_render_json_report(self):
        product = make_product(variant=make_variant(price='0.00', sku=''))
        issues = run_product_integrity_check([product], {})

        report = render_json(issues, 'example-store.myshopify.com')

        self.assertEqual(report['store_domain'], 'example-store.myshopify.com')
        self.assertEqual(report['summary']['total_issues'], len(issues))
        self.assertGreaterEqual(report['summary']['critical'], 1)


if __name__ == '__main__':
    unittest.main()
