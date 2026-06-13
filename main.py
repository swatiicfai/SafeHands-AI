import os
import io
import json
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from PIL import Image

# Load environment variables from .env file if it exists
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

AIML_API_KEY = os.getenv("AIML_API_KEY")
FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")

if not AIML_API_KEY or not FEATHERLESS_API_KEY:
    print("[WARNING] AIML_API_KEY or FEATHERLESS_API_KEY is missing in the .env file.")
else:
    print("[INFO] Partner API keys detected.")

# Initialize the OpenAI clients for both partners
aiml_client = OpenAI(
    api_key=AIML_API_KEY or "missing_key",
    base_url="https://api.aimlapi.com/v1"
)

featherless_client = OpenAI(
    api_key=FEATHERLESS_API_KEY or "missing_key",
    base_url="https://api.featherless.ai/v1"
)

app = FastAPI(title="SafeHands AI Compliance Orchestrator")

class ClaimOutput(BaseModel):
    status: str
    estimated_loss: float
    confidence_score: float
    legal_rationale: str
    action_executed: str

def encode_image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode('utf-8')

# --- Multi-Agent Orchestration Classes ---

class IntakeAgent:
    """Agent responsible for analyzing the driver's transcript."""
    def extract(self, transcript: str) -> dict:
        prompt = f"""
        You are the Intake Agent for a logistics claims system.
        Analyze this driver transcript and extract the key details in strictly valid JSON format:
        {{
            "claimed_cargo_type": "string",
            "reported_damage": "string",
            "reported_temperature": "string or null"
        }}
        Transcript: "{transcript}"
        """
        response = featherless_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        if not content:
            return {"error": "LLM returned empty response"}
            
        clean_text = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            import re
            # Fallback: try to extract JSON between braces
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse JSON from response: {content}")

class VisionAgent:
    """Agent responsible for analyzing the cargo imagery."""
    def analyze(self, image_bytes: bytes) -> dict:
        base64_image = encode_image_to_base64(image_bytes)
        
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
        if not content:
            return {"error": "LLM returned empty response"}
            
        clean_text = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            import re
            # Fallback: try to extract JSON between braces
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse JSON from response: {content}")

class ComplianceAgent:
    """Agent responsible for cross-checking reports and making the final decision."""
    def evaluate(self, intake_report: dict, vision_report: dict) -> dict:
        prompt = f"""
        You are the Chief Compliance Agent. 
        You have received two reports:
        
        1. Intake Agent Report (from driver):
        {json.dumps(intake_report, indent=2)}
        
        2. Vision Agent Report (from cargo imagery):
        {json.dumps(vision_report, indent=2)}
        
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
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        if not content:
            return {"error": "LLM returned empty response"}
            
        clean_text = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            import re
            # Fallback: try to extract JSON between braces
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse JSON from response: {content}")

# -----------------------------------------

@app.post("/api/v1/compliance/verify", response_model=ClaimOutput)
async def verify_compliance_claim(
    driver_transcript: str = Form(...),
    cargo_image: UploadFile = File(...)
):
    try:
        if not AIML_API_KEY or not FEATHERLESS_API_KEY:
            raise ValueError("AIML_API_KEY or FEATHERLESS_API_KEY is not configured.")

        # Load inbound image
        image_bytes = await cargo_image.read()
        
        # Instantiate the 3 Agents
        intake_agent = IntakeAgent()
        vision_agent = VisionAgent()
        compliance_agent = ComplianceAgent()
        
        # Step 1: Intake Agent parses transcript
        intake_report = intake_agent.extract(driver_transcript)
        
        # Step 2: Vision Agent analyzes image
        vision_report = vision_agent.analyze(image_bytes)
        
        # Step 3: Compliance Agent evaluates both and makes final decision
        final_decision = compliance_agent.evaluate(intake_report, vision_report)
        
        return ClaimOutput(**final_decision)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Agent workflow execution fault: {str(e)}"
        )

# Serve static files and frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(static_dir, "index.html"))