"""MCP JSON-RPC stdio server for genpark-agentic-commerce-intent-cart-checkout-skill."""
import sys
import json
from client import AgenticCommerceCartCheckoutEngine

engine = AgenticCommerceCartCheckoutEngine()

def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})
    if name != "manage_commerce_intent":
        return {"error": f"Unknown tool '{name}'"}
        
    action = args.get("action")
    if action == "parse_shopping_intent":
        return engine.parse_shopping_intent(
            goal_text=args.get("goal_text", "Order weekly groceries"),
            budget_max=float(args.get("budget_max", 300.0))
        )
    elif action == "aggregate_multi_merchant_cart":
        return engine.aggregate_multi_merchant_cart(
            items=args.get("items", []),
            cart_id=args.get("cart_id")
        )
    elif action == "calculate_checkout_summary":
        return engine.calculate_checkout_summary(
            cart_id=args.get("cart_id", ""),
            coupon_code=args.get("coupon_code")
        )
    elif action == "generate_delegated_order":
        return engine.generate_delegated_order(
            cart_id=args.get("cart_id", ""),
            delivery_address=args.get("delivery_address", "100 Market St, San Francisco CA")
        )
    else:
        return {"error": f"Unknown action '{action}'"}

def main():
    if "--test" in sys.argv:
        print("[TEST] Running self-test for AgenticCommerceCartCheckoutEngine...")
        p_res = engine.parse_shopping_intent("Book hotel and buy organic groceries", 500.0)
        assert len(p_res["detected_categories"]) >= 2
        
        sample_items = [
            {"merchant": "Instacart", "title": "Organic Avocados 4pk", "quantity": 2, "unit_price_usd": 5.99},
            {"merchant": "Shopify Direct", "title": "Insulated Beach Cooler Bag", "quantity": 1, "unit_price_usd": 39.99}
        ]
        cart_res = engine.aggregate_multi_merchant_cart(sample_items)
        assert cart_res["merchants_count"] == 2
        cid = cart_res["cart_id"]
        
        sum_res = engine.calculate_checkout_summary(cid, coupon_code="GENPARK10")
        assert sum_res["summary"]["final_total_usd"] > 0
        
        ord_res = engine.generate_delegated_order(cid)
        assert ord_res["status"] == "success"
        print(f"[TEST] Success! Created Delegated Order: {ord_res['order_manifest']['order_id']}")
        return

    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
            method = req.get("method")
            msg_id = req.get("id")
            
            if method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [
                            {
                                "name": "manage_commerce_intent",
                                "description": "Parse consumer shopping goals, assemble multi-merchant carts, calculate checkout summaries, and compile delegated order payloads.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "action": {"type": "string", "enum": ["parse_shopping_intent", "aggregate_multi_merchant_cart", "calculate_checkout_summary", "generate_delegated_order"]},
                                        "goal_text": {"type": "string"},
                                        "budget_max": {"type": "number"},
                                        "items": {"type": "array", "items": {"type": "object"}},
                                        "delivery_address": {"type": "string"}
                                    },
                                    "required": ["action"]
                                }
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                res = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
