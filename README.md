# Stationery Junction

Full-stack e-commerce platform for retail and wholesale stationery — built with **Next.js 14**, **FastAPI**, and optional **Oracle DB** (falls back to JSON file storage).

---

## Architecture

```
Ecommerce app/
├── backend/          FastAPI Python API
├── frontend/
│   ├── src/          Next.js 14 web app (App Router)
│   ├── mobile/       Expo React Native app
│   └── packages/
│       └── api-client/  Shared Axios client (web + mobile)
└── docker-compose.yml
```

| Layer | Stack |
|-------|-------|
| Web frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Mobile | Expo 54, React Native, NativeWind, Zustand |
| Backend API | FastAPI, Pydantic v2, SQLAlchemy 2 async |
| Database | Oracle (optional) or JSON file storage |
| Object storage | Oracle Cloud Infrastructure (OCI) |
| Auth | JWT (access + refresh), HttpOnly cookies, bcrypt |
