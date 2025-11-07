#!/usr/bin/env python3
"""
AI Moving Quote Agent - Streamlit Demo Launcher
"""
import subprocess
import sys

def main():
    print("🚚 AI Moving Quote Agent - Starting Demo...")
    print("📱 Opening Streamlit app at http://localhost:8501")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port=8501"])
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try: pip install streamlit")

if __name__ == "__main__":
    main()