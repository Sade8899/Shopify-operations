"""
Cartability checks for products that are likely blocked from checkout.

Simulates cart validation using basic product rules since we don't have storefront
API access.
"""
from typing import List
from models import ProductSummary, HealthIssue


def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """Check for variants that likely cannot be added to cart."""
    issues = []

    for product in products:
        for variant in product.variants:
            if product.status != 'active':
                issues.append(HealthIssue(
                    check_name='cartability_check',
                    severity='info',
                    title=f'Variant in non-active product: {product.title} - {variant.title}',
                    details=f'Product status is "{product.status}", variant cannot be purchased',
                    recommended_fix='Activate the product to allow purchases',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))
                continue

            if not product.published_at:
                issues.append(HealthIssue(
                    check_name='cartability_check',
                    severity='info',
                    title=f'Variant in unpublished product: {product.title} - {variant.title}',
                    details=f'Product is not published, variant cannot be added to cart',
                    recommended_fix='Publish the product to make it available for purchase',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))
                continue

            try:
                price_value = float(variant.price)
            except (ValueError, TypeError):
                price_value = None

            if price_value is None or price_value == 0:
                issues.append(HealthIssue(
                    check_name='cartability_check',
                    severity='critical',
                    title=f'Published variant has no valid price: {product.title} - {variant.title}',
                    details=f'Variant ID {variant.variant_id} is in published product but has invalid/zero price',
                    recommended_fix='Set a valid price or unpublish the product',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))

            if variant.inventory_management == 'shopify':
                if (variant.inventory_policy == 'deny' and
                    variant.inventory_quantity is not None and
                    variant.inventory_quantity <= 0):

                    issues.append(HealthIssue(
                        check_name='cartability_check',
                        severity='critical',
                        title=f'Published variant blocked by inventory: {product.title} - {variant.title}',
                        details=f'Variant has inventory_policy "deny" with quantity {variant.inventory_quantity}',
                        recommended_fix='Restock inventory, change policy to "continue", or unpublish',
                        product_id=product.product_id,
                        variant_id=variant.variant_id,
                        sku=variant.sku
                    ))

            elif variant.inventory_management is None and not variant.available:
                issues.append(HealthIssue(
                    check_name='cartability_check',
                    severity='info',
                    title=f'Variant marked unavailable: {product.title} - {variant.title}',
                    details=f'Variant has no inventory management but available flag is false',
                    recommended_fix='Check variant availability settings in Shopify admin',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))

    return issues
