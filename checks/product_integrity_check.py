"""
Product integrity check - identifies products with missing or invalid data.
"""
from typing import List
from models import ProductSummary, HealthIssue


def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """
    Check for product data integrity issues.

    Flags:
    - Products with no variants
    - Variants with missing or zero price
    - Products with missing title or handle

    Args:
        products: List of ProductSummary objects
        config: Configuration dictionary

    Returns:
        List of HealthIssue objects
    """
    issues = []

    for product in products:
        # Check for missing title
        if not product.title or product.title.strip() == '':
            issues.append(HealthIssue(
                check_name='product_integrity_check',
                severity='critical',
                title=f'Product missing title: ID {product.product_id}',
                details=f'Product ID {product.product_id} has no title',
                recommended_fix='Add a descriptive title to the product',
                product_id=product.product_id
            ))

        # Check for missing handle
        if not product.handle or product.handle.strip() == '':
            issues.append(HealthIssue(
                check_name='product_integrity_check',
                severity='warning',
                title=f'Product missing handle: {product.title or "Untitled"}',
                details=f'Product ID {product.product_id} has no URL handle',
                recommended_fix='Generate or assign a URL handle for the product',
                product_id=product.product_id
            ))

        # Check for products with no variants
        if product.variant_count == 0 or len(product.variants) == 0:
            issues.append(HealthIssue(
                check_name='product_integrity_check',
                severity='critical',
                title=f'Product has no variants: {product.title}',
                details=f'Product ID {product.product_id} has no variants and cannot be sold',
                recommended_fix='Add at least one variant to the product',
                product_id=product.product_id
            ))
            continue  # Skip variant checks if no variants exist

        # Check each variant for price issues
        for variant in product.variants:
            try:
                price_value = float(variant.price)
            except (ValueError, TypeError):
                price_value = None

            # Missing or invalid price
            if price_value is None:
                issues.append(HealthIssue(
                    check_name='product_integrity_check',
                    severity='critical',
                    title=f'Variant has invalid price: {product.title} - {variant.title}',
                    details=f'Variant ID {variant.variant_id} has invalid price value: {variant.price}',
                    recommended_fix='Set a valid numeric price for the variant',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))

            # Zero price
            elif price_value == 0:
                issues.append(HealthIssue(
                    check_name='product_integrity_check',
                    severity='critical',
                    title=f'Variant has zero price: {product.title} - {variant.title}',
                    details=f'Variant ID {variant.variant_id} (SKU: {variant.sku or "N/A"}) has price of $0.00',
                    recommended_fix='Set a non-zero price or unpublish if this is a placeholder',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))

            # Missing SKU (warning, not critical)
            if not variant.sku or variant.sku.strip() == '':
                issues.append(HealthIssue(
                    check_name='product_integrity_check',
                    severity='info',
                    title=f'Variant missing SKU: {product.title} - {variant.title}',
                    details=f'Variant ID {variant.variant_id} has no SKU assigned',
                    recommended_fix='Assign a SKU for inventory tracking and fulfillment',
                    product_id=product.product_id,
                    variant_id=variant.variant_id
                ))

    return issues
