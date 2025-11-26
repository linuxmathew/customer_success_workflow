from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
import os

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# initiate a connection with google spreadsheet and fetch sheet data
# MCP integration with Google Sheets server
# use - https://github.com/freema/mcp-gsheets
mcp_sheets_server = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "mcp-gsheets@latest"],
            env={
                "GOOGLE_PROJECT_ID": GOOGLE_PROJECT_ID,
                "GOOGLE_APPLICATION_CREDENTIALS": os.path.abspath(
                    GOOGLE_APPLICATION_CREDENTIALS
                ),
                # Critical: Only load the one tool we need
                # "MCP_GSHEETS_TOOLS": "sheets_batch_get_values",
            },
            tool_filter=["sheets_batch_get_values"],  # only expose relevant tools
        ),
        timeout=120,
    )
)
