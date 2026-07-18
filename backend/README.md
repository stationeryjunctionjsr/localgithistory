# Stationery Junction - Python/FastAPI Backend (New Tech Stack)

This is the Python/FastAPI backend for the new tech stack version.

## Setup

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Run

```bash
python run.py
```

Runs on http://localhost:8000

API docs available at: http://localhost:8000/docs

## Environment Variables

Create `.env` file:
```env
PORT=8000
JWT_SECRET=your-secret-key-here
ENVIRONMENT=development
```

## Create Super Admin

```bash
python scripts/create_super_admin.py
```

## Frontend

The frontend for this backend is in the `../frontend` folder.
