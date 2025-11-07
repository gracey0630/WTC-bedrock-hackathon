import boto3
import json
from config.settings import settings

print("🧪 Testing AWS Bedrock Connection...\n")

# Test connection
client = boto3.client('bedrock-runtime', region_name=settings.AWS_REGION)

try:
    response = client.invoke_model(
        modelId=settings.CLAUDE_MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Hello from Claude Sonnet 4!' if you can read this."
                }
            ]
        })
    )
    
    result = json.loads(response['body'].read())
    print("✅ SUCCESS! Bedrock is working!")
    print(f"\nClaude's response: {result['content'][0]['text']}\n")
    print(f"Model used: {settings.CLAUDE_MODEL_ID}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
