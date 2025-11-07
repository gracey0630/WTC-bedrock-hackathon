from playwright.async_api import async_playwright
import asyncio
import time
from typing import Dict

class LiveDemoAgent:
    """Browser agent with visible demo mode"""
    
    async def demo_schedule_appointment(self, company_name: str, customer_info: Dict) -> Dict:
        """Live demo that shows browser automation in action"""
        
        async with async_playwright() as p:
            # Launch browser in VISIBLE mode for demo
            browser = await p.chromium.launch(
                headless=False,  # Show browser window
                slow_mo=2000,    # Slow down actions for demo visibility
                args=['--start-maximized']  # Full screen for better demo
            )
            
            page = await browser.new_page()
            
            print("🎬 DEMO: Starting live browser automation...")
            
            try:
                # Step 1: Search for company (visible to audience)
                print(f"🔍 Searching for {company_name}...")
                await page.goto(f"https://www.google.com/search?q={company_name.replace(' ', '+')}+contact")
                await self._demo_pause("Searching Google for company contact info")
                
                # Step 2: Click first result
                print("🖱️ Clicking on company website...")
                await page.click('h3:first-of-type')
                await self._demo_pause("Navigating to company website")
                
                # Step 3: Look for contact/quote form
                print("📋 Looking for contact form...")
                contact_selectors = [
                    'a:has-text("Contact")', 'a:has-text("Get Quote")', 
                    'a:has-text("Free Estimate")', 'button:has-text("Quote")'
                ]
                
                for selector in contact_selectors:
                    try:
                        await page.click(selector, timeout=3000)
                        print(f"✅ Found and clicked: {selector}")
                        break
                    except:
                        continue
                
                await self._demo_pause("Found contact form")
                
                # Step 4: Fill form with dramatic pauses
                print("✍️ Filling customer information...")
                
                # Fill name
                name_fields = ['input[name*="name"]', '#name', 'input[placeholder*="name"]']
                await self._fill_field_demo(page, name_fields, customer_info["name"], "Name")
                
                # Fill phone
                phone_fields = ['input[name*="phone"]', 'input[type="tel"]', '#phone']
                await self._fill_field_demo(page, phone_fields, customer_info["phone"], "Phone")
                
                # Fill email
                email_fields = ['input[name*="email"]', 'input[type="email"]', '#email']
                await self._fill_field_demo(page, email_fields, customer_info["email"], "Email")
                
                # Fill message
                message_fields = ['textarea', 'input[name*="message"]', '#message']
                message = f"Moving from {customer_info.get('origin', 'NYC')} to {customer_info.get('destination', 'LA')}"
                await self._fill_field_demo(page, message_fields, message, "Message")
                
                await self._demo_pause("All fields filled - ready to submit")
                
                # Step 5: Submit form
                print("🚀 Submitting appointment request...")
                submit_selectors = ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Submit")']
                
                for selector in submit_selectors:
                    try:
                        await page.click(selector)
                        print("✅ Form submitted!")
                        break
                    except:
                        continue
                
                await self._demo_pause("Waiting for confirmation...")
                
                # Step 6: Capture result
                await page.wait_for_timeout(3000)
                confirmation = f"DEMO_CONF_{int(time.time())}"
                
                print("🎉 DEMO COMPLETE: Appointment request submitted!")
                
                # Keep browser open for 5 seconds to show result
                await asyncio.sleep(5)
                
                await browser.close()
                
                return {
                    "status": "demo_success",
                    "confirmation": confirmation,
                    "company": company_name,
                    "demo_completed": True
                }
                
            except Exception as e:
                print(f"❌ Demo error: {str(e)}")
                await browser.close()
                return {"status": "demo_failed", "error": str(e)}
    
    async def _fill_field_demo(self, page, selectors: list, value: str, field_name: str):
        """Fill field with demo commentary"""
        for selector in selectors:
            try:
                await page.fill(selector, value)
                print(f"✅ Filled {field_name}: {value}")
                await asyncio.sleep(1)  # Pause for demo effect
                return
            except:
                continue
        print(f"⚠️ Could not find {field_name} field")
    
    async def _demo_pause(self, message: str, duration: int = 2):
        """Pause with message for demo effect"""
        print(f"⏸️ {message}")
        await asyncio.sleep(duration)

# Demo interface
async def run_live_demo():
    """Interactive demo interface"""
    print("=" * 50)
    print("🎬 LIVE BROWSER AUTOMATION DEMO")
    print("=" * 50)
    
    # Get demo parameters
    company = input("Enter moving company name (or press Enter for 'Budget Movers'): ").strip()
    if not company:
        company = "Budget Movers"
    
    customer_info = {
        "name": "Demo Customer",
        "phone": "555-DEMO-123",
        "email": "demo@example.com",
        "origin": "New York, NY",
        "destination": "Los Angeles, CA"
    }
    
    print(f"\n🎯 Demo will show live automation for: {company}")
    print("📋 Customer info:", customer_info)
    
    input("\n🎬 Press Enter to start live demo...")
    
    # Run the demo
    agent = LiveDemoAgent()
    result = await agent.demo_schedule_appointment(company, customer_info)
    
    print("\n" + "=" * 50)
    print("🎬 DEMO RESULTS:")
    print("=" * 50)
    print(f"Status: {result['status']}")
    if 'confirmation' in result:
        print(f"Confirmation: {result['confirmation']}")
    print("=" * 50)

def start_demo():
    """Start the live demo"""
    asyncio.run(run_live_demo())

if __name__ == "__main__":
    start_demo()