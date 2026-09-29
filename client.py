"""Client module for AgenticCommerceCartCheckoutEngine (100% Python Standard Library)."""
import json
import time
import uuid
import re
import hashlib
from typing import Dict, Any, List, Optional

class AgenticCommerceCartCheckoutEngine:
    """Orchestrates multi-merchant agentic commerce journeys from natural language
    consumer intent to cross-merchant cart consolidation and structured order payloads."""
    
    SUPPORTED_MERCHANTS = {
        "grocery": ["Instacart", "Walmart Grocery"],
        "retail": ["Shopify Direct", "Amazon Prime", "Target"],
        "travel": ["Expedia", "Booking.com", "Airbnb"],
        "food": ["DoorDash", "UberEats"]
    }

    def __init__(self):
        self.active_carts: Dict[str, Dict[str, Any]] = {}

    def parse_shopping_intent(self, goal_text: str, budget_max: float = 300.0) -> Dict[str, Any]:
        """Parses natural language shopping intent into structured merchant categories and requirements."""
        goal_lower = goal_text.lower()
        categories = []
        if any(w in goal_lower for w in ["grocery", "groceries", "food", "milk", "eggs", "coffee", "bbq", "dinner"]):
            categories.append("grocery")
        if any(w in goal_lower for w in ["hotel", "flight", "trip", "stay", "airbnb", "car rental", "expedia"]):
            categories.append("travel")
        if any(w in goal_lower for w in ["buy", "order", "shoes", "jacket", "chair", "gadget", "headphones", "retail"]):
            categories.append("retail")
            
        if not categories:
            categories = ["retail"]
            
        suggested_merchants = []
        for cat in categories:
            suggested_merchants.extend(self.SUPPORTED_MERCHANTS.get(cat, []))
            
        return {
            "status": "success",
            "goal": goal_text,
            "detected_categories": categories,
            "budget_max_usd": budget_max,
            "target_merchants": suggested_merchants[:4],
            "execution_ready": True
        }

    def aggregate_multi_merchant_cart(self, items: List[Dict[str, Any]], cart_id: Optional[str] = None) -> Dict[str, Any]:
        """Consolidates items across disparate merchants into a unified agentic shopping cart."""
        cid = cart_id or f"cart_{uuid.uuid4().hex[:8]}"
        merchant_buckets: Dict[str, List[Dict[str, Any]]] = {}
        
        for item in items:
            m_name = item.get("merchant", "Shopify Direct")
            merchant_buckets.setdefault(m_name, []).append({
                "item_id": item.get("item_id", f"sku_{uuid.uuid4().hex[:6]}"),
                "title": item.get("title", "Product Item"),
                "quantity": int(item.get("quantity", 1)),
                "unit_price_usd": float(item.get("unit_price_usd", 19.99)),
                "currency": "USD"
            })
            
        self.active_carts[cid] = {
            "cart_id": cid,
            "created_at": time.time(),
            "merchants": merchant_buckets,
            "item_count": sum(len(v) for v in merchant_buckets.values())
        }
        
        return {
            "status": "success",
            "cart_id": cid,
            "merchants_count": len(merchant_buckets),
            "merchants": list(merchant_buckets.keys()),
            "total_line_items": self.active_carts[cid]["item_count"],
            "details": self.active_carts[cid]
        }

    def calculate_checkout_summary(self, cart_id: str, coupon_code: Optional[str] = None) -> Dict[str, Any]:
        """Calculates accurate subtotals, merchant delivery fees, estimated taxes, and net total."""
        if cart_id not in self.active_carts:
            return {"status": "error", "message": f"Cart '{cart_id}' not found."}
            
        cart = self.active_carts[cart_id]
        subtotal = 0.0
        merchant_breakdowns = {}
        
        for m_name, items in cart["merchants"].items():
            m_subtotal = sum(i["quantity"] * i["unit_price_usd"] for i in items)
            m_delivery = 4.99 if "Grocery" in m_name or "Instacart" in m_name else 0.00
            m_tax = round(m_subtotal * 0.0825, 2)
            merchant_breakdowns[m_name] = {
                "subtotal": round(m_subtotal, 2),
                "delivery_fee": m_delivery,
                "estimated_tax": m_tax,
                "merchant_total": round(m_subtotal + m_delivery + m_tax, 2)
            }
            subtotal += m_subtotal
            
        total_delivery = sum(b["delivery_fee"] for b in merchant_breakdowns.values())
        total_tax = sum(b["estimated_tax"] for b in merchant_breakdowns.values())
        
        discount = 0.0
        if coupon_code and coupon_code.upper() in ["GENPARK10", "MUSE10"]:
            discount = round(subtotal * 0.10, 2)
            
        total_usd = round(subtotal + total_delivery + total_tax - discount, 2)
        
        summary = {
            "cart_id": cart_id,
            "subtotal_usd": round(subtotal, 2),
            "delivery_fees_usd": round(total_delivery, 2),
            "estimated_taxes_usd": round(total_tax, 2),
            "discount_applied_usd": discount,
            "final_total_usd": total_usd,
            "merchant_breakdowns": merchant_breakdowns
        }
        cart["last_summary"] = summary
        return {"status": "success", "summary": summary}

    def generate_delegated_order(self, cart_id: str, delivery_address: str = "100 Innovation Way, Austin TX") -> Dict[str, Any]:
        """Compiles finalized delegated order payload ready for Agentic Payment Authorization handoff."""
        if cart_id not in self.active_carts:
            return {"status": "error", "message": f"Cart '{cart_id}' not found."}
            
        cart = self.active_carts[cart_id]
        summary = cart.get("last_summary") or self.calculate_checkout_summary(cart_id)["summary"]
        
        order_id = f"ord_{uuid.uuid4().hex[:10]}"
        order_manifest = {
            "order_id": order_id,
            "cart_id": cart_id,
            "created_at": time.time(),
            "destination_address": delivery_address,
            "total_payable_usd": summary["final_total_usd"],
            "merchants_involved": list(cart["merchants"].keys()),
            "status": "AWAITING_PAYMENT_DELEGATION",
            "delegation_payload_hash": hashlib.sha256(f"{order_id}_{summary['final_total_usd']}".encode()).hexdigest()[:16]
        }
        return {"status": "success", "order_manifest": order_manifest}
