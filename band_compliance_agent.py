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
BAND_API_KEY = os.environ.get("COMPLIANCE_AGENT_API_KEY")

# Initialize AI/ML API Client
aiml_client = OpenAI(
    api_key=AIML_API_KEY,
    base_url="https://api.aimlapi.com/v1"
)

class ComplianceAdapter(SimpleAdapter[list]):
    
    def __init__(self):
        super().__init__()
        self.state = {"intake_report": None, "vision_report": None}

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
        
        if "Intake Output:" in msg.text:
            raw_json = msg.text.split("Intake Output:")[1].strip()
            self.state["intake_report"] = raw_json
            print("[ComplianceAgent] Logged Intake Report.")
            
        if "Vision Output:" in msg.text:
            raw_json = msg.text.split("Vision Output:")[1].strip()
            self.state["vision_report"] = raw_json
            print("[ComplianceAgent] Logged Vision Report.")
            
        # Check if both are ready
        if self.state["intake_report"] and self.state["vision_report"]:
            print("[ComplianceAgent] Both reports received. Executing final evaluation...")
            
            prompt = f"""
            You are the Chief Compliance Agent. 
            You have received two reports:
            
            1. Intake Agent Report (from driver):
            {self.state['intake_report']}
            
            2. Vision Agent Report (from cargo imagery):
            {self.state['vision_report']}
            
            Tasks:
            1. Cross-check for discrepancies between claimed cargo and detected cargo.
            2. Evaluate the severity of the damage.
            3. Determine whether to Approve or Reject the claim.
            4. Calculate financial loss estimation based on the vision report.
            
            Return structural JSON conforming precisely to this format:
            {{
                "status": "APPROVED" or "REJECTED",
                "estimated_loss": float,
                "confidence_score": float,
                "legal_rationale": "Detailed explanation matching enterprise criteria",
                "action_executed": "API_LEDGER_REFUND_TRIGGERED"
            }}
            """
            
            response = aiml_client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content
            clean_text = content.replace("```json", "").replace("```", "").strip()
            
            print(f"[ComplianceAgent] Final Decision: {clean_text}")
            
            # Broadcast final decision to Web App / Webhook
            await tools.send_message(f"Final Decision: {clean_text}")
            
            # Reset state for next claim
            self.state = {"intake_report": None, "vision_report": None}

async def main():
    print("Starting Compliance Agent on Band Platform...")
    agent_id = os.environ.get("COMPLIANCE_AGENT_ID")
    
    async with Agent.create(
        adapter=ComplianceAdapter(),
        agent_id=agent_id,
        api_key=BAND_API_KEY
    ) as agent:
        await agent.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
