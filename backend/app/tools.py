# backend/app/tools.py
import os
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

# SCOPES setup for read-only access to Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# 🔑 DIRECT ENVIRONMENT VARIABLES ACCESS (Render Friendly Setup)
raw_private_key = os.getenv("GOOGLE_PRIVATE_KEY")

if not raw_private_key:
    # Render system environment mein key missing hone par safe warning handle karein
    print("CRITICAL WARNING: GOOGLE_PRIVATE_KEY environment variable is missing!")
    formatted_private_key = None
else:
    # Handle normal newlines and literal \n combinations dynamically
    formatted_private_key = raw_private_key.replace("\\n", "\n")

# Combined Google Service Account Credentials Layout
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

# Credentials Object generation (Used globally by all endpoints)
if formatted_private_key and SERVICE_ACCOUNT_INFO["client_email"]:
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
else:
    creds = None


def search_drive(query: str, folder_id: str = None):
    """
    Search Google Drive for files matching the query string.
    Optionally filters inside a specific parent folder scope.
    """
    if not creds:
        return "Error: Google Credentials not initialized properly."
    try:
        service = build('drive', 'v3', credentials=creds)
        
        # Base query text logic (MimeType folder nahi hona chahiye, sirf actual files fetch karein)
        q_string = f"name contains '{query}' and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
        
        # Feature 4: Agar specific folder select kiya hai toh query mein filter apply karein
        if folder_id and folder_id != "all_drive":
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
    Fetches all available folders from the connected Google Drive directory.
    Used to populate the dynamic frontend select dropdown template.
    """
    if not creds:
        return []
    try:
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(
            q="mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)",
            pageSize=50
        ).execute()
        return results.get('files', [])
    except Exception as e:
        return []


def read_drive_file_content(file_id: str) -> str:
    """
    Google Drive API se file (PDF ya Text) ka raw content download karke
    uska plain text extract karta hai.
    """
    if not creds:
        return "Error: Google Credentials not initialized."
    try:
        # 'creds' global scope se automatic read ho jayega, no self-import issues
        service = build('drive', 'v3', credentials=creds)
        
        # 1. File ka metadata check karein (PDF hai ya normal text document)
        file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        mime_type = file_metadata.get("mimeType", "")
        
        # 2. File content download karne ke liye stream request create karein
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        file_stream.seek(0)
        
        # 3. Content Type validation layout ke hisab se text parse karein
        if "application/pdf" in mime_type:
            # PDF parsing via pypdf structure engine
            reader = PdfReader(file_stream)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text() or ""
            return text_content if text_content.strip() else "This PDF seems empty or contains only images."
        else:
            # Raw text decode parameters
            return file_stream.read().decode('utf-8', errors='ignore')
            
    except Exception as e:
        return f"Error reading file content from Google Drive: {str(e)}"