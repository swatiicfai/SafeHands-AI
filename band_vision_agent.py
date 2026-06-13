import os
import json
import asyncio
from openai import OpenAI
from band import Agent
from band.core.simple_adapter import SimpleAdapter
from band.core.types import PlatformMessage
from band.core.protocols import AgentToolsProtocol

# Load environment configuration
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                key, val = line.strip().split("=", 1)
                os.environ[key.strip()] = val.strip()

AIML_API_KEY = os.environ.get("AIML_API_KEY")
FEATHERLESS_API_KEY = os.environ.get("FEATHERLESS_API_KEY")
BAND_API_KEY = os.environ.get("VISION_AGENT_API_KEY")

# Initialize AI/ML API Client (for text tasks)
aiml_client = OpenAI(
    api_key=AIML_API_KEY,
    base_url="https://api.aimlapi.com/v1"
)

# Initialize Featherless Client (for vision tasks - Qwen2.5-VL)
featherless_client = OpenAI(
    api_key=FEATHERLESS_API_KEY,
    base_url="https://api.featherless.ai/v1"
)

class VisionAdapter(SimpleAdapter[list]):
    async def on_message(
        self,
        msg: PlatformMessage,
        tools: AgentToolsProtocol,
        history: list,
        participants_msg: str | None,
        contacts_msg: str | None,
        *,
        is_session_bootstrap: bool,
        room_id: str,
    ) -> None:
        
        # If this isn't targeted at VisionAgent or doesn't contain image data, ignore
        if "Image Data:" not in msg.text:
            return
            
        print("[VisionAgent] Received image data for analysis.")
        
        # Extract base64 image from message
        base64_image = msg.text.split("Image Data:")[1].strip()
        
        prompt = """
        You are the Vision Audit Agent for a logistics claims system.
        Analyze this cargo image and report your findings in strictly valid JSON format:
        {
            "detected_cargo_type": "string",
            "visible_damage_description": "string",
            "visible_temperature_reading": "string or null",
            "estimated_damage_percentage": float
        }
        """
        
        response = featherless_client.chat.completions.create(
            model="Qwen/Qwen2.5-VL-72B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        content = response.choices[0].message.content
        clean_text = content.replace("```json", "").replace("```", "").strip()
        print(f"[VisionAgent] Extracted Context: {clean_text}")
        
        # Pass context via Band Platform to the Compliance Agent
        await tools.send_message(
            f"Vision Output: {clean_text}", 
            mentions=["@gupta.swati1361/compliance-agent"]
        )

async def main():
    print("Starting Vision Agent on Band Platform...")
    agent_id = os.environ.get("VISION_AGENT_ID")
    
    async with Agent.create(
        adapter=VisionAdapter(),
        agent_id=agent_id,
        api_key=BAND_API_KEY
    ) as agent:
        await agent.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
