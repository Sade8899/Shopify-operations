"""
Subscription product checks based on tags and product type.

Selling plan details are not included in the basic REST product response used by
this tool, so these findings are prompts for manual review.
"""
from typing import List
from models import ProductSummary, HealthIssue


def run(products: List[ProductSummary], config: dict) -> List[HealthIssue]:
    """Check for likely subscription product configuration issues."""
    issues = []

    keywords = config.get('subscription_tag_keywords', ['subscription', 'subscribe', 'recurring'])

    for product in products:
        tags_lower = product.tags.lower() if product.tags else ''
        product_type_lower = product.product_type.lower() if product.product_type else ''

        is_subscription = False
        matched_keyword = None

        for keyword in keywords:
            if keyword.lower() in tags_lower or keyword.lower() in product_type_lower:
                is_subscription = True
                matched_keyword = keyword
                break

        if is_subscription:
            issues.append(HealthIssue(
                check_name='subscription_check',
                severity='info',
                title=f'Subscription product detected: {product.title}',
                details=f'Product contains "{matched_keyword}" in tags or product type. Has {product.variant_count} variant(s).',
                recommended_fix='Verify selling plan configuration in your subscription app (Recharge, Seal, etc.)',
                product_id=product.product_id
            ))

            if product.variant_count == 0:
                issues.append(HealthIssue(
                    check_name='subscription_check',
                    severity='warning',
                    title=f'Subscription product has no variants: {product.title}',
                    details=f'Product appears to be a subscription but has no purchasable variants',
                    recommended_fix='Add variants or verify product configuration',
                    product_id=product.product_id
                ))

            if product.published_at and product.status != 'active':
                issues.append(HealthIssue(
                    check_name='subscription_check',
                    severity='warning',
                    title=f'Published subscription not active: {product.title}',
                    details=f'Product is published but status is "{product.status}"',
                    recommended_fix='Activate product or unpublish to avoid customer confusion',
                    product_id=product.product_id
                ))

    return issues
