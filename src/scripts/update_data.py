from pathlib import Path

from google.cloud.storage import Client

WORK_DIR = Path("../input_data")
BUCKET_NAME = "crypto_data192"
STORAGE_DIR = Path("data")
PERIODS = 900  # 15min


def fetch_data_from_storage(file_name: str) -> None:
    client = Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(str(STORAGE_DIR / file_name))
    blob.download_to_filename(str(WORK_DIR / file_name))


if __name__ == "__main__":
    fetch_data_from_storage(file_name="btf_periods900.csv")
