"""
Inventory health check - identifies out of stock and inventory issues.
"""
from typing import List
from models import ProductSummary, HealthIssue


def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """
    Check for inventory issues.

    Flags:
    - Products that are active/published but have total inventory <= 0
    - Variants with Shopify inventory management that are out of stock but purchasable

    Args:
        products: List of ProductSummary objects
        config: Configuration dictionary

    Returns:
        List of HealthIssue objects
    """
    issues = []

    for product in products:
        # Skip draft products
        if product.status != 'active':
            continue

        # Calculate total inventory across all variants
        total_inventory = 0
        for variant in product.variants:
            if variant.inventory_quantity is not None:
                total_inventory += variant.inventory_quantity

        # Check if published product has zero or negative inventory
        if product.published_at and total_inventory <= 0:
            issues.append(HealthIssue(
                check_name='inventory_check',
                severity='warning',
                title=f'Published product out of stock: {product.title}',
                details=f'Product ID {product.product_id} is published and active but has total inventory of {total_inventory}',
                recommended_fix='Restock inventory or unpublish product to avoid customer disappointment',
                product_id=product.product_id
            ))

        # Check individual variants for misleading availability
        for variant in product.variants:
            # Variant managed by Shopify, out of stock, but can still be purchased
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

            # Variant not managed but marked as unavailable
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
