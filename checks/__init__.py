"""
Health check modules for Shopify Store Health Monitor.
"""
from . import inventory_check
from . import product_integrity_check
from . import cartability_check
from . import subscription_check
from . import merchant_policy_check

# List of all available checks
ALL_CHECKS = [
    inventory_check,
    product_integrity_check,
    cartability_check,
    subscription_check,
    merchant_policy_check
]
