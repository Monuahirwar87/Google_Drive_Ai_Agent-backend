# backend/app/tools.py
import os
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Safe private key initialization
raw_private_key = os.getenv("GOOGLE_PRIVATE_KEY")
formatted_private_key = None

if raw_private_key:
    formatted_private_key = raw_private_key.replace("\\n", "\n")
    if not formatted_private_key.startswith("-----BEGIN PRIVATE KEY-----"):
        formatted_private_key = f"-----BEGIN PRIVATE KEY-----\n{formatted_private_key}\n-----END PRIVATE KEY-----"

SERVICE_ACCOUNT_INFO = {
    "type": os.getenv("GOOGLE_TYPE", "service_account"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": formatted_private_key,
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
}

def get_google_creds():
    """Dynamically yields credentials avoiding initialization freeze frames"""
    try:
        if formatted_private_key and SERVICE_ACCOUNT_INFO["client_email"]:
            return Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    except Exception as e:
        print(f"Credentials setup warning: {e}")
    return None

def search_drive(query: str, folder_id: str = None):
    creds = get_google_creds()
    if not creds:
        return "Error: Google Credentials not initialized properly."
    try:
        service = build('drive', 'v3', credentials=creds)
        q_string = f"name contains '{query}' and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
        
        if folder_id and folder_id != "all_drive" and folder_id != "None":
            q_string += f" and '{folder_id}' in parents"
            
        results = service.files().list(q=q_string, fields="files(id, name, webViewLink, mimeType)", pageSize=10).execute()
        return results.get('files', [])
    except Exception as e:
        return f"Error searching drive: {str(e)}"

def get_all_folders():
    creds = get_google_creds()
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
    creds = get_google_creds()
    if not creds:
        return "Error: Google Credentials not initialized."
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        mime_type = file_metadata.get("mimeType", "")
        
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        
        if "application/pdf" in mime_type:
            reader = PdfReader(file_stream)
            text_content = "".join([page.extract_text() or "" for page in reader.pages])
            return text_content if text_content.strip() else "This PDF seems empty."
        return file_stream.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Error reading file: {str(e)}"