"""Example usage for AgenticCommerceCartCheckoutEngine."""
import json
from client import AgenticCommerceCartCheckoutEngine

def main():
    print("=== Agentic Commerce Intent & Cart Checkout Demo ===")
    commerce = AgenticCommerceCartCheckoutEngine()
    
    # 1. Parse high-level consumer goal
    intent = commerce.parse_shopping_intent("Plan outdoor barbecue party with steaks from Instacart and lawn chairs from Walmart", budget_max=250.0)
    print("Parsed Intent:", json.dumps(intent, indent=2))
    
    # 2. Aggregate multi-merchant cart
    items = [
        {"merchant": "Instacart", "title": "Prime Ribeye Steak 2pk", "quantity": 2, "unit_price_usd": 24.50},
        {"merchant": "Instacart", "title": "Charcoal Briquettes 15lb", "quantity": 1, "unit_price_usd": 14.99},
        {"merchant": "Walmart", "title": "Foldable Heavy-Duty Lawn Chair", "quantity": 2, "unit_price_usd": 29.99}
    ]
    cart = commerce.aggregate_multi_merchant_cart(items)
    print("\nAggregated Cart:", json.dumps(cart, indent=2))
    
    # 3. Calculate checkout breakdown
    cid = cart["cart_id"]
    summary = commerce.calculate_checkout_summary(cid, coupon_code="GENPARK10")
    print("\nCheckout Summary:", json.dumps(summary, indent=2))
    
    # 4. Generate delegated order
    order = commerce.generate_delegated_order(cid)
    print("\nFinal Delegated Order Manifest:", json.dumps(order, indent=2))

if __name__ == "__main__":
    main()
