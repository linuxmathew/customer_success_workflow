from google.adk.agents.llm_agent import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.google_llm import Gemini
from google.adk.tools.function_tool import FunctionTool
from google.genai import types
import requests


def create_trello_ticket(payload):
    card_name = payload.get("title")
    card_desc = payload.get("description")

    url = "https://api.trello.com/1/cards"
    params = {
        "idList": "LIST_ID",
        "key": "TRELLO_API_KEY",
        "token": "TRELLO_TOKEN",
        "name": card_name,
        "desc": card_desc,
    }

    r = requests.post(url, params=params, timeout=10)
    return r.json()


create_ticket_tool = FunctionTool(
    create_trello_ticket,
)


retry_config = types.HttpRetryOptions(
    attempts=6, exp_base=2, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)

escalation_agent = LlmAgent(
    name="escalation_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    tools=[create_ticket_tool],
    # instructions="""
    # When a user is inactive for 14+ days, create a Trello ticket.
    # Use the `create_ticket` tool with a title and description.
    # """,
)

root_agent = escalation_agent
