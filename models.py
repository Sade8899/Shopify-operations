"""
Data models for Shopify Store Health Monitor.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class VariantSummary:
    """Summary of a product variant."""
    variant_id: int
    title: str
    sku: Optional[str]
    price: str
    available: bool
    inventory_item_id: int
    inventory_quantity: Optional[int]
    inventory_management: Optional[str]
    inventory_policy: str


@dataclass
class ProductSummary:
    """Summary of a Shopify product."""
    product_id: int
    title: str
    handle: str
    status: str
    published_at: Optional[str]
    tags: str
    variant_count: int
    variants: List[VariantSummary] = field(default_factory=list)
    product_type: Optional[str] = None


@dataclass
class HealthIssue:
    """Represents a health check issue found in the store."""
    check_name: str
    severity: str  # 'critical', 'warning', or 'info'
    title: str
    details: str
    recommended_fix: str
    product_id: Optional[int] = None
    variant_id: Optional[int] = None
    sku: Optional[str] = None

    def __post_init__(self):
        """Validate severity level."""
        valid_severities = {'critical', 'warning', 'info'}
        if self.severity not in valid_severities:
            raise ValueError(f"Severity must be one of {valid_severities}, got '{self.severity}'")


def parse_product(product_data: dict) -> ProductSummary:
    """Parse raw Shopify API product data into ProductSummary."""
    variants = []
    for variant in product_data.get('variants', []):
        variants.append(VariantSummary(
            variant_id=variant['id'],
            title=variant.get('title', ''),
            sku=variant.get('sku'),
            price=variant.get('price', '0.00'),
            available=variant.get('available', False),
            inventory_item_id=variant.get('inventory_item_id', 0),
            inventory_quantity=variant.get('inventory_quantity'),
            inventory_management=variant.get('inventory_management'),
            inventory_policy=variant.get('inventory_policy', 'deny')
        ))

    return ProductSummary(
        product_id=product_data['id'],
        title=product_data.get('title', ''),
        handle=product_data.get('handle', ''),
        status=product_data.get('status', ''),
        published_at=product_data.get('published_at'),
        tags=product_data.get('tags', ''),
        variant_count=len(variants),
        variants=variants,
        product_type=product_data.get('product_type')
    )
