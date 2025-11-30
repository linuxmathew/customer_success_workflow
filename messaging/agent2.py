from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from email_tool import BrevoEmailTool

retry_config = types.HttpRetryOptions(
    attempts=6, exp_base=2, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)


root_agent = Agent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="messaging_agent",
    description="An email generator and dispatch agent",
    instruction="""You are a email generation and sending agent. Your job is to compose a nice email based on the user information you got. If the reason in the user data reads, "3_days_reminder", compose a nice and wonderful email to the user ex""",
    tools=[BrevoEmailTool],
)
