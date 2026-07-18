import sys
import os
from pathlib import Path

# Add backend directory to path to import app config
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import oci
from app.services.oci_storage import _get_client
from app.config.oci import OCI_BUCKET_NAME, OCI_NAMESPACE, OCI_REGION

print("Bucket Name:", OCI_BUCKET_NAME)
print("Namespace:", OCI_NAMESPACE)
print("Region:", OCI_REGION)

client = _get_client()
if not client:
    print("Failed to initialize OCI Client!")
    sys.exit(1)

print("OCI Client initialized successfully.")

# Attempt to list objects in the bucket to verify access
try:
    print("Listing objects in bucket...")
    objects = client.list_objects(namespace_name=OCI_NAMESPACE, bucket_name=OCI_BUCKET_NAME, limit=5)
    print("Success! Objects:")
    for obj in objects.data.objects:
        print(f" - {obj.name}")
except Exception as e:
    print("Error listing objects:", e)
