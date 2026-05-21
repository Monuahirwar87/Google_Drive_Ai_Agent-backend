# backend/app/tools.py
import os
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

# SCOPES setup for read-only access to Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# 🔑 SAFE & DIRECT ENVIRONMENT VARIABLES ACCESS (Render Friendly Setup)
raw_private_key = os.getenv("GOOGLE_PRIVATE_KEY")
formatted_private_key = None

if raw_private_key:
    # Remove literal escaped strings and handle line breaks dynamically
    formatted_private_key = raw_private_key.replace("\\n", "\n")
    # Wrap with standard cryptographic markers if missing in raw string
    if not formatted_private_key.startswith("-----BEGIN PRIVATE KEY-----"):
        formatted_private_key = f"-----BEGIN PRIVATE KEY-----\n{formatted_private_key}\n-----END PRIVATE KEY-----"
else:
    print("CRITICAL WARNING: GOOGLE_PRIVATE_KEY environment variable is missing!")

# Master layouts structure for Google Service Account info dictionary
SERVICE_ACCOUNT_INFO = {
    "type": os.getenv("GOOGLE_TYPE", "service_account"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": formatted_private_key,
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN", "googleapis.com")
}


def get_google_creds():
    """
    Dynamically yields credentials avoiding initialization freeze frames or stale states.
    """
    try:
        if formatted_private_key and SERVICE_ACCOUNT_INFO["client_email"]:
            return Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    except Exception as e:
        print(f"Credentials dynamic execution setup warning: {e}")
    return None


def search_drive(query: str, folder_id: str = None):
    """
    Search Google Drive for files matching the query string.
    Optionally filters inside a specific parent folder scope index.
    """
    creds = get_google_creds()
    if not creds:
        return "Error: Google Credentials not initialized properly."
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Base logical parsing layout string (Bypasses parent folder structures)
        q_string = f"name contains '{query}' and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
        
        # Inject safe string validation to prevent 'None' variable bindings crashes
        if folder_id and folder_id != "all_drive" and folder_id != "None" and folder_id != "":
            q_string += f" and '{folder_id}' in parents"
            
        results = service.files().list(
            q=q_string,
            fields="files(id, name, webViewLink, alternateLink, mimeType)",
            pageSize=10
        ).execute()
        return results.get('files', [])
    except Exception as e:
        return f"Error searching drive: {str(e)}"


def get_all_folders():
    """
    Fetches all available folders from the connected Google Drive directory,
    including sub-folders shared with or inside the root directory visibility scope.
    """
    creds = get_google_creds()
    if not creds:
        return []
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Super Query Matrix: Targets child nodes inside nested folder environments
        query = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        
        results = service.files().list(
            q=query,
            fields="files(id, name, parents)",
            pageSize=50
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"Error fetching nested folders track list: {str(e)}")
        return []


def read_drive_file_content(file_id: str) -> str:
    """
    Google Drive API se file (PDF ya Text) ka raw content download karke uska plain text extract karta hai.
    """
    creds = get_google_creds()
    if not creds:
        return "Error: Google Credentials not initialized."
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Metadata check module execution layer
        file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        mime_type = file_metadata.get("mimeType", "")
        
        # Core dynamic media downloader streaming layout
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        file_stream.seek(0)
        
        # Mime-Type routing loops (PDF processing via pypdf stream parse structures)
        if "application/pdf" in mime_type:
            reader = PdfReader(file_stream)
            text_content = "".join([page.extract_text() or "" for page in reader.pages])
            return text_content if text_content.strip() else "This PDF seems empty or contains only images."
        else:
            # Standard plain-text layout decoder
            return file_stream.read().decode('utf-8', errors='ignore')
            
    except Exception as e:
        return f"Error reading file content from Google Drive: {str(e)}"