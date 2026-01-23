"""
Merchant policy check - identifies products that may violate merchant center policies.

Since we don't have direct Google Merchant Center API access, this check identifies
products flagged with merchant-related tags in Shopify.
"""
from typing import List
from models import ProductSummary, HealthIssue


def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """
    Check for products flagged for merchant policy issues.

    Identifies products tagged with:
    - The configured google_merchant_product_tag
    - Generic merchant policy tags like 'disapproved', 'merchant'

    Args:
        products: List of ProductSummary objects
        config: Configuration dictionary

    Returns:
        List of HealthIssue objects
    """
    issues = []

    # Get the configured merchant tag
    merchant_tag = config.get('google_merchant_product_tag', 'google_merchant_disapproved')

    # Keywords that might indicate merchant issues
    policy_keywords = ['disapproved', 'merchant', 'policy_violation', 'suspended']

    for product in products:
        tags_lower = product.tags.lower() if product.tags else ''

        # Check for configured merchant tag
        if merchant_tag.lower() in tags_lower:
            issues.append(HealthIssue(
                check_name='merchant_policy_check',
                severity='warning',
                title=f'Product flagged for Google Merchant: {product.title}',
                details=f'Product is tagged with "{merchant_tag}"',
                recommended_fix='Review product in Google Merchant Center and fix policy violations',
                product_id=product.product_id
            ))

        # Check for other policy-related keywords
        else:
            for keyword in policy_keywords:
                if keyword in tags_lower:
                    issues.append(HealthIssue(
                        check_name='merchant_policy_check',
                        severity='warning',
                        title=f'Product may have merchant policy issue: {product.title}',
                        details=f'Product tags contain "{keyword}"',
                        recommended_fix='Review merchant center status and product compliance',
                        product_id=product.product_id
                    ))
                    break  # Only report once per product

        # Additional check: Published products that might need GTIN/MPN
        # This is a heuristic since we can't access metafields easily
        if product.published_at and product.status == 'active':
            # Check if product type suggests it needs identifiers (e.g., electronics, books)
            product_type_lower = product.product_type.lower() if product.product_type else ''
            identifier_required_types = [
                'electronics', 'books', 'media', 'toys', 'games',
                'apparel', 'clothing', 'shoes', 'accessories'
            ]

            needs_identifier = any(ptype in product_type_lower for ptype in identifier_required_types)

            if needs_identifier:
                # Check if any variants have SKU (rough proxy for having identifiers)
                has_skus = any(variant.sku for variant in product.variants)

                if not has_skus:
                    issues.append(HealthIssue(
                        check_name='merchant_policy_check',
                        severity='info',
                        title=f'Product may need GTIN/MPN identifiers: {product.title}',
                        details=f'Product type "{product.product_type}" typically requires identifiers for merchant feeds',
                        recommended_fix='Add GTIN, MPN, or brand information to product and variants',
                        product_id=product.product_id
                    ))

    return issues
