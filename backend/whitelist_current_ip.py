import os
import sys
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

backend_root = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_root))

load_dotenv()

import oci

def get_public_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=10) as response:
            return response.read().decode("utf-8").strip()
    except Exception as e:
        print(f"Error fetching public IP: {e}")
        return None

def main():
    ip = get_public_ip()
    if not ip:
        print("Could not resolve current public IP. Skipping whitelisting.")
        return
    
    print(f"Current Public IP: {ip}")
    
    key_content = os.environ.get("OCI_PRIVATE_KEY", "").replace("\\n", "\n")
    if key_content.startswith('"') and key_content.endswith('"'):
        key_content = key_content[1:-1]
        
    config = {
        "user": os.environ.get("OCI_USER_OCID"),
        "fingerprint": os.environ.get("OCI_FINGERPRINT"),
        "tenancy": os.environ.get("OCI_TENANCY_OCID"),
        "region": os.environ.get("OCI_REGION"),
        "key_content": key_content
    }
    
    db_client = oci.database.DatabaseClient(config)
    sjuatdb_ocid = "ocid1.autonomousdatabase.oc1.ap-hyderabad-1.anuhsljrtzuv55aad74dalkb6ighs5ttvjkmhbdzen5cagwlekouqfs2ismq"
    
    print("Fetching current whitelisted IPs from Oracle OCI...")
    try:
        db_details = db_client.get_autonomous_database(sjuatdb_ocid).data
        current_whitelist = db_details.whitelisted_ips or []
        print(f"Current Whitelisted IPs: {current_whitelist}")
        
        if ip in current_whitelist:
            print(f"[+] Current IP {ip} is already whitelisted.")
            return
            
        print(f"Adding {ip} to whitelist...")
        new_whitelist = list(current_whitelist)
        new_whitelist.append(ip)
        
        update_details = oci.database.models.UpdateAutonomousDatabaseDetails(
            whitelisted_ips=new_whitelist
        )
        
        print("Sending update request to Oracle OCI...")
        db_client.update_autonomous_database(sjuatdb_ocid, update_details)
        print("[+] IP whitelist updated successfully!")
    except Exception as e:
        print(f"[-] Error whitelisting IP: {e}")

if __name__ == "__main__":
    main()
