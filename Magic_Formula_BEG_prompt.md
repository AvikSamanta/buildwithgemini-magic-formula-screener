# Magic Formula BEG Prompt

> **Master Build Prompt for Google Antigravity / ADK AI Assistant**  
> Use this prompt to recreate the Nifty 100 Magic Formula Screener AI Agent from scratch.

---

```markdown
Build a production-grade, value-investing AI Agent using Google Agent Development Kit (ADK) and Vertex AI Agent Platform for Indian stocks (Nifty 100 index), based on Joel Greenblatt's Magic Formula investment strategy.

### 🎯 Core Strategy & Formula Specification
1. **Earnings Yield (EY)** = EBIT / Enterprise Value (EV)
2. **Return on Capital (ROC)** = EBIT / (Net Working Capital + Net Fixed Assets)
3. Rank all companies separately by EY (descending) and ROC (reverse/descending), sum the two ranks to compute a Combined Score, and output the top-ranked value stocks.

---

### 🛠️ Required Tools & Capabilities
Implement the following custom function tools in `app/tools.py`:
1. `get_top_magic_formula_stocks(limit: int = 10)`:
   - Queries a Google Cloud Firestore `stocks` collection containing company financial metrics (ebit_cr, enterprise_value_cr, net_working_capital_cr, net_fixed_assets_cr, ticker, company_name, sector).
   - Computes EY %, ROC %, EY rank, ROC rank, and combined rank.
   - Returns a structured JSON list of the top stocks.

2. `get_stock_financials(ticker: str)` & `save_stock_financials(...)`:
   - Firestore CRUD tools to fetch and update individual company metrics.

3. `export_screener_to_csv(limit: int = 10)`:
   - Formats top stocks into CSV bytes and uploads directly to a Google Cloud Storage bucket (`gs://<your-bucket-name>`).
   - Sets public read permissions and returns a direct `https://storage.googleapis.com/...` download link.

4. `get_currency_exchange_rate(base_currency: str = "USD", target_currency: str = "INR")`:
   - Fetches live foreign exchange conversion rates using an open currency API endpoint (`https://open.er-api.com/v6/latest/USD`).

5. `generate_stock_chart_image(prompt: str)`:
   - Generates stock chart infographics using Vertex AI Imagen/Gemini model (`gemini-3.1-flash-lite-image` in `global` location).
   - Saves the artifact via `tool_context.save_artifact()` and uploads PNG bytes to Google Cloud Storage, returning a public image URL.

6. **Sandbox Python Code Execution**:
   - Attach `AgentEngineSandboxCodeExecutor` via a dedicated sub-agent `CodeExecutionAgent` wrapped in `AgentTool` to perform compound interest, financial modeling, and ratio calculations safely in an Agent Engine sandbox.

7. **Cross-Session Memory Bank**:
   - Add `PreloadMemoryTool()` to `root_agent.tools` and register `after_agent_callback=generate_memories_callback`.
   - Configure process-wide `VertexAiMemoryBankService` in `app/app_utils/services.py` so user preferences and risk tolerances persist across sessions.

8. **A2UI Rich Card Rendering (v0.8)**:
   - Generate system prompt using `A2uiSchemaManager(version="0.8", catalogs=[BasicCatalog.get_config("0.8")])`.
   - Wrap output with `after_model_callback=a2ui_callback` (`a2ui_utils.py`) to render interactive stock cards in `adk web`.

---

### 📦 Database Seeding Script
Create a `seed_firestore.py` script to populate Firestore with sample Nifty 100 stock records (e.g., TCS, INFY, HDFCBANK, ITC, RELIANCE, COALINDIA, BAJAJ-AUTO, BHARTIARTL).

---

### 🚀 Execution & Deployment Instructions
1. Include setup commands in `README.md` for running locally:
   `uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<MEMORY_BANK_ID>`
2. Deploy to Vertex AI Agent Runtime:
   `agents-cli deploy --service-name my-agent --no-confirm-project --update-env-vars "MEMORY_SERVICE_URI=agentengine://<MEMORY_BANK_ID>"`
3. Include `gcloud` commands to grant the agent's service account `roles/datastore.user` (Firestore) and `roles/storage.objectAdmin` (GCS bucket).
```
