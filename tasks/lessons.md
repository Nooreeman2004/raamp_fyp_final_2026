# RAAMP Agent Lessons

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
