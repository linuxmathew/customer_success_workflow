# 🛠️ Global Installation Guide

For the Multi-Agent Customer Engagement Workflow

This document provides the system-wide installation steps required before running any of the agents in the workflow.
Each agent has its own dedicated setup instructions inside its own folder, but the steps below must be completed first.

## 1️⃣ Install Global Dependencies

Your project includes a central requirements.txt file used for shared libraries across all agents (Python-based tools, utilities, or MCP servers).

Run:

```
pip install -r requirements.txt
```

If you are using a virtual environment (recommended):

```
python3 -m venv .venv
source .venv/bin/activate     # macOS / Linux
.venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

## 2️⃣ Ensure Each Agent Has Its .env File

Each agent in the customer_success_workflow/ directory requires its own environment variables to function correctly.

📌 Folder structure example:

```bash
customer_success_workflow/
├── data/
│ ├── .env.example
│ └── .env ← must be created
│ └── agent.py
├── monitoring/
│ ├── .env.example
│ └── .env
│ └── agent.py
├── messaging/
│ ├── .env.example
│ └── .env
│ └── agent.py
├── escalation/
│ ├── .env.example
│ └── .env
│ └── agent.py
└── supervisor/
├── .env.example
└── .env
│ └── agent.py
```

### ✔️ Step Required for Every Agent

For each agent folder:

1. Locate the .env.example file
2. Create a real .env file

```
cp .env.example .env

```

3. Fill in the required keys
   (Spreadsheet IDs, API keys, service credentials paths, agent-specific config, etc.)
   ⚠️ Never commit .env files. Each agent’s .env.example shows only the required keys—not values.

## 3️⃣ Create Required Credential Files (If Applicable)

Some agents (such as the Data Agent) require external authentication files like:

- Google service account credentials

* API JSON tokens

* OAuth tokens

Make sure:

- The file exists (e.g., service_credentials.json)

- The absolute path is correctly referenced inside the .env file of that agent

- The file is added to .gitignore

## 5️⃣ Run Agents Individually or as a Workflow

After all dependencies and .env files are set:

### ▶️ Run a Single Agent

From the project root:

```bash
cd customer_success_workflow
adk run {AGENT_NAME}
```

Example — running the Data Agent:

```bash
adk run data
```

### ▶️ Run the Full Workflow

To start the complete automated pipeline, run the Supervisor Agent:

```bash

adk run supervisor

```
