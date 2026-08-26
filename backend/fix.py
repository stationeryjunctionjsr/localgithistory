import sys

with open("app/config/database.py") as f:
    code = f.read()

code = code.replace(
    'if use_oracle(): connect_args["config_dir"] = wallet_path',
    'if DATABASE_URL and DATABASE_URL.startswith("oracle"):\n            connect_args["config_dir"] = wallet_path',
)
code = code.replace(
    'if use_oracle(): connect_args["wallet_location"] = wallet_path',
    'if DATABASE_URL and DATABASE_URL.startswith("oracle"):\n            connect_args["wallet_location"] = wallet_path',
)
code = code.replace(
    'connect_args["wallet_password"] = os.environ.get("WALLET_PASSWORD", "WalletPassword123#")',
    'if DATABASE_URL and DATABASE_URL.startswith("oracle"):\n            connect_args["wallet_password"] = os.environ.get("WALLET_PASSWORD", "WalletPassword123#")',
)

with open("app/config/database.py", "w") as f:
    f.write(code)
