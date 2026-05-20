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