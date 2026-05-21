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

import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader
from app.tools import creds
def read_drive_file_content(file_id: str) -> str:
    """
    Google Drive API se file (PDF ya Text) ka raw content download karke
    uska text extract karta hai.
    """
    try:
        # 1. Google Drive API client service build karein
        # Note: Aapne search_drive mein jo credentials use kiye hain, wahi same yahan use honge.
        # Agar aapka creds object 'creds' naam se hai, toh use yahan pass karein:
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