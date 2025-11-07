# 🚚 AI Moving Quote Agent

An intelligent moving quote system that uses AWS Bedrock AI to parse natural language requests and provide personalized moving quotes with PDF reports.

## ✨ Features

- **Natural Language Processing**: Describe your move in plain English
- **AI-Powered Analysis**: AWS Bedrock Claude 4.0 Sonnet extracts customer information
- **Multi-Company Quotes**: Compare prices from multiple moving companies
- **Professional Reports**: Generate and download PDF analysis reports
- **Modern UI**: Clean Streamlit interface with chat-style interaction

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AWS Credentials**
   ```bash
   aws configure
   # or set environment variables:
   # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
   ```

3. **Run the Demo**
   ```bash
   python run_demo.py
   ```

4. **Open Browser**
   - Navigate to: http://localhost:8501
   - Enter your moving details naturally
   - Get instant quotes and analysis

## 💬 Example Input

```
"Hi, I'm Sarah Johnson, moving my 2-bedroom apartment from Boston to Miami in March. 
Email: sarah@email.com, phone: 555-0123. Need quotes for a long-distance move."
```

## 📁 Files

- `streamlit_app.py` - Main Streamlit application
- `final_quote_agent.py` - AI processing and PDF generation
- `run_demo.py` - Demo launcher script
- `requirements.txt` - Python dependencies

## 🤖 AI Technology

- **AWS Bedrock**: Claude 4.0 Sonnet for natural language understanding
- **Smart Parsing**: Extracts names, contacts, locations, dates automatically
- **Quote Analysis**: Intelligent price comparison and recommendations
- **Report Generation**: Professional PDF reports with insights

## 🎯 Demo Flow

1. **Input**: Natural language moving request
2. **Parse**: AI extracts customer information
3. **Quote**: Get estimates from multiple companies
4. **Compare**: Side-by-side price analysis
5. **Report**: Download professional PDF summary

---
*Powered by AWS Bedrock AI • Built with Streamlit*