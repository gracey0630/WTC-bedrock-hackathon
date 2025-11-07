import json
import logging
from utils.bedrock_client import bedrock_client

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DecisionAgent:
    """
    Decision agent that analyzes items and decides whether to:
    - MOVE: Transport the item to new location
    - SELL_AND_REPLACE: Sell old item, buy new at destination
    - DONATE: Give away if not worth moving or selling
    
    Uses Amazon price checks and cost-benefit analysis.
    """

    def __init__(self, session_id):
        self.session_id = session_id

    def execute(self, task, state):
        """Execute decision-making tasks"""
        if "decide" in task.lower() or "analyze" in task.lower():
            return self.analyze_and_decide(state)
        else:
            return {"status": "success", "summary": f"Decision task: {task}"}

    def analyze_and_decide(self, state):
        """
        Main decision logic: analyze each item and decide move vs sell/replace
        """
        items = state.get("inventory", [])
        
        if not items:
            return {
                "status": "failed",
                "error": "No inventory to analyze"
            }

        distance = state.get("distance", 1800)
        budget = state.get("budget", 3000)
        from_location = state.get("from", "")
        to_location = state.get("to", "")

        print(f"\n{'='*60}")
        print(f"🧠 DECISION AGENT - Analyzing {len(items)} items")
        print(f"   Distance: {distance} miles | Budget: ${budget}")
        print(f"{'='*60}\n")

        # Process each item
        analyzed_items = []
        total_moving_cost = 0
        total_replacement_cost = 0
        total_selling_revenue = 0

        for idx, item in enumerate(items):
            print(f"📦 Analyzing item {idx+1}/{len(items)}: {item['name']}")
            
            # Get Amazon price estimate
            amazon_price = self.estimate_amazon_price(item)
            
            # Calculate moving cost (estimate volume and multiply by rate)
            item_volume = self.estimate_volume(item)
            moving_cost = item_volume * 1.5  # $1.50 per cubic foot
            
            # Estimate selling price (used item, typically 30-50% of new)
            selling_price = amazon_price * 0.4 if amazon_price > 0 else 50
            
            # Decision logic
            decision_data = self.make_decision(
                item=item,
                amazon_price=amazon_price,
                moving_cost=moving_cost,
                selling_price=selling_price,
                distance=distance
            )
            
            # Update item with decision data
            item.update({
                "volume": item_volume,
                "moving_cost": round(moving_cost, 2),
                "amazon_price": round(amazon_price, 2),
                "selling_price": round(selling_price, 2),
                "disposition": decision_data["disposition"],
                "reasoning": decision_data["reasoning"],
                "savings": decision_data["savings"]
            })
            
            analyzed_items.append(item)
            
            # Accumulate costs
            if decision_data["disposition"] == "MOVE":
                total_moving_cost += moving_cost
            elif decision_data["disposition"] == "SELL_AND_REPLACE":
                total_replacement_cost += amazon_price
                total_selling_revenue += selling_price
            
            print(f"   ✅ Decision: {decision_data['disposition']} (Savings: ${decision_data['savings']:.2f})")
            print(f"   Reasoning: {decision_data['reasoning']}\n")

        # Calculate totals
        move_items = [i for i in analyzed_items if i["disposition"] == "MOVE"]
        replace_items = [i for i in analyzed_items if i["disposition"] == "SELL_AND_REPLACE"]
        donate_items = [i for i in analyzed_items if i["disposition"] == "DONATE"]

        net_cost = total_moving_cost + total_replacement_cost - total_selling_revenue
        total_savings = sum(i["savings"] for i in analyzed_items)

        # Budget check
        within_budget = net_cost <= budget
        budget_status = "✅ WITHIN BUDGET" if within_budget else "⚠️ OVER BUDGET"

        summary = f"""
Decision Analysis Complete:
- Total Items: {len(analyzed_items)}
- Move: {len(move_items)} items (${total_moving_cost:.2f})
- Sell & Replace: {len(replace_items)} items (Cost: ${total_replacement_cost:.2f}, Revenue: ${total_selling_revenue:.2f})
- Donate: {len(donate_items)} items
- Net Cost: ${net_cost:.2f}
- Total Savings: ${total_savings:.2f}
- Budget: ${budget:.2f} - {budget_status}
"""

        print(f"\n{'='*60}")
        print(summary)
        print(f"{'='*60}\n")

        return {
            "status": "success",
            "summary": summary.strip(),
            "state_update": {
                "inventory": analyzed_items,
                "total_moving_cost": round(total_moving_cost, 2),
                "total_replacement_cost": round(total_replacement_cost, 2),
                "total_selling_revenue": round(total_selling_revenue, 2),
                "net_cost": round(net_cost, 2),
                "total_savings": round(total_savings, 2),
                "within_budget": within_budget,
                "move_items_count": len(move_items),
                "replace_items_count": len(replace_items),
                "donate_items_count": len(donate_items)
            }
        }

    def estimate_amazon_price(self, item):
        """
        Use Claude to estimate Amazon price based on item description
        """
        prompt = f"""Based on the item description below, estimate the current Amazon price for a NEW similar item.

Item: {item['name']}
Description: {item.get('description', 'N/A')}
Notes: {item.get('notes', 'N/A')}

Consider:
- Item type and quality indicators (leather, wood, large, etc.)
- Current market prices
- Reasonable price ranges for this category

Return ONLY a JSON object with the estimated price:
{{
  "estimated_price": 450,
  "confidence": "high",
  "price_range": "400-500"
}}

RETURN ONLY VALID JSON, no additional text.
"""

        try:
            response = bedrock_client.invoke_text(prompt, max_tokens=500)
            result = bedrock_client.parse_json_response(response)
            estimated_price = result.get("estimated_price", 100)
            
            print(f"   💰 Amazon price estimate: ${estimated_price} ({result.get('confidence', 'medium')} confidence)")
            return float(estimated_price)
        
        except Exception as e:
            logger.warning(f"Failed to estimate Amazon price for {item['name']}: {e}")
            # Fallback: use heuristics based on item type
            return self._fallback_price_estimate(item)

    def _fallback_price_estimate(self, item):
        """Fallback price estimation if API fails"""
        name_lower = item['name'].lower()
        
        # Basic heuristics
        if any(word in name_lower for word in ['sofa', 'couch', 'sectional']):
            return 800
        elif any(word in name_lower for word in ['bed', 'mattress']):
            return 600
        elif any(word in name_lower for word in ['table', 'desk', 'dining']):
            return 400
        elif any(word in name_lower for word in ['chair', 'stool']):
            return 150
        elif any(word in name_lower for word in ['dresser', 'cabinet', 'bookshelf']):
            return 350
        elif any(word in name_lower for word in ['lamp', 'mirror', 'decor']):
            return 80
        else:
            return 100  # default

    def estimate_volume(self, item):
        """
        Estimate item volume in cubic feet using Claude
        """
        prompt = f"""Estimate the volume in cubic feet for this item:

Item: {item['name']}
Description: {item.get('description', 'N/A')}
Notes: {item.get('notes', 'N/A')}

Consider typical dimensions for this type of furniture/item.

Return ONLY a JSON object:
{{
  "volume_cubic_feet": 45,
  "reasoning": "Large sofa, approximately 7ft x 3ft x 3ft"
}}

RETURN ONLY VALID JSON.
"""

        try:
            response = bedrock_client.invoke_text(prompt, max_tokens=300)
            result = bedrock_client.parse_json_response(response)
            volume = result.get("volume_cubic_feet", 10)
            return float(volume)
        
        except Exception as e:
            logger.warning(f"Failed to estimate volume for {item['name']}: {e}")
            return self._fallback_volume_estimate(item)

    def _fallback_volume_estimate(self, item):
        """Fallback volume estimation"""
        name_lower = item['name'].lower()
        desc_lower = item.get('description', '').lower()
        
        # Check size descriptors
        is_large = 'large' in desc_lower
        is_small = 'small' in desc_lower
        
        # Base estimates
        if any(word in name_lower for word in ['sofa', 'couch', 'sectional']):
            return 50 if is_large else 35
        elif any(word in name_lower for word in ['bed', 'mattress']):
            return 45 if 'king' in desc_lower or 'queen' in desc_lower else 30
        elif any(word in name_lower for word in ['table', 'desk', 'dining']):
            return 25 if is_large else 15
        elif any(word in name_lower for word in ['chair']):
            return 8 if is_large else 5
        elif any(word in name_lower for word in ['dresser', 'cabinet', 'bookshelf']):
            return 30 if is_large else 20
        else:
            return 5  # small items

    def make_decision(self, item, amazon_price, moving_cost, selling_price, distance):
        """
        Core decision logic: move vs sell/replace vs donate
        
        Decision criteria:
        1. If (selling_price + moving_cost) < amazon_price: SELL_AND_REPLACE
        2. If moving_cost < (amazon_price * 0.3): MOVE (item worth moving)
        3. If item_value < $50: DONATE
        4. Else: MOVE (default to keeping items)
        """
        
        # Cost to keep item (sell + move)
        cost_to_replace = amazon_price - selling_price
        
        # Savings from selling and replacing
        savings_if_replace = moving_cost - cost_to_replace
        
        # Decision thresholds
        MIN_VALUE_THRESHOLD = 50  # Below this, just donate
        DISTANCE_THRESHOLD = 500  # For short moves, more likely to move items
        
        # Low-value items: DONATE
        if amazon_price < MIN_VALUE_THRESHOLD:
            return {
                "disposition": "DONATE",
                "reasoning": f"Low value item (${amazon_price:.2f}), not worth moving or selling",
                "savings": moving_cost  # Save the moving cost
            }
        
        # Short distance moves: prefer MOVE
        if distance < DISTANCE_THRESHOLD and moving_cost < (amazon_price * 0.5):
            return {
                "disposition": "MOVE",
                "reasoning": f"Short move ({distance} mi), moving cost (${moving_cost:.2f}) reasonable vs replacement (${amazon_price:.2f})",
                "savings": 0
            }
        
        # Long distance: analyze replacement economics
        if savings_if_replace > 50:  # Significant savings
            return {
                "disposition": "SELL_AND_REPLACE",
                "reasoning": f"Save ${savings_if_replace:.2f} by selling (${selling_price:.2f}) and buying new (${amazon_price:.2f}) vs moving (${moving_cost:.2f})",
                "savings": savings_if_replace
            }
        
        # Check if item is worth moving based on value ratio
        value_ratio = amazon_price / moving_cost if moving_cost > 0 else 0
        
        if value_ratio > 3:  # Item worth at least 3x the moving cost
            return {
                "disposition": "MOVE",
                "reasoning": f"High value item (${amazon_price:.2f}), worth moving (${moving_cost:.2f})",
                "savings": 0
            }
        elif value_ratio < 1.5:  # Marginal value
            return {
                "disposition": "SELL_AND_REPLACE",
                "reasoning": f"Replacement (${amazon_price:.2f}) cheaper than moving (${moving_cost:.2f}) + selling (${selling_price:.2f})",
                "savings": max(0, savings_if_replace)
            }
        else:
            # Default: MOVE for mid-value items
            return {
                "disposition": "MOVE",
                "reasoning": f"Mid-value item, moving (${moving_cost:.2f}) is reasonable",
                "savings": 0
            }

    def generate_optimization_plan(self, state):
        """
        Generate a detailed plan showing budget optimization
        """
        items = state.get("inventory", [])
        budget = state.get("budget", 3000)
        net_cost = state.get("net_cost", 0)
        
        move_items = [i for i in items if i.get("disposition") == "MOVE"]
        replace_items = [i for i in items if i.get("disposition") == "SELL_AND_REPLACE"]
        donate_items = [i for i in items if i.get("disposition") == "DONATE"]
        
        plan = {
            "budget_analysis": {
                "total_budget": budget,
                "net_cost": net_cost,
                "remaining": budget - net_cost,
                "within_budget": net_cost <= budget
            },
            "action_plan": {
                "move": [{"name": i["name"], "cost": i["moving_cost"]} for i in move_items],
                "sell_and_replace": [
                    {
                        "name": i["name"],
                        "sell_for": i["selling_price"],
                        "buy_new_for": i["amazon_price"],
                        "net_cost": i["amazon_price"] - i["selling_price"]
                    } for i in replace_items
                ],
                "donate": [i["name"] for i in donate_items]
            },
            "timeline": [
                "Week 1-2: List items for sale on Facebook Marketplace/Craigslist",
                "Week 2-3: Purchase replacement items (ship to new address)",
                "Week 3: Donate unsold items, pack items to move",
                "Week 4: Execute move with selected items"
            ]
        }
        
        return plan