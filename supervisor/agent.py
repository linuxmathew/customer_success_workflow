from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.agents import SequentialAgent
from data.agent import root_agent as data_manager
from monitoring.agent import root_agent as monitoring_manager


retry_config = types.HttpRetryOptions(
    attempts=6, exp_base=2, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)


supervisor_agent = SequentialAgent(
    name="supervisor_agent", sub_agents=[data_manager, monitoring_manager]
)

root_agent = supervisor_agent
