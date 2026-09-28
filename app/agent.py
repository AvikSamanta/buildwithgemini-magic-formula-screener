# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

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
MEMORY_BANK_ID = "8738801869331103744"
GCP_PROJECT_ID = "qwiklabs-gcp-02-8acb2ff2c23a"
GCP_LOCATION = "us-east1"

# Build system instruction using A2uiSchemaManager v0.8 and BasicCatalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert investment assistant specializing in Joel Greenblatt's Magic Formula strategy "
        "for the Indian stock market (Nifty 100). "
        "You remember the user's stated preferences, investment goals, risk tolerance, and favorite stocks from previous conversations."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate when displaying stock metrics, ranks, financials, exchange rates, or recommendations.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

# Read Agent Engine resource name from deployment_metadata.json if present
metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_resource_name = None
if metadata_file.exists():
    try:
        meta = json.loads(metadata_file.read_text())
        agent_engine_resource_name = meta.get("remote_agent_runtime_id")
    except Exception:
        pass

# Create Agent Engine Sandbox Code Executor
code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)

# Sub-agent dedicated to code execution using the Agent Engine sandbox
code_execution_agent = Agent(
    name="CodeExecutionAgent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a specialized Python code execution agent. "
        "Write and execute Python code in your Agent Engine sandbox to solve math problems, "
        "perform financial calculations, analyze stock ratios, and process datasets."
    ),
    code_executor=code_executor,
)


# WRITE: Callback to send session events to Memory Bank for extraction after each turn
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    # Keep in sync with agents-cli-manifest.yaml: agents-cli derives this name
    # from the project `name:` recorded there, and telemetry reports it as
    # gen_ai.agent.name. Renaming the agent only here makes the two disagree,
    # and anything selecting traces by name stops finding this agent's.
    name="Agent_197115",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
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
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)


app = App(
    root_agent=root_agent,
    name="app",
)









app = App(
    root_agent=root_agent,
    name="app",
)

