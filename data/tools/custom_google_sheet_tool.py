from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from google.adk.tools import tool
import os


# === Environment & Credentials ===
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GOOGLE_PROJECT_ID or not GOOGLE_APPLICATION_CREDENTIALS:
    raise ValueError("Missing required Google credentials in .env")


# === Custom Google Sheets Batch Get Function ===
@tool
def batch_get_values(spreadsheet_id: str, ranges: list[str]) -> dict:
    """
    Fetches values from Google Sheets using batchGet API.

    Args:
        spreadsheet_id (str): The ID of the spreadsheet.
        ranges (list[str]): List of A1 notation ranges (e.g., ["Sheet1!A1:Z"]).

    Returns:
        dict: {"values": [[...]]} or {"error": "message"} on failure.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        service = build("sheets", "v4", credentials=credentials)

        result = (
            service.spreadsheets()
            .values()
            .batchGet(spreadsheetId=spreadsheet_id, ranges=ranges)
            .execute()
        )

        return {"values": result.get("valueRanges", [{}])[0].get("values", [])}
    except HttpError as e:
        return {"error": f"API error: {e.content.decode('utf-8')}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
