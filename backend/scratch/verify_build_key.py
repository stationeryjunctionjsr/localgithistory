import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.oci_storage import build_key
from app.config.settings import settings

print("--- Testing key generation under different environments ---")

# Save original environment
original_env = settings.environment

try:
    for env in ["development", "uat", "production"]:
        settings.environment = env
        key = build_key(prefix="products", filename="test_image.png", entity_id="123")
        print(f"Environment: {env:<15} -> Key: {key}")

        # Test uploads prefix
        uploads_key = build_key(prefix="uploads", filename="another.png")
        print(f"Environment: {env:<15} -> Uploads Key: {uploads_key}")

finally:
    # Restore environment
    settings.environment = original_env

print("\nVerification completed successfully!")
