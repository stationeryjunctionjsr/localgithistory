import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_root))

load_dotenv()

import oci


def main():
    db_type = os.environ.get("DB_TYPE", "oracle").lower()
    if db_type == "mysql":
        print("DB_TYPE=mysql — skipping Oracle Autonomous DB startup.", flush=True)
        return

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

    db_client = oci.database.DatabaseClient(config)
    sjuatdb_ocid = (
        "ocid1.autonomousdatabase.oc1.ap-hyderabad-1.anuhsljrtzuv55aad74dalkb6ighs5ttvjkmhbdzen5cagwlekouqfs2ismq"
    )

    print("Checking database state...", flush=True)
    try:
        db_details = db_client.get_autonomous_database(sjuatdb_ocid).data
        state = db_details.lifecycle_state
        print(f"Current Lifecycle State: {state}", flush=True)

        if state == "STOPPED":
            print("Database is stopped. Starting Autonomous Database...", flush=True)
            db_client.start_autonomous_database(sjuatdb_ocid)
            print("Start request sent successfully. Polling state...", flush=True)

            while True:
                time.sleep(15)
                db_details = db_client.get_autonomous_database(sjuatdb_ocid).data
                state = db_details.lifecycle_state
                print(f"Current State: {state}", flush=True)
                if state == "AVAILABLE":
                    print("[+] Database is now AVAILABLE!", flush=True)
                    break
                elif state not in ("STARTING", "STOPPED"):
                    print(f"[-] Database entered unexpected state: {state}", flush=True)
                    break
        elif state == "AVAILABLE":
            print("[+] Database is already AVAILABLE.", flush=True)
        else:
            print(f"[*] Database is in state: {state}. Waiting for it to become AVAILABLE...", flush=True)
            while True:
                time.sleep(15)
                db_details = db_client.get_autonomous_database(sjuatdb_ocid).data
                state = db_details.lifecycle_state
                print(f"Current State: {state}", flush=True)
                if state == "AVAILABLE":
                    print("[+] Database is now AVAILABLE!", flush=True)
                    break
    except Exception as e:
        print("Error starting database:", e, flush=True)


if __name__ == "__main__":
    main()
