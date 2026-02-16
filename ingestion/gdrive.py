"""Google Drive client for downloading documents for ingestion.

Requires:
    pip install google-api-python-client google-auth

Setup:
    1. Create a Google Cloud project and enable the Google Drive API
    2. Create a service account and download the JSON key file
    3. Share your Drive folder with the service account email
    4. Set GDRIVE_CREDENTIALS_FILE and GDRIVE_FOLDER_ID env vars
"""

import os
import io
import logging
import tempfile
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Google Drive MIME types and their export formats
GOOGLE_EXPORT_MAP = {
    "application/vnd.google-apps.document": {
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "ext": ".docx",
    },
    "application/vnd.google-apps.spreadsheet": {
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ext": ".xlsx",
    },
    "application/vnd.google-apps.presentation": {
        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "ext": ".pptx",
    },
}

# Supported native file extensions (downloaded as-is)
SUPPORTED_EXTENSIONS = {
    ".md", ".markdown", ".txt",
    ".pdf",
    ".docx", ".doc",
    ".pptx", ".ppt",
    ".xlsx", ".xls",
    ".html", ".htm",
    ".mp3", ".wav", ".m4a", ".flac",
}


class GoogleDriveClient:
    """Client for downloading files from Google Drive using a service account."""

    def __init__(self, credentials_file: str):
        """
        Initialize with service account credentials.

        Args:
            credentials_file: Path to the service account JSON key file.
        """
        self.credentials_file = credentials_file
        self.service = None

    def authenticate(self):
        """Authenticate with Google Drive API using service account credentials."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
            self.service = build("drive", "v3", credentials=credentials)
            logger.info("Authenticated with Google Drive API")

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}. "
                "Download a service account key from Google Cloud Console."
            )
        except Exception as e:
            raise RuntimeError(f"Google Drive authentication failed: {e}")

    def list_files(self, folder_id: str) -> List[Dict]:
        """
        List supported files in a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID.

        Returns:
            List of file metadata dicts with keys: id, name, mimeType.
        """
        if not self.service:
            self.authenticate()

        files = []
        page_token = None

        while True:
            response = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, size)",
                pageToken=page_token,
                pageSize=100,
            ).execute()

            for f in response.get("files", []):
                mime = f["mimeType"]
                name = f["name"]

                # Google Workspace files (exportable)
                if mime in GOOGLE_EXPORT_MAP:
                    files.append(f)
                    continue

                # Native files — check extension
                ext = Path(name).suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    files.append(f)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        logger.info(f"Found {len(files)} supported files in Drive folder {folder_id}")
        return files

    def download_file(self, file_meta: Dict, dest_dir: str) -> Optional[str]:
        """
        Download a single file from Google Drive.

        Args:
            file_meta: File metadata dict (from list_files).
            dest_dir: Local directory to save the file.

        Returns:
            Local file path, or None if download failed.
        """
        if not self.service:
            self.authenticate()

        from googleapiclient.http import MediaIoBaseDownload

        file_id = file_meta["id"]
        name = file_meta["name"]
        mime = file_meta["mimeType"]

        try:
            # Google Workspace files — export to Office format
            if mime in GOOGLE_EXPORT_MAP:
                export_info = GOOGLE_EXPORT_MAP[mime]
                export_mime = export_info["mime"]
                ext = export_info["ext"]

                # Strip any existing extension and add the export one
                base_name = Path(name).stem
                dest_path = os.path.join(dest_dir, f"{base_name}{ext}")

                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime
                )

            else:
                # Native file — download as-is
                dest_path = os.path.join(dest_dir, name)
                request = self.service.files().get_media(fileId=file_id)

            # Download with progress
            fh = io.FileIO(dest_path, "wb")
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            fh.close()
            logger.info(f"Downloaded: {name} -> {dest_path}")
            return dest_path

        except Exception as e:
            logger.error(f"Failed to download {name}: {e}")
            return None

    def download_folder(self, folder_id: str, dest_dir: Optional[str] = None) -> str:
        """
        Download all supported files from a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID.
            dest_dir: Local directory to save files (creates temp dir if None).

        Returns:
            Path to the directory containing downloaded files.
        """
        if dest_dir is None:
            dest_dir = tempfile.mkdtemp(prefix="gdrive_ingest_")

        os.makedirs(dest_dir, exist_ok=True)

        files = self.list_files(folder_id)

        if not files:
            logger.warning(f"No supported files found in Drive folder {folder_id}")
            return dest_dir

        downloaded = 0
        for f in files:
            path = self.download_file(f, dest_dir)
            if path:
                downloaded += 1

        logger.info(
            f"Downloaded {downloaded}/{len(files)} files to {dest_dir}"
        )
        return dest_dir
