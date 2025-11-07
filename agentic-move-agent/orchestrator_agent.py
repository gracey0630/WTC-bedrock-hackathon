import json
from datetime import datetime
from utils.bedrock_client import bedrock_client
from utils.simple_state import state_manager
from agents.marketplace_agent import MarketplaceAgent
from agents.logistics_agent import LogisticsAgent
from agents.decision_agent import DecisionAgent


class OrchestratorAgent:
    """
    Master orchestrator that plans and executes the entire move.
    
    IMPORTANT: This orchestrator expects inventory to already be analyzed.
    It does NOT analyze photos - that must be done in Streamlit first.
    
    Workflow:
    1. User uploads photos in Streamlit
    2. Streamlit calls InventoryAgent.analyze_photos()
    3. Inventory is saved to st.session_state.inventory
    4. User clicks "Generate Moving Plan"
    5. Orchestrator receives the pre-analyzed inventory
    6. Orchestrator runs DecisionAgent and other planning steps
    """
    def __init__(self, user_request=None, session_id=None, inventory=None):
        """
        Initialize orchestrator.
        
        Parameters:
        - user_request: dict with keys 'from', 'to', 'budget', 'priority' (optional)
        - session_id: optional session identifier
        - inventory: list of items (REQUIRED) - must be pre-analyzed from Streamlit
        """
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.execution_log = []
        
        # Load previous state if exists
        self.current_state = state_manager.load_state(self.session_id) or {}

        # Merge user input into current state
        if user_request:
            self.current_state.update({
                "from": user_request.get("from", self.current_state.get("from")),
                "to": user_request.get("to", self.current_state.get("to")),
                "budget": user_request.get("budget", self.current_state.get("budget", 3000)),
                "priority": user_request.get("priority", self.current_state.get("priority", "minimize cost")),
            })

            # Calculate distance if not provided
            if "distance" not in self.current_state:
                self.current_state["distance"] = self.estimate_distance(
                    self.current_state["from"], self.current_state["to"]
                )

        # SET INVENTORY - This is REQUIRED
        if inventory:
            self.current_state['inventory'] = inventory
            print(f"✅ Orchestrator initialized with {len(inventory)} items from inventory")
        elif 'inventory' not in self.current_state or not self.current_state['inventory']:
            # No inventory provided - this is an error
            print("⚠️ WARNING: No inventory provided to orchestrator!")
            self.current_state['inventory'] = []

        # Initialize specialized agents (NO InventoryAgent - photos already analyzed)
        self.marketplace_agent = MarketplaceAgent(self.session_id)
        self.logistics_agent = LogisticsAgent(self.session_id)
        self.decision_agent = DecisionAgent(self.session_id)

    def estimate_distance(self, from_location, to_location):
        """
        Placeholder function for distance estimation.
        Can later integrate Google Maps API or any routing service.
        """
        # Simple heuristic based on location keywords
        if not from_location or not to_location:
            return 1800
        
        # Check if same city/state
        from_lower = from_location.lower()
        to_lower = to_location.lower()
        
        if "brooklyn" in from_lower and "brooklyn" in to_lower:
            return 10  # Same borough
        elif ("new york" in from_lower or "nyc" in from_lower) and ("brooklyn" in to_lower or "queens" in to_lower):
            return 15  # Within NYC
        elif "new york" in from_lower and "new york" in to_lower:
            return 50  # Within state
        else:
            return 1800  # Cross-country default

    def execute_move(self, user_request=None):
        """Main orchestrator execution loop - ONLY for planning, NOT photo analysis."""
        if user_request:
            self.current_state.update(user_request)
        
        print(f"\n{'='*60}")
        print(f"🤖 ORCHESTRATOR STARTED - Session: {self.session_id}")
        print(f"📊 Inventory: {len(self.current_state.get('inventory', []))} items")
        print(f"{'='*60}\n")

        # Validate inventory exists
        if not self.current_state.get('inventory'):
            error_msg = "No inventory found! Photos must be analyzed in Streamlit first."
            print(f"❌ ERROR: {error_msg}")
            return {
                "status": "failed",
                "error": error_msg,
                "message": "Please upload and analyze photos in Tab 1 before generating a plan"
            }

        # Step 1: Generate plan (NO photo analysis steps)
        print("🧠 Generating execution plan...")
        plan = self.get_planning_steps()
        print(f"✅ Plan created: {len(plan)} steps\n")

        # Step 2: Execute plan
        for step in plan:
            print(f"{'='*60}")
            print(f"🔄 Step {step['step']}: [{step['agent'].upper()}]")
            print(f"Task: {step['task']}")
            print(f"{'='*60}")

            result = self.execute_step(step)

            self.execution_log.append({
                "step": step,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

            # Save state after each step
            state_manager.save_state(self.session_id, self.current_state)

            if result.get("status") == "failed":
                print(f"⚠️ Step failed: {result.get('error')}\n")
            else:
                print(f"✅ {result.get('summary', 'Success')}\n")

        # Step 3: Generate summary
        summary = self.generate_summary()

        print(f"\n{'='*60}")
        print(f"🎉 EXECUTION COMPLETE")
        print(f"{'='*60}\n")

        return summary

    def get_planning_steps(self):
        """
        Return planning steps ONLY - NO photo analysis.
        Assumes inventory is already populated.
        """
        return [
            {"step": 1, "agent": "decision", "task": "Analyze items and decide move vs sell/replace"},
            {"step": 2, "agent": "marketplace", "task": "Price items for sale"},
            {"step": 3, "agent": "logistics", "task": "Get moving quotes"},
            {"step": 4, "agent": "logistics", "task": "Select best quote"},
            {"step": 5, "agent": "marketplace", "task": "List items for sale"},
            {"step": 6, "agent": "logistics", "task": "Schedule utilities"},
            {"step": 7, "agent": "orchestrator", "task": "Generate timeline"},
            {"step": 8, "agent": "orchestrator", "task": "Create final checklist"}
        ]

    def execute_step(self, step):
        agent_name = step["agent"]
        task = step["task"]

        try:
            if agent_name == "decision":
                result = self.decision_agent.execute(task, self.current_state)
            elif agent_name == "marketplace":
                result = self.marketplace_agent.execute(task, self.current_state)
            elif agent_name == "logistics":
                result = self.logistics_agent.execute(task, self.current_state)
            elif agent_name == "orchestrator":
                result = self.execute_orchestrator_task(task)
            else:
                result = {"status": "failed", "error": f"Unknown agent: {agent_name}"}

            # Update state with any changes from the step
            if "state_update" in result:
                self.current_state.update(result["state_update"])

            return result

        except Exception as e:
            print(f"❌ Exception in step: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def execute_orchestrator_task(self, task):
        """Execute orchestrator-specific tasks"""
        if "timeline" in task.lower():
            return self.generate_timeline()
        elif "checklist" in task.lower():
            return self.generate_checklist()
        else:
            return {"status": "success", "summary": f"Orchestrator: {task}"}

    def generate_timeline(self):
        """Generate a week-by-week timeline"""
        items_to_sell = [i for i in self.current_state.get('inventory', []) 
                        if i.get('disposition') == 'SELL_AND_REPLACE']
        
        timeline = [
            "Week 1: List items for sale on Facebook Marketplace/Craigslist",
            "Week 2: Follow up on sales, get moving quotes, book mover" if items_to_sell else "Week 2: Get moving quotes, book mover",
            "Week 3: Donate unsold items, begin packing",
            "Week 4: Moving day! Final packing and coordination"
        ]
        
        return {
            "status": "success",
            "summary": "Timeline generated",
            "state_update": {"timeline": timeline}
        }

    def generate_checklist(self):
        """Generate final moving checklist"""
        items = self.current_state.get('inventory', [])
        items_to_move = [i for i in items if i.get('disposition') == 'MOVE']
        items_to_sell = [i for i in items if i.get('disposition') == 'SELL_AND_REPLACE']
        items_to_donate = [i for i in items if i.get('disposition') == 'DONATE']
        
        checklist = [
            f"□ Pack {len(items_to_move)} items for moving",
            f"□ List {len(items_to_sell)} items for sale" if items_to_sell else None,
            f"□ Arrange donation pickup for {len(items_to_donate)} items" if items_to_donate else None,
            "□ Confirm moving company booking",
            "□ Schedule utility shutoff at old location",
            "□ Schedule utility setup at new location",
            "□ Update address with USPS",
            "□ Transfer internet/cable service"
        ]
        
        # Remove None items
        checklist = [item for item in checklist if item]
        
        return {
            "status": "success",
            "summary": "Checklist created",
            "state_update": {"checklist": checklist}
        }

    def generate_summary(self):
        """Final summary with all analysis results"""
        items = self.current_state.get("inventory", [])
        items_to_move = [i for i in items if i.get("disposition") == "MOVE"]
        items_to_replace = [i for i in items if i.get("disposition") == "SELL_AND_REPLACE"]
        items_to_donate = [i for i in items if i.get("disposition") == "DONATE"]
        
        # Get costs from state (updated by DecisionAgent)
        total_moving_cost = self.current_state.get("total_moving_cost", 0)
        total_replacement_cost = self.current_state.get("total_replacement_cost", 0)
        total_selling_revenue = self.current_state.get("total_selling_revenue", 0)
        net_cost = self.current_state.get("net_cost", 0)
        total_savings = self.current_state.get("total_savings", 0)
        within_budget = self.current_state.get("within_budget", True)
        
        return {
            "session_id": self.session_id,
            "status": "success",
            "move_details": {
                "from": self.current_state.get("from"),
                "to": self.current_state.get("to"),
                "distance": self.current_state.get("distance"),
                "budget": self.current_state.get("budget")
            },
            "item_summary": {
                "total_items": len(items),
                "items_to_move": len(items_to_move),
                "items_to_replace": len(items_to_replace),
                "items_to_donate": len(items_to_donate)
            },
            "cost_analysis": {
                "total_moving_cost": total_moving_cost,
                "total_replacement_cost": total_replacement_cost,
                "total_selling_revenue": total_selling_revenue,
                "net_cost": net_cost,
                "total_savings": total_savings,
                "within_budget": within_budget,
                "budget_remaining": self.current_state.get("budget", 0) - net_cost
            },
            "items_to_move": [
                {
                    "name": i["name"],
                    "description": i.get("description", ""),
                    "moving_cost": i.get("moving_cost", 0),
                    "reasoning": i.get("reasoning", "")
                } for i in items_to_move
            ],
            "items_to_replace": [
                {
                    "name": i["name"],
                    "description": i.get("description", ""),
                    "sell_for": i.get("selling_price", 0),
                    "buy_new_for": i.get("amazon_price", 0),
                    "net_cost": i.get("amazon_price", 0) - i.get("selling_price", 0),
                    "reasoning": i.get("reasoning", "")
                } for i in items_to_replace
            ],
            "items_to_donate": [
                {"name": i["name"], "description": i.get("description", "")} 
                for i in items_to_donate
            ],
            "timeline": self.current_state.get("timeline", []),
            "checklist": self.current_state.get("checklist", []),
            "execution_log": self.execution_log,
            "current_state": self.current_state
        }