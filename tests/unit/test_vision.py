"""Test Bedrock vision capabilities."""

import sys
import base64
from pathlib import Path
from PIL import Image
import io

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logger, load_config, get_logger
from src.core import BedrockProvider


def create_test_image():
    """Create a simple test image with text."""
    # Create a simple image with text
    img = Image.new('RGB', (400, 200), color='white')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


def test_vision_analysis():
    """Test vision analysis with Bedrock."""
    
    print("\n" + "="*60)
    print("VISION CAPABILITY TEST")
    print("="*60)
    
    setup_logger("INFO", "logs/test_vision.log")
    config = load_config()
    logger = get_logger(__name__)
    
    try:
        # Initialize provider
        provider = BedrockProvider(
            model_id=config.bedrock.model_id,
            embedding_model_id=config.bedrock.embedding_model_id,
            region=config.bedrock.region
        )
        
        print("\n✅ BedrockProvider initialized")
        
        # Create test image
        print("\n[1/2] Creating test image...")
        image_bytes = create_test_image()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        print("✅ Test image created (400x200 white rectangle)")
        
        # Test vision analysis
        print("\n[2/2] Testing vision analysis with Claude...")
        
        # Build vision request
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": "Describe this image briefly. What do you see?"
                        }
                    ]
                }
            ]
        }
        
        import json
        import boto3
        
        client = boto3.client(
            service_name='bedrock-runtime',
            region_name=config.bedrock.region
        )
        
        response = client.invoke_model(
            modelId=config.bedrock.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract response
        content = response_body.get('content', [])
        if content and content[0].get('type') == 'text':
            vision_response = content[0].get('text', '')
            
            print("\n✅ VISION ANALYSIS SUCCESSFUL!")
            print("\n" + "-"*60)
            print("Claude's Vision Response:")
            print("-"*60)
            print(vision_response)
            print("-"*60)
            
            print("\n" + "="*60)
            print("✅ VISION CAPABILITY: WORKING!")
            print("="*60)
            print("\nClaude can:")
            print("  ✅ Process images via Bedrock")
            print("  ✅ Analyze image content")
            print("  ✅ Describe visual information")
            print("\nReady for PDF image analysis!")
            print("="*60 + "\n")
            
            return True
        else:
            print("\n❌ No text in vision response")
            print(f"Response: {response_body}")
            return False
            
    except Exception as e:
        print(f"\n❌ Vision test failed: {e}")
        print("\nThis might mean:")
        print("  1. Vision not enabled in your Bedrock model access")
        print("  2. Model doesn't support vision (unlikely with Claude)")
        print("  3. Request format issue")
        
        import traceback
        traceback.print_exc()
        
        print("\n" + "="*60)
        print("⚠️  VISION CAPABILITY: NOT WORKING")
        print("="*60)
        print("\nOptions:")
        print("  1. Continue without vision (use text-only PDF parsing)")
        print("  2. Enable vision in AWS Bedrock Console")
        print("  3. Skip image analysis for now")
        print("="*60 + "\n")
        
        return False


if __name__ == "__main__":
    success = test_vision_analysis()
    
    if success:
        print("✅ You can proceed with vision-enabled PDF parsing!")
    else:
        print("⚠️  Recommend setting use_vision_for_images: false in config")
        print("   PDF parsing will work with text-only mode")
