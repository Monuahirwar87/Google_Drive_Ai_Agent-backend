# backend/app/tools.py
import os
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

# SCOPES setup for read-only access to Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_google_creds():
    """
    Dynamically yields credentials avoiding initialization freeze frames or stale states.
    Reads latest configurations directly at request runtime.
    """
    try:
        # 🔑 Safety Check: Read from primary names OR alternate dashboard fallbacks
        raw_private_key = os.getenv("GOOGLE_PRIVATE_KEY") or os.getenv("PRIVATE_KEY") or ""
        client_email = os.getenv("GOOGLE_CLIENT_EMAIL") or os.getenv("GOOGLE_CLIENT_ID") or ""
        
        if not raw_private_key:
            print("CRITICAL WARNING: Neither GOOGLE_PRIVATE_KEY nor PRIVATE_KEY is set!")
            return None

        # Remove literal escaped strings and handle line breaks dynamically
        if "\\n" in raw_private_key:
            formatted_private_key = raw_private_key.replace("\\n", "\n")
        else:
            formatted_private_key = raw_private_key

        # Wrap with standard cryptographic markers if missing in raw string
        if formatted_private_key and not formatted_private_key.startswith("-----BEGIN PRIVATE KEY-----"):
            formatted_private_key = f"-----BEGIN PRIVATE KEY-----\n{formatted_private_key}\n-----END PRIVATE KEY-----\n"

        # Master layouts structure built dynamically inside the frame runtime execution
        service_account_info = {
            "type": os.getenv("GOOGLE_TYPE", "service_account"),
            "project_id": os.getenv("GOOGLE_PROJECT_ID"),
            "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
            "private_key": formatted_private_key,
            "client_email": client_email,
            "client_id": os.getenv("GOOGLE_CLIENT_ID") or "",
            "auth_uri": os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN", "googleapis.com")
        }

        if formatted_private_key and client_email:
            return Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
            
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
        return "Error: Google Drive credentials have not been initialized properly. Please check your Render configuration environment parameters."
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Base logical parsing layout string (Bypasses parent folder structures)
        q_string = f"name contains '{query}' and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
        
        # Inject safe string validation to prevent 'None' variable bindings crashes
        if folder_id and folder_id != "all_drive" and folder_id != "None" and folder_id != "":
            q_string += f" and '{folder_id}' in parents"
            
        results = service.files().list(
            q=q_string,
            fields="nextPageToken, files(id, name, webViewLink, mimeType)",
            pageSize=10
        ).execute()
        return results.get('files,', [])
    except Exception as e:
        return f"Error searching drive: {str(e)}"


def get_all_folders():
    """
    Fetches all available folders from the connected Google Drive directory.
    """
    creds = get_google_creds()
    if not creds:
        return []
    try:
        service = build('drive', 'v3', credentials=creds)
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
    Downloads raw content from Google Drive and extracts plain text (supports PDFs and Text files).
    """
    creds = get_google_creds()
    if not creds:
        return "Error: Google Credentials not initialized properly."
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