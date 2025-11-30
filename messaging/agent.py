# File: customer_success_workflow/messaging/messaging_agent.py
import os
import json
from datetime import datetime, timezone
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Any, Optional

from google.adk.agents.llm_agent import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from dotenv import load_dotenv
import os
import requests

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
if BREVO_API_KEY is None:
    print(
        "Error: Missing Required environment variable in ./messaging/.env:\n"
        "BREVO_API_KEY"
    )
    exit()

retry_config = types.HttpRetryOptions(
    attempts=4, exp_base=2, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)


# sending email using brevo
def send_email(email: str, username: str, subject: str, message: str) -> dict:
    """
    This send email tool is used to send customers email messages
    parameters:
        email: the users email address.
        username: the user's username
        subject: the email's subject
        message: the email's message body
    Returns: A dictionary as follows.
        { status_code:<http status code> }
        since the email is being sent via an smtp provider's api, use the http status code to understand whether the email sending was successful and respond to the user appropriately
    """
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    data = {
        "sender": {"name": "Based incorporated", "email": "kiokopeterkinash@gmail.com"},
        "to": [{"email": email, "name": username}],
        "subject": subject,
        "htmlContent": f"<html><head></head><body><p>Hello,</p>{message}</p></body></html>",
    }

    response = requests.post(url, headers=headers, json=data)
    return {"status_code": response.status_code}


messaging_agent = Agent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="messaging_agent",
    description="Email Reminder agent",
    instruction="You are an email reminder agent. Your job is to send our customers an email based on the number of days they have been away from our very awesome app. if the user has been away for three days, send them a soft email gently requesting their return. It's subject must be 'Gentle three day reminder' If the user has been away for seven days, send them a more serious email. It's subject must be 'been a week yoh, what up\n'. Use the send email tool to send the emails. Otherwise, please alert the user that there's nothing to be done for the customer",
    tools=[send_email],
)


root_agent = messaging_agent
