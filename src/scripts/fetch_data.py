from pathlib import Path

from google.cloud.storage import Client

WORK_DIR = Path("../input_data")
BUCKET_NAME = "crypto_data192"
STORAGE_DIR = Path("data")
PERIODS = [60, 300, 900, 3600, 86400]


def fetch_data_from_storage(file_name: str) -> None:
    client = Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(str(STORAGE_DIR / file_name))
    blob.download_to_filename(str(WORK_DIR / file_name))


if __name__ == "__main__":
    for period in PERIODS:
        file_name = f"btf_periods{period}.csv"
        fetch_data_from_storage(file_name=file_name)
