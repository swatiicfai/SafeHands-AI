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

FEATHERLESS_API_KEY = os.environ.get("FEATHERLESS_API_KEY")
BAND_API_KEY = os.environ.get("INTAKE_AGENT_API_KEY")

# Initialize Featherless Client
featherless_client = OpenAI(
    api_key=FEATHERLESS_API_KEY,
    base_url="https://api.featherless.ai/v1"
)

class IntakeAdapter(SimpleAdapter[list]):
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
        print(f"[IntakeAgent] Received message: {msg.text}")
        
        # We assume the message contains the driver transcript
        prompt = f"""
        You are the Intake Agent for a logistics claims system.
        Analyze this driver transcript and extract the key details in strictly valid JSON format:
        {{
            "claimed_cargo_type": "string",
            "reported_damage": "string",
            "reported_temperature": "string or null"
        }}
        Transcript: "{msg.text}"
        """
        
        # Execute via Featherless API
        response = featherless_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content
        clean_text = content.replace("```json", "").replace("```", "").strip()
        
        print(f"[IntakeAgent] Extracted Context: {clean_text}")
        
        # Pass context via Band Platform to the Vision Agent
        await tools.send_message(
            f"Intake Output: {clean_text}", 
            mentions=["@gupta.swati1361/vision-agent"]
        )

async def main():
    print("Starting Intake Agent on Band Platform...")
    agent_id = os.environ.get("INTAKE_AGENT_ID")
    
    async with Agent.create(
        adapter=IntakeAdapter(),
        agent_id=agent_id,
        api_key=BAND_API_KEY
    ) as agent:
        await agent.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
