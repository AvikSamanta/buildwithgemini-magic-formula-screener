# Build With Gemini - Magic Formula Screener AI Agent (Nifty 100)

An intelligent, data-driven investment assistant powered by **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Vertex AI Agent Platform**. The agent automates value investing analysis for top Indian companies (Nifty 100) using Joel Greenblatt's Magic Formula strategy.

---

## 🚀 What the Agent Does

The agent provides interactive stock screening, financial lookup, ratio calculations, and visual reporting for Indian equities using the following implemented tools and Google Cloud services:

### 🛠️ Implemented Tools
- **Magic Formula Stock Screener (`get_top_magic_formula_stocks`)**:
  Queries the Firestore `stocks` database collection, calculates Earnings Yield ($\text{EBIT} / \text{EV}$) and Return on Capital ($\text{EBIT} / (\text{NWC} + \text{NFA})$), ranks companies on both dimensions, and returns combined rankings.
- **Financial Metrics Lookup (`get_stock_financials`)**:
  Retrieves detailed financial metrics (EBIT, Enterprise Value, Net Working Capital, Net Fixed Assets) for individual ticker symbols from Firestore.
- **Update Financial Data (`save_stock_financials`)**:
  Saves or updates company financial records in Firestore.
- **CSV Report Export (`export_screener_to_csv`)**:
  Compiles stock rankings into a CSV file, uploads it to a public Google Cloud Storage bucket, and returns a public download URL.
- **Live Currency Exchange Rates (`get_currency_exchange_rate`)**:
  Fetches real-time foreign exchange conversion rates (e.g. USD to INR) via an open API.
- **Chart Image Generation (`generate_stock_chart_image`)**:
  Generates custom financial chart infographics using `gemini-3.1-flash-lite-image` on Vertex AI, saves the image artifact, and uploads the PNG bytes to Cloud Storage to return a public image URL.
- **Python Sandbox Code Execution (`CodeExecutionAgent`)**:
  Delegates complex math, ratio analysis, or financial formulas to a dedicated sub-agent powered by `AgentEngineSandboxCodeExecutor` for safe execution in an Agent Engine Python sandbox.

---

## ☁️ Google Cloud & ADK Technologies Wired Up

- **Vertex AI Agent Platform / Agent Runtime**:
  Managed container hosting and orchestration for the deployed ADK agent.
- **Google Cloud Firestore**:
  NoSQL database storing the `stocks` collection containing financial metrics for Nifty 100 companies.
- **Google Cloud Storage (GCS)**:
  Public storage bucket hosting generated CSV reports and chart PNG images.
- **Vertex AI Gemini Models**:
  `gemini-2.5-flash` for agent reasoning and tool orchestration; `gemini-3.1-flash-lite-image` for image generation.
- **Vertex AI Memory Bank**:
  Durable cross-session memory service using `PreloadMemoryTool` and session extraction callbacks to remember investor risk tolerance, portfolio goals, and preferences across sessions.
- **A2UI Rich UI Rendering (v0.8)**:
  System instructions built with `A2uiSchemaManager` and `BasicCatalog`, combined with an `after_model_callback` (`a2ui_utils.py`) to render structured visual cards in `adk web`.

---

## 📋 Planned / Future Improvements

- **Full Nifty 100 Automated Data Ingestion Pipeline**:
  Automatic real-time data ingestion for all 100 companies from official stock exchange feeds (currently seeded with representative Nifty 100 stocks in Firestore).

---

## 💻 Local Development & Setup Instructions

### Prerequisites
- Python 3.12 or 3.13
- `uv` package manager installed (`uv --version`)
- Google Cloud SDK (`gcloud`) authenticated to your GCP project

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment
Set required environment variables or create a `.env` file in the project root:
```bash
export GOOGLE_GENAI_USE_VERTEXAI="true"
export GOOGLE_CLOUD_PROJECT="YOUR_GCP_PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="us-east1"
```

### 3. Seed Firestore Database (Optional)
```bash
uv run python seed_firestore.py
```

### 4. Run Locally in ADK Web Playground
To run the agent locally with hot reloading and Memory Bank support:
```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://YOUR_MEMORY_BANK_ID
```
Then open `http://127.0.0.1:8080` in your web browser.

> **Note**: For A2UI rich cards to render in the playground, ensure **Token Streaming is turned OFF** (gear icon in the playground header).

---

## 🚢 Deployment Instructions

To deploy the agent to Vertex AI Agent Runtime:

```bash
agents-cli deploy --no-confirm-project --update-env-vars "MEMORY_SERVICE_URI=agentengine://YOUR_MEMORY_BANK_ID"
```

To check deployment status:
```bash
agents-cli deploy --status
```
