from google.adk.agents.llm_agent import Agent, LlmAgent
from google.adk.agents import SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.function_tool import FunctionTool
from google.genai import types

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path
import os
from datetime import date

load_dotenv()


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


def get_today() -> str:
    """
    Returns today's date in YYYY-MM-DD format (ISO standard).
    Use this tool whenever you need the current date for calculations.
    """
    return date.today().isoformat()  # → "2025-11-30"


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
instruction_for_later = """
        You are a data enrichment agent.

        CRITICAL RULE: You do NOT know today's date. You MUST call the `get_today` tool first — it is the only way to get the correct current date.

        Step-by-step process (follow exactly):

        1. Call the `get_today` tool with no arguments.
        2. Receive the result (a string like "2025-11-30").
        3. Now process the input data: {cleaned_user_data}
            For each user in the list:
            - Parse `last_login` as YYYY-MM-DD date
            - Compute days_inactive = (today_date - last_login_date).days → integer
            - Add field: "days_inactive"
            - Add field: "status" based on days_inactive:
                    • 0–2 days   → "active"
                    • 3–6 days   → "warning"
                    • 7–13 days  → "at-risk"
                    • ≥14 days   → "escalate"

        Final output: Return ONLY the enriched JSON list. No text, no explanations, no markdown.

        Example:
        [
            {
                "email": "alice@example.com",
                "last_login": "2025-11-29",
                "client_id": "C123",
                "days_inactive": 1,
                "status": "active"
            }
        ]
"""

# compute data agent
compute_agent = LlmAgent(
    name="data_computing_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    output_key="user_data",
    instruction="""
        You are a data enrichment agent.

       

        Step-by-step process (follow exactly):

        1. Using the value 2025-12-01 in the format YYYY-MM-DD as today_date.
        2. Now process the input data: {cleaned_user_data}
            For each user in the list:
            - Parse `last_login` as YYYY-MM-DD date
            - Compute days_inactive = (today_date - last_login_date).days → integer
            - Add field: "days_inactive"
            - Add field: "status" based on days_inactive:
                    • 0–2 days   → "active"
                    • 3–6 days   → "warning"
                    • 7–13 days  → "at-risk"
                    • ≥14 days   → "escalate"

        Final output: Return ONLY the enriched JSON list. No text, no explanations, no markdown.

        Example:
        [
            {
                "email": "alice@example.com",
                "last_login": "2025-11-29",
                "client_id": "C123",
                "days_inactive": 1,
                "status": "active"
            }
        ]
""".strip(),
)

pipeline = SequentialAgent(
    name="data_agent",
    sub_agents=[data_fetching_agent, cleaning_agent, compute_agent],
)

root_agent = pipeline
