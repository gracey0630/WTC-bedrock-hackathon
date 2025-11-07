

import base64
import io
import json
import logging
import boto3
from PIL import Image
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class InventoryAgent:
    """
    Inventory management using Amazon Bedrock + Claude 3 Vision
    """

    def __init__(self, session_id, region_name="us-east-1"):
        self.session_id = session_id
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=region_name
        )

    def execute(self, task, state):
        """Execute inventory tasks"""
        if "analyze" in task.lower() and "photo" in task.lower():
            return self.analyze_photos(state.get("uploaded_photos", []))
        elif "calculate" in task.lower() and "volume" in task.lower():
            return self.calculate_volume(state.get("inventory", []))
        else:
            return {"status": "success", "summary": f"Inventory task: {task}"}

    def analyze_photos(self, photos):
        """Analyze uploaded room photos using Claude 3 multimodal"""
        if not photos:
            return {"status": "failed", "error": "No photos provided for analysis"}

        all_items = []
        for idx, photo in enumerate(photos):
            print(f"📸 Analyzing photo {idx+1}/{len(photos)}...")
            try:
                items = self.detect_items(photo)
                all_items.extend(items)
            except Exception as e:
                print(f"❌ Failed to analyze photo {idx+1}: {e}")
                raise Exception(f"Vision analysis failed for photo {idx+1}: {str(e)}")

        print(f"✅ Detected {len(all_items)} items total")

        return {
            "status": "success",
            "summary": f"Cataloged {len(all_items)} items from {len(photos)} photos",
            "state_update": {"inventory": all_items},
        }

    def image_to_base64(self, image):
        """Convert various image inputs to base64 string"""
        try:
            if isinstance(image, str):  # file path
                with open(image, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            elif isinstance(image, Image.Image):  # PIL image
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
            elif isinstance(image, bytes):
                return base64.b64encode(image).decode("utf-8")
            elif hasattr(image, "read"):  # file-like (e.g., Streamlit upload)
                image.seek(0)
                return base64.b64encode(image.read()).decode("utf-8")
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")
        except Exception as e:
            print(f"⚠️ Image conversion error: {e}")
            raise

    def run_claude_multimodal(self, image_b64, image_ext, prompt, max_tokens=2000):
        """Invoke Claude 3 Sonnet with image + text prompt"""
        message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{image_ext}",
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [message],
        })

        try:
            response = self.bedrock_runtime.invoke_model(
                body=body, modelId=self.model_id
            )
            response_body = json.loads(response.get("body").read())
            return response_body
        except ClientError as e:
            msg = e.response["Error"]["Message"]
            logger.error(f"AWS ClientError: {msg}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def detect_items(self, image):
        """Use Claude 3 to analyze room and detect furniture"""
        prompt = """Analyze this room photo and detect all furniture/items include all objects (furnitures/decor) in the room. For each item provide:
1. Item name (e.g., "Sofa", "Dining Table", "Bed Frame"). If there are duplicates mention each separately if they have differnet descriptions.
2. A desciption of the object including the color, material you think it would be (wood/leather), size of possible (large/small)
3. Notes (fragile, heavy, valuable, condition, etc.)

Return ONLY valid JSON in this exact format with NO additional text:
{
  "items": [
    {
      "name": "Sofa",
      "description": "a red leather large sofa.",
      "notes": "Heavy"
    }
  ]
}
"""

        # Convert image to base64
        image_b64 = self.image_to_base64(image)
        image_ext = "png"  # safe default

        # Run Bedrock multimodal inference
        response = self.run_claude_multimodal(image_b64, image_ext, prompt)
        print(f"🤖 Raw model response: {json.dumps(response, indent=2)[:400]}")

        # Extract model output text
        model_output = response["content"][0]["text"]

        # Parse the returned JSON safely
        try:
            result = json.loads(model_output)
            items = result.get("items", [])
        except json.JSONDecodeError:
            raise ValueError(f"Model did not return valid JSON: {model_output[:200]}")

        if not items:
            raise ValueError("No items detected or malformed JSON output.")
        
        print(f"✅ Detected {len(items)} items")
        return items

    def calculate_volume(self, inventory):
        """Compute total volume from all items"""
        if not inventory:
            return {
                "status": "success",
                "summary": "No items in inventory",
                "state_update": {"total_volume": 0},
            }

        total_volume = sum(item.get("volume", 0) for item in inventory)
        return {
            "status": "success",
            "summary": f"Total volume: {total_volume} cubic feet",
            "state_update": {"total_volume": total_volume},
        }
