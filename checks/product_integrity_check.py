"""Product data checks for missing or invalid catalogue fields."""
from typing import List
from models import ProductSummary, HealthIssue


def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """Check for product data integrity issues."""
    issues = []

    for product in products:
        if not product.title or product.title.strip() == '':
            issues.append(HealthIssue(
                check_name='product_integrity_check',
                severity='critical',
                title=f'Product missing title: ID {product.product_id}',
                details=f'Product ID {product.product_id} has no title',
                recommended_fix='Add a descriptive title to the product',
                product_id=product.product_id
            ))

        if not product.handle or product.handle.strip() == '':
            issues.append(HealthIssue(
                check_name='product_integrity_check',
                severity='warning',
                title=f'Product missing handle: {product.title or "Untitled"}',
                details=f'Product ID {product.product_id} has no URL handle',
                recommended_fix='Generate or assign a URL handle for the product',
                product_id=product.product_id
            ))

        if product.variant_count == 0 or len(product.variants) == 0:
            issues.append(HealthIssue(
                check_name='product_integrity_check',
                severity='critical',
                title=f'Product has no variants: {product.title}',
                details=f'Product ID {product.product_id} has no variants and cannot be sold',
                recommended_fix='Add at least one variant to the product',
                product_id=product.product_id
            ))
            continue

        for variant in product.variants:
            try:
                price_value = float(variant.price)
            except (ValueError, TypeError):
                price_value = None

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
