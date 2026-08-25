import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import oci
from app.services.oci_storage import _get_client
from app.config.oci import OCI_BUCKET_NAME, OCI_NAMESPACE


def create_local_folders():
    print("--- Local Object Storage ---")
    base_dir = Path(__file__).resolve().parents[1] / "object_storage"
    folders = ["SJ_LOCAL", "SJ_UAT", "SJ_PROD"]
    for folder in folders:
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Created local directory: {folder_path}")


def create_oci_folders():
    print("\n--- OCI Object Storage ---")
    client = _get_client()
    if not client:
        print("OCI Client could not be initialized. Skipping OCI folders.")
        return

    folders = ["SJ_LOCAL/", "SJ_UAT/", "SJ_PROD/"]
    for folder in folders:
        try:
            print(f"Creating OCI folder placeholder: '{folder}' in bucket '{OCI_BUCKET_NAME}'...")
            client.put_object(
                namespace_name=OCI_NAMESPACE, bucket_name=OCI_BUCKET_NAME, object_name=folder, put_object_body=b""
            )
            print(f"Successfully created OCI folder: '{folder}'")
        except Exception as e:
            print(f"Failed to create OCI folder '{folder}': {e}")


if __name__ == "__main__":
    create_local_folders()
    create_oci_folders()
    print("\nDone!")
