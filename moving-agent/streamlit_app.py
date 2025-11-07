import streamlit as st
import asyncio
import json
from datetime import datetime
import time
from final_quote_agent import parse_customer_input, generate_ai_report, export_to_pdf

# Page config
st.set_page_config(
    page_title="AI Moving Quote Agent",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal CSS for header only
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1e3a8a 0%, #7c3aed 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'customer_info' not in st.session_state:
    st.session_state.customer_info = None
if 'quotes' not in st.session_state:
    st.session_state.quotes = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Header
st.markdown("""
<div class="main-header">
    <h1>🚚 AI Moving Quote Agent</h1>
    <p>Get instant quotes from multiple moving companies using AI</p>
</div>
""", unsafe_allow_html=True)

# Chat interface
st.subheader("💬 Chat with AI Assistant")

# Display chat messages using Streamlit components
for message in st.session_state.messages:
    if message['type'] == 'user':
        with st.chat_message("user"):
            st.write(message['content'])
    else:
        with st.chat_message("assistant"):
            st.write(message['content'])

# Input area
if not st.session_state.processing:
    with st.form("chat_form", clear_on_submit=True):
        st.write("**Tell me about your move:**")
        user_input = st.text_area(
            "Example: I'm Sarah Johnson, moving from Boston to Miami in March. 2-bedroom apartment. Email: sarah@email.com, phone: 555-0123",
            height=100,
            placeholder="Describe your move naturally..."
        )
        submitted = st.form_submit_button("🚀 Get Quotes", use_container_width=True)
        
        if submitted and user_input.strip():
            # Add user message
            st.session_state.messages.append({'type': 'user', 'content': user_input})
            st.session_state.processing = True
            
            # Parse customer info
            with st.spinner("🧠 AI is analyzing your request..."):
                customer_info = parse_customer_input(user_input)
                st.session_state.customer_info = customer_info
            
            # Show extracted info
            # Show extracted info in a nice format
            st.success("✅ Information Successfully Extracted!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Customer Details:**")
                st.write(f"Name: {customer_info['name']}")
                st.write(f"Email: {customer_info['email']}")
                st.write(f"Phone: {customer_info['phone']}")
            
            with col2:
                st.write("**Move Details:**")
                st.write(f"From: {customer_info['origin']}")
                st.write(f"To: {customer_info['destination']}")
                st.write(f"Date: {customer_info.get('move_date', 'TBD')}")
            
            info_message = "Information extracted and quote search initiated."
            st.session_state.messages.append({'type': 'bot', 'content': info_message})
            
            # Simulate quote gathering
            with st.spinner("🚛 Getting quotes from U-Haul, Budget Truck, and others..."):
                time.sleep(3)  # Simulate processing time
                
                # Mock quotes for demo
                quotes = [
                    {
                        'company': 'U-Haul',
                        'total': '$1,234',
                        'categories': {
                            'truck_rental': '$89/day',
                            'mileage': '$1.29/mile',
                            'deposit': '$150',
                            'insurance': '$28/day'
                        },
                        'method': 'AI'
                    },
                    {
                        'company': 'Budget Truck',
                        'total': '$1,456',
                        'categories': {
                            'truck_rental': '$95/day',
                            'mileage': '$1.35/mile',
                            'deposit': '$200',
                            'insurance': '$32/day'
                        },
                        'method': 'AI'
                    }
                ]
                
                st.session_state.quotes = quotes
            
            # Show results
            result_message = f"Found {len(quotes)} quotes for your move. Check the comparison below!"
            st.session_state.messages.append({'type': 'bot', 'content': result_message})
            st.session_state.processing = False
            st.rerun()

else:
    st.info("🔄 Processing your request... Please wait.")

# Results section
if st.session_state.quotes:
    st.markdown("---")
    st.subheader("📊 Quote Comparison")
    
    col1, col2 = st.columns(2)
    
    for i, quote in enumerate(st.session_state.quotes):
        with col1 if i % 2 == 0 else col2:
            with st.container():
                st.subheader(f"🚛 {quote['company']}")
                st.metric("Total Estimate", quote['total'])
                
                if quote.get('categories'):
                    st.write("**Price Breakdown:**")
                    for category, price in quote['categories'].items():
                        st.write(f"• {category.replace('_', ' ').title()}: **{price}**")
                
                st.write(f"*Source: {quote.get('method', 'Unknown')} Analysis*")
    
    # Savings calculation
    if len(st.session_state.quotes) >= 2:
        prices = []
        for quote in st.session_state.quotes:
            price_num = float(quote['total'].replace('$', '').replace(',', ''))
            prices.append((quote['company'], price_num))
        
        prices.sort(key=lambda x: x[1])
        cheapest = prices[0]
        most_expensive = prices[-1]
        savings = most_expensive[1] - cheapest[1]
        
        st.success(f"💰 **Best Deal:** {cheapest[0]} - ${cheapest[1]:,.0f}")
        st.info(f"💸 **You Save:** ${savings:,.0f} by choosing {cheapest[0]} over {most_expensive[0]}")
    
    # Generate report
    st.markdown("---")
    st.subheader("📄 Generate Report")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("📋 Generate AI Analysis Report", use_container_width=True):
            with st.spinner("🤖 AI is generating your personalized report..."):
                ai_report = generate_ai_report(st.session_state.customer_info, st.session_state.quotes)
                
                # Display report
                st.markdown("### 🤖 AI Analysis Report")
                st.write(ai_report)
                
                # Generate PDF
                try:
                    pdf_filename = export_to_pdf(st.session_state.customer_info, st.session_state.quotes, ai_report)
                    
                    with open(pdf_filename, "rb") as pdf_file:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_file.read(),
                            file_name=f"moving_quote_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    st.success("✅ Report generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating PDF: {str(e)}")

# Sidebar with info
with st.sidebar:
    st.markdown("### 🚚 How it works")
    st.markdown("""
    1. **Describe your move** in natural language
    2. **AI extracts** your information automatically  
    3. **Get quotes** from multiple companies
    4. **Compare prices** and save money
    5. **Download report** for your records
    """)
    
    st.markdown("### 💡 Example Input")
    st.markdown("""
    "Hi, I'm Maria Garcia, moving my 2-bedroom apartment from Chicago to Austin in April. 
    Email: maria@email.com, phone: 312-555-0199."
    """)
    
    if st.session_state.customer_info:
        st.markdown("### 👤 Customer Info")
        st.json(st.session_state.customer_info)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    🤖 Powered by AWS Bedrock AI • 🚚 Moving Quote Agent Demo
</div>
""", unsafe_allow_html=True)