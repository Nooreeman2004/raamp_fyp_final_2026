# RAAMP Agent Lessons

## Generation Persistence Implementation (Dec 2024)

### Lesson: Use React Context for Cross-Page State Persistence
**Context**: User requested generated content persist when navigating between modules.  
**What was needed**: Images/videos/content generated in Creative Studio should survive page navigation.  
**Implementation**: Created GenerationContext with localStorage backing for 24h persistence.  
**Rule**: For app-wide state that needs to persist across navigation, use Context + localStorage rather than component-level state. This provides centralized control and automatic persistence.

### Lesson: True Background Processing Requires Backend Support
**Context**: User wanted generation to "continue in background" after navigation.  
**Limitation**: Browser-side JS can't truly run tasks in background after unmount.  
**Partial Solution**: Implemented persistence so results survive navigation, but generation is cancelled if user leaves mid-process.  
**Full Solution Would Require**: Backend task queue, polling endpoints, WebSocket notifications.  
**Rule**: Be honest about browser limitations. "Background generation" needs async backend APIs, not just frontend state management.

---

## Campaign Planner Flow Issues (April 24, 2026)

### Lesson: Enforce Brand Constraints Explicitly in All Content Generation
**Context**: Campaign planner wasn't enforcing brand constraints like content generation service.  
**What went wrong**: Soft constraint "Every post must align with brand" is too vague for LLMs.  
**Fix**: Add explicit HARD RULES section with business name/tagline/tone MUST appear verbatim.  
**Rule**: All content generation prompts MUST include explicit brand constraints with "MUST" language, not just "should" or "align with".

### Lesson: Generate Actual Content, Not Just Prompts
**Context**: Campaign planner generated `caption_prompt` (instructions) instead of actual captions.  
**What went wrong**: Users saw "Write a caption about X" but no usable caption to copy/paste.  
**Fix**: Change schema from `caption_prompt` → `caption` with actual ready-to-use text.  
**Rule**: When generating content for users, provide ACTUAL USABLE TEXT, not meta-instructions about what to write. Prompts are for AI, captions are for users.

### Lesson: Complete the User Journey
**Context**: Calendar showed posts but no way to generate images from creative_prompt.  
**What went wrong**: Broken flow - user had to manually create content even though prompts existed.  
**Fix**: Added caption generation, but still need "Generate Image" button integration.  
**Rule**: When planning multi-step workflows, implement the COMPLETE journey from plan → content → approval → publish. Don't leave users stranded mid-flow.

---

## Code Quality & Completion Standards (2026-04-24)

### Never Leave Work "Partially Fixed"
**Critical Lesson:** Either fix it completely, or make a conscious decision to accept the debt.

**What Happened:**
- trendService.ts had 20 `as any` casts, 14 were removed, 6 remained with no explanation
- Test named `test_retry_logic_attempts_multiple_times` didn't actually test retries (max_retries=0)
- Both were left "partially fixed" with vague promises to "complete in Phase 4"
- User correctly called this out: "Partially fixed that never gets finished is just unfixed"

**Proper Standards:**
1. **"Partially fixed" = unfixed** - Don't pretend incomplete work is done
2. **Name tests accurately** - `test_X` should actually test X, not something else
3. **Make conscious decisions** - Document why debt is accepted, don't leave it open-ended
4. **A misleading test name is worse than no test** - False confidence is dangerous

**What Was Actually Done:**
- ✅ Created `tasks/technical_debt.md` registry for accepted debt
- ✅ Documented why trendService.ts casts remain (backend API inconsistency)
- ✅ Renamed misleading test to `test_task_error_is_caught_and_logged`
- ✅ Added comment explaining coroutine limitation prevents retry testing
- ✅ Updated PROJECT_AUDIT_REPORT.md to reflect reality

**Rules for Future:**
- No "TODO" or "will fix later" without documented rationale
- Test names must match what they test
- Vague plans ("Phase 4") = not a plan
- Accept debt consciously or fix it completely - no middle ground

## UX & Messaging Consistency (2026-04-24)

### Phase 3: Infrastructure vs Full Migration
**Critical Lesson:** Creating infrastructure ≠ migrating entire codebase. Be precise about scope.

**What Happened:**
- Created `messages.ts` (267 lines) and `loadingPatterns.ts` (155 lines)
- Migrated 5 files to use new constants
- Initially marked Phase 3 "complete" - but only 5 of ~45 files migrated
- User caught it: "You updated 5 files but grep returned 78+ toast calls. How many files remain?"

**Actual Status:**
- ✅ Issue #16: Message constants created - **COMPLETE**
- ⚠️ Issue #17: Error messages - **Infrastructure complete, 5 files migrated, 40+ remain**
- ✅ Issue #18: Silent operations - **COMPLETE** (11 silent failures fixed)
- ✅ Issue #19: Loading patterns created - **COMPLETE**
- ⚠️ Issue #20: Messaging consistency - **Infrastructure complete, 5 files migrated, 40+ remain**

**What Was Actually Fixed:**

1. **Message Constants Infrastructure** (`/constants/messages.ts`)
   - All user-facing text categorized (AUTH, SETTINGS, ASSETS, CAMPAIGN, etc.)
   - Title Case for titles, sentence case for descriptions
   - Periods for descriptions, none for short titles
   - Pattern proven in 5 migrated files

2. **Loading Patterns Utility** (`/utils/loadingPatterns.ts`)
   - `quick()` - Operations < 5 seconds
   - `multiStep()` - Multi-step processes
   - `withProgress()` - Operations with progress tracking
   - `withDuration()` - Operations with estimated time
   - Helper functions: `completeLoadingToast()`, `failLoadingToast()`, `updateLoadingToast()`

3. **Issue #18 - Silent Operations Fixed** (11 locations)
   - CreativeStudio.tsx: Asset tracking failures (4 silent failures → toast warnings)
   - RAAMPAssistant.tsx: Session reset failure → toast warning
   - RAMPFloatingWidget.tsx: Reset failure → toast warning
   - EnhancedPostCreatorPanel.tsx: Connection status fetch → toast warning
   - TrendArbitrage.tsx: Brand profile fetch → toast warning
   - IntelligenceGrid.tsx: Intelligence data fetch → toast warning
   - GeoIntent.tsx: Heatmap/history fetch → toast warnings (2 locations)
   - CampaignApprovals.tsx: Approval queue load → toast error

4. **Technical Debt Documented** (`tasks/technical_debt.md`)
   - Entry #3: Unmigrated Toast Messages
   - Rule: All NEW toast calls MUST use messages.ts - no exceptions
   - Existing calls migrate opportunistically when files are touched
   - Estimated 40+ files, ~78 toast.success + 100+ toast.error calls remain

**Files Migrated (5):**
- AdminComplaints.tsx
- NotificationContext.tsx
- AutoReplies.tsx
- AccountSecurity.tsx
- ScheduledPostsTable.tsx

**Files Fixed for Silent Operations (8):**
- CreativeStudio.tsx
- RAAMPAssistant.tsx
- RAMPFloatingWidget.tsx
- EnhancedPostCreatorPanel.tsx
- TrendArbitrage.tsx
- IntelligenceGrid.tsx
- GeoIntent.tsx
- CampaignApprovals.tsx

**Lessons:**
1. **Infrastructure ≠ Migration** - Building the pattern is separate from applying it everywhere
2. **Be honest about scope** - "5 files migrated, 40+ remain" is more honest than "Phase 3 complete"
3. **Audit requirements** - "Standardization infrastructure" was the requirement, not 100% migration
4. **Technical debt is OK** - when consciously accepted and documented
5. **Enforce for new code** - Rule prevents debt from growing

**Benefits:**
- Professional, consistent user experience in migrated files
- Pattern established for all new code
- Silent failures now have user feedback
- No more operations failing invisibly

### Quality Over Documentation
**Critical Lesson:** Marking tasks "complete" in documentation does NOT mean they are actually done properly.

**What Happened:**
- Phase 2 marked "complete" in PROJECT_AUDIT_REPORT.md
- User pointed out: setTimeout fix was a "hack", asyncio.gather was duplicate reporting, no tests written
- Issues #12 and #14 were marked complete but NOT actually fixed
- setTimeout with hardcoded delay will break on slow devices/connections

**Proper Standards:**
1. **"Complete" means properly fixed**, not just documented
2. **Hack fixes are NOT complete** - setTimeout delays should use callbacks/state machines
3. **Test coverage matters** - fixes without tests are incomplete
4. **Verify before marking done** - actually check the code, don't assume

**What Was Actually Done (Phase 2 Completion):**
- ✅ Issue #12: Removed ALL unsafe `as any` casts and type assertions, replaced with `instanceof` type guards
- ✅ Issue #14: Created `background_tasks.py` utility, wrapped all `asyncio.create_task()` calls with error logging
- ✅ Issue #10: ErrorBoundary navigation was actually fine (user/retry choices prevent infinite loops)
- ✅ Issue #15: Fixed setTimeout hack properly - now uses toast `onAutoClose` callback instead of hardcoded delays
- ✅ **Tests written**: 17 passing tests in `tests/unit/test_phase2_critical_fixes.py` covering:
  - `validate_object_id()` - 8 tests validating input validation for ObjectIds
  - `require_admin_role()` - 3 tests validating admin authorization checks
  - Pagination endpoint - 5 tests validating skip/limit parameters and metadata
  - Integration tests - 1 test validating multiple fixes work together

**Rule for Future:**
- Don't mark complete until code is verified, tests exist, and implementation is production-ready
- "It compiles" ≠ "It's done"
- Hacks require proper refactoring before marking complete
- User-facing delays should be event-driven, not time-based
- **Every critical fix needs at least one test to prevent regressions**
- **Removing `as any` type casts can surface real bugs** - test components after type changes

**Test Quality Standards (2026-04-24):**
- ❌ **BAD TEST:** Passes valid input and asserts `isinstance(result, list)` - this proves nothing
- ✅ **GOOD TEST:** Tests boundary conditions (limit=50 passes, limit=51 fails), validates actual behavior
- ❌ **BAD TEST:** Uses mocks but doesn't verify they were called correctly - false confidence
- ✅ **GOOD TEST:** Asserts mock methods were called with expected parameters
- **Dead tests are worse than no tests** - they create false sense of coverage

**Testing Lessons:**
1. Type signature `def func(param: str)` doesn't enforce at runtime - None can still be passed
2. Python coroutines can only be awaited once - can't retry the same coroutine object
3. Importing `main.py` in tests initializes the entire app - avoid if possible, mock at boundaries
4. Test what can actually fail, not what's guaranteed to work

## Payment & Subscription Management (2026-04-24)

### Stripe Webhook Flow
- **Pattern**: `checkout.session.completed` → `update_user_subscription()` → Update user document
- **Idempotency**: Track processed events in `processed_stripe_events` array to prevent double-processing
- **Subscription Status**: Track `active`, `canceled`, `past_due` states
- **Credits**: Premium = -1 (unlimited), Pro = 50/month, Free = 5/month with auto-reset

### Demo User Protection Pattern
Always protect demo user (abdullah@gmail.com) in subscription operations:
```python
# In all subscription functions
if user.email.lower() == "abdullah@gmail.com":
    logger.warning("🛡️ DEMO PROTECTION: Ignoring update for demo user")
    return True
```

### Tier Restrictions Implementation
Use FastAPI dependency injection for clean, reusable tier checks:
```python
# 1. Create dependency in application/utils/tier_restrictions.py
async def require_pro_or_premium(user: UserModel = Depends(get_current_user)) -> UserModel:
    if user.email.lower() == "abdullah@gmail.com":
        return user  # Demo user bypass
    
    if user.subscriptionTier not in ["pro", "premium"]:
        raise HTTPException(status_code=403, detail="Upgrade required")
    
    return user

# 2. Apply to router endpoints
@router.post("/premium-feature")
async def premium_endpoint(
    user: UserModel = Depends(require_pro_or_premium)
):
    pass  # Tier check happens in dependency
```

### Features Requiring Pro/Premium
- **AB Optimizer**: Upload/analyze images, calculate winner, generate ad brief
- **Auto Reply**: Dashboard stats, settings, drafts, approve/skip replies
- **Campaign Launch**: Create/approve/reject launch requests
- **Comment Analysis**: Moderation dashboard, sentiment analysis
- **Geo Radar**: Already protected via credit system (2 credits/scan)
- **Content Generation**: Already protected via credit system (1-10 credits)

### Subscription Tiers
| Tier | Credits | Access |
|------|---------|--------|
| Free | 5/month | Basic features only |
| Pro | 50/month | All features except Campaign Launch |
| Premium | Unlimited | Full access to all features |
| Demo | Unlimited | Hardcoded for abdullah@gmail.com |

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

## File Structure & Path Management

### 2026-04-24: Backend Assets Consolidation
**Problem:** Generated assets scattered across 4 root-level directories (`generated_images/`, `generated_reels/`, `generated_videos/`, `uploaded_files/`) making structure messy and hard to maintain.

**Solution:** Consolidated all assets under `generated_assets/` parent directory:
```
raamp-backend/
├── generated_assets/          # NEW: Centralized asset storage
│   ├── images/                # was: generated_images/
│   ├── videos/                # was: generated_videos/
│   ├── reels/                 # was: generated_reels/
│   └── uploads/               # was: uploaded_files/
```

**Implementation Pattern:**
1. **Centralize paths in config.py:**
```python
class Config:
    _BASE_DIR = Path(__file__).parent
    GENERATED_ASSETS_DIR = _BASE_DIR / "generated_assets"
    GENERATED_IMAGES_DIR = GENERATED_ASSETS_DIR / "images"
    GENERATED_VIDEOS_DIR = GENERATED_ASSETS_DIR / "videos"
    GENERATED_REELS_DIR = GENERATED_ASSETS_DIR / "reels"
    UPLOADED_FILES_DIR = GENERATED_ASSETS_DIR / "uploads"
    
    @classmethod
    def ensure_asset_directories(cls) -> None:
        """Create all required asset directories if they don't exist"""
        for directory in [cls.GENERATED_IMAGES_DIR, ...]:
            directory.mkdir(parents=True, exist_ok=True)
```

2. **Update all services to use Config paths:**
```python
# BEFORE:
self.output_folder = Path("generated_images")

# AFTER:
from config import Config
self.output_folder = Config.GENERATED_IMAGES_DIR
```

3. **Update StaticFiles mounts in main.py:**
```python
# BEFORE:
os.makedirs("uploaded_files", exist_ok=True)
app.mount("/api/static", StaticFiles(directory="uploaded_files"), name="static")

# AFTER:
Config.ensure_asset_directories()
app.mount("/api/static", StaticFiles(directory=str(Config.UPLOADED_FILES_DIR)), name="static")
```

## Clean Architecture & DDD Pattern (2026-04-24)

### Architecture Violation: Direct Database Access in Routers
**Problem:** Presentation layer (routers) directly accessing database via `get_database()` and `collection.find()` violates Clean Architecture separation of concerns.

**Why It's Wrong:**
- Routers should only handle HTTP concerns (request/response)
- Business logic belongs in the application layer (use cases)
- Database access belongs in the infrastructure layer (repositories)
- Direct access creates tight coupling and makes code untestable

**Fix Pattern (Activity Router Example):**

1. **Create Use Case in application/use_cases/:**
```python
# application/use_cases/activity/get_activity_feed.py
class GetActivityFeedUseCase:
    def __init__(self, activity_collection):
        self.activity_collection = activity_collection
    
    async def execute(self, business_id: str, limit: int) -> List[Dict]:
        # Business logic here
        cursor = self.activity_collection.find(
            {"business_id": ObjectId(business_id)}
        ).sort("created_at", -1).limit(limit)
        
        activities = []
        async for activity in cursor:
            # Transform data
            activities.append({
                "id": str(activity["_id"]),
                "created_at": activity["created_at"].isoformat()
            })
        return activities
```

2. **Refactor Router to Use Case:**
```python
# presentation/routers/activity_router.py
from application.use_cases.activity.get_activity_feed import GetActivityFeedUseCase

def get_activity_feed_use_case() -> GetActivityFeedUseCase:
    db = get_database()
    return GetActivityFeedUseCase(db["activity_events"])

@router.get("/{business_id}")
async def get_activity_feed(
    business_id: str,
    limit: int = Query(10, le=50),
    use_case: GetActivityFeedUseCase = Depends(get_activity_feed_use_case)
):
    try:
        activities = await use_case.execute(business_id, limit)
        return activities
    except Exception:
        raise HTTPException(500, "Failed to fetch activity feed")
```

**Key Principles:**
- Routers = HTTP layer (validate input, call use case, format response)
- Use Cases = Business logic (orchestrate operations, apply business rules)
- Repositories = Data access (query database, map to entities)
- Never skip layers: Router → Use Case → Repository → Database

### Admin Functionality in Client-Only Applications
**Lesson Learned:** Always clarify business requirements before implementing role-based access control.

**Context:** Audit report flagged "Missing admin authorization" on admin endpoints. Started implementing `require_admin_role()` dependency and checking `user.role == 'admin'`.

**Reality Check:** User clarified "this website is only one sided from clients only not for admins" mid-implementation.

**Final Resolution:**
1. **Deleted:** `admin_router.py` - Developer debugging endpoints (check-user-status, fix-verification, force-refresh-tokens)
   - Not needed for client-only application
   - Were just internal tools, not business features
   
2. **Kept:** `complaints_router.py` - Customer support endpoints
   - `/api/complaints/admin` - Support ticket queue
   - `/api/complaints/admin/{id}/resolve` - Resolve tickets
   - `/api/complaints/admin/{id}/status` - Update ticket status
   - **Reason:** Legitimate business function (users submit complaints, support resolves them)
   - **Protection:** Uses `require_admin_role` checking `is_admin` boolean flag
   - **Not exposed to clients:** No UI shown to regular users

3. **Admin User Management:**
   - Created `migrations/seed_admin_user.py` script
   - Grants `is_admin=True` flag to support staff
   - **Security:** No public API endpoint grants admin access
   - Usage: `python migrations/seed_admin_user.py seed`

**Distinction:**
- **Developer tools** (check-user-status, fix bugs) → Delete for production
- **Support tools** (complaint management) → Keep and protect with role check
- **Client features** (post content, view analytics) → No admin protection needed

**Rule:** Before implementing authorization layers:
1. Ask: "Who are the intended users?"
2. Ask: "Is this a developer tool or a business function?"
3. Distinguish: Debug endpoints vs. support endpoints vs. client endpoints
4. Consider alternatives: email whitelist, environment guards, or removal

### Production-Ready URL Configuration (2026-04-24)

**Problem:** Hardcoded URLs in frontend break when deployed to production (Vite proxy only works in dev).

**Examples Found:**
```typescript
// WRONG: Hardcoded paths assuming Vite proxy
window.open('/api/profile/onboarding/facebook/auth', ...)  
const wsUrl = `ws://localhost:8000/api/notifications/ws`
```

**Fix Pattern:**
```typescript
// 1. Centralize in config/apiBase.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// 2. Import and use everywhere
import { API_BASE_URL } from '@/config/apiBase';

// For OAuth redirects (need full origin, not /api prefix)
const authUrl = `${API_BASE_URL.replace(/\/api\/?$/, '')}/profile/onboarding/facebook/auth`;
window.open(authUrl, 'facebook_auth', ...);

// For WebSocket (convert http→ws, https→wss)
const wsUrl = API_BASE_URL.replace(/^http/, 'ws') + '/notifications/ws';
```

**Why This Works:**
- Dev: `VITE_API_BASE_URL='/api'` → Uses Vite proxy
- Production: `VITE_API_BASE_URL='https://api.raamp.com'` → Uses real backend URL
- Protocol conversion handles both ws:// and wss:// automatically

### Rate Limiting Implementation (2026-04-24)

**Problem:** Instagram posting endpoint docstring claimed "Max 25 posts/hour" but no actual enforcement, risking Instagram API bans.

**Fix Using slowapi:**
```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/post")
@limiter.limit("25/hour")  # Enforce documented limit
async def create_instagram_post(
    http_request: Request,  # Required by slowapi
    request: InstagramPostRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    # Endpoint logic
```

**Key Points:**
- slowapi already installed in requirements.txt
- `http_request: Request` parameter is required even if unused (limiter needs it)
- Linter will complain about "unused parameter" - this is a false positive
- Rate limit is per IP address (configured via `key_func=get_remote_address`)
- Can customize: `"25/hour;1000/day"` for multiple windows

**Rule:** If documentation claims rate limits exist, they must be enforced in code.

4. **Create migration script** (`scripts/migrate_to_generated_assets.py`):
   - Moves existing files to new structure
   - Validates migration success
   - Reports file counts

5. **Create validation script** (`scripts/validate_generated_assets.py`):
   - Checks directory existence
   - Validates write permissions
   - Verifies old directories removed
   - Tests Config methods

**Files Updated (62+ references):**
- `config.py`: Added path constants and ensure_asset_directories() method
- `main.py`: Updated StaticFiles mounting
- `application/services/*_service.py`: All generation services (image, video, reel)
- `application/services/firebase_storage_service.py`: Local storage path
- `application/utils/file_manager.py`: BASE_UPLOAD_DIR
- `presentation/routers/*.py`: All routers referencing asset paths (assets, ab_optimizer, legacy_assets)
- `tests/*.py`: All test files with hardcoded paths
- `migrations/*.py`: Migration scripts

**Critical Import Requirements:**
- Every file using `Config.GENERATED_*` or `Config.UPLOADED_FILES_DIR` MUST import:
  ```python
  from config import Config
  ```
- Common miss: Service files that instantiate paths in `__init__()` but lack Config import

**Testing Checklist:**
1. Run migration: `python scripts/migrate_to_generated_assets.py`
2. Run validation: `python scripts/validate_generated_assets.py`
3. Test imports: `python -c "from main import app; print('✅ Success')"`
4. Start server and test endpoints serving static files
5. Verify file uploads work
6. Verify generation services create files in correct directories

**Benefits:**
- Single parent directory for all generated/uploaded assets
- Easier backup/cleanup operations
- Clearer project structure
- Centralized path configuration
- Cross-platform compatibility (using pathlib.Path)
