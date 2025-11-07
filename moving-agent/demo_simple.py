import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List

class SimpleMovingAgent:
    """Moving agent demo without browser dependencies"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def find_and_schedule_demo(self, company_name: str, customer_info: Dict) -> Dict:
        """Demo that simulates browser automation without actual browser"""
        
        print(f"🎬 DEMO: Finding and scheduling with {company_name}")
        print("=" * 50)
        
        # Step 1: Search simulation
        print("🔍 Step 1: Searching for moving company...")
        time.sleep(1)
        search_results = self._simulate_search(company_name)
        print(f"   Found {len(search_results)} results")
        
        # Step 2: Website visit simulation
        print("🌐 Step 2: Visiting company website...")
        time.sleep(1)
        website_data = self._simulate_website_visit(company_name)
        print(f"   Loaded: {website_data['url']}")
        
        # Step 3: Form detection simulation
        print("📋 Step 3: Finding contact form...")
        time.sleep(1)
        form_fields = self._simulate_form_detection()
        print(f"   Found {len(form_fields)} form fields")
        
        # Step 4: Form filling simulation
        print("✍️ Step 4: Filling customer information...")
        time.sleep(1)
        filled_data = self._simulate_form_filling(customer_info, form_fields)
        for field, value in filled_data.items():
            print(f"   {field}: {value}")
            time.sleep(0.5)
        
        # Step 5: Submission simulation
        print("🚀 Step 5: Submitting appointment request...")
        time.sleep(2)
        confirmation = self._simulate_submission(company_name)
        print(f"   ✅ Submitted! Confirmation: {confirmation}")
        
        print("🎉 DEMO COMPLETE!")
        print("=" * 50)
        
        return {
            "status": "success",
            "company": company_name,
            "confirmation": confirmation,
            "customer": customer_info["name"],
            "method": "simulated_demo"
        }
    
    def _simulate_search(self, company_name: str) -> List[str]:
        """Simulate Google search results"""
        return [
            f"{company_name} Official Website",
            f"{company_name} Reviews",
            f"{company_name} Contact Info"
        ]
    
    def _simulate_website_visit(self, company_name: str) -> Dict:
        """Simulate visiting company website"""
        return {
            "url": f"https://www.{company_name.lower().replace(' ', '')}.com",
            "title": f"{company_name} - Moving Services",
            "has_contact_form": True
        }
    
    def _simulate_form_detection(self) -> List[str]:
        """Simulate finding form fields"""
        return ["name", "phone", "email", "message", "origin", "destination"]
    
    def _simulate_form_filling(self, customer_info: Dict, fields: List[str]) -> Dict:
        """Simulate filling form fields"""
        filled = {}
        for field in fields:
            if field == "name":
                filled["Name"] = customer_info["name"]
            elif field == "phone":
                filled["Phone"] = customer_info["phone"]
            elif field == "email":
                filled["Email"] = customer_info["email"]
            elif field == "message":
                filled["Message"] = f"Moving from {customer_info['origin']} to {customer_info['destination']}"
            elif field == "origin":
                filled["Origin"] = customer_info["origin"]
            elif field == "destination":
                filled["Destination"] = customer_info["destination"]
        return filled
    
    def _simulate_submission(self, company_name: str) -> str:
        """Simulate form submission"""
        return f"DEMO_{company_name.replace(' ', '_').upper()}_{int(time.time())}"

def run_simple_demo():
    """Run demo without browser dependencies"""
    print("=" * 60)
    print("🚚 AI MOVING AGENT - SIMULATION DEMO")
    print("=" * 60)
    print("📝 Note: This demo simulates browser automation")
    print("    For live browser demo, install system dependencies")
    print("=" * 60)
    
    # Get demo inputs
    company = input("Enter moving company (or press Enter for 'Two Men and a Truck'): ").strip()
    if not company:
        company = "Two Men and a Truck"
    
    customer_info = {
        "name": "Demo Customer",
        "phone": "555-DEMO-123",
        "email": "demo@example.com",
        "origin": "New York, NY",
        "destination": "Los Angeles, CA"
    }
    
    print(f"\n🎯 Demo company: {company}")
    print("📋 Customer Info:")
    for key, value in customer_info.items():
        print(f"  {key.title()}: {value}")
    
    input("\n🎬 Press Enter to start simulation demo...")
    print()
    
    # Run the demo
    agent = SimpleMovingAgent()
    result = agent.find_and_schedule_demo(company, customer_info)
    
    # Show results
    print("\n📊 DEMO RESULTS:")
    print("=" * 30)
    print(f"Status: {result['status']}")
    print(f"Company: {result['company']}")
    print(f"Customer: {result['customer']}")
    print(f"Confirmation: {result['confirmation']}")
    print("=" * 30)

if __name__ == "__main__":
    run_simple_demo()