from google.adk.agents.llm_agent import Agent, LlmAgent
from google.adk.agents import SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path
import os

load_dotenv()


# === Environment & Credentials ===
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GOOGLE_PROJECT_ID or not GOOGLE_APPLICATION_CREDENTIALS:
    raise ValueError("Missing required Google credentials in .env")
# FLOW
# fetch_data_agent - cleaning_agent -> compute_agent

retry_config = types.HttpRetryOptions(
    attempts=6, exp_base=2, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)

# Due to unavailabilty of a working google-sheet mcp server. A custom tool was used
# === Custom Tool ===
CREDENTIALS_PATH = Path(__file__).parent / "service_credentials.json"


def batch_get_values(spreadsheet_id: str, ranges: list[str]) -> dict:
    """Fetch data from Google Sheets."""
    if not CREDENTIALS_PATH.exists():
        return {"error": "Service account JSON not found at " + str(CREDENTIALS_PATH)}

    creds = service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=creds)
    result = (
        service.spreadsheets()
        .values()
        .batchGet(spreadsheetId=spreadsheet_id, ranges=ranges)
        .execute()
    )
    values = result.get("valueRanges", [{}])[0].get("values", [])
    return {"values": values}


# Wrap as ADK FunctionTool (auto-generates schema)
# sheets_tool = FunctionTool.from_function(
#     batch_get_values,
#     description="Fetches tabular data from Google Sheets. Provide spreadsheet_id and a list of ranges (e.g., ['Sheet1!A1:Z']). Returns a 2D array of values.",
# )

# agent that fetches google spreadsheet data with mcp
data_fetching_agent = LlmAgent(
    name="data_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    output_key="raw_user_data",
    tools=[batch_get_values],
    instruction=""" 
    You are a precise data retrieval agent. Your only job is to fetch tabular data from the connected Google Spreadsheet.
    
    Rules:
    - Use the `sheets_batch_get_values` tool.
    - Always include the header row in your range (e.g., "Sheet1!A1:Z").
    - If the user doesn't specify a range, ask once for the exact range (e.g., spreadsheet ID + sheet name + range).
    - Convert the 2D array result into a clean list of dictionaries:
    - First row → keys
    - Subsequent rows → values
    - If no header row exists, use column letters (A, B, C...) as keys.

    Output exactly this JSON (no markdown, no extra text):
    [
    {"Name": "Alice", "Email": "alice@example.com", "Last Login": "2025-11-20", ...},
    ...
    ]

    On tool error, return: {"error": "Brief error message"}
    """,
)
# fetch all user data from sheet ID 1el7ibH0P1aNV9djhA3F5eLbfbSNcYoGQkzzldmKjZbA from 'Sheet1!A1:Z'

#  data cleaning agent - takes the output of fetch_data_agent and clean it
cleaning_agent = LlmAgent(
    name="data_cleaning_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    output_key="cleaned_user_data",
    instruction="""
    You are a strict data cleaning agent.

    Input data: {raw_user_data}

    Required fields (case-insensitive, extra whitespace allowed):
    - email
    - last_login (or lastLogin, LastLogin, etc.)
    - client_id (or clientId, ClientID)

    Tasks:
    1. Normalize field names: convert to lowercase with underscores (e.g., "Last Login" → "last_login")
    2. For each record, check if ALL three required fields exist and are non-empty strings.
    3. Remove any record missing or having empty values in any required field.
    4. Return ONLY the filtered list of valid records as clean JSON.

    If no records remain valid, return exactly: []

    Example valid output:
    [
    {"email": "alice@example.com", "last_login": "2025-11-20", "client_id": "C123"},
    {"email": "bob@example.com",   "last_login": "2025-10-15", "client_id": "C456"}
    ]
    """,
)

# compute data agent
compute_agent = Agent(
    name="data_computing_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    output_key="user_data",
    instruction="""
        You are a data enrichment agent. Current date is 2025-11-25.

        Input: {cleaned_user_data}

        For each user:
        1. Parse `last_login` as an ISO date (YYYY-MM-DD).
        2. Compute days_inactive = (today - last_login_date).days  → integer
        3. Add key: "days_inactive"
        4. Add key: "status" based on days_inactive:
        - 0–2 days    → "active"
        - 3–6 days    → "warning"
        - 7–13 days   → "at-risk"
        - ≥14 days    → "escalate"

        Return the enriched list exactly as JSON. No explanations.

        Example output:
        [
        {
            "email": "alice@example.com",
            "last_login": "2025-11-24",
            "client_id": "C123",
            "days_inactive": 1,
            "status": "active"
        },
        {
            "email": "bob@example.com",
            "last_login": "2025-10-01",
            "client_id": "C456",
            "days_inactive": 55,
            "status": "escalate"
        }
        ]
        """,
)

pipeline = SequentialAgent(
    name="data_agent",
    sub_agents=[data_fetching_agent, cleaning_agent, compute_agent],
)

root_agent = pipeline
