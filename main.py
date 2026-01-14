import os
import json
import io
import pickle
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# ================== KONFIG ==================
FOLDER_ID = "1nKSO2v_YWZn1EE1HMvEP_rM9EqrHkQV2"  # folder Drive kamu
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/youtube.upload"
]
# ============================================

def get_credentials():
    creds = None

    # Load token.json jika ada
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Jika token invalid, refresh
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # Jika belum ada token, buat dari SECRET
    if not creds:
        print("❌ token.json tidak ditemukan / invalid")
        print("➡️ Pastikan token.json sudah diupload ke repo GitHub")
        exit(1)

    return creds

def get_drive():
    gauth = GoogleAuth()

    # Pakai token.json
    gauth.LoadCredentialsFile("token.json")
    if gauth.credentials is None:
        print("❌ token.json tidak valid")
        exit(1)
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("token.json")
    return GoogleDrive(gauth)

def get_youtube(creds):
    return build("youtube", "v3", credentials=creds)

def get_oldest_video(drive):
    print("🔍 Mengecek folder Drive...")

    file_list = drive.ListFile({
        "q": f"'{FOLDER_ID}' in parents and trashed=false",
        "orderBy": "createdDate asc"
    }).GetList()

    if not file_list:
        print("📭 Tidak ada video di Drive.")
        return None

    return file_list[0]

def download_file(file):
    print(f"⬇️ Mengambil: {file['title']}")

    file.GetContentFile("video.mp4")
    return "video.mp4", file["title"]

def upload_youtube(youtube, filepath, title):
    print("🚀 Upload ke YouTube...")

    body = {
        "snippet": {
            "title": os.path.splitext(title)[0],
            "description": "",
            "tags": ["shorts"],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(filepath, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()

    print("✅ Upload sukses:", response["id"])

def main():
    print("🔑 Login Google OK")

    creds = get_credentials()
    drive = get_drive()
    youtube = get_youtube(creds)

    file = get_oldest_video(drive)
    if not file:
        print("⏭️ Tidak ada video, skip.")
        return

    path, title = download_file(file)
    upload_youtube(youtube, path, title)

    print("🗑️ Hapus video dari Drive...")
    file.Delete()

    try:
        os.remove(path)
    except:
        pass

    print("🎉 SELESAI")

if __name__ == "__main__":
    main()
