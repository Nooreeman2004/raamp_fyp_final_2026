# Data Architecture

## 1. Overview of Data Architecture

The RAAMP (Revolutionary AI-Powered Autonomous Marketing Platform) system implements a multi-layered data architecture designed to support AI-driven marketing automation for local businesses. The architecture follows a clean separation of concerns with distinct layers for data ingestion, processing, storage, and retrieval.

### Data Flow Pipeline

```
External APIs → Backend Services → Processing Layer → MongoDB Storage → API Responses
     ↓              ↓                    ↓                  ↓              ↓
(Trends, Weather, (FastAPI Routes)  (AI Models,      (Collections)   (JSON/REST)
 Social Media,                       Transformations,
 Maps, Payments)                     Aggregations)
```

The system processes data through the following stages:

1. **Input Stage**: User inputs, API webhooks, external data sources
2. **Processing Stage**: AI inference, trend detection, content generation, signal aggregation
3. **Storage Stage**: MongoDB collections with Beanie ODM
4. **Output Stage**: REST API responses, real-time notifications, scheduled posts

---

## 2. Data Sources

### 2.1 User-Generated Data
- User registration and profile information
- Campaign ideas and marketing preferences
- Business details (name, location, specialties, brand colors)
- Manual content uploads (images, captions)
- Chat interactions with AI assistant

### 2.2 External API Data Sources
- **Google Trends API**: Search interest time-series, related queries, rising queries, geographic distribution
- **SerpAPI**: Alternative trends provider with fallback support
- **PyTrends**: Local trends data provider
- **Tomorrow.io Weather API**: Weather conditions, forecasts for geo-intent analysis
- **Google Maps Places API**: Business location data, nearby places, place types, crowd density signals
- **Facebook Graph API**: Page data, post metrics, comment events, user profiles
- **Instagram Graph API**: Media data, story metrics, comment events, business account information
- **Stripe API**: Payment events, subscription status, billing profiles
- **Cloudinary API**: Image hosting and transformation
- **Google Gemini API**: AI text generation for captions, hashtags, campaign messages
- **OpenAI API**: Alternative AI model support for content generation

### 2.3 Webhook Data Sources
- **Meta Webhooks**: Real-time comment events from Facebook and Instagram
- **Stripe Webhooks**: Payment confirmations, subscription updates, invoice events

### 2.4 Static Data Assets
- **FAQ Embeddings**: Pre-processed knowledge base chunks (`raamp_chunks.json`, `raamp_faq_chunks_complete.pkl`)
- **Kaggle Datasets**: Spam detection training data (SMS, YouTube comments)
- **Industry Templates**: Business domain-specific prompt templates

---

## 3. Data Storage

### 3.1 Primary Database: MongoDB

**Connection Configuration**:
- Database Name: `raamp_db`
- Connection: MongoDB Atlas (cloud) or local MongoDB instance
- ODM Framework: Beanie (async document mapper built on Motor and Pydantic)

### 3.2 MongoDB Collections

#### User Management Collections
- **users**: User accounts, authentication, profile data, subscription tiers, billing information
- **pending_verifications**: Email verification OTP codes with expiry timestamps
- **profile_edit_verifications**: OTP codes for profile modification approval
- **password_resets**: Password reset tokens and expiry tracking
- **account_deletion_verifications**: Account deletion confirmation tokens

#### Business & Location Collections
- **business_domains**: Business categories (restaurant, cafe, bakery, fashion, tech, etc.)
- **businesses**: Business profiles with Google Maps place details, location coordinates, specialties

#### Social Media Integration Collections
- **facebook_connections**: OAuth tokens, page access tokens, page metadata
- **instagram_connections**: OAuth tokens, business account IDs, profile metadata
- **social_media_accounts**: Unified social account management
- **oauth_states**: OAuth flow state management with CSRF protection

#### Content & Campaign Collections
- **instagram_posts**: Published Instagram posts with metadata
- **scheduled_instagram_posts**: Scheduled posts with timing and status
- **instagram_stories**: Story posts with 9:16 format metadata
- **facebook_posts**: Published Facebook posts
- **scheduled_facebook_posts**: Scheduled Facebook posts
- **assets**: Generated and uploaded media files (images, videos, reels)
- **caption_logs**: AI-generated caption history with performance tracking
- **campaign_drafts**: Draft campaigns created via "Create Pack" feature
- **campaign_plans**: Brand-driven campaign planning with multi-post sequences
- **campaign_planned_posts**: Individual posts within campaign plans
- **campaign_launch_requests**: Approval-gated campaign launches from trend arbitrage
- **campaign_logs**: Geo-intent campaign execution logs
- **campaign_briefs**: AI-generated campaign briefs with targeting recommendations
- **posting_logs**: Unified posting activity logs across platforms

#### Trend Intelligence Collections
- **trend_signals**: Google Trends data with search interest time-series, related queries, arbitrage scores
- **trend_detections**: Spike detection results with lifecycle stage classification
- **trend_watchlists**: User-tracked keywords for continuous monitoring
- **trend_retry_jobs**: Failed trend fetch retry queue
- **trend_caches**: Cached trends data with TTL expiry (1-hour default)
- **trend_ai_analyses**: AI-generated trend interpretations and recommendations
- **trend_activities**: User activity logs for trend interactions

#### Geo-Intent Engine Collections
- **heat_scores**: Geographic heat scores with urgency classification (0-100 scale)
- **campaign_logs**: Geo-intent scan results with signal breakdowns (trends, places, weather)

#### Auto-Reply System Collections
- **comment_events**: Raw comment events from Meta webhooks (Facebook/Instagram)
- **auto_reply_decisions**: Intent classification results with policy actions
- **auto_reply_drafts**: Review-required reply suggestions with expiry
- **auto_reply_sent**: Successfully posted replies with idempotency tracking
- **auto_reply_settings**: User-configured auto-reply policies and templates
- **social_escalation_tickets**: Flagged comments requiring manual review

#### Analytics & Performance Collections
- **conversion_events**: Tracked conversion actions (clicks, purchases, sign-ups)
- **campaign_performance**: Aggregated campaign metrics with ROI calculations
- **comment_analyses**: Sentiment analysis results for social media comments

#### Notification & Communication Collections
- **notifications**: In-app notifications with type classification and priority
- **notification_settings**: User notification preferences per channel
- **chat_sessions**: Chatbot conversation sessions with message history
- **chat_interactions**: Individual chat messages with role and timestamp

#### Billing & Subscription Collections
- **billing_profiles**: Stripe customer profiles with payment methods
- **wallets**: User credit balances and transaction history
- **security_settings**: User security preferences and 2FA settings

#### System Monitoring Collections
- **job_execution_logs**: Background job health monitoring with success/failure tracking
- **ab_test_images**: A/B test variants with performance metrics

#### Support & Feedback Collections
- **complaints**: User-submitted complaints with status tracking
- **consultation_requests**: Business consultation booking requests

### 3.3 File Storage

**Base Directory**: `raamp-backend/generated_assets/`

**Subdirectories**:
- `images/`: AI-generated and uploaded images
- `videos/`: Generated video content
- `reels/`: Instagram Reels content
- `uploads/`: User-uploaded files

**Storage Strategy**: Local filesystem with Cloudinary CDN integration for public URLs

### 3.4 Vector Storage (Embeddings)

**Location**: `raamp-backend/data/embeddings_data/`

**Files**:
- `raamp_chunks.json`: 80 FAQ chunks with metadata (category, keywords, user level)
- `raamp_faq_chunks_complete.pkl`: Serialized embeddings for semantic search

**Purpose**: RAG (Retrieval-Augmented Generation) for chatbot knowledge base

---

## 4. Data Processing Layer

### 4.1 Trend Detection Pipeline

**Input**: User niche, category, location, timeframe
**Processing Steps**:
1. Keyword generation from niche mapping
2. Location code conversion (country name → ISO 3166-1 alpha-2)
3. Timeframe conversion to Google Trends format
4. Parallel API calls to SerpAPI (primary) and PyTrends (fallback)
5. Time-series data validation (non-empty dates, matching lengths, non-zero values)
6. Z-score spike detection with rolling window (14-day default)
7. EWMA smoothing (alpha=0.3)
8. Lifecycle stage classification (Emerging, Breakout, Mainstream, Saturated, Declining)
9. Arbitrage score calculation (Velocity / Saturation)
10. Hashtag extraction from related queries

**Output**: TrendSignal entity with computed metrics and status

### 4.2 Geo-Intent Signal Aggregation

**Input**: Business location (lat/lng), radius, keywords, indoor/outdoor flag
**Processing Steps**:
1. Parallel signal ingestion:
   - **Trends Score**: Keyword search interest normalization (0-1)
   - **Places Score**: Nearby POI density calculation (0-1)
   - **Weather Score**: Condition favorability scoring (0-1)
2. Weighted heat score computation: `(trends × 0.35 + places × 0.40 + weather × 0.25) × 100`
3. Urgency classification: Critical (90+), High (61-89), Medium (31-60), Low (0-30)
4. Persona split calculation using POI types, time of day, day of week, weather, trends
5. Radar feed generation with real-time signal notifications

**Output**: Heat score (0-100), urgency label, persona distribution, radar feed

### 4.3 Content Generation Pipeline

**Input**: Campaign idea, brand context, target audience, platform type (post/story/reel)
**Processing Steps**:
1. Brand context enrichment (business name, tagline, tone, colors, specialties)
2. Industry-specific prompt injection (restaurant/food/fashion/tech templates)
3. System prompt selection based on platform type
4. Google Gemini API call with JSON schema enforcement
5. Brand-lock validation (business name and tagline verbatim presence)
6. Retry loop (up to 3 attempts) for validation failures
7. Image generation prompt creation
8. Caption logging with asset type classification

**Output**: 3 caption variants, 3 hashtag sets, 3 WhatsApp messages, 3 email campaigns, 3 image prompts

### 4.4 Auto-Reply Decision Pipeline

**Input**: Comment event from Meta webhook
**Processing Steps**:
1. Deduplication using `dedupe_key` (platform + comment_id + hash)
2. Intent classification (pricing/hours/location/complaint/spam)
3. Confidence scoring (0-1)
4. Risk level assessment (low/medium/high)
5. Policy action determination (auto_reply/needs_review/skip)
6. Draft generation for review-required comments
7. Idempotency check before posting reply
8. Reply normalization and hash generation

**Output**: AutoReplyDecision, optional AutoReplyDraft, optional AutoReplySent

### 4.5 Comment Sentiment Analysis

**Input**: Social media comments
**Processing Steps**:
1. Text preprocessing (lowercasing, punctuation removal)
2. Spam detection using Kaggle-trained models
3. Sentiment classification (positive/negative/neutral)
4. Toxicity scoring
5. Intent extraction

**Output**: CommentAnalysis entity with sentiment scores

---

## 5. Data Flow

### 5.1 User Registration Flow
```
User Input (email, username, password) 
  → Password hashing (bcrypt)
  → UserModel creation
  → OTP generation (6-digit)
  → PendingVerificationModel creation
  → Email sending (Mailtrap SMTP/API)
  → MongoDB insert
  → JWT token generation
  → Response with user_id and token
```

### 5.2 Trend Arbitrage Flow
```
User Request (niche, category, location, timeframe)
  → Credit check (2 credits deduction)
  → TrendSignal creation (status: pending)
  → Keyword generation from niche mapping
  → Google Trends API call (SerpAPI → PyTrends fallback)
  → Time-series validation
  → Spike detection (Z-score, EWMA)
  → Arbitrage score calculation
  → TrendSignal update (status: completed)
  → MongoDB upsert
  → Response with trend_id and metrics
```

### 5.3 Geo-Intent Scan Flow
```
User Request (business_id, keywords, lat/lng, radius)
  → Credit check (2 credits deduction)
  → Parallel signal ingestion:
     - Google Trends API (keyword search interest)
     - Google Maps Places API (nearby POIs)
     - Tomorrow.io Weather API (conditions)
  → Signal normalization (0-1 scale)
  → Heat score computation (weighted sum × 100)
  → Urgency classification
  → Persona split calculation
  → Background tasks:
     - CampaignLogModel insert
     - HeatScoreModel insert
     - Notification creation (threshold crossings only)
  → Response with score, urgency, persona_split, radar_feed
```

### 5.4 Content Generation Flow
```
User Request (campaign_idea, brand_context, platform_type)
  → Credit check (1 credit deduction)
  → Brand context enrichment
  → Industry template injection
  → System prompt selection (post/story/reel)
  → Google Gemini API call (JSON mode)
  → Brand-lock validation (business name, tagline)
  → Retry loop (max 3 attempts)
  → Image prompt generation
  → CaptionLogModel insert
  → Response with caption_variants, hashtag_sets, whatsapp_variants, email_variants, image_prompts
```

### 5.5 Auto-Reply Flow
```
Meta Webhook (comment event)
  → Signature verification
  → Deduplication check (dedupe_key)
  → CommentEventModel insert
  → User lookup (page_id/ig_business_id → user_email)
  → Settings check (auto_reply enabled?)
  → Intent classification
  → Policy action determination
  → If auto_reply:
     - Reply generation
     - Idempotency check
     - Graph API post
     - AutoReplySentModel insert
  → If needs_review:
     - Draft generation
     - Approval nonce creation
     - AutoReplyDraftModel insert
     - Notification creation
  → Response with status
```

### 5.6 Campaign Launch Flow
```
User Request (trend_keyword, platform, mode, media_url, caption)
  → CampaignLaunchRequestModel creation (status: pending)
  → Admin approval (manual or automated)
  → Status update (approved)
  → Platform routing:
     - Instagram: InstagramPostingService
     - Facebook: FacebookPostingService
     - Both: Sequential posting
  → Result capture (post_id, errors)
  → CampaignLaunchRequestModel update (status: completed/failed)
  → PostingLogModel insert
  → Response with post_ids and status
```

---

## 6. Data Models / Entities

### 6.1 Core Domain Entities

#### User Entity
```python
@dataclass
class User:
    id: Optional[str]
    username: str  # 7-20 characters, unique
    email: EmailStr  # unique
    password_hash: str
    agreed_to_terms: bool
    is_verified: bool
    first_name: str
    last_name: str
    phone_number: str
    company: str
    role: str
    bio: str
    business_domain: Optional[str]  # ObjectId reference
    profile_completed: bool
    facebook_connected: bool
    instagram_connected: bool
    google_maps_connected: bool
    profile_picture: Optional[str]
    subscriptionTier: str  # free, pro, premium
    adCreditsRemaining: int
    stripeCustomerId: Optional[str]
    created_at: datetime
    updated_at: datetime
```

#### TrendSignal Entity
```python
@dataclass
class TrendSignal:
    id: Optional[str]
    user_email: str
    niche: str  # fashion, food, tech, crypto, etc.
    category: str
    location: str  # city, country, region
    radius: Optional[str]
    keywords: List[str]
    search_interest: Dict  # time-series data
    geo_data: Dict
    related_queries: Dict
    rising_queries: Dict
    provider: Optional[str]  # serpapi, pytrends
    arbitrage_score: Optional[float]
    saturation_score: Optional[float]
    social_score: Optional[float]
    lifecycle_stage: Optional[str]  # Emerging, Breakout, etc.
    predicted_growth_pct: Optional[float]
    fetch_status: str  # pending, processing, completed, failed
    fetched_at: Optional[datetime]
    created_at: datetime
```

#### CommentEvent Entity
```python
@dataclass
class CommentEvent:
    id: Optional[str]
    user_id: Optional[str]
    platform: str  # facebook, instagram
    page_id: Optional[str]
    ig_business_id: Optional[str]
    post_id: Optional[str]
    media_id: Optional[str]
    comment_id: str
    from_id: Optional[str]
    text: str
    created_time: Optional[datetime]
    raw_payload: Dict
    dedupe_key: str
    status: str  # received, processed, replied, skipped, failed
    error: Optional[str]
    created_at: datetime
```

#### CampaignLaunchRequest Entity
```python
@dataclass
class CampaignLaunchRequest:
    id: Optional[str]
    user_email: str
    source: str  # trend, planner
    trend_keyword: Optional[str]
    trend_signal_id: Optional[str]
    platform: str  # instagram, facebook, both
    mode: str  # post_now, schedule_post, post_story
    media_url: str
    caption: Optional[str]
    scheduled_time: Optional[str]
    status: str  # pending, approved, rejected, executing, completed, failed
    result: Dict
    created_at: datetime
```

### 6.2 Computed Metrics

#### Heat Score Metrics
- **score**: Integer 0-100 (weighted combination of trends, places, weather)
- **urgency**: String (Critical, High, Medium, Low)
- **trends_score**: Float 0-1 (normalized search interest)
- **places_score**: Float 0-1 (normalized POI density)
- **weather_score**: Float 0-1 (normalized weather favorability)

#### Arbitrage Metrics
- **arbitrage_score**: Float (Velocity / Saturation)
- **saturation_score**: Float 0-100 (market competition)
- **social_score**: Float 0-100 (social media engagement potential)
- **breakout_probability**: Float 0-100 (likelihood of trend breakout)

#### Performance Metrics
- **conversion_rate**: Float (conversions / impressions)
- **roi**: Float (revenue / ad_spend)
- **engagement_rate**: Float (interactions / reach)

---

## 7. Data Access Layer

### 7.1 Repository Pattern

All data access is abstracted through repository interfaces implementing CRUD operations:

**Example Repository Interface**:
```python
class ITrendSignalRepository(ABC):
    @abstractmethod
    async def create(self, trend_signal: TrendSignal) -> TrendSignal
    
    @abstractmethod
    async def get_by_id(self, trend_id: str) -> Optional[TrendSignal]
    
    @abstractmethod
    async def get_latest_by_user(self, user_email: str, limit: int) -> List[TrendSignal]
    
    @abstractmethod
    async def update_status(self, trend_id: str, status: str, error: Optional[str]) -> bool
    
    @abstractmethod
    async def update_trend_data(self, trend_id: str, **kwargs) -> bool
```

### 7.2 FastAPI Routers

**API Endpoint Structure**:
- `/api/auth/*`: Authentication and user management
- `/api/trends/*`: Trend arbitrage and detection
- `/api/geo-intent/*`: Geo-intent engine scans
- `/api/content/*`: Content generation
- `/api/instagram/*`: Instagram posting and scheduling
- `/api/facebook/*`: Facebook posting and scheduling
- `/api/auto-reply/*`: Auto-reply management
- `/api/campaigns/*`: Campaign planning and launch
- `/api/analytics/*`: Performance analytics
- `/api/billing/*`: Subscription and payment management
- `/api/notifications/*`: Notification management
- `/api/chatbot/*`: AI chatbot interactions

### 7.3 Query Mechanisms

#### MongoDB Queries
- **Indexed Queries**: All collections have indexes on frequently queried fields (user_email, created_at, status)
- **Compound Indexes**: Multi-field indexes for complex queries (e.g., `[("user_email", 1), ("created_at", -1)]`)
- **Aggregation Pipelines**: Used for analytics and reporting (e.g., campaign performance aggregation)
- **Geospatial Queries**: GeoJSON Point queries for heat score heatmaps

#### Caching Strategy
- **Trends Cache**: 1-hour TTL for Google Trends API responses
- **Cache Key**: MD5 hash of `{keywords, location, timeframe}`
- **Cache Storage**: MongoDB `trend_caches` collection with `expires_at` field

#### Vector Search (RAG)
- **Embeddings**: Pre-computed FAQ embeddings stored as pickle files
- **Retrieval**: Semantic similarity search for chatbot knowledge base
- **Chunks**: 80 FAQ chunks with category, keywords, user level metadata

---

## 8. Data Consistency & Validation

### 8.1 Unique Constraints

**Database-Level Unique Indexes**:
- `users.email`: Unique email addresses
- `users.username`: Unique usernames (7-20 characters)
- `comment_events.dedupe_key`: Prevents duplicate webhook processing
- `auto_reply_sent.idempotency_key`: Prevents duplicate reply posting

### 8.2 Input Validation

**Pydantic Schema Validation**:
- Email format validation (EmailStr)
- Password strength validation (min 8 characters, uppercase, lowercase, digit, special char)
- Username length validation (7-20 characters)
- ObjectId format validation (24 hex characters)
- URL validation for media URLs
- Enum validation for status fields

**Business Logic Validation**:
- Credit balance checks before expensive operations
- Subscription tier restrictions (free: 5 credits, pro: 50 credits, premium: unlimited)
- OAuth token expiry validation
- Webhook signature verification (Meta, Stripe)

### 8.3 Deduplication Logic

**Comment Event Deduplication**:
```python
dedupe_key = f"{platform}:{comment_id}:{hash(raw_payload)}"
existing = await CommentEventModel.find_one({"dedupe_key": dedupe_key})
if existing:
    return  # Skip duplicate
```

**Reply Idempotency**:
```python
normalized_hash = hashlib.sha256(normalized_reply.encode()).hexdigest()
idempotency_key = f"{platform}:{comment_id}:{normalized_hash}"
existing = await AutoReplySentModel.find_one({"idempotency_key": idempotency_key})
if existing:
    return  # Skip duplicate reply
```

**Trends Cache Deduplication**:
```python
cache_key = hashlib.md5(json.dumps({"keywords": sorted(keywords), "location": location, "timeframe": timeframe}).encode()).hexdigest()
cached = await TrendCacheModel.find_one({"namespace": "google_trends", "key": cache_key, "expires_at": {"$gt": datetime.utcnow()}})
if cached:
    return cached.value  # Return cached data
```

### 8.4 Data Integrity

**Referential Integrity**:
- `user.business_domain` → `business_domains._id` (ObjectId reference)
- `trend_signal.user_email` → `users.email` (email reference)
- `comment_event.user_id` → `users.email` (email reference)
- `campaign_launch_request.trend_signal_id` → `trend_signals._id` (ObjectId reference)

**Cascade Behavior**:
- User deletion triggers account_deletion_verification workflow
- OAuth token revocation updates connection status flags
- Expired drafts are marked as `expired` (soft delete)

**Timestamp Tracking**:
- All entities have `created_at` and `updated_at` timestamps
- Automatic timestamp updates on document modification
- TTL indexes for automatic expiry (OTP codes, cache entries)

---

## Summary

The RAAMP data architecture implements a robust, scalable system for AI-driven marketing automation. Key architectural strengths include:

1. **Clean Separation**: Domain entities, infrastructure repositories, and presentation schemas are clearly separated
2. **Async-First**: All database operations use async/await with Motor and Beanie
3. **Validation-Heavy**: Multi-layer validation (Pydantic, business logic, database constraints)
4. **Idempotency**: Deduplication and idempotency keys prevent duplicate operations
5. **Caching**: Strategic caching reduces API costs and improves response times
6. **Observability**: Comprehensive logging, job health monitoring, and error tracking
7. **Extensibility**: Repository pattern and dependency injection enable easy testing and extension

The architecture supports real-time webhook processing, parallel signal aggregation, AI content generation, and multi-platform social media posting while maintaining data consistency and integrity.
