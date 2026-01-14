import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# =========================
# KONFIG
# =========================
FOLDER_ID = "1nKSO2v_YWZn1EE1HMvEP_rM9EqrHkQV2"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/youtube.upload"
]

# =========================
# LOGIN GOOGLE
# =========================
creds = None

if os.path.exists("token.json"):
    with open("token.json", "rb") as token:
        creds = pickle.load(token)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secrets.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open("token.json", "wb") as token:
        pickle.dump(creds, token)

print("✅ Login Google OK")

# =========================
# KONEK DRIVE
# =========================
drive_service = build("drive", "v3", credentials=creds)

# =========================
# AMBIL VIDEO TERLAMA
# =========================
results = drive_service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    orderBy="createdTime",
    fields="files(id, name)"
).execute()

items = results.get("files", [])

if not items:
    print("❌ Tidak ada video di folder. Skip.")
    exit(0)

video = items[0]
print("📥 Mengambil:", video["name"])

# =========================
# DOWNLOAD FILE
# =========================
from googleapiclient.http import MediaIoBaseDownload
import io

request = drive_service.files().get_media(fileId=video["id"])
with open("video.mp4", "wb") as fh:
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()


# =========================
# UPLOAD KE YOUTUBE
# =========================
youtube = build("youtube", "v3", credentials=creds)

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": video["name"],
            "description": "#shorts",
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    },
    media_body=MediaFileUpload("video.mp4", resumable=True)
)

response = request.execute()
print("✅ Upload sukses:", response["id"])

# =========================
# HAPUS DARI DRIVE
# =========================
drive_service.files().delete(fileId=video["id"]).execute()
print("🗑️ Video dihapus dari Drive")

# =========================
# BERSIHKAN
# =========================
try:
    os.remove("video.mp4")
except:
    print("⚠️ Gagal hapus file lokal, tapi tidak masalah.")

print("🎉 Selesai 1 video")
