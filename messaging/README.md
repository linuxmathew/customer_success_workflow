# 📩 Messaging Agent (Email Only)

The **Messaging Agent** handles all **email-based communication** triggered by the Monitoring Agent.  
It sends reminder and check-in emails to users who have been inactive for **3 or 7 days**.  
This agent ensures customers receive timely, personalized guidance that encourages re-engagement with the platform.

---

## 🚀 Overview

This agent:

- Receives **structured user activity data**
- Sends the appropriate email based on **inactivity thresholds**
- Does **not** decide when to send an email — the Monitoring Agent handles that logic
- Can run **sequentially** or **in parallel**, depending on the workflow design

---

## 🧠 Responsibilities

| Task                          | Description                                                      |
| ----------------------------- | ---------------------------------------------------------------- |
| **3-day inactivity reminder** | Sends a friendly re-engagement email.                            |
| **7-day inactivity check-in** | Sends a helpful “Do you need assistance?” email.                 |
| **Email personalization**     | Uses recipient name, last login date, and other contextual data. |
| **Clean structured response** | Returns metadata detailing what was sent.                        |
| **Logging hooks**             | Supports external logging by the Supervisor Agent.               |

## 🔗 Input Format

The Messaging Agent receives a user object:

```
{
  "email": "alice@example.com",
  "days_inactive": 7,
  "client_id": "C123",
  "status": "notify"
}
```

Or a list of such items when batched.

The Monitoring Agent ensures only users needing emails reach this agent.

## 🔄 Output Format

The agent replies with a structured summary of the email action:

```
{
  "email": "alice@example.com",
  "message_type": "7_day_check_in",
  "status": "sent",
  "timestamp": "2025-11-25T11:12:54Z"
}
```

## 📨 Messaging Logic (Email Only)

3-Day Inactivity — Friendly Reminder Email

Example:

```text

Subject: We Miss You at Acme Platform

Hi Alice,
We noticed you haven’t logged in for a few days.
Is there anything we can help you find or set up?
```

7-Day Inactivity — Check-In Email

Example:

```text
Subject: Need Assistance with Acme Platform?

Hi Alice,
It looks like you haven’t logged in for a week.
If you're experiencing any difficulty, feel free to reply — we're happy to help!
```

## 🧩 Workflow Within the Multi-Agent System

1. Monitoring Agent flags user with days_inactive = 3 or 7.

2. Supervisor routes the data to the Messaging Agent.

3. Messaging Agent composes a personalized email.

4. Messaging Agent sends email via the email tool (MCP tool, SMTP tool, or custom tool).

5. Agent returns a structured “email sent” log.

6. Supervisor logs activity and proceeds with workflow.

## ⚙️ Technical Architecture

| Component              | Role                                                                  |
| ---------------------- | --------------------------------------------------------------------- |
| **LLM Behavior**       | Drafts email content and merges personalization variables.            |
| **Email Sending Tool** | Sends the actual email (via SMTP, MCP email tool, or REST email API). |
| **Supervisor Agent**   | Receives success/error logs for observability.                        |
| **Monitoring Agent**   | Triggers the Messaging Agent based on inactivity rules.               |

## 📁 Folder Structure Example

```markdown
customer_success_workflow/
--messaging/
----messaging_agent.py
----README.md
```

## 🛠 Implementation Notes

- Only email delivery is supported (SMS, push, in-app can be added later).

- The agent should:

  - Accept batches or single user items.

  - Use an email tool for actual message delivery.

  - Return structured JSON only (no free-text).

- The agent’s system prompt should enforce:

  - No side effects outside messaging.

  - Clear message classification (3-day vs 7-day).

  - Deterministic responses for downstream agents
