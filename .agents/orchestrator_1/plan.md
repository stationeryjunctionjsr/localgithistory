# Project Execution Plan

## Objective
Refactor all remaining router files in `backend/app/routers` to remove `.get()` dictionary workarounds on request payloads/internal data structures and replace them with strict Pydantic models, matching the pattern in `ads.py`.

## Strategy
1. **Phase 0: Survey & Discovery**
   - Dispatch 3 Explorers in parallel:
     - Explorer 1: Inspect `backend/app/routers/ads.py` and `app/models/schemas.py` to establish the exact reference patterns, coding conventions, imports, and model definitions.
     - Explorer 2: Scan all files in `backend/app/routers` to catalog all `.get()` usages, distinguish exempt usages (e.g. `headers.get`, `query_params.get`, or standard dict get if any) vs payload/data dict workarounds, and list all target files.
     - Explorer 3: Scan `backend/app/routers` for endpoint functions accepting `payload: dict` or `data: dict` or untyped request bodies, and check current FastAPI startup/test command.
   - Aggregate findings into `PROJECT.md` Feature Inventory & Milestones.

2. **Phase 1: Milestone Decomposition & Architecture**
   - Group the target router files into manageable, coherent milestones.
   - Set up interface contracts and model locations (inline vs `schemas.py`).

3. **Phase 2: Milestone Iteration Loops**
   - For each milestone:
     - Worker: Implement Pydantic models and update endpoint signatures/dot-notation access, run tests/startup check.
     - Reviewers: Verify model quality, type annotations, and absence of payload `.get()`.
     - Challengers: Stress-test endpoints / models.
     - Forensic Auditor: Verify authenticity and integrity.
     - Gate evaluation.

4. **Phase 3: Global Acceptance & Verification**
   - Search across `backend/app/routers/` to verify zero `.get(` on request payloads/internal data structures.
   - Verify FastAPI startup command passes without syntax/import/Pydantic errors.
   - Verify all dict payload endpoints are replaced with Pydantic models.

5. **Phase 4: Synthesis & Sentinel Notification**
   - Report final status to Sentinel.
