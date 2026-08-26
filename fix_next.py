nc = "frontend/next.config.js"
with open(nc, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'", "process.env.NEXT_PUBLIC_API_URL"
)
content = content.replace(
    "process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api'", "process.env.NEXT_PUBLIC_API_URL"
)
content = content.replace(
    "process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'", "process.env.NEXT_PUBLIC_API_URL"
)

with open(nc, "w", encoding="utf-8") as f:
    f.write(content)
