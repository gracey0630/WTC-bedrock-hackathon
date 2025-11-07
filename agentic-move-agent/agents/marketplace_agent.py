from utils.bedrock_client import bedrock_client

class MarketplaceAgent:
    """
    Marketplace management for selling items
    """
    def __init__(self, session_id):
        self.session_id = session_id
    
    def execute(self, task, state):
        """Execute marketplace tasks"""
        if "price" in task.lower():
            return self.price_items(state.get("inventory", []))
        elif "list" in task.lower() and "sale" in task.lower():
            return self.list_items_for_sale(state.get("inventory", []))
        else:
            return {"status": "success", "summary": f"Marketplace task: {task}"}
    
    def price_items(self, inventory):
        """Estimate selling prices for items"""
        # Price database (market averages for used furniture)
        price_database = {
            "sofa": {"min": 100, "max": 500, "avg": 250},
            "couch": {"min": 100, "max": 500, "avg": 250},
            "coffee table": {"min": 30, "max": 200, "avg": 80},
            "dining table": {"min": 150, "max": 800, "avg": 400},
            "table": {"min": 50, "max": 300, "avg": 120},
            "tv stand": {"min": 50, "max": 300, "avg": 120},
            "bed": {"min": 100, "max": 600, "avg": 250},
            "bed frame": {"min": 100, "max": 600, "avg": 250},
            "desk": {"min": 75, "max": 400, "avg": 150},
            "bookshelf": {"min": 40, "max": 250, "avg": 100},
            "dresser": {"min": 80, "max": 450, "avg": 200},
            "chair": {"min": 25, "max": 200, "avg": 75},
            "nightstand": {"min": 30, "max": 150, "avg": 60},
            "lamp": {"min": 10, "max": 100, "avg": 30},
            "rug": {"min": 20, "max": 300, "avg": 100}
        }
        
        # Price each item
        for item in inventory:
            item_name_lower = item.get("name", "").lower()
            
            # Find matching price
            price_found = False
            for key, price_range in price_database.items():
                if key in item_name_lower:
                    item["selling_price"] = price_range["avg"]
                    item["price_range"] = f"${price_range['min']}-${price_range['max']}"
                    price_found = True
                    break
            
            # Default price if no match
            if not price_found:
                item["selling_price"] = 100
                item["price_range"] = "$50-$200"
        
        total_value = sum(item.get("selling_price", 0) for item in inventory)
        
        return {
            "status": "success",
            "summary": f"Priced {len(inventory)} items. Total estimated value: ${total_value}",
            "state_update": {"inventory": inventory}
        }
    
    def list_items_for_sale(self, inventory):
        """Create listings for items marked to sell"""
        items_to_sell = [item for item in inventory if item.get("disposition") == "SELL"]
        
        if not items_to_sell:
            return {
                "status": "success",
                "summary": "No items marked for sale yet"
            }
        
        listings = []
        for item in items_to_sell:
            listing = {
                "item": item["name"],
                "price": item.get("selling_price", 100),
                "description": f"{item['name']} - {item.get('notes', 'Good condition')}",
                "platforms": ["Facebook Marketplace", "Craigslist", "OfferUp"]
            }
            listings.append(listing)
            print(f"  📝 Would list: {item['name']} for ${item.get('selling_price', 100)}")
        
        return {
            "status": "success",
            "summary": f"Created {len(listings)} listings across 3 platforms",
            "state_update": {"active_listings": listings}
        }
