import os
import sys
from pathlib import Path

# Add backend root so app imports work
backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_root))
os.chdir(backend_root)

from dotenv import load_dotenv

load_dotenv()

import oci


def main():
    print("Initializing OCI Database Client...")

    # Clean up key content formatting from env
    key_content = os.environ.get("OCI_PRIVATE_KEY", "").replace("\\n", "\n")
    if key_content.startswith('"') and key_content.endswith('"'):
        key_content = key_content[1:-1]

    config = {
        "user": os.environ.get("OCI_USER_OCID"),
        "fingerprint": os.environ.get("OCI_FINGERPRINT"),
        "tenancy": os.environ.get("OCI_TENANCY_OCID"),
        "region": os.environ.get("OCI_REGION"),
        "key_content": key_content,
    }

    # Check config validity
    for k, v in config.items():
        if not v:
            print(f"ERROR: {k} is not set in environment.")
            return

    db_client = oci.database.DatabaseClient(config)
    compartment_id = config["tenancy"]

    print(f"Listing Autonomous Databases in compartment: {compartment_id}...")
    try:
        response = db_client.list_autonomous_databases(compartment_id)
        dbs = response.data
        if not dbs:
            print("No Autonomous Databases found.")
            return

        print(f"Found {len(dbs)} Autonomous Database(s):")
        for db in dbs:
            print(f"- Name: {db.db_name}, Lifecycle State: {db.lifecycle_state}, OCID: {db.id}")

            # If the database is stopped or stopping, let's start it!
            if db.lifecycle_state == "STOPPED":
                print(f"Database {db.db_name} is STOPPED. Triggering START...")
                start_resp = db_client.start_autonomous_database(db.id)
                print(f"Start requested! New lifecycle state: {start_resp.data.lifecycle_state}")
            elif db.lifecycle_state == "AVAILABLE":
                print(f"Database {db.db_name} is already AVAILABLE.")
            else:
                print(f"Database lifecycle state is {db.lifecycle_state}. No action taken.")

    except Exception as e:
        print(f"OCI Error: {e}")


if __name__ == "__main__":
    main()
