class LogisticsAgent:
    """
    Logistics coordination for moving and services
    """
    def __init__(self, session_id):
        self.session_id = session_id
    
    def execute(self, task, state):
        """Execute logistics tasks"""
        if "quote" in task.lower():
            return self.get_moving_quotes(state)
        elif "select" in task.lower() and "quote" in task.lower():
            return self.select_best_quote(state)
        elif "book" in task.lower():
            return self.book_mover(state)
        elif "schedule" in task.lower() and "utility" in task.lower():
            return self.schedule_utilities(state)
        else:
            return {"status": "success", "summary": f"Logistics task: {task}"}
    
    def get_moving_quotes(self, state):
        """Get quotes from moving companies"""
        volume = state.get("total_volume", 100)
        distance = state.get("distance", 1800)
        
        # Mock moving companies with different rates
        companies = [
            {
                "company": "QuickMove Pro",
                "rate": 1.4,
                "rating": 4.8,
                "insurance": "Full coverage included"
            },
            {
                "company": "SafeHaul Movers",
                "rate": 1.6,
                "rating": 4.6,
                "insurance": "Basic coverage included"
            },
            {
                "company": "Elite Relocations",
                "rate": 1.8,
                "rating": 4.9,
                "insurance": "Premium coverage included"
            }
        ]
        
        quotes = []
        for company in companies:
            # Calculate price: volume * rate * 10 (base multiplier)
            price = int(volume * company["rate"] * 10)
            
            quotes.append({
                "company": company["company"],
                "price": price,
                "rating": company["rating"],
                "insurance": company["insurance"]
            })
            
            print(f"  💰 {company['company']}: ${price} ({company['rating']}⭐)")
        
        return {
            "status": "success",
            "summary": f"Got {len(quotes)} quotes ranging from ${min(q['price'] for q in quotes)} to ${max(q['price'] for q in quotes)}",
            "state_update": {"quotes": quotes}
        }
    
    def select_best_quote(self, state):
        """Select the best moving quote"""
        quotes = state.get("quotes", [])
        budget = state.get("budget", 3000)
        
        if not quotes:
            return {"status": "failed", "error": "No quotes available"}
        
        # Filter quotes under budget
        affordable_quotes = [q for q in quotes if q["price"] <= budget]
        
        if affordable_quotes:
            # Select best rating among affordable options
            best_quote = max(affordable_quotes, key=lambda x: x["rating"])
        else:
            # Select cheapest if all over budget
            best_quote = min(quotes, key=lambda x: x["price"])
            print(f"  ⚠️ All quotes over budget. Selected cheapest option.")
        
        print(f"  ✅ Selected: {best_quote['company']} - ${best_quote['price']}")
        
        return {
            "status": "success",
            "summary": f"Selected {best_quote['company']} at ${best_quote['price']} ({best_quote['rating']}⭐)",
            "state_update": {"selected_quote": best_quote}
        }
    
    def book_mover(self, state):
        """Book the selected moving company"""
        quote = state.get("selected_quote")
        
        if not quote:
            return {"status": "failed", "error": "No quote selected"}
        
        booking = {
            "company": quote["company"],
            "price": quote["price"],
            "deposit": int(quote["price"] * 0.2),  # 20% deposit
            "move_date": state.get("move_date", "2025-12-01"),
            "status": "confirmed"
        }
        
        print(f"  💳 Booking {quote['company']} - Deposit: ${booking['deposit']}")
        
        return {
            "status": "success",
            "summary": f"Booked {quote['company']} for {booking['move_date']}. Deposit: ${booking['deposit']}",
            "state_update": {"booking": booking}
        }
    
    def schedule_utilities(self, state):
        """Schedule utility services"""
        utilities = ["Electric", "Gas", "Internet", "Water"]
        move_date = state.get("move_date", "2025-12-01")
        
        scheduled = []
        for utility in utilities:
            scheduled.append({
                "service": utility,
                "disconnect_date": move_date,
                "connect_date": move_date,
                "status": "scheduled"
            })
            print(f"  📞 Scheduled {utility} disconnect/connect for {move_date}")
        
        return {
            "status": "success",
            "summary": f"Scheduled {len(utilities)} utility services for {move_date}",
            "state_update": {"utilities": scheduled}
        }
