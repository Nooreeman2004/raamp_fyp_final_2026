# Content Generation (Creative Studio) — Internal Documentation

This document describes **everything related to content generation** in RAAMP: backend endpoints, request/response contracts, credit charging, brand-context usage, asset logging, and the frontend Creative Studio flow.

---

## 1. What “Content Generation” means in RAAMP

Content Generation is the **text + image** part of the Creative Studio:

- **Text**: captions, hashtags, WhatsApp messages, email messages (all generated via Gemini text model).
- **Images**: optional “generate 3 images” flow (Gemini text model generates a prompt, then Gemini image model generates images).

Video/Reel generation is a separate module under “Media Generation” (see section **9**).

---

## 2. Backend API surface (FastAPI)

### 2.1 Router

- **Router file**: `raamp-backend/presentation/routers/content_generation_router.py`
- **Prefix**: `/api/content`
- **Auth**: required (uses `get_current_user_email` dependency).

### 2.2 Endpoints

#### A) Generate content (one call)

- **Method/Path**: `POST /api/content/generate`
- **Auth**: required
- **Purpose**: generate a “complete marketing package” in one request (or a subset, via `content_type`).
- **Backend entrypoint**: `ContentGenerationUseCase.generate_social_content(...)`

#### B) Get brand context

- **Method/Path**: `GET /api/content/brand-context`
- **Auth**: required
- **Purpose**: return the brand voice + identity fields used to guide generation.

#### C) Platforms endpoint (note)

Static UI config endpoint.

- **Test reference**: `raamp-backend/tests/test_content_generation.py`
- **Status**: **implemented**
- **Method/Path**: `GET /api/content/platforms`
- **Auth**: not required (static config)
- **Purpose**: returns a list of supported platforms and their supported aspect ratios / generation types.

---

## 3. Request/response contracts (Pydantic schemas)

- **Schema file**: `raamp-backend/presentation/schemas/content_generation_schema.py`

### 3.1 Request schema

`ContentGenerationRequest`:

- **campaign_idea** (required, 10–1000 chars)
- **target_audience** (optional)
- **campaign_tone** (optional; overrides brand tone for this generation)
- **platform_type** (default `"post"`; `"post" | "story" | "reel"`)
  - If provided and valid, it selects the **prompt mode** in the text generation service.
  - If omitted/invalid at the API boundary, the router derives it from `aspect_ratio` (`9:16 → story`, else `post`).
- **aspect_ratio** (default `"1:1"`; `"1:1" | "9:16" | "4:5"`)
- **content_type** (optional; default `"all"`)
  - `"captions"`: captions + per-caption hashtags
  - `"hashtags"`: hashtag sets only
  - `"whatsapp"`: WhatsApp variants
  - `"emails"`: email variants
  - `"images"`: image generation only (returns images + asset IDs; other arrays are intentionally emptied)
  - `"all"`: generate all **text** types (default) (captions/hashtags/whatsapp/emails). Images are only generated when `content_type="images"`.
- **campaign_id** (optional; used to group generated outputs)

### 3.2 Response schema

`ContentGenerationResponse` returns:

- **brand_context**: `BrandContext` (business name, tagline, tone, theme, colors, etc.)
- **caption_variants**: 3 variants (each contains `caption`, `hashtags`, and may include `predicted_performance`)
- **hashtag_sets**: 3 sets (each has a unique `hashtag_id`)
- **whatsapp_variants**: 3 variants
- **email_variants**: 3 variants
- **message_variants**: legacy combined list (kept for backwards compatibility)
- **image_prompts**: list of prompts (or placeholders)
- **image_paths**: list of generated image URLs (only when `content_type="images"` triggers real image generation)
- **asset_ids**: list of asset IDs for generated images (usage tracking + asset library)
- **validation_warnings**: list of non-blocking warnings if brand-lock validation fails after bounded retries
- **logo_used** / **logo_warning**: optional transparency fields for image generation (logo fetch success/failure)
- **generated_at**: ISO timestamp

Important implementation note:
- The backend returns **IDs used for usage tracking**:
  - captions include `caption_id`
  - WhatsApp/Email include `message_id`
  - hashtag sets include `hashtag_id`
  - images return `asset_ids`

---

## 4. Backend architecture (service + use case)

### 4.1 Use case

- **File**: `raamp-backend/application/use_cases/content_generation_use_case.py`
- Responsibilities:
  - fetch brand context from DB (`BusinessRepository.get_by_user_id`)
  - validate inputs
  - enforce credits (`CreditService.check_and_deduct`)
  - call the AI service (`ContentGenerationService.generate_content`)

Credit charging currently happens here:

- `check_and_deduct(user_id, "caption_generation")` for non-image generation
- `check_and_deduct(user_id, "image_generation")` for `content_type="images"`

Brand-profile gating (before credits):

- The use case rejects generation with **HTTP 400** if required brand fields are missing:
  - `business_name`, `tagline`, `tone_of_voice`
- Error response includes `missing_fields` so the frontend can direct the user to complete their brand profile.

Example error (brand profile incomplete):

```json
{
  "detail": {
    "success": false,
    "error": "brand_profile_incomplete",
    "missing_fields": ["business_name", "tagline"],
    "message": "Your brand profile is incomplete. Please update your brand settings and try again."
  }
}
```

Credit failure:

- Credits are checked/deducted via `CreditService.check_and_deduct(...)`.
- When insufficient, the service raises an HTTP error (typically **402 Payment Required**) with a structured error payload.

### 4.2 Content generation service (Gemini text + orchestration)

- **File**: `raamp-backend/application/services/content_generation_service.py`
- Key points:
  - Uses **Google GenAI SDK** (`google.genai`) directly.
  - Requires `GEMINI_API_KEY`.
  - Model used for text generation:
    - `GEMINI_TEXT_MODEL` (default: `"gemini-3-flash-preview"`)
  - Builds a structured **JSON-only** prompt and requests `response_mime_type="application/json"`.
  - Normalizes LLM output to avoid common “JSON mode” shape drift:
    - `caption_variants` / `hashtag_sets` dict→list conversion
    - ensures at least **3 variants** exist
    - ensures caption hashtags have at least **5** tags
  - Supports platform prompts:
    - `"post"`, `"story"`, `"reel"`
  - **Aspect ratio → platform_type mapping** (router behavior):
    - `"9:16"` → `"story"`
    - everything else → `"post"`
  - **Brand-lock retries**:
    - After parsing Gemini JSON, the service performs a string-level brand-lock validation and will retry up to **2** times (bounded) before returning output with `validation_warnings`.

### 4.3 ML enrichment (captions)

Inside `ContentGenerationService.generate_content`, caption variants are optionally enriched via:

- `application/services/ml_enrichment_service.py` (`enrich_captions`)

Behavior:
- If ML model is available, it attaches `ml_score` and computes `best_caption_id`.
- If ML fails/unavailable, it gracefully skips and uses the existing `best_caption_id`.

### 4.4 Logging generated outputs (caption log repository)

The content generation service logs generated assets as “caption logs” (non-blocking; failures do not fail the request):

- Captions → `AssetTypeEnum.POST|STORY|REEL`
- Hashtag sets → `AssetTypeEnum.HASHTAG`
- WhatsApp → `AssetTypeEnum.WHATSAPP`
- Emails → `AssetTypeEnum.EMAIL`

This is used for **creative history** and usage tracking.

---

## 5. Image generation pipeline (Gemini text prompt → Gemini images → assets)

- **File**: `raamp-backend/application/services/image_generation_service.py`
- Trigger condition:
  - Only runs when `content_type == "images"` (set by frontend image generation section).

### 5.1 Env/config

- `GEMINI_API_KEY` (required)
- `GEMINI_TEXT_MODEL` (default `"gemini-3-flash-preview"`)
- `GEMINI_IMAGE_MODEL` (default `"gemini-3.1-flash-image-preview"`)

### 5.2 Prompt generation (brand-aware, campaign-first)

The prompt generator is intentionally strict:

- prioritizes **campaign idea theme** over generic brand context
- attempts to fetch `brand_logo_url` and pass it as a multimodal “logo reference” to Gemini
- includes strict **color constraints** in the brand prompt block (dominant palette must match brand colors; avoid off-brand palettes unless the campaign explicitly requires it)

Logo fetch transparency:

- Image generation returns `logo_used` and (when not used) a `logo_warning` string so the frontend can inform the user when logo reference could not be loaded.

### 5.3 Image generation strategies

It attempts two SDK methods (with retries) per variation:

- Strategy 1: `client.models.generate_content(... response_modalities=["TEXT","IMAGE"])` and save `inline_data`
- Strategy 2: `client.models.generate_image(...)`

### 5.4 Outputs + asset saving

- Images are written under `generated_images/<campaign_id>/variation_*.png`
- They are served by FastAPI static mount:
  - `/api/generated/...`
- Each generated image is saved as an asset:
  - uses `AssetRepository`
  - uploads to Cloudinary if configured/available
  - returns `asset_ids[]` for tracking

---

## 6. Credits / tier enforcement

- **File**: `raamp-backend/application/services/credit_service.py`
- Action costs (current):
  - `caption_generation`: **1**
  - `image_generation`: **2**
  - `video_generation`: **10**
  - (others exist for geo/trends modules)

Important notes:

- **Demo bypass**: `abdullah@gmail.com` is treated as Premium (no deduction).
- Premium users: unlimited access for metered actions.

Implementation note:
- The use case deducts:
  - **`caption_generation`** for `captions/hashtags/whatsapp/emails/all`
  - **`image_generation`** for `images`

---

## 7. Frontend: Creative Studio flow

### 7.1 Entry points

- **Page**: `raamp-frontend/src/pages/CreativeStudio.tsx`
- **Text generation API client**: `raamp-frontend/src/services/contentGenerationService.ts`

### 7.2 Generate Creative Brief

User flow:

- User writes a campaign idea.
- Selects:
  - `contentType`: `captions | hashtags | whatsapp | emails | all`
  - `aspectRatio`: `1:1 | 9:16 | 4:5`
- Clicks **Generate Creative Brief**:
  - calls `contentGenerationService.generateContent()` → `POST /content/generate`
  - stores full `ContentGenerationResponse` in `generatedContent`
  - uses backend’s `best_*_id` fields to badge the recommended variant in the UI

### 7.3 Variant selection + usage tracking

When user clicks “Copy & Select”, Creative Studio will call usage tracking:

- Captions: `assetService.markCaptionUsed(caption_id)`
- Hashtags: uses the same endpoint (stores `hashtag_id` into caption_id field server-side)
- WhatsApp/Emails: `assetService.markCaptionUsed(message_id)`

### 7.4 Standalone Image Generation section

Creative Studio’s “Image Generation” section calls the **same** `/api/content/generate` endpoint, but with:

- `content_type: "images"`
- `campaign_idea`: an “enriched prompt” built from user’s image details UI

It then reads:

- `image_paths[]` (URLs)
- `asset_ids[]` (usage tracking for downloads)

---

## 8. Environment variables (content-gen related)

Backend `.env` template: `raamp-backend/.env.example`

Required / commonly used:

- `GEMINI_API_KEY` (**required** for content + image generation)
- `GEMINI_TEXT_MODEL` (optional; defaults in code)
- `GEMINI_IMAGE_MODEL` (optional; defaults in code; used for image generation)

Optional (image hosting/asset access):

- Cloudinary variables (if you want generated images uploaded and publicly accessible):
  - `CLOUDINARY_CLOUD_NAME`
  - `CLOUDINARY_API_KEY`
  - `CLOUDINARY_API_SECRET`

---

## 9. Related module: Media Generation (Reels/Videos)

This is not “content generation” (text/images), but it is part of the same Creative Studio UX.

- **Backend router**: `raamp-backend/presentation/routers/media_generation_router.py`
- **Prefix**: `/api/media`
- **Frontend service**: `raamp-frontend/src/services/mediaGenerationService.ts`

Endpoints:

- `POST /api/media/generate-quick-reel`
- `POST /api/media/reels/generate-prompt`
- `POST /api/media/reels/generate`
- `POST /api/media/videos/generate-prompt`
- `POST /api/media/videos/generate`

Static serving:

- reels: mounted at `/api/reels` from `generated_reels/`
- videos: mounted at `/api/videos` from `generated_videos/`

---

## 10. Known gaps / mismatches

- **`GET /api/content/platforms`**: Implemented (static config response).
- **Docs vs actual routes mismatch**:
  - Some docs mention `/api/content-generation` and `/api/media-generation`, but the implemented routers are:
    - content generation: `/api/content/*`
    - media generation: `/api/media/*`
- **Credit charging granularity**: Implemented for `images` vs non-images (charges `image_generation` for images, `caption_generation` otherwise).
- **Image generation aspect ratio threading**: Implemented (request `aspect_ratio` is passed into the image generation pipeline).
- **Image prompt key/shape inconsistency**: Implemented (standardized to `image_prompts: List[str]` + backward compatible parsing).
- **“Reel” text mode reachability**: Implemented (client can send `platform_type="reel"`; backend still falls back to aspect_ratio mapping if invalid/omitted).
- **`best_hashtag_set_id`**: Implemented (lightweight deterministic heuristic scoring; no longer hardcoded to 1).

---

## 11. `/api/content/platforms` contract (UI config)

- **Method/Path**: `GET /api/content/platforms`
- **Auth**: not required (static UI config)
- **Response**: `{ "platforms": PlatformInfo[] }` where each `PlatformInfo` includes:
  - `id`, `name`, `description`, `guidelines`
  - `supported_generation_types`: e.g. `["post","story","reel"]`
  - `supported_aspect_ratios`: e.g. `["1:1","4:5","9:16"]`

Example response:

```json
{
  "platforms": [
    {
      "id": "instagram",
      "name": "Instagram",
      "description": "Best for visual-first marketing: feed posts, stories, and reels.",
      "guidelines": "Keep captions punchy. Use 5–15 hashtags. Prefer strong hooks and clear CTAs.",
      "supported_generation_types": ["post", "story", "reel"],
      "supported_aspect_ratios": ["1:1", "4:5", "9:16"]
    }
  ]
}
```

