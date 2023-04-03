import base64
from pathlib import Path

import functions_framework
from google.cloud.storage import Client

from library.crawler import add_data

WORK_DIR = Path("/tmp")
BUCKET_NAME = "crypto_data192"
STORAGE_DIR = Path("data")
PERIODS = 900  # 15min


@functions_framework.cloud_event
def run(cloud_event) -> None:
    file_name = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    update_data(file_name)


def update_data(file_name: str) -> None:
    fetch_current_data_from_storage(file_name=file_name)
    add_data(periods=PERIODS, save_path=WORK_DIR / file_name)
    upload_to_storage(file_name=file_name)


def fetch_current_data_from_storage(file_name: str) -> None:
    client = Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(str(STORAGE_DIR / file_name))
    blob.download_to_filename(str(WORK_DIR / file_name))


def upload_to_storage(file_name: str) -> None:
    client = Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(str(STORAGE_DIR / file_name))
    blob.upload_from_filename(str(WORK_DIR / file_name))
