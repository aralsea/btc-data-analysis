from pathlib import Path

import functions_framework
from google.cloud.storage import Client

from library.crawler import add_data

WORK_DIR = Path("/tmp")
BUCKET_NAME = "crypto_data192"
STORAGE_DIR = Path("data")
PERIODS = [60, 300, 900, 3600, 86400]


@functions_framework.cloud_event
def run(cloud_event) -> None:
    for period in PERIODS:
        update_data(period)


def update_data(period: int) -> None:
    file_name = f"btf_periods{period}.csv"
    fetch_current_data_from_storage(file_name=file_name)
    add_data(periods=period, save_path=WORK_DIR / file_name)
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
