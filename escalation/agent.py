from google.adk.agents.llm_agent import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.google_llm import Gemini
from google.adk.tools.function_tool import FunctionTool
from google.genai import types
import requests
import os

from dotenv import load_dotenv

load_dotenv()


LIST_ID = os.getenv("LIST_ID")
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")

print("LIST_ID =", LIST_ID)


def create_trello_ticket(title: str, description: str) -> str:
    """
    Creates a Trello ticket in the given list.
    """
    url = "https://api.trello.com/1/cards"
    params = {
        "idList": LIST_ID,
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "name": title,
        "desc": description,
    }

    r = requests.post(url, params=params, timeout=10)
    try:
        data = r.json()
        card_id = data.get("id")
        card_url = data.get("url")
        return f"Created Trello card: {card_id} — {card_url}"
    except Exception:
        return f"Error: {r.status_code} — {r.text}"


create_ticket_tool = FunctionTool(create_trello_ticket)


retry_config = types.HttpRetryOptions(
    attempts=6, exp_base=2, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)


class SafeAgent(LlmAgent):
    async def run_async(self, invocation_context):
        async for event in super().run_async(invocation_context):
            # This single line fixes the NoneType crash forever
            if getattr(event, "content", None) and event.content.parts is None:
                event.content.parts = []
            yield event


escalation_agent = SafeAgent(
    name="escalation_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    tools=[create_ticket_tool],
    instruction="""
    You are the Escalation Agent.
    
    INPUT FORMAT YOU WILL ALWAYS RECEIVE:
    {
        "email": "string",
        "client_id": "string",
        "days_inactive": number,
        "reason": "escalate_14_plus"
    }

    YOUR TASK:
    - Create a Trello escalation ticket using the tool: create_trello_ticket
    with EXACTLY two JSON fields:
    {
    "title": "...",
    "description": "..."
    }

    - title MUST be a short line like: "🚨 Inactive user: <email>"
    - description MUST contain:
    - email
    - client_id
    - days_inactive
    - reason

    DO NOT include extra fields.
    DO NOT put JSON inside markdown.

    If days_inactive >= 14, you MUST call the tool.
    Respond ONLY with a tool call.
    """,
)

root_agent = escalation_agent
