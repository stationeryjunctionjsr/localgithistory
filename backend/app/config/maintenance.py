"""Scheduled upgrade / maintenance mode copy and API allowlist."""

MAINTENANCE_MESSAGE_PARAGRAPHS = [
    (
        "The application is currently undergoing a scheduled update and services will be "
        "temporarily unavailable during this time."
    ),
    ("Access to the application will be restored once the update has been successfully completed."),
    ("We regret the inconvenience caused and appreciate your patience and understanding."),
]

# Paths that remain reachable while maintenance mode is active (prefix match).
MAINTENANCE_ALLOWLIST_PREFIXES = (
    "/api/health",
    "/api/app/maintenance",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics",
)
