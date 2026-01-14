import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "ITEMS"


class GoogleSheetsClient:
    """Google Sheets client for accessing ITEMS sheet only."""

    def __init__(self) -> None:
        """Initialize client using service account from env variable."""
        service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", "")

        if not service_account_path:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON env variable not set")
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID env variable not set")

        self._spreadsheet_id = spreadsheet_id
        self._credentials = Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES
        )
        self._service = build("sheets", "v4", credentials=self._credentials)
        self._sheets = self._service.spreadsheets()

    def get_items_sheet(self):
        """Return reference to ITEMS sheet for read operations."""
        return self._sheets.values().get(
            spreadsheetId=self._spreadsheet_id,
            range=SHEET_NAME
        )


sheets_client: GoogleSheetsClient | None = None


def get_sheets_client() -> GoogleSheetsClient:
    """Get or create singleton GoogleSheetsClient instance."""
    global sheets_client
    if sheets_client is None:
        sheets_client = GoogleSheetsClient()
    return sheets_client
