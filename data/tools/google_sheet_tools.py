from google.adk.tools import AgentTool
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


class GoogleSheetsTool(AgentTool):
    name = "google_sheets"
    description = "Fetches data from a Google Sheets document"

    def __init__(self, credentials_path, spreadsheet_id):
        super().__init__()
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id

        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        self.client = build("sheets", "v4", credentials=creds)

    async def run(self, context, sheet_name: str):
        """Fetch a sheet by name and return rows as JSON."""
        sheet = self.client.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=self.spreadsheet_id, range=sheet_name)
            .execute()
        )

        values = result.get("values", [])

        return {"sheet": sheet_name, "rows": values}
