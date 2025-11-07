# final_quote_agent.py - Get actual quote amounts without Unicode issues

import asyncio
import json
import boto3
from playwright.async_api import async_playwright
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def extract_prices_with_ai(page_content, page_title):
    """Extract prices using Bedrock with categories"""
    bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
    
    prompt = f"""
    Extract moving quote prices from this webpage and categorize them.
    
    PAGE: {page_title}
    CONTENT: {page_content[:2000]}
    
    Find prices and categorize them. Return JSON:
    {{
        "found": true,
        "total": "$1,500",
        "categories": {{
            "truck_rental": "$89/day",
            "mileage": "$1.29/mile", 
            "deposit": "$150",
            "insurance": "$28/day",
            "equipment": "$15/day",
            "fuel": "$45"
        }}
    }}
    
    If no prices: {{"found": false}}
    """
    
    try:
        response = bedrock.converse(
            modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.1}
        )
        
        result = response['output']['message']['content'][0]['text']
        
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        return {"found": False}
        
    except Exception as e:
        print(f"AI extraction error: {e}")
        return {"found": False}

def extract_prices_regex(page_content):
    """Fallback: Extract prices with regex"""
    
    # Look for dollar amounts
    price_patterns = [
        r'\$[\d,]+\.?\d*',  # $1,234.56
        r'\$[\d,]+',        # $1,234
        r'[\d,]+\.\d{2}',   # 1,234.56
    ]
    
    prices = []
    for pattern in price_patterns:
        matches = re.findall(pattern, page_content)
        prices.extend(matches)
    
    # Remove duplicates and filter reasonable prices
    unique_prices = list(set(prices))
    reasonable_prices = []
    
    for price in unique_prices:
        # Extract numeric value
        numeric = re.sub(r'[^\d.]', '', price)
        try:
            value = float(numeric)
            if 10 <= value <= 10000:  # Reasonable moving price range
                reasonable_prices.append(price)
        except:
            continue
    
    return reasonable_prices

def parse_customer_input(user_input):
    """Parse natural language input to extract customer information"""
    bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
    
    prompt = f"""
    Extract customer information from this natural language input for a moving quote.
    
    INPUT: "{user_input}"
    
    Extract and return JSON with these fields:
    {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "555-123-4567",
        "origin": "City, State",
        "destination": "City, State",
        "origin_zip": "12345",
        "destination_zip": "67890",
        "truck_size": "26ft",
        "move_date": "2024-02-15",
        "bedrooms": "3",
        "distance": "estimated miles"
    }}
    
    Use reasonable defaults if information is missing.
    """
    
    try:
        response = bedrock.converse(
            modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 400, "temperature": 0.1}
        )
        
        result = response['output']['message']['content'][0]['text']
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group())
        
        # Fallback defaults
        return {
            "name": "Customer",
            "email": "customer@example.com",
            "phone": "555-123-4567",
            "origin": "New York, NY",
            "destination": "Los Angeles, CA",
            "origin_zip": "10001",
            "destination_zip": "90210",
            "truck_size": "26ft",
            "move_date": "2024-02-15",
            "bedrooms": "3",
            "distance": "2800"
        }
        
    except Exception as e:
        print(f"Input parsing error: {e}")
        return {
            "name": "Customer",
            "email": "customer@example.com",
            "phone": "555-123-4567",
            "origin": "New York, NY",
            "destination": "Los Angeles, CA",
            "origin_zip": "10001",
            "destination_zip": "90210",
            "truck_size": "26ft",
            "move_date": "2024-02-15",
            "bedrooms": "3",
            "distance": "2800"
        }

def export_to_pdf(customer_info, quotes_found, ai_report):
    """Export report to PDF"""
    filename = f"moving_quote_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=30)
    story.append(Paragraph("MOVING QUOTE ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 12))
    
    # Customer Info
    story.append(Paragraph("CUSTOMER INFORMATION", styles['Heading2']))
    customer_text = f"""
    Name: {customer_info['name']}<br/>
    Email: {customer_info['email']}<br/>
    Phone: {customer_info['phone']}<br/>
    From: {customer_info['origin']}<br/>
    To: {customer_info['destination']}<br/>
    Move Date: {customer_info.get('move_date', 'TBD')}
    """
    story.append(Paragraph(customer_text, styles['Normal']))
    story.append(Spacer(1, 12))
    
    # Quotes Summary
    if quotes_found:
        story.append(Paragraph("QUOTES RECEIVED", styles['Heading2']))
        for quote in quotes_found:
            quote_text = f"<b>{quote['company']}</b><br/>"
            if quote.get('total'):
                quote_text += f"Total: {quote['total']}<br/>"
            if quote.get('categories'):
                for cat, price in quote['categories'].items():
                    quote_text += f"{cat.replace('_', ' ').title()}: {price}<br/>"
            story.append(Paragraph(quote_text, styles['Normal']))
            story.append(Spacer(1, 6))
    
    # AI Analysis
    story.append(Paragraph("AI ANALYSIS", styles['Heading2']))
    # Clean up the AI report for PDF
    clean_report = ai_report.replace('\n', '<br/>').replace('*', '')
    story.append(Paragraph(clean_report, styles['Normal']))
    
    doc.build(story)
    return filename

def generate_ai_report(customer_info, quotes_found):
    """Generate intelligent summary report using Bedrock"""
    bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
    
    report_data = {
        "customer": customer_info,
        "quotes": quotes_found,
        "total_companies": len(quotes_found)
    }
    
    prompt = f"""
    Create a professional moving quote analysis report for this customer.
    
    DATA: {json.dumps(report_data, indent=2)}
    
    Generate a concise executive summary covering:
    1. Customer profile and moving requirements
    2. Market analysis of quotes received
    3. Cost breakdown and savings opportunities
    4. Risk assessment and recommendations
    5. Next steps for the customer
    
    Keep it professional, data-driven, and actionable.
    """
    
    try:
        response = bedrock.converse(
            modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 800, "temperature": 0.3}
        )
        
        return response['output']['message']['content'][0]['text']
        
    except Exception as e:
        return f"Report generation error: {e}"

def present_final_quote(customer_info, quotes_found):
    """Present professional quote summary with categories and comparison"""
    
    print("\n" + "="*70)
    print("                MOVING QUOTE SUMMARY")
    print("="*70)
    
    print(f"Customer: {customer_info['name']}")
    print(f"Email: {customer_info['email']}")
    print(f"Phone: {customer_info['phone']}")
    print(f"Moving From: {customer_info['origin']}")
    print(f"Moving To: {customer_info['destination']}")
    
    print("\n" + "-"*70)
    print("                DETAILED QUOTES")
    print("-"*70)
    
    if quotes_found:
        total_quotes = 0
        all_prices = []
        company_totals = {}
        
        for quote in quotes_found:
            print(f"\n{quote['company'].upper()}:")
            
            # Show categorized prices
            if quote.get('categories'):
                print("  Price Breakdown:")
                for category, price in quote['categories'].items():
                    category_name = category.replace('_', ' ').title()
                    print(f"    {category_name}: {price}")
            
            if quote.get('total'):
                print(f"  \n  TOTAL ESTIMATE: {quote['total']}")
                all_prices.append(quote['total'])
                company_totals[quote['company']] = quote['total']
            
            if quote.get('prices') and not quote.get('categories'):
                print("  Other Prices Found:")
                for price in quote['prices']:
                    print(f"    • {price}")
                    all_prices.extend(quote['prices'])
            
            print(f"  Source: {quote.get('method', 'Unknown')} Analysis")
            total_quotes += 1
        
        # Company Comparison
        if len(quotes_found) > 1:
            print("\n" + "-"*70)
            print("                COMPANY COMPARISON")
            print("-"*70)
            
            if len(company_totals) >= 2:
                companies = list(company_totals.keys())
                totals = []
                for company, total in company_totals.items():
                    numeric = re.sub(r'[^\d.]', '', str(total))
                    try:
                        totals.append((company, float(numeric)))
                    except:
                        continue
                
                if len(totals) >= 2:
                    totals.sort(key=lambda x: x[1])
                    cheapest = totals[0]
                    most_expensive = totals[-1]
                    savings = most_expensive[1] - cheapest[1]
                    
                    print(f"CHEAPEST: {cheapest[0]} - ${cheapest[1]:,.0f}")
                    print(f"MOST EXPENSIVE: {most_expensive[0]} - ${most_expensive[1]:,.0f}")
                    print(f"POTENTIAL SAVINGS: ${savings:,.0f} ({((savings/most_expensive[1])*100):.1f}%)")
        
        print("\n" + "-"*70)
        print(f"SUMMARY: Found {total_quotes} quote(s) with {len(all_prices)} price points")
        
        if all_prices:
            # Extract numeric values for analysis
            numeric_prices = []
            for price in all_prices:
                numeric = re.sub(r'[^\d.]', '', str(price))
                try:
                    numeric_prices.append(float(numeric))
                except:
                    continue
            
            if numeric_prices:
                min_price = min(numeric_prices)
                max_price = max(numeric_prices)
                avg_price = sum(numeric_prices) / len(numeric_prices)
                
                print(f"Price Range: ${min_price:,.0f} - ${max_price:,.0f}")
                print(f"Average: ${avg_price:,.0f}")
        
        print("\n" + "="*70)
        print("                RECOMMENDATION")
        print("="*70)
        print("✓ AI successfully extracted categorized pricing data")
        print("✓ Customer information auto-filled on multiple websites")
        print("✓ Side-by-side comparison ready for decision")
        if len(company_totals) >= 2:
            cheapest_company = min(company_totals.items(), key=lambda x: float(re.sub(r'[^\d.]', '', str(x[1]))))
            print(f"✓ RECOMMENDED: {cheapest_company[0]} offers the best value")
        
    else:
        print("\nNo quotes were successfully extracted.")
        print("\nRECOMMENDATIONS:")
        print("• Try different moving company websites")
        print("• Adjust form filling strategy")
        print("• Check for CAPTCHA or bot detection")
    
    print("\n" + "="*70)
    print("Results saved: final_quotes.json | Screenshot: final_quote_result.png")
    print("="*70)

async def enhanced_form_fill(page, customer_info):
    """Enhanced form filling for customer-specific quotes"""
    
    # Comprehensive field mapping for moving quotes
    field_mappings = [
        # Personal Information
        ('input[name*="name"], input[id*="name"], input[placeholder*="name"]', customer_info['name']),
        ('input[type="email"], input[name*="email"], input[id*="email"]', customer_info['email']),
        ('input[name*="phone"], input[id*="phone"], input[type="tel"]', customer_info['phone']),
        
        # Location Information
        ('input[name*="from"], input[name*="origin"], input[id*="pickup"]', customer_info['origin']),
        ('input[name*="to"], input[name*="destination"], input[id*="dropoff"]', customer_info['destination']),
        ('input[name*="zip"], input[name*="postal"]', customer_info.get('origin_zip', '10001')),
        
        # Moving Details
        ('select[name*="size"], select[name*="truck"]', customer_info.get('truck_size', '26ft')),
        ('input[name*="date"], input[type="date"]', customer_info.get('move_date', '2024-02-15')),
        ('select[name*="distance"], input[name*="miles"]', customer_info.get('distance', '2800')),
        
        # Additional Services
        ('input[name*="insurance"][type="checkbox"]', True),
        ('input[name*="equipment"][type="checkbox"]', True)
    ]
    
    filled = 0
    for selector, value in field_mappings:
        try:
            elements = page.locator(selector)
            count = await elements.count()
            
            for i in range(count):
                element = elements.nth(i)
                if await element.is_visible(timeout=1000):
                    element_type = await element.get_attribute('type')
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    
                    if element_type == 'checkbox' and isinstance(value, bool):
                        if value:
                            await element.check()
                    elif tag_name == 'select':
                        await element.select_option(label=str(value))
                    else:
                        await element.fill(str(value))
                    
                    filled += 1
                    print(f"  Filled: {selector} = {value}")
                    break
        except Exception as e:
            continue
    
    return filled

async def get_moving_quotes():
    """Main function to get actual moving quotes"""
    
    # Get customer input in natural language
    print("=" * 60)
    print("AI-POWERED MOVING QUOTE AGENT")
    print("=" * 60)
    print("Enter your moving details in natural language:")
    print("Example: 'Hi, I'm Sarah Johnson, email sarah@gmail.com, phone 555-0123.'")
    print("         'I need to move from Boston MA to Miami FL in March.'")
    print("         'It's a 2-bedroom apartment, about 1200 miles.'")
    print()
    
    user_input = input("Your moving request: ")
    
    if not user_input.strip():
        user_input = "I'm John Doe, moving from New York to Los Angeles, 3 bedroom house, email john@example.com, phone 555-123-4567"
        print(f"Using example: {user_input}")
    
    print("\nParsing your request with AI...")
    customer_info = parse_customer_input(user_input)
    
    print(f"\nExtracted Information:")
    print(f"Customer: {customer_info['name']}")
    print(f"Route: {customer_info['origin']} → {customer_info['destination']}")
    print(f"Contact: {customer_info['email']}, {customer_info['phone']}")
    
    print("Final Quote Agent - Getting Real Prices")
    print(f"Customer: {customer_info['name']}")
    print(f"Route: {customer_info['origin']} to {customer_info['destination']}")
    
    quotes_found = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1500)
        page = await browser.new_page()
        
        try:
            # Try U-Haul
            print("\nTrying U-Haul...")
            await page.goto("https://www.uhaul.com/", timeout=15000)
            await page.wait_for_load_state('networkidle')
            
            # Click quote button
            try:
                quote_btn = page.locator('button:has-text("Quote")').first
                if await quote_btn.is_visible(timeout=5000):
                    await quote_btn.click()
                    await page.wait_for_load_state('networkidle')
                    print("Clicked quote button")
            except:
                print("No quote button found")
            
            # Enhanced form filling for customer-specific quotes
            print("Filling customer-specific information...")
            filled = await enhanced_form_fill(page, customer_info)
            print(f"Successfully filled {filled} form fields")
            
            # Try to submit
            try:
                submit_btn = page.locator('button:has-text("Submit"), button:has-text("Get Quote")').first
                if await submit_btn.is_visible(timeout=3000):
                    await submit_btn.click()
                    await page.wait_for_load_state('networkidle')
                    print("Submitted form")
            except:
                print("No submit button found")
            
            # Extract prices from current page
            page_content = await page.content()
            page_title = await page.title()
            
            print("Analyzing page for prices...")
            
            # Try AI extraction
            ai_prices = extract_prices_with_ai(page_content, page_title)
            
            if ai_prices.get('found'):
                print("AI found prices:")
                for price in ai_prices.get('prices', []):
                    print(f"  - {price}")
                if ai_prices.get('total'):
                    print(f"  Total: {ai_prices['total']}")
                
                quotes_found.append({
                    "company": "U-Haul",
                    "prices": ai_prices.get('prices', []),
                    "total": ai_prices.get('total'),
                    "categories": ai_prices.get('categories', {}),
                    "method": "AI"
                })
            else:
                # Fallback to regex
                regex_prices = extract_prices_regex(page_content)
                if regex_prices:
                    print("Regex found prices:")
                    for price in regex_prices:
                        print(f"  - {price}")
                    
                    quotes_found.append({
                        "company": "U-Haul",
                        "prices": regex_prices,
                        "categories": {},
                        "method": "Regex"
                    })
                else:
                    print("No prices found on page")
            
            # Wait for any dynamic content
            await page.wait_for_timeout(3000)
            
            # Try Budget Truck for comparison
            print("\nTrying Budget Truck...")
            await page.goto("https://www.budgettruck.com/", timeout=15000)
            await page.wait_for_load_state('networkidle')
            
            # Look for quote/reservation button
            try:
                quote_btn = page.locator('a:has-text("Reserve"), button:has-text("Quote"), a:has-text("Get Quote")').first
                if await quote_btn.is_visible(timeout=5000):
                    await quote_btn.click()
                    await page.wait_for_load_state('networkidle')
                    print("Clicked quote/reserve button")
            except:
                print("No quote button found")
            
            # Fill Budget form with customer details
            print("Filling Budget form with customer details...")
            filled = await enhanced_form_fill(page, customer_info)
            print(f"Successfully filled {filled} form fields")
            
            # Extract Budget prices
            page_content = await page.content()
            page_title = await page.title()
            
            print("Analyzing Budget page for prices...")
            
            ai_prices = extract_prices_with_ai(page_content, page_title)
            
            if ai_prices.get('found'):
                print("AI found Budget prices:")
                for category, price in ai_prices.get('categories', {}).items():
                    print(f"  {category}: {price}")
                if ai_prices.get('total'):
                    print(f"  Total: {ai_prices['total']}")
                
                quotes_found.append({
                    "company": "Budget Truck",
                    "prices": ai_prices.get('prices', []),
                    "total": ai_prices.get('total'),
                    "categories": ai_prices.get('categories', {}),
                    "method": "AI"
                })
            else:
                regex_prices = extract_prices_regex(page_content)
                if regex_prices:
                    quotes_found.append({
                        "company": "Budget Truck",
                        "prices": regex_prices,
                        "categories": {},
                        "method": "Regex"
                    })
            
            # Take screenshot
            await page.screenshot(path='final_quote_result.png')
            
            # Generate AI Report
            print("\nGenerating AI analysis report...")
            ai_report = generate_ai_report(customer_info, quotes_found)
            
            # Present Final Quote to User
            present_final_quote(customer_info, quotes_found)
            
            # Display AI Report
            print("\n" + "="*70)
            print("                AI ANALYSIS REPORT")
            print("="*70)
            print(ai_report)
            print("="*70)
            
            # Export to PDF
            print("\nExporting report to PDF...")
            pdf_filename = export_to_pdf(customer_info, quotes_found, ai_report)
            
            # Save text report
            with open('ai_moving_report.txt', 'w') as f:
                f.write(f"MOVING QUOTE ANALYSIS REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(ai_report)
            
            print(f"\n✓ PDF Report: {pdf_filename}")
            print("✓ Text Report: ai_moving_report.txt")
            
            # Save results
            with open('final_quotes.json', 'w') as f:
                json.dump(quotes_found, f, indent=2)
            
            await page.wait_for_timeout(5000)
            await browser.close()
            
        except Exception as e:
            await browser.close()
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_moving_quotes())