# 📦 SafeHands AI: Compliance Orchestrator

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/swatiicfai/SafeHands-AI)

SafeHands AI is a distributed, multi-agent AI pipeline designed to automate logistics and insurance claims. By separating cognitive tasks across specialized agents connected via the **Band** coordination layer, SafeHands AI detects insurance fraud in real-time by cross-checking driver claims against multi-modal computer vision analysis.

---

## 🚀 The Challenge We Solved
Logistics and freight insurance fraud costs enterprises billions annually. A human adjuster has to manually read a driver's transcript ("the cargo was completely destroyed") and cross-reference it against photographic evidence, which is slow and error-prone.

**Our Solution:** We built a multi-agent AI system that automatically ingests the driver's transcript, analyzes the cargo imagery using a Vision AI, and passes both reports to a Chief Compliance Agent to detect discrepancies and make an instant approval or rejection decision.

---

## 🧠 Multi-Agent Architecture

This project was built for the **Band of Agents Hackathon** and utilizes three highly specialized agents running concurrently:

```mermaid
graph TD
    User([Driver / User]) -->|Voice Transcript| Intake[🎙️ Intake Agent]
    User -->|Cargo Image Upload| Vision[👁️ Vision Agent]
    
    subgraph "Band Collaboration Layer"
    Intake -->|Extracts JSON| Compliance[⚖️ Compliance Agent]
    Vision -->|Analyzes Image to JSON| Compliance
    end
    
    Compliance -->|Fraud Discrepancy Check| Ledger[(Immutable Ledger Log)]
    Compliance -->|Decision: Approve/Reject| Output([Final Audit Report])
```

### The 3 Agents
1. **Intake Agent (Featherless API / Llama 3.1 8B):** Parses unstructured driver transcripts into structured JSON data (claimed damage, cargo type).
2. **Vision Agent (Featherless API / Qwen2.5-VL 72B):** A powerful multi-modal model that analyzes the cargo image, detects the cargo type, and estimates the *actual* damage percentage.
3. **Compliance Agent (AI/ML API / Llama 3.3 70B):** The central decision-maker. It cross-references the Intake and Vision reports to catch liars. If the driver claims 100% damage but the Vision agent sees 30% damage, the Compliance agent instantly flags the discrepancy and REJECTS the claim.

---

## 📸 Screenshots

*(Hackathon Judges: See our intelligent discrepancy detection in action below!)*

### Scenario 1: Fraud Detected & Claim Rejected
*(Drag and drop the screenshot of the REJECTED tomatoes claim here)*

### Scenario 2: Truthful Claim Approved
*(Drag and drop the screenshot of the APPROVED strawberries claim here)*

---

## 🛠️ Tech Stack & Partner APIs

* **Orchestration:** [Band SDK](https://band.ai/) (WebSocket remote agent coordination)
* **Backend:** FastAPI (Python)
* **LLM APIs (Partner Track):**
  * [Featherless.ai](https://featherless.ai/) (Hosting Llama 3.1 & Qwen Vision)
  * [AI/ML API](https://aimlapi.com/) (Hosting Llama 3.3 70B)
* **Frontend:** Vanilla JS / CSS with Glassmorphism UI

---

## ⚙️ Running Locally

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Add your API keys to a `.env` file:
```env
FEATHERLESS_API_KEY=your_key
AIML_API_KEY=your_key
INTAKE_AGENT_ID=your_id
INTAKE_AGENT_API_KEY=your_key
VISION_AGENT_ID=your_id
VISION_AGENT_API_KEY=your_key
COMPLIANCE_AGENT_ID=your_id
COMPLIANCE_AGENT_API_KEY=your_key
```
4. Start the 3 Band Agents in background processes:
```bash
python band_intake_agent.py
python band_vision_agent.py
python band_compliance_agent.py
```
5. Start the web dashboard:
```bash
python -m uvicorn main:app --reload
```
