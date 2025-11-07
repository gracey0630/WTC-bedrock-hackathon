import boto3
import json
import base64
from io import BytesIO
from PIL import Image
from config.settings import settings

class BedrockClient:
    """Bedrock API client for Claude 3 Opus"""
    
    def __init__(self):
        # Use default credentials from your AWS studio
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION
        )
        self.model_id = settings.CLAUDE_MODEL_ID
    
    def invoke_text(self, prompt, system_prompt=None, max_tokens=None):
        """Text-only inference"""
        messages = [{"role": "user", "content": prompt}]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or settings.MAX_TOKENS,
            "messages": messages,
            "temperature": settings.TEMPERATURE
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            print(f"❌ Bedrock API error: {e}")
            raise
    
    def invoke_vision(self, image_base64, prompt, max_tokens=None):
        """
        Vision + text inference with Claude 3 Opus
        Accepts base64-encoded image string directly
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or settings.MAX_TOKENS,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",  # Changed to PNG
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "temperature": settings.TEMPERATURE
        }
        
        try:
            print(f"  🔄 Calling Bedrock with model: {self.model_id}")
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            result_text = response_body['content'][0]['text']
            
            print(f"  ✅ Received response from Bedrock")
            return result_text
            
        except Exception as e:
            print(f"❌ Bedrock Vision API error: {e}")
            print(f"  Model ID: {self.model_id}")
            print(f"  Image data length: {len(image_base64) if image_base64 else 0}")
            raise
    
    def parse_json_response(self, response_text):
        """Safely parse JSON from LLM response"""
        # Remove markdown code blocks if present
        cleaned = response_text.strip()
        
        # Remove ```json and ``` markers
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse JSON: {e}")
            print(f"Response text (first 500 chars): {cleaned[:500]}...")
            raise

bedrock_client = BedrockClient()