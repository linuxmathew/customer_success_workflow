# 🚨 Escalation Agent

**Handles 14+ Day User Inactivity — Customer Success Automation**

The **Escalation Agent** detects long-term user inactivity and automatically generates customer success alerts, tasks, and internal tickets. It is triggered when a user remains inactive for **14 days or more**, as reported by the Monitoring Agent.

---

## 🎯 Purpose

This agent ensures that _at-risk users_ are surfaced early to the Customer Success Team, reducing chances of churn. It automates internal workflows by generating structured escalation tasks and notifying the Supervisor Agent.

---

## 🧠 Responsibilities

### 1. Validate Escalation Input

The agent receives structured data containing:

- `email`
- `client_id`
- `days_inactive`
- `reason`

It verifies that:  
**`days_inactive >= 14`**

---

### 2. Generate Risk Assessment

The agent classifies the user’s risk level:

- **High Risk:** 30+ days inactive
- **Medium Risk:** 21–29 days inactive
- **Low Risk:** 14–20 days inactive

---

### 3. Create Internal CS Ticket

The agent simulates creation of a Customer Success task, including:

- **Ticket ID**
- **Assignment**
- **Summary of issue**
- **Recommended next step**

---

### 4. Notify Supervisor Agent

It prepares a structured notification packet containing:

- User data
- Risk level
- Ticket information
- Recommended next action

This supports full observability and workflow tracking.

---

## 📥 Input Format

```json
{
  "email": "bob@example.com",
  "client_id": "C456",
  "days_inactive": 55,
  "reason": "14+ days inactivity — escalate"
}
```

## 📤 Output Format

```json
{
  "action": "escalation_created",
  "ticket_id": "T-2025-9921",
  "risk_level": "high",
  "assigned_to": "customer_success_team",
  "notes": "User has been inactive for 55 days. Requires manual follow-up.",
  "notify_supervisor": true
}
```

## ⚙️ Agent Type

Sequential Agent — processes one escalation case at a time to ensure accurate internal ticketing and logging.
