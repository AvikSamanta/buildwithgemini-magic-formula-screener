# Magic Formula Investment Build With Gemini Agent

**Project Name**: Magic Formula Investment Build With Gemini Agent  
**Framework**: Google Agent Development Kit (ADK)  
**Deployment Target**: Google Cloud Vertex AI Agent Platform (Agent Runtime)  
**GCP Project ID**: `qwiklabs-gcp-02-8acb2ff2c23a`  
**GCP Region**: `us-east1`  
**Agent Engine / Memory Bank ID**: `8738801869331103744`  
**Cloud Storage Bucket**: `gs://magic-formula-screener-qwiklabs-gcp-02-8acb2ff2c23a`  

---

## 🌟 Executive Overview

The **Magic Formula Investment Build With Gemini Agent** is an automated value investing research assistant built with the **Google Agent Development Kit (ADK)**. It applies Joel Greenblatt’s Magic Formula strategy to top Indian equities (Nifty 100 index), evaluating companies based on **Earnings Yield** ($\text{EBIT} / \text{EV}$) and **Return on Capital** ($\text{EBIT} / (\text{NWC} + \text{NFA})$).

The project incorporates 6 core capabilities:
1. **Firestore Database Queries & Seeding**: Persists and queries financial metrics for Nifty 100 companies.
2. **Cloud Storage File Exports**: Exports screener output as formatted CSV files to public Cloud Storage URLs.
3. **External Currency Exchange API**: Real-time USD to INR rate lookups.
4. **Vertex AI Gemini Image Generation**: Generates stock chart infographics using `gemini-3.1-flash-lite-image`.
5. **Sandbox Code Execution**: Safely executes Python code for financial math using `AgentEngineSandboxCodeExecutor`.
6. **Cross-Session Memory Bank & A2UI**: Retains investor preferences across sessions via `VertexAiMemoryBankService` and renders structured A2UI v0.8 cards in `adk web`.

---

## 🏗️ System Architecture

```
                                +---------------------------+
                                |    User / ADK Web / CLI   |
                                +-------------+-------------+
                                              |
                                              v
                                +-------------+-------------+
                                |  Agent_197115 Root Agent  |
                                |     (gemini-2.5-flash)    |
                                +------+------+------+------+
                                       |      |      |
      +--------------------------------+      |      +--------------------------------+
      |                                       |                                       |
      v                                       v                                       v
+-----+------+                         +------+-----+                          +------+------+
| Firestore  |                         | GCS Bucket |                          | Memory Bank |
|  'stocks'  |                         | CSV & PNG  |                          | Vertex AI   |
+------------+                         +------------+                          +-------------+
      |                                       |
      v                                       v
+-----+------+                         +------+-----+                          +------+------+
| Currency   |                         | Gemini 3.1 |                          | Sandbox Code|
| Exchange   |                         | Flash Image|                          | Execution   |
+------------+                         +------------+                          +-------------+
```

---

## 🛠️ Complete Source Code Reference

### 1. `app/tools.py` (Custom Function Tools)
```python
import io
import json
import os
import requests
from google.cloud import datastore, firestore, storage
from google.genai import client, types
from google.adk.tools.tool_context import ToolContext

GCP_PROJECT_ID = "qwiklabs-gcp-02-8acb2ff2c23a"
GCS_BUCKET_NAME = "magic-formula-screener-qwiklabs-gcp-02-8acb2ff2c23a"

def get_top_magic_formula_stocks(limit: int = 10) -> str:
    """Query Firestore 'stocks' collection and calculate Greenblatt Magic Formula ranks."""
    db = firestore.Client(project=GCP_PROJECT_ID)
    docs = db.collection("stocks").stream()
    
    stocks = []
    for doc in docs:
        data = doc.to_dict()
        ebit = data.get("ebit_cr", 0.0)
        ev = data.get("enterprise_value_cr", 1.0)
        nwc = data.get("net_working_capital_cr", 0.0)
        nfa = data.get("net_fixed_assets_cr", 0.0)
        
        ey = (ebit / ev) if ev > 0 else 0.0
        capital = nwc + nfa
        roc = (ebit / capital) if capital > 0 else 0.0
        
        data["ey_pct"] = ey * 100
        data["roc_pct"] = roc * 100
        stocks.append(data)
        
    stocks.sort(key=lambda s: s["ey_pct"], reverse=True)
    for rank, s in enumerate(stocks, 1):
        s["ey_rank"] = rank
        
    stocks.sort(key=lambda s: s["roc_pct"], reverse=True)
    for rank, s in enumerate(stocks, 1):
        s["roc_rank"] = rank
        s["combined_score"] = s["ey_rank"] + s["roc_rank"]
        
    stocks.sort(key=lambda s: s["combined_score"])
    
    result = []
    for final_rank, s in enumerate(stocks[:limit], 1):
        result.append({
            "magic_rank": final_rank,
            "ticker": s.get("ticker"),
            "company_name": s.get("company_name"),
            "sector": s.get("sector"),
            "earnings_yield_pct": f"{s['ey_pct']:.2f}%",
            "roc_pct": f"{s['roc_pct']:.2f}%",
            "enterprise_value_cr": f"₹{s.get('enterprise_value_cr', 0):,.2f} Cr",
            "combined_score": s["combined_score"]
        })
    return json.dumps(result, indent=2)

def export_screener_to_csv(limit: int = 10) -> str:
    """Export top stocks to CSV and upload to Cloud Storage."""
    stocks_json = get_top_magic_formula_stocks(limit=limit)
    stocks = json.loads(stocks_json)
    
    output = io.StringIO()
    output.write("MagicRank,Ticker,CompanyName,Sector,EarningsYield,ROC,EnterpriseValueCr\n")
    for s in stocks:
        output.write(f"{s['magic_rank']},{s['ticker']},\"{s['company_name']}\",\"{s['sector']}\",{s['earnings_yield_pct']},{s['roc_pct']},{s['enterprise_value_cr'].replace(',', '')}\n")
        
    csv_bytes = output.getvalue().encode("utf-8")
    
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob("exports/magic_formula_top_10.csv")
    blob.upload_from_string(csv_bytes, content_type="text/csv")
    
    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/exports/magic_formula_top_10.csv"
    return f"Successfully exported top {len(stocks)} stocks to CSV!\n\n📥 Download: {public_url}"

def generate_stock_chart_image(prompt: str, tool_context: ToolContext = None) -> str:
    """Generate financial infographic chart image using gemini-3.1-flash-lite-image."""
    genai_client = client.Client(location="global")
    response = genai_client.models.generate_images(
        model="gemini-3.1-flash-lite-image",
        prompt=f"A sleek financial chart infographic: {prompt}",
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9",
            output_mime_type="image/png",
        ),
    )
    
    image_bytes = response.generated_images[0].image.image_bytes
    
    if tool_context:
        tool_context.save_artifact("stock_chart.png", image_bytes, mime_type="image/png")
        
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob("charts/magic_formula_chart.png")
    blob.upload_from_string(image_bytes, content_type="image/png")
    
    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/charts/magic_formula_chart.png"
    return f"Successfully generated chart!\n\n🖼️ Public URL: {public_url}"
```

---

### 2. `app/agent.py` (Root Agent & Memory Wiring)
```python
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import PreloadMemoryTool
from google.adk.models.gemini import Gemini
from google.adk.tools import AgentTool
from a2ui.schemas import A2uiSchemaManager, BasicCatalog

from app.a2ui_utils import a2ui_callback
from app.tools import (
    export_screener_to_csv,
    generate_stock_chart_image,
    get_currency_exchange_rate,
    get_stock_financials,
    get_top_magic_formula_stocks,
    save_stock_financials,
)

MODEL = "gemini-2.5-flash"
GCP_PROJECT_ID = "qwiklabs-gcp-02-8acb2ff2c23a"
MEMORY_BANK_ID = "8738801869331103744"

# Sandbox Code Executor
code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=f"projects/427964782674/locations/us-east1/reasoningEngines/{MEMORY_BANK_ID}"
)

code_execution_agent = Agent(
    name="CodeExecutionAgent",
    model=Gemini(model=MODEL),
    instruction="Write and execute Python code in your Agent Engine sandbox for math and ratio calculations.",
    code_executor=code_executor,
)

# A2UI System Prompt Generator
a2ui_manager = A2uiSchemaManager(version="0.8", catalogs=[BasicCatalog.get_config("0.8")])
a2ui_instruction = a2ui_manager.get_agent_instruction()

root_agent = Agent(
    name="Agent_197115",
    model=Gemini(model=MODEL),
    instruction=f"You are a Magic Formula investment assistant.\n\n{a2ui_instruction}",
    tools=[
        PreloadMemoryTool(),
        get_top_magic_formula_stocks,
        get_stock_financials,
        save_stock_financials,
        export_screener_to_csv,
        get_currency_exchange_rate,
        generate_stock_chart_image,
        AgentTool(agent=code_execution_agent),
    ],
    after_model_callback=a2ui_callback,
)

app = App(root_agent=root_agent, name="app")
```

---

## ⚡ Setup & Deployment Command Reference

### Local Run Command
```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://8738801869331103744
```

### Agent Platform Redeployment Command
```bash
agents-cli deploy --service-name my-agent --no-confirm-project --update-env-vars "MEMORY_SERVICE_URI=agentengine://8738801869331103744"
```

### Required GCP Service Account IAM Roles
```bash
# Grant Firestore access
gcloud projects add-iam-policy-binding qwiklabs-gcp-02-8acb2ff2c23a \
  --member="serviceAccount:service-427964782674@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Grant Storage Bucket Admin access
gsutil iam ch \
  serviceAccount:service-427964782674@gcp-sa-aiplatform-re.iam.gserviceaccount.com:objectAdmin \
  gs://magic-formula-screener-qwiklabs-gcp-02-8acb2ff2c23a
```

---

*Document prepared for external reference and portfolio archiving.*
