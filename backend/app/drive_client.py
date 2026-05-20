import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Drive API scope (read-only access)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Local path to service account credentials (used during development)
SERVICE_ACCOUNT_FILE = (
    Path(__file__).resolve().parent.parent
    / "credentials"
    / "service-account.json"
)


def get_drive_service():
    """
    Authenticate and return a Google Drive API client.

    Credential loading strategy:
    1. If GOOGLE_SERVICE_ACCOUNT_JSON is set (e.g. on Railway),
       load credentials from the environment variable.
    2. Otherwise, load credentials from the local
       credentials/service-account.json file.
    """
    # Try to load credentials from environment variable
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        # Railway / production deployment path
        credentials_info = json.loads(service_account_json)

        credentials = (
            service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=SCOPES,
            )
        )
    else:
        # Local development path
        credentials = (
            service_account.Credentials.from_service_account_file(
                str(SERVICE_ACCOUNT_FILE),
                scopes=SCOPES,
            )
        )

    # Build Google Drive API client
    service = build("drive", "v3", credentials=credentials)
    return service


def search_files(query: str, page_size: int = 20):
    """
    Search Google Drive using a Google Drive query string.

    Example query:
        "name contains 'invoice'"

    Returns:
        List of file dictionaries containing:
        - id
        - name
        - mimeType
        - webViewLink
        - modifiedTime
    """
    service = get_drive_service()

    results = (
        service.files()
        .list(
            q=query,
            pageSize=page_size,
            fields="files(id, name, mimeType, webViewLink, modifiedTime)",
        )
        .execute()
    )

    return results.get("files", [])