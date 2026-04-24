# Technical Debt Registry

**Purpose:** Conscious decisions to accept technical debt with documented rationale.  
**Rule:** "Partially fixed" = unfixed. Either fix completely or document why debt is accepted.

---

## 1. trendService.ts - Remaining `as any` Type Casts

**Status:** ✅ ACCEPTED (2026-04-24)  
**Location:** `raamp-frontend/src/services/trendService.ts` (15 instances, lines 272-398)  

**Issue:** Backend API returns inconsistent response shapes:
- Sometimes: `{trends: [...], count: number}`
- Sometimes: `[...]` (bare array)
- Sometimes: `{opportunities: [...]}` vs `{timeline: [...]}`

**Decision:** Keep defensive `as any` casts with fallback logic.

**Rationale:**
1. Backend contract changes would require coordinated frontend/backend refactor
2. Current casts are **controlled** - they're followed immediately by type checks and fallbacks
3. Runtime safety is preserved: `(data as any)?.field ?? []` prevents crashes
4. Cost/benefit: Full type safety requires backend API redesign (Phase 5+ work)
5. No user-facing bugs caused by these casts

**Alternative Fix (Future):**
- Standardize backend API responses to always return `{data: T, count: number}` shape
- Create proper TypeScript interfaces for all response types
- Remove all `as any` casts and rely on compile-time type checking

**Priority:** Low (cosmetic - does not affect functionality)

---

## 2. Background Task Retry Logic - Implementation Bug

**Status:** ✅ ACCEPTED (2026-04-24)  
**Location:** `raamp-backend/application/utils/background_tasks.py`  

**Issue:** `_safe_task_wrapper()` attempts to retry failed tasks by awaiting the same coroutine multiple times. This is **impossible in Python** - coroutines can only be awaited once.

**Current Behavior:**
- `max_retries > 0`: Only first attempt runs, retries silently fail
- `max_retries = 0`: Works correctly (error caught and logged)
- Most code uses `max_retries=0`, so bug rarely surfaces

**Decision:** Accept the bug. Do not claim retry functionality works.

**Rationale:**
1. Proper fix requires API change: accept `Callable` instead of `Coroutine`, call it on each retry
2. This would break all existing usage: `create_background_task(my_coro(), ...)` → `create_background_task(my_func, ...)`
3. Current usage throughout codebase uses `max_retries=0`, so retries aren't actually needed
4. Background tasks are non-critical (activity logging, analytics) - single attempt is sufficient
5. Cost/benefit: Large refactor for rarely-used feature

**Test Status:**
- Test renamed: `test_retry_logic_attempts_multiple_times` → `test_task_error_is_caught_and_logged`
- Test now accurately describes what it tests (error catching, not retries)
- Added comment explaining coroutine limitation and why retries can't be tested

**Alternative Fix (Future):**
```python
def create_background_task(
    func: Callable[[], Coroutine],  # Accept callable, not coroutine
    task_name: str,
    max_retries: int = 0
):
    async def wrapper():
        for attempt in range(max_retries + 1):
            try:
                await func()  # Call func() on each attempt
                return
            except Exception as e:
                if attempt < max_retries:
                    continue
                logger.error(f"Task {task_name} failed: {e}")
    
    return asyncio.create_task(wrapper())

# Usage would change:
create_background_task(lambda: log_activity(...), "log_activity")  # Not log_activity(...)
```

**Priority:** Low (most background tasks succeed on first attempt)

---

## 3. Unmigrated Toast Messages - Hardcoded Strings

**Status:** ✅ ACCEPTED (2026-04-24)  
**Location:** `raamp-frontend/src/` (40+ files with hardcoded toast messages)

**Issue:** Phase 3 created centralized message constants (`constants/messages.ts`) and loading patterns (`utils/loadingPatterns.ts`), but only 5 files migrated to use them. Remaining ~40 files still have hardcoded strings in `toast.success()` and `toast.error()` calls.

**Files Migrated (5):**
- AdminComplaints.tsx
- NotificationContext.tsx
- AutoReplies.tsx
- AccountSecurity.tsx
- ScheduledPostsTable.tsx

**Files NOT Migrated (40+):**
- TrendArbitrage.tsx (~10+ toast calls)
- CreativeStudio.tsx (~15+ toast calls)
- AssetLibrary.tsx (~10+ toast calls)
- Onboarding.tsx (~10+ toast calls)
- Complaints.tsx (~10+ toast calls)
- SocialModeration.tsx (~8+ toast calls)
- GeoIntent.tsx (~5+ toast calls)
- Login.tsx (~5+ toast calls)
- EnhancedPostCreatorPanel.tsx (~5+ toast calls)
- Plus 30+ additional files...

**Total:** ~78 `toast.success()` calls + 100+ `toast.error()` calls unmigrated

**Decision:** Accept as technical debt. Migrate opportunistically.

**Rationale:**
1. **Infrastructure is complete** - `messages.ts` and `loadingPatterns.ts` exist and are proven to work
2. **Pattern is established** - 5 files demonstrate correct usage
3. **Scope is massive** - Full migration is a separate multi-day project, not Phase 3 work
4. **Audit requirement met** - Audit called for "standardization infrastructure and consistent patterns going forward," not 100% migration
5. **No user impact** - Existing hardcoded messages work correctly

**Migration Rule (Going Forward):**
- ✅ **All NEW toast calls MUST use `messages.ts` constants** - no exceptions
- ✅ **Existing calls get migrated opportunistically** - when a file is touched for other reasons, migrate its toasts
- ✅ **No new hardcoded strings** - enforced via code review

**Alternative Fix (Future):**
- Dedicate focused sprint to migrate all 40+ files
- Use AST-based codemod to automate migration where possible
- Estimated effort: 2-3 days

**Priority:** Low (infrastructure complete, new code uses correct pattern)

---

## Guidelines for Adding Debt

1. **Document WHY** - What's the alternative? Why not fix it?
2. **Document COST** - What's the effort to fix properly?
3. **Document IMPACT** - Does it affect users? Security? Performance?
4. **Set PRIORITY** - Critical / High / Medium / Low
5. **Review Date** - When should this be reconsidered?

**Rule:** No "TODO" or "FIXME" comments in code. Either:
- Fix it now, OR
- Document it here with rationale, OR
- Delete it if it doesn't matter
