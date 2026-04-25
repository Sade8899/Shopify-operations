"""Inventory checks for stock and overselling issues."""
from typing import List
from models import ProductSummary, HealthIssue


def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """Check for inventory issues."""
    issues = []

    for product in products:
        if product.status != 'active':
            continue

        total_inventory = 0
        for variant in product.variants:
            if variant.inventory_quantity is not None:
                total_inventory += variant.inventory_quantity

        if product.published_at and total_inventory <= 0:
            issues.append(HealthIssue(
                check_name='inventory_check',
                severity='warning',
                title=f'Published product out of stock: {product.title}',
                details=f'Product ID {product.product_id} is published and active but has total inventory of {total_inventory}',
                recommended_fix='Restock inventory or unpublish product to avoid customer disappointment',
                product_id=product.product_id
            ))

        for variant in product.variants:
            if (variant.inventory_management == 'shopify' and
                variant.inventory_quantity is not None and
                variant.inventory_quantity <= 0 and
                variant.inventory_policy == 'continue'):

                issues.append(HealthIssue(
                    check_name='inventory_check',
                    severity='critical',
                    title=f'Variant allows overselling when out of stock: {product.title} - {variant.title}',
                    details=f'Variant ID {variant.variant_id} has inventory {variant.inventory_quantity} but policy is "continue"',
                    recommended_fix='Change inventory policy to "deny" or restock inventory',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))

            elif variant.inventory_management is None and not variant.available:
                issues.append(HealthIssue(
                    check_name='inventory_check',
                    severity='info',
                    title=f'Unmanaged variant marked unavailable: {product.title} - {variant.title}',
                    details=f'Variant ID {variant.variant_id} has no inventory management but is marked unavailable',
                    recommended_fix='Review variant availability settings or enable inventory tracking',
                    product_id=product.product_id,
                    variant_id=variant.variant_id,
                    sku=variant.sku
                ))

    return issues
