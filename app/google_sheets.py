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

    def get_all_items(self) -> list[dict]:
        """Get all rows from ITEMS sheet. Returns list of dicts with row data."""
        result = self.get_items_sheet().execute()
        rows = result.get("values", [])
        
        items = []
        for idx, row in enumerate(rows):
            if len(row) > 10:
                item = {
                    "row_index": idx + 1,
                    "inventory_id": row[10] if len(row) > 10 else "",
                    "checkbox_t": row[19].upper() == "TRUE" if len(row) > 19 and row[19] else False,
                    "data": {
                        "A": row[0] if len(row) > 0 else "",
                        "B": row[1] if len(row) > 1 else "",
                        "C": row[2] if len(row) > 2 else "",
                        "D": row[3] if len(row) > 3 else "",
                        "E": row[4] if len(row) > 4 else "",
                        "F": row[5] if len(row) > 5 else "",
                        "G": row[6] if len(row) > 6 else "",
                        "H": row[7] if len(row) > 7 else "",
                        "I": row[8] if len(row) > 8 else "",
                        "J": row[9] if len(row) > 9 else "",
                        "K": row[10] if len(row) > 10 else "",
                        "L": row[11] if len(row) > 11 else "",
                        "M": row[12] if len(row) > 12 else "",
                        "N": row[13] if len(row) > 13 else "",
                        "O": row[14] if len(row) > 14 else "",
                        "P": row[15] if len(row) > 15 else "",
                        "Q": row[16] if len(row) > 16 else "",
                        "R": row[17] if len(row) > 17 else "",
                        "S": row[18] if len(row) > 18 else "",
                        "T": row[19] if len(row) > 19 else "",
                        "U": row[20] if len(row) > 20 else "",
                        "V": row[21] if len(row) > 21 else "",
                        "W": row[22] if len(row) > 22 else "",
                        "X": row[23] if len(row) > 23 else "",
                    }
                }
                items.append(item)
        return items

    def find_item_by_inventory_id(self, inventory_id: str) -> dict | None:
        """Find item by inventory_id in column K. Returns item dict or None."""
        items = self.get_all_items()
        for item in items:
            if str(item["inventory_id"]).strip() == str(inventory_id).strip():
                return item
        return None

    def update_checkbox(self, row_index: int, value: bool) -> bool:
        """Update column T (checkbox) for given row. Returns success status."""
        range_notation = f"{SHEET_NAME}!T{row_index}"
        body = {"values": [[value]]}
        
        self._sheets.values().update(
            spreadsheetId=self._spreadsheet_id,
            range=range_notation,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        
        return True


sheets_client: GoogleSheetsClient | None = None


def get_sheets_client() -> GoogleSheetsClient:
    """Get or create singleton GoogleSheetsClient instance."""
    global sheets_client
    if sheets_client is None:
        sheets_client = GoogleSheetsClient()
    return sheets_client
