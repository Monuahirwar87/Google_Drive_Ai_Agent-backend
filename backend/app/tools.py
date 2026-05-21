from app.drive_client import search_files


def search_drive(keyword: str):
    """
    Search Google Drive for files whose names contain the given keyword.

    Example:
        search_drive("invoice")
    """
    query = f"name contains '{keyword}'"

    files = search_files(query)

    results = []

    for file in files:
        results.append({
            "name": file["name"],
            "id": file["id"],
            "mimeType": file["mimeType"],
            "link": file.get("webViewLink"),
        })

    return results

# backend/app/tools.py mein humne ek function banaya hai jo Google Drive mein search karega aur matching files ke naam, ID, MIME type, aur link return karega. Ye function `search_files` ko call karta hai jo `drive_client.py` mein defined hai aur Google Drive API se interact karta hai.

import os
import io
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader

# Load environment variables
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

# SCOPES setup
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Google Service Account Credentials Setup
# (Yeh aapka pehle se chal raha purana credentials setup hai)
SERVICE_ACCOUNT_INFO = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n") if os.getenv("GOOGLE_PRIVATE_KEY") else None,
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN", "googleapis.com")
}

# Credentials Object (Jo dono functions use karenge)
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)


def search_drive(query: str):
    """
    Search Google Drive for files matching the query string.
    """
    try:
        service = build('drive', 'v3', credentials=creds)
        # Aapka existing search_drive logic yahan chal raha hai...
        results = service.files().list(
            q=f"name contains '{query}' and trashed = false",
            fields="files(id, name, webViewLink, alternateLink, mimeType)",
            pageSize=10
        ).execute()
        return results.get('files', [])
    except Exception as e:
        return f"Error searching drive: {str(e)}"


# 🔑 FIXED: Is function ke andar se humne self-import line hata di hai!
def read_drive_file_content(file_id: str) -> str:
    """
    Google Drive API se file (PDF ya Text) ka raw content download karke
    uska text extract karta hai.
    """
    try:
        # 'creds' upar global scope mein defined hai, isliye direct use ho jayega
        service = build('drive', 'v3', credentials=creds)
        
        # 2. File ka metadata check karein (PDF hai ya normal text)
        file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        mime_type = file_metadata.get("mimeType", "")
        
        # 3. File content download karne ke liye request banayein
        # Content download stream setup
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        file_stream.seek(0)
        
        # 4. Content Type ke hisab se text extract karein
        # PDF handling
        if "application/pdf" in mime_type:
            # Agar PDF hai toh pypdf se read karein
            reader = PdfReader(file_stream)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text() or ""
            return text_content if text_content.strip() else "This PDF seems empty or contains only images."
            
        else:
            # Agar normal Text/.txt file hai toh direct decode karein
            return file_stream.read().decode('utf-8', errors='ignore')
            
    except Exception as e:
        return f"Error reading file content from Google Drive: {str(e)}"