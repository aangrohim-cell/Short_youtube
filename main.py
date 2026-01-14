import os
import json
import io
import pickle
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# =========================
# KONFIG
# =========================
FOLDER_ID = "1nKSO2v_YWZn1EE1HMvEP_rM9EqrHkQV2"  # Folder Google Drive kamu
LOCAL_VIDEO = "video.mp4"
TOKEN_FILE = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/youtube.upload"
]

# =========================
# LOGIN GOOGLE
# =========================
def get_credentials():
    creds = None

    # Load token jika ada
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Kalau belum ada / expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔁 Refresh token...")
            creds.refresh(Request())
        else:
            print("🌐 Login Google diperlukan...")

            # Ambil client secrets dari ENV (GitHub Secrets)
            if "CLIENT_SECRETS_JSON" in os.environ:
                client_config = json.loads(os.environ["CLIENT_SECRETS_JSON"])
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            else:
                # Fallback lokal (kalau masih ada file)
                flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)

            creds = flow.run_local_server(port=0)

        # Simpan token
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    print("✅ Login Google OK")
    return creds

# =========================
# MAIN
# =========================
def main():
    creds = get_credentials()

    drive_service = build("drive", "v3", credentials=creds)
    youtube_service = build("youtube", "v3", credentials=creds)

    print("🔍 Mengecek folder Drive...")

    # Ambil video tertua (FIFO)
    results = drive_service.files().list(
        q=f"'{FOLDER_ID}' in parents and trashed=false",
        orderBy="createdTime",
        fields="files(id, name, createdTime)"
    ).execute()

    items = results.get("files", [])

    if not items:
        print("📭 Folder kosong. Tidak ada video untuk diupload.")
        return

    video = items[0]
    print("📥 Mengambil:", video["name"])

    # =========================
    # DOWNLOAD FILE
    # =========================
    request = drive_service.files().get_media(fileId=video["id"])

    with open(LOCAL_VIDEO, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    print("💾 Download selesai")

    # =========================
    # UPLOAD KE YOUTUBE
    # =========================
    print("🚀 Upload ke YouTube...")

    request = youtube_service.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": video["name"],  # Judul = nama file
                "description": "#shorts",
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(LOCAL_VIDEO, resumable=True)
    )

    response = request.execute()
    print("✅ Upload sukses! Video ID:", response["id"])

    # =========================
    # HAPUS DARI DRIVE
    # =========================
    drive_service.files().delete(fileId=video["id"]).execute()
    print("🗑️ Video dihapus dari Drive")

    # =========================
    # HAPUS FILE LOKAL
    # =========================
    try:
        os.remove(LOCAL_VIDEO)
        print("🧹 File lokal dihapus")
    except:
        print("⚠️ Gagal hapus file lokal, tapi tidak masalah.")

    print("🎉 Selesai 1 video.")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ ERROR:", str(e))
        raise
