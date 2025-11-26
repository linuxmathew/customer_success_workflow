# 📊 Data Agent

### Part of the 5-Agent Customer Engagement Automation System

The **Data Agent** is responsible for retrieving, validating, and transforming user activity data from an external spreadsheet (such as Google Sheets). It acts as the foundational agent that supplies clean, structured, and reliable data to the rest of the system — including the Monitoring, Messaging, Escalation, and Supervision Agents.

This agent does **not** persist data locally. Instead, it performs a fresh fetch-and-prepare operation on every request to ensure real-time accuracy.

---

## 🚀 Purpose

The Data Agent provides the entire system with standardized, query-ready user activity information. It serves as the single source of truth for:

- User login timestamps
- Client IDs
- Emails
- Days since last login
- User engagement categorization (Active / Warning / At-risk)

All other agents rely on this one for accurate and timely data.

---

## 🧠 Responsibilities

### ✔️ 1. Connect to Spreadsheet Data Source

- Uses an MCP or OpenAPI tool connected to Google Sheets (or any spreadsheet platform).
- Retrieves the full dataset or specific rows on demand.

---

### ✔️ 2. Validate and Clean Data

Ensures incoming data includes required fields:

| Field      | Required | Description         |
| ---------- | -------- | ------------------- |
| email      | Yes      | Identifies the user |
| last_login | Yes      | ISO timestamp       |
| client_id  | Yes      | Internal system ID  |

Invalid timestamps, missing fields, or empty rows are cleaned or flagged.

---

### ✔️ 3. Compute Days Since Last Login

Automatically calculates:
days_inactive = NOW - last_login

This value is used by Monitoring and Messaging Agents.

---

### ✔️ 4. Categorize User Activity

Classifies each user based on inactivity:

| Days Inactive | Category            |
| ------------- | ------------------- |
| 0–2           | Active              |
| 3–6           | In Warning Cycle    |
| 7–13          | At-risk             |
| ≥ 14          | Escalation Required |

These categories are used by downstream agents to decide actions.

---

## ✔️ 5. Provide Standardized Output

Example JSON output:

```json
{
  "email": "john@example.com",
  "client_id": "C001",
  "last_login": "2025-01-13T10:32:00Z",
  "days_inactive": 7,
  "status": "at_risk"
}
```

Delivered using A2A-style agent communication.

🔌 Tools Used

This agent may leverage:

MCP Google Sheets connector

Custom fetch-and-parse tools

Built-in code execution for data formatting

A2A message passing

It remains simple, stateless, and reliable by not storing any persistent data.

🔄 Workflow Overview

```
Spreadsheet → Data Agent → Standardized JSON → Other Agents
```

Request from another agent:

“Get all user activity records.”

Output

A cleaned, computed, and categorized user list.

Example Response:

```json
{
  "users": [
    {
      "email": "ada@example.com",
      "client_id": "CL-09",
      "last_login": "2025-01-18T19:02:00Z",
      "days_inactive": 3,
      "status": "warning"
    }
  ]
}
```
