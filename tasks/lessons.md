# RAAMP Agent Lessons

## Critical Backend Issues

### 2026-04-24: Python Server Zombie Process & Cached Modules
**Problem:** Backend server serving old/phantom routes even after file edits and "restarts"  
**Symptoms:**
- OpenAPI docs show routes that don't exist in code (e.g., `/test-analyse`)
- Router imports correctly in isolation but server loads different version
- Hot-reload crashes with Windows multiprocessing errors
- Test endpoint returns 404 even after code is added

**Root Causes:**
1. Python bytecode cache (`.pyc`, `__pycache__`) persists old code
2. Uvicorn auto-reload fails on Windows with multiprocessing issues
3. Zombie processes remain on port 8000 after manual restarts

**Solution (ALWAYS follow this order):**
```powershell
# 1. Kill ALL Python processes
Get-Process python | Stop-Process -Force

# 2. Clear bytecode cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

# 3. Start fresh
cd raamp-backend
python main.py
```

**Verification:**
- Check OpenAPI: `curl http://localhost:8000/openapi.json | jq '.paths | keys'`  
- Test import separately: Run `python -c "from presentation.routers import comment_analysis_router"` to verify code
- Expect **401** (auth required) not **404** (not found) for protected endpoints

### 2026-04-24: Frontend Double API Prefix Bug
**Problem:** Frontend requests fail with 404: `/api/api/comments/moderation` (double `/api/`)  
**Root Cause:** `apiClient` base URL is `/api`, but services also added `/api/` prefix in endpoint paths  
**Fix:** Remove `/api/` prefix from service endpoint paths - use `/comments/moderation` not `/api/comments/moderation`  
**Rule:** When API client has base URL, endpoints should be relative without repeating the prefix

## Performance Lessons

### 2026-04-23: Campaign Planner JSON Serialization Error
**Problem:** 500 error when creating campaign plans: `TypeError: Object of type datetime is not JSON serializable`

**Root Cause:** The `brief` parameter contained Pydantic-parsed `datetime` objects (start_date, end_date). When building the LLM prompt, `json.dumps(brief)` failed because Python's json module can't serialize datetime objects by default.

**Fix:** Added `_serialize_for_json()` helper that recursively converts datetime objects to ISO strings before JSON serialization in `_build_prompt()`.

**Rule:** Always serialize datetime objects to strings before passing data to `json.dumps()`. Never assume dictionaries from Pydantic models are JSON-serializable.

### 2026-04-23: Campaign Planner Generation Performance
**Problem:** Campaign plan generation taking excessively long (20-30+ seconds) causing poor UX.

**Root Causes:** 
1. LLM `max_output_tokens=2048` was too low for complex campaigns with many posts, causing slow generation
2. Individual database inserts in a loop (one per post) added significant latency
3. Default timeout of 25s was being reached frequently

**Fix:** 
1. Increased `max_output_tokens` from 2048 to 4096 for faster, more complete responses
2. Replaced sequential inserts with bulk `insert_many()` for all posts (reduces N round trips to 1)
3. Increased timeout from 25s to 35s to accommodate complex campaigns
4. Updated frontend message to reflect accurate timing (15-20s)

**Rule:** For LLM-generated content with variable output sizes, use generous token limits. Always use bulk database operations when inserting multiple related documents.

### 2026-04-23: Plan Mode Trigger Optimization
**Problem:** Agent was entering "Plan Mode" too aggressively, causing slow response times for simple requests.

**Root Cause:** copilot-instructions.md had "Enter Plan Mode for ANY non-trivial task (3+ steps)" which triggered excessive planning.

**Fix:** Changed to only plan for truly complex work (multi-file refactors, new modules, architectural changes). Default to action-first for bug fixes, single-file edits, and simple features.

**Rule:** Only use heavy planning for 5+ interconnected steps or new module implementations.
