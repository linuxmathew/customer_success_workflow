
# 🧠 Multi-Agent Customer Engagement Automation System

<img width="1185" height="642" alt="image" src="https://github.com/user-attachments/assets/04c42631-c62a-46ac-b883-94a72c6619a6" />

A fully modular, autonomous 5-agent system designed to monitor user activity, send targeted communication, escalate at-risk accounts, and provide full workflow observability.
Each agent is isolated in its own folder with clear responsibilities, allowing the system to scale, evolve, and adapt with minimal coupling.

This project implements a structured, deterministic, and production-oriented approach to customer engagement automation.

## 🚀 High-Level Purpose

The system continuously evaluates user activity and automatically performs the correct follow-up action:

- Send 3-day friendly reminders

- Send 7-day check-in emails

- Trigger 14-day+ escalation workflows

- Create internal CS tasks for high-risk users

- Provide logging and supervisory oversight

It achieves this through a chain of specialized agents that pass structured JSON to one another.

## 🏗️ Architecture Overview

The system is composed of five agents, each with strict responsibilities:

Supervisor Agent → Data Agent → Monitoring Agent → (Messaging Agent OR Escalation Agent)

### 🔷 1. Supervisor Agent (Observability & Oversight)

Role:
The agent pipeline starts here. ie. triggering the overall customer success workflow, which could happen, say, once every 24 hours triggers the supervisor agent, then:
Supervisor Agent → Data Agent → Monitoring Agent → (Messaging Agent OR Escalation Agent)


### 🔷 2. Data Agent (Input Normalization)

Role:
Fetches, cleans, and normalizes raw user login data into a consistent JSON structure.

Outputs:

email

client_id

last_login

days_inactive

status (e.g., active, at_risk)

### 🔷 3. Monitoring Agent (Decision Maker)

Role:
Acts as the brain of the system.
It interprets user inactivity and routes each user to the appropriate downstream agent.

Responsibilities:

Classify inactivity into: Active, Warning, At-Risk, Escalate

Recompute or verify days_inactive

Decide whether the next action is:

No action

3-day reminder

7-day check-in

14-day escalation

Produce structured next_step and handoff_agent instructions

Example Output:
{
  "email": "jane@example.com",
  "days_inactive": 7,
  "next_step": "send_help_message",
  "handoff_agent": "messaging_agent"
}

### 🔷 4. Messaging Agent (3-Day & 7-Day Email Delivery)

Role:
Handles all email-based outreach for 3-day and 7-day inactivity.

Behaviors:

Compose personalized reminder emails

Send them  to the user using [brevo](https://app.brevo.com/)'s [api](https://developers.brevo.com/docs/send-a-transactional-email) 

### 🔷 5. Escalation Agent (14-Day+ CS Workflows)

Role:
Handles long-duration inactivity (14+ days) and generates internal Customer Success tasks.

Responsibilities:


Assign risk level (low, medium, high)

Create internal escalation tickets. These are added to an internal trello board



## Workflow Summary

A typical full cycle looks like:

Data Agent normalizes raw login data.

Monitoring Agent evaluates inactivity and determines the next action.

If 3 or 7 days inactive → Messaging Agent sends the appropriate email.

If 14+ days inactive → Escalation Agent creates CS tasks.

All results are logged
