from playwright.async_api import async_playwright
import asyncio
from typing import Dict

class MovingAgentDemo:
    """Minimal AI moving agent with live browser demo"""
    
    async def find_and_schedule(self, company_name: str, customer_info: Dict) -> Dict:
        """Complete demo: find movers and schedule appointment"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Visible browser for demo
                slow_mo=1500     # Slow actions for visibility
            )
            page = await browser.new_page()
            
            print(f"🎬 DEMO: Finding and scheduling with {company_name}")
            
            try:
                # Step 1: Search for moving company
                print("🔍 Searching for moving company...")
                search_query = f"{company_name} moving company contact"
                await page.goto(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
                await asyncio.sleep(2)
                
                # Step 2: Click first result
                print("🖱️ Opening company website...")
                await page.click('h3:first-of-type')
                await asyncio.sleep(3)
                
                # Step 3: Look for contact form
                print("📋 Looking for contact form...")
                contact_buttons = [
                    'a:has-text("Contact")', 'a:has-text("Get Quote")', 
                    'a:has-text("Free Estimate")', 'button:has-text("Quote")',
                    'a:has-text("Request Quote")'
                ]
                
                for button in contact_buttons:
                    try:
                        await page.click(button, timeout=2000)
                        print(f"✅ Found: {button}")
                        break
                    except:
                        continue
                
                await asyncio.sleep(2)
                
                # Step 4: Fill contact form
                print("✍️ Filling customer information...")
                
                # Fill name
                name_selectors = ['input[name*="name"]', '#name', 'input[placeholder*="Name"]']
                await self._fill_field(page, name_selectors, customer_info["name"], "Name")
                
                # Fill phone
                phone_selectors = ['input[name*="phone"]', 'input[type="tel"]', '#phone']
                await self._fill_field(page, phone_selectors, customer_info["phone"], "Phone")
                
                # Fill email
                email_selectors = ['input[name*="email"]', 'input[type="email"]', '#email']
                await self._fill_field(page, email_selectors, customer_info["email"], "Email")
                
                # Fill message/details
                message = f"Moving from {customer_info['origin']} to {customer_info['destination']}"
                message_selectors = ['textarea', 'input[name*="message"]', 'input[name*="details"]']
                await self._fill_field(page, message_selectors, message, "Message")
                
                await asyncio.sleep(2)
                
                # Step 5: Submit form
                print("🚀 Submitting appointment request...")
                submit_selectors = [
                    'button[type="submit"]', 'input[type="submit"]', 
                    'button:has-text("Submit")', 'button:has-text("Send")'
                ]
                
                for selector in submit_selectors:
                    try:
                        await page.click(selector)
                        print("✅ Form submitted!")
                        break
                    except:
                        continue
                
                await asyncio.sleep(3)
                
                # Step 6: Show result
                print("🎉 DEMO COMPLETE!")
                confirmation_id = f"DEMO_{company_name.replace(' ', '_').upper()}_{int(asyncio.get_event_loop().time())}"
                
                # Keep browser open for 5 seconds to show result
                await asyncio.sleep(5)
                await browser.close()
                
                return {
                    "status": "success",
                    "company": company_name,
                    "confirmation": confirmation_id,
                    "customer": customer_info["name"]
                }
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                await browser.close()
                return {"status": "failed", "error": str(e)}
    
    async def _fill_field(self, page, selectors: list, value: str, field_name: str):
        """Fill form field with multiple selector attempts"""
        for selector in selectors:
            try:
                await page.fill(selector, value)
                print(f"  ✅ {field_name}: {value}")
                await asyncio.sleep(1)
                return
            except:
                continue
        print(f"  ⚠️ Could not find {field_name} field")

async def run_demo():
    """Interactive demo runner"""
    print("=" * 60)
    print("🚚 AI MOVING AGENT - LIVE BROWSER DEMO")
    print("=" * 60)
    
    # Get demo inputs
    company = input("Enter moving company (or press Enter for 'Two Men and a Truck'): ").strip()
    if not company:
        company = "Two Men and a Truck"
    
    print(f"\n🎯 Demo will show live automation for: {company}")
    
    customer_info = {
        "name": "Demo Customer",
        "phone": "555-DEMO-123",
        "email": "demo@example.com",
        "origin": "New York, NY",
        "destination": "Los Angeles, CA"
    }
    
    print("📋 Customer Info:")
    for key, value in customer_info.items():
        print(f"  {key.title()}: {value}")
    
    input("\n🎬 Press Enter to start live browser demo...")
    
    # Run the demo
    agent = MovingAgentDemo()
    result = await agent.find_and_schedule(company, customer_info)
    
    # Show results
    print("\n" + "=" * 60)
    print("📊 DEMO RESULTS:")
    print("=" * 60)
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Company: {result['company']}")
        print(f"Customer: {result['customer']}")
        print(f"Confirmation: {result['confirmation']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_demo())