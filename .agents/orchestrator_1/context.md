# Project Context

## Project Info
- Path: `c:\Ecommerce app`
- Target directory: `backend/app/routers` (56 router files + ads.py reference)
- Schemas directory: `backend/app/models/schemas.py` or inline schemas where appropriate

## Goal
Eliminate `.get()` workarounds on request payloads / internal dictionaries and replace with strict Pydantic models with dot-notation field access.

## Requirements
- R1: Eliminate `.get()` dictionary workarounds on payloads/data structures in routers. (`request.headers.get()` is exempt).
- R2: Introduce Pydantic models for generic dict payloads.
- R3: Strict Pydantic dot-notation (e.g. `payload.product_id`) with appropriate type hints and fallback defaults.

## Acceptance Criteria
- Zero results for `.get(` on request payloads/internal data structures in `backend/app/routers/`.
- FastAPI application starts up without import/syntax/Pydantic errors.
- Review confirms all dict payload parameters replaced with Pydantic models.
