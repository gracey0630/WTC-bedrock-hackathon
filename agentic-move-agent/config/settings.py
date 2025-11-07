import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # AWS Bedrock Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # Claude 3 Opus Model ID for Bedrock (Vision + Text)
    CLAUDE_MODEL_ID = "anthropic.claude-3-opus-20240229-v1:0"
    
    # Model parameters
    MAX_TOKENS = 4096  # Opus supports up to 4096 output tokens
    TEMPERATURE = 0.7
    
    # Application settings
    SESSION_TIMEOUT = 3600  # 1 hour
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB per image

settings = Settings()