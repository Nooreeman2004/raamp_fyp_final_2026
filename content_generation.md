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

The test suite references `GET /api/content/platforms`, but **it is not implemented** in `content_generation_router.py` currently.

- **Test reference**: `raamp-backend/tests/test_content_generation.py`
- **Status**: **missing endpoint** (documentation only; not implemented here)

---

## 3. Request/response contracts (Pydantic schemas)

- **Schema file**: `raamp-backend/presentation/schemas/content_generation_schema.py`

### 3.1 Request schema

`ContentGenerationRequest`:

- **campaign_idea** (required, 10–1000 chars)
- **target_audience** (optional)
- **campaign_tone** (optional; overrides brand tone for this generation)
- **aspect_ratio** (optional; `"1:1"` default; `"9:16"` vertical; `"4:5"` portrait)
- **content_type** (optional; default `"all"`)
  - `"captions"`: captions + per-caption hashtags
  - `"hashtags"`: hashtag sets only
  - `"whatsapp"`: WhatsApp variants
  - `"emails"`: email variants
  - `"images"`: image generation only (returns images + asset IDs; other arrays are intentionally emptied)
  - `"all"`: generate all types (default)
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

- `check_and_deduct(user_id, "caption_generation")`

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
- can optionally fetch `brand_logo_url` and pass it as a multimodal “logo reference” to Gemini

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
- Content generation use-case currently deducts **`caption_generation`** even when generating non-caption types; image generation service itself does **not** currently deduct `image_generation` (it relies on upstream orchestration).

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

- **`GET /api/content/platforms`** is referenced by tests but not implemented in the router.
- **Docs vs actual routes mismatch**:
  - Some docs mention `/api/content-generation` and `/api/media-generation`, but the implemented routers are:
    - content generation: `/api/content/*`
    - media generation: `/api/media/*`
- **Credit charging granularity**:
  - the use case always deducts `caption_generation` today; if you want separate costs for images/messages-only, you’d likely want to charge by `content_type` (and add `image_generation` deduction when `content_type="images"`).
- **Image generation does not honor requested aspect ratio end-to-end**:
  - Frontend sends `aspect_ratio` when generating images.
  - The backend image generation pipeline supports aspect ratios internally, but the content-gen path does not pass the requested ratio through, so output isn’t reliably controlled by `1:1 / 4:5 / 9:16`.
- **Image prompt key/shape inconsistency**:
  - The LLM prompt inside `ContentGenerationService` asks for `image_generation_prompts` as a list of objects (`{id, prompt}`),
  - but the API schema/response path uses `image_prompts: List[str]`.
  - Result: image-prompt data can be ignored or replaced by placeholders depending on the exact LLM output.
- **“Reel” text mode is not reachable from `/api/content/generate`**:
  - The router only maps aspect ratio to `platform_type="story"` (when `9:16`) or `"post"` (otherwise).
  - There is no request field that selects `"reel"` prompt behavior for text generation in this endpoint.
- **`best_hashtag_set_id` is effectively a placeholder**:
  - Response includes `best_hashtag_set_id`, but backend does not compute it (it defaults to `1` in the router response building).

