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

# Retry config for model/tool calls (keeps parity with other agents)
retry_config = types.HttpRetryOptions(
    attempts=4, exp_base=2, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)


# ---------- Email sending helper (SMTP by default) ----------
def send_email_smtp(
    to_email: str, subject: str, body: str, from_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an email using SMTP. Returns a result dict with status, message_id, error.
    Configure SMTP via env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM_ADDRESS
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = from_address or os.getenv("SMTP_FROM_ADDRESS")

    result = {
        "status": "failed",
        "provider": "smtp",
        "message_id": None,
        "error": None,
    }

    if not smtp_host or not smtp_from:
        result["error"] = "SMTP_HOST or SMTP_FROM_ADDRESS not configured"
        return result

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    try:
        # Use STARTTLS
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
            smtp.ehlo()
            if smtp_port in (587, 25):
                smtp.starttls()
                smtp.ehlo()
            if smtp_user and smtp_pass:
                smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        result["status"] = "sent"
        # SMTP doesn't always return message-id; we set one for traceability
        result["message_id"] = (
            f"smtp-{int(datetime.now(timezone.utc).timestamp()*1000)}"
        )
    except Exception as e:
        result["error"] = str(e)

    return result


# ---------- Email templates ----------
TEMPLATES = {
    "3_day_reminder": {
        "subject": "We miss you — quick check-in from Acme Platform",
        "body": lambda name, last_login: (
            f"Hi {name or ''},\n\n"
            "We noticed you haven't logged in for a few days. "
            "If there's anything you need or if you want a quick walkthrough, reply to this email and we'll help.\n\n"
            "Best,\nThe Acme Support Team"
        ),
    },
    "7_day_check_in": {
        "subject": "Need help with Acme Platform?",
        "body": lambda name, last_login: (
            f"Hi {name or ''},\n\n"
            "It looks like you haven't logged in for a week. "
            "If you're having trouble finding something or need assistance, please reply and we'll schedule a quick call.\n\n"
            "Warmly,\nThe Acme Support Team"
        ),
    },
}

# ---------- Agent instruction ----------
instruction = """
You are the Messaging Agent (email-only). You receive a single user JSON or a list of user JSONs.
Each user object has the following fields:
  - email (string) -- required
  - client_id (string) -- required
  - reason (string) -- expected values: "3_day_reminder" or "7_day_check_in"
  - last_login (string, optional) -- 'YYYY-MM-DD'

Your job:
  1. Validate input.
  2. For each user, choose the correct email template based on `reason`.
  3. Send the email using the configured email provider (SMTP by default).
  4. Return a JSON array of results for each user with keys:
     email, client_id, reason, status, provider, message_id, error, timestamp

Important rules:
  - Do NOT perform any other side effects (no CRM writes).
  - Always return structured JSON; do not return freeform prose.
  - If input is invalid for a user, include a result with status "failed" and error describing the problem.
"""

# ---------- Build the Agent ----------
messaging_agent = Agent(
    name="messaging_agent",
    description="Sends email reminders for 3-day and 7-day inactivity reasons (email-only).",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    tools=[],  # uses internal helper for SMTP; if you use external tools, add them here
    instruction=instruction,
)


# ---------- Helper function to process a single user ----------
def process_user_send_email(user: Dict[str, Any]) -> Dict[str, Any]:
    # Basic validation
    email = user.get("email")
    client_id = user.get("client_id")
    reason = user.get("reason")
    last_login = user.get("last_login")
    name = user.get("name") or None  # optional personalization

    base_result = {
        "email": email,
        "client_id": client_id,
        "reason": reason,
        "status": "failed",
        "provider": "smtp",
        "message_id": None,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if not email or not client_id or not reason:
        base_result["error"] = "Missing required field: email, client_id, or reason"
        return base_result

    if reason not in ("3_day_reminder", "7_day_check_in"):
        base_result["error"] = f"Unsupported reason: {reason}"
        return base_result

    template = TEMPLATES.get(reason)
    subject = template["subject"]
    body = template["body"](name, last_login)

    # Send email via SMTP (provider function)
    send_result = send_email_smtp(to_email=email, subject=subject, body=body)
    base_result["status"] = send_result.get("status", "failed")
    base_result["message_id"] = send_result.get("message_id")
    base_result["error"] = send_result.get("error")
    base_result["provider"] = send_result.get("provider")
    base_result["timestamp"] = datetime.now(timezone.utc).isoformat()
    return base_result


# ---------- Agent run wrapper ----------
# We override the agent.run() behavior by exposing a helper that will be used by other agents
def run_messaging_agent(payload: Any) -> str:
    """
    payload can be:
      - a single user dict
      - a list of user dicts
      - or a dict: { "users": [...] }
    Returns a JSON string (list of result dicts) — suitable as an agent response body.
    """
    # normalize input into list
    users = []
    if isinstance(payload, dict) and "users" in payload:
        users = payload["users"]
    elif isinstance(payload, dict):
        users = [payload]
    elif isinstance(payload, list):
        users = payload
    else:
        # invalid payload
        err = [
            {
                "email": None,
                "client_id": None,
                "reason": None,
                "status": "failed",
                "provider": "smtp",
                "message_id": None,
                "error": "Invalid payload type",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
        return json.dumps(err)

    results: List[Dict[str, Any]] = []
    for u in users:
        try:
            res = process_user_send_email(u)
        except Exception as exc:
            res = {
                "email": u.get("email"),
                "client_id": u.get("client_id"),
                "reason": u.get("reason"),
                "status": "failed",
                "provider": "smtp",
                "message_id": None,
                "error": f"Unhandled exception: {str(exc)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        results.append(res)

    return json.dumps(results)


# Expose the runnable function as an attribute so AgentTool.from_agent(...) can wrap this module
# (When using AgentTool.from_agent you import the agent object; for programmatic invocation you can call run_messaging_agent)
messaging_agent.run_messaging_agent = run_messaging_agent

# If executed directly, allow a quick local test (not used in production)
if __name__ == "__main__":
    # Example single-user test payload
    test_payload = {
        "email": os.getenv("TEST_TO_EMAIL", "user@example.com"),
        "client_id": "TEST-1",
        "reason": "3_day_reminder",
        "last_login": "2025-11-23",
        "name": "Test User",
    }
    print(run_messaging_agent(test_payload))
