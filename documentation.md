# RAAMP Feature Documentation

This document provides a feature-by-feature breakdown of currently implemented functionality within the RAAMP (Revolutionary AI-powered Autonomous Marketing Platform) project.

**Note**: Some areas (especially Geo-Intent + Trends) are implemented with specific fallbacks, caching, and tier-gating. This document reflects the current code behavior.

---

## 1. AI Creative Studio
**Purpose**: To provide a centralized environment for generating high-quality marketing assets including text, images, and video content.

**How it works**: Uses advanced AI models (via backend routers like `/api/content-generation` and `/api/media-generation`) to process natural language prompts and parameters (aspect ratio, tone) to create multiple variants of marketing material.

**User interaction**: 
- Users input a "Campaign Idea" in natural language.
- Users select content types (Captions, Hashtags, WhatsApp, Emails, or All).
- Users can trigger generation for specific assets like standalone images or AI-generated Reels/Videos.
- Users can view, copy, and download generated variants.

**Data/API involved**: 
- `content-generation-router`: For text and image generation.
- `media-generation-router`: For Reel and Video generation.
- `asset-service`: For tracking usage and saving generated content.

**Output/Result**: Multiple variants of captions, hashtag sets, business messages (WhatsApp/Email), AI-generated images, and short-form vertical/horizontal videos.

---

## 2. Trend Arbitrage Engine
**Purpose**: To identify emerging market trends and "profit windows" before they become mainstream, allowing businesses to capitalize on spikes in interest.

**How it works**: Scans global signal nodes (Google Trends and Instagram) to detect volume spikes (sigma scores) and velocity changes. It compares search interest against social media saturation to identify "market gaps."

**User interaction**: 
- Users can trigger a "Global Scan" for their specific location and niche.
- Users monitor a live ticker of detected spikes.
- Users can view detailed analytics including "Arbitrage Potential," "Social Score," and "Profit Score."

**Data/API involved**: 
- `arbitrage-router`: For trend analysis and scoring.
- `trend-analytics-service`: Core service for processing and persisting dynamic market insights.
- `trend-signal-router`: For fetching live data from external sources.
- `watchlist-router`: For tracking specific keywords.

**Output/Result**: List of live trends with spike scores, market gap analysis, platform reach metrics, and AI-generated campaign recommendations for detected trends. Persisted trend data ensures historical tracking.

---

## 3. Viral Audio & Intelligence
**Purpose**: To provide real-time audio trends and viral signals to enhance creative content alignment.

**How it works**: Integrates with Spotify Web API and Apple Music RSS to fetch top-charting and "viral" tracks localized to the user's market. It uses genre-vibe heuristics to recommend audio that matches the business niche and trend energy.

**Data/API involved**: 
- `Spotify Web API`: For real-time track metadata and popularity indexing.
- `ViralAudioProvider`: Internal service that scores tracks against platform vibes (TikTok vs. Instagram).

---

## 4. Competitor Benchmarking Radar
**Purpose**: To monitor competitor engagement and density within specific market segments.

**How it works**: Utilizes SerpAPI to fetch local competitor data and engagement signals. It visualizes competitor proximity and provides benchmarking metrics (Engagement share, Review velocity) to identify competitive market gaps.

**Data/API involved**:
- `SerpAPI (Google Local)`: For competitor location and review data.
- `IntelligenceGrid`: Frontend component for visualizing competitor vs. business performance.

---

## 5. Geo-Intent Marketing Engine (Geo-Intent Targeting)
**Purpose**: To provide hyper-local marketing intelligence by fusing **macro digital intent** with **street-level physical density** and **weather mobility context**, producing a 0–100 Heat Score plus persona split and deployable campaign guidance.

**How it works (current implementation)**:
- **Signals (0.0–1.0 each)**:
  - **Trends (Macro-Intent)**: Google Trends time-series interest averaged over a 7‑day window (`now 7-d`). This is treated as a **regional/sub-regional** “macro wave” signal (not street-level).
  - **Places (Local Density)**: Google Places Nearby Search result count (up to **2 pages** for performance) → normalised density proxy.
  - **Weather (Mobility Modifier)**: Tomorrow.io realtime weather; rain effect flips based on **indoor vs outdoor** business type.
- **Resilience**: Each external fetcher is timeout-protected and **never raises**; on failure it returns **neutral 0.5** so the engine still responds.
- **Tier gating**:
  - **Free tier**: Places only. Trends + Weather return score `0.5` with status `"limited"`.
  - **Premium/Demo**: All three signals fetched concurrently.
- **Caching**:
  - Geo-Intent signal fetchers cache by geo/radius/keywords (service TTL cache).
  - Google Trends service caches provider results in MongoDB with a TTL (default ~1 hour).
- **Heat Score**: Aggregates into 0–100 with weighted fusion: **35% Trends, 40% Places, 25% Weather**.

**User interaction (frontend)**:
- **Profile-driven targeting**: Uses the user’s onboarding location and attempts to use Google `place_id` as the stable `business_id`. If missing, falls back to a deterministic onboarding-coordinates key.
- **Radius control**: 1–50 km slider (persisted in localStorage) triggers a debounced re-scan.
- **Custom zones**: Users can draw a polygon; the UI recenters a sweep to the polygon centroid.
- **Outputs shown**:
  - Heat Score + urgency state
  - Per-signal status + explanation (explicitly calls out trends as “city/state scale”)
  - Live radar feed messages
  - Visitor persona distribution
  - Heatmap layer + history + strategy history replay

**Data/API involved (key pieces)**:
- Backend services:
  - `raamp-backend/application/services/geo_intent_fetchers.py`: Async signal fetchers + tier gating + neutral fallback rules.
  - `raamp-backend/application/services/google_trends_service.py`: Trends provider selection + validation + MongoDB caching.
- Frontend:
  - `raamp-frontend/src/pages/GeoIntent.tsx`: Main Geo-Intent dashboard and flows.
  - `raamp-frontend/src/services/geoIntentService.ts`: API client (used by the page).

**Output/Result**: Heat Score (0–100), urgency classification, signal breakdown, persona split, radar feed, heatmap points, sweep history, and AI-generated campaign briefs with replay.

---

## 6. RAAMP Assistant (AI Marketing Chatbot)
**Purpose**: To act as a 24/7 AI-powered marketing consultant that provides strategic advice and platform assistance.

**How it works**: A conversational interface powered by a Large Language Model (LLM) that has context about the user's business profile and current market trends.

**User interaction**: Users type questions or marketing requests into a chat interface and receive structured advice or creative assistance.

**Data/API involved**: 
- `chatbot-router`: For processing conversational AI requests.

**Output/Result**: Text-based strategic answers, content ideas, and platform guidance generated by AI.

**Advanced Technical Architecture (RAG)**:
- **Embeddings**: Uses `text-embedding-004` (Gemini) or OpenAI embeddings for vectorizing the RAAMP Knowledge Base.
- **Vector Store**: MongoDB Atlas Vector Search for high-relevance retrieval.
- **Pipeline**: Implements a Retrieve-Augment-Generate (RAG) pipeline that fetches platform documentation, marketing best practices, and user-specific business context before generating a response.
- **Context Management**: Maintains conversation history with summarization logic to ensure long-term memory stability.

---

## 7. Support Center & Complaint Management
**Purpose**: To handle technical issues and feature requests through a structured support ticketing system.

**How it works**: Users can submit complaints with priority levels, attachments, and specific descriptions. The system allows for real-time status updates and two-way communication (comments) between the user and support.

**User interaction**: 
- Submit new complaints via the Support Center.
- Upload attachments (logs, screenshots) up to 10MB.
- Rate the support experience once a complaint is "Resolved."

**Data/API involved**:
- `complaints-router`: Full CRUD lifecycle for tickets.
- `complaint-service`: Backend orchestrator for persistence and notifications.

---

## 8. Asset Library & Media Management
**Purpose**: To manage all generated and uploaded marketing assets in one structured repository.

**How it works**: Stores metadata and file paths for all assets in a database, allowing for filtering by type, source, and favorites. It also links assets to performance metrics if they have been posted to social media.

**User interaction**: 
- Users can browse "Media" (Images/Videos) and "Text Assets" (Captions/Hashtags).
- Users can favorite, delete, or download assets.
- Users can "Rescan Files" to sync the library with the filesystem.

**Data/API involved**: 
- `assets-router`: For CRUD operations on assets and favorites.
- `instagram-roi-router`: For fetching performance data (Reach, Impressions) for posted assets.

**Output/Result**: Organized grid of media, text snippets with usage tracking, and ROI summary for top-performing assets.

---

## 9. Smart Scheduling & Cross-Platform Posting
**Purpose**: To automate and plan the deployment of marketing content across social media platforms like Instagram and Facebook.

**How it works**: Allows users to schedule posts for future dates/times. A backend scheduler (APScheduler) processes these jobs and triggers automated posting via platform APIs.

**User interaction**: 
- Users fill out a posting form with media and captions.
- Users select "Post Now" or "Schedule for Later."
- Users view a "Deployment Lifecycle" timeline on the dashboard.

**Data/API involved**: 
- `instagram-posting-router` / `facebook-posting-router`: For direct deployment.
- `instagram-scheduler-router`: For managing and executing scheduled jobs.

**Output/Result**: Successfully deployed or scheduled social media posts with automated reminders and status tracking.

---

## 10. Performance Dashboard & Real-time Analytics
**Purpose**: To provide a high-level overview of business performance, marketing health, and live customer activity.

**How it works**: Aggregates data from multiple services (Billing, Social ROI, Geo-Intent) into a Unified KPI strip and interactive charts. Uses WebSockets for real-time "Conversion Pings."

**User interaction**: 
- Users monitor top-level KPIs (Revenue, Social Footprint, Ad Credits).
- **Connection-Aware States**: If social or location services are disconnected, the dashboard shows informative placeholders and guides to onboarding.
- Users view "Live Attribution" maps of recent customer activity.
- Users read "Strategic Insights" generated by AI analysis.

**Data/API involved**: 
- `dashboard-analytics-router`: Core summary and KPI data.
- `connection-service`: Backend check for linked API accounts.
- `activity-router`: For the live activity feed.

**Output/Result**: Unified performance summary, proactive connection alerts, interactive growth charts, and actionable marketing intelligence suggestions.

---

## 11. ML Caption Intelligence & Variant Recommendations
**Purpose**: To predict the success of marketing copy and recommend the best-performing variant using machine learning.

**How it works**:
- **Generation (business-specific)**: Captions and primary hashtags are generated by Gemini using the user’s saved **brand context** (business type/name/tone). This keeps outputs aligned to the user’s niche.
- **ML scoring (ranking-only)**: A dedicated ML layer scores each caption variant (`ml_score`) and selects the best variant (`best_caption_id`). The ML model uses caption-level numeric features (structure + timing + sentiment + CTA signals). It does **not** rewrite caption text.
- **ML hashtag suggestions (optional)**: The backend may attach `ml_hashtags` (cluster-based suggestions) for inspection/experimentation, but the system **does not override** Gemini’s business-specific hashtags by default.

**Data note (important)**:
- The current training labels in this project are **synthetic / bootstrapped** in most environments. This makes the model behavior coherent for demos, but the reported metrics are **not** evidence of real-world predictive accuracy.
- We ran a Kaggle augmentation experiment and found a **target-definition mismatch** (Kaggle-style engagement proxies vs. RAAMP’s ROI-labelled engagement), which degraded generalization. That experiment is documented as a learning outcome, and the default training source remains the project’s own caption logs.

**User interaction**: 
- Automatically runs when content is generated in the Creative Studio.
- Users see a "Recommended" badge on the variant with the highest ML score.
- **Hashtag Intelligence**:
  - Users primarily see the Gemini hashtags (business-specific).
  - `ml_hashtags` can be surfaced later as an “experimental suggestions” panel if desired.
- Users can view "Why this works" reasoning for the top recommendation.

**Data/API involved**: 
- `ml_router`: For engagement prediction and scoring.
- `training_pipeline_service`: For periodic model updates using local datasets.
- `variant_recommendation_router`: For ranking and providing the logic for recommendations.

**Output/Result**: Engagement-optimized content variants, hashtag popularity predictors, and a clear AI-backed recommendation for deployment.

---

## 12. Business Onboarding & Setup
**Purpose**: To gather essential business information and configure the platform's AI engines for the specific user.

**How it works**: A multi-step flow that saves the business "Identity" (Domain, Specialties) and "Location" (Physical coordinates) to the user's profile.

**User interaction**: 
- Users complete steps to define their niche (e.g., Restaurant, Retail).
- Users select "Business Specialties" for targeted trend detection.
- Users set their physical "Base of Operations" on a map.
- **Onboarding Gating**: Critical features (Trends, Geo-Intent) are locked behind a "Connection Required" state until the profile is complete.

**Data/API involved**: 
- `onboarding_router`: For managing the multi-step configuration flow.
- `profile_guard`: Frontend component that enforces onboarding completion.
- `business_domain_router`: For domain-specific settings.
- `hyperlocal_setup_router`: For setting coordinates and reach parameters.

**Output/Result**: A fully configured user profile with mandatory data fields that powers specialized results and unlocks the platform's core engines.

---

## 13. Social Media Integration (Instagram & Facebook)
**Purpose**: To connect the user's social identity to RAAMP for data syncing and automated actions.

**How it works**: Uses Facebook/Instagram Graph API (OAuth) to authenticate business accounts and retrieve business IDs and access tokens.

**User interaction**: 
- Users click "Connect" buttons to launch the platform's OAuth flow.
- Users can view connection status and "Footprint" metrics once linked.

**Data/API involved**: 
- `profile_connections_router`: For managing account links.
- `instagram_router`: For fetching social account metadata.

**Output/Result**: Securely linked social media accounts with synced audience data and posting capabilities.

---

## 14. Subscription & Billing Management
**Purpose**: To manage the user's financial relationship with the platform, including credits for AI generation.

**How it works**: Integrates with Stripe for payments and a custom **CreditService** for usage metering. Each AI action (Brief generation, Content variant creation) consumes credits based on the user's tier.
- **Free Tier**: Limited to Google Places signals; no AI Brief generation.
- **Premium Tier**: Full access to Google Trends, Weather context, and high-volume AI generation.

**User interaction**: 
- Users view current balance and "Ad Credits Remaining" on the KPI strip.
- Users view transaction history and top-up funds.
- Automatic credit deduction when triggering AI workflows.

**Data/API involved**: 
- `billing_router`: For balance and history.
- `credit_service`: Centralized logic for metering and usage enforcement.
- `stripe_router`: For payment processing.

**Output/Result**: Real-time credit tracking across the dashboard, tier-based feature gating, and secure payment processing.

---

## 15. User Profile & Security Settings
**Purpose**: To allow users to manage their personal information, account security, and notification preferences.

**How it works**: Provides standard account management functionality including profile updates, password resets, and preference toggles.

**User interaction**: 
- Users update personal details (Email, Phone).
- Users manage security settings (Two-Factor Authentication, Password changes).
- Users toggle email/push notification preferences.

**Data/API involved**: 
- `auth_router`: For security and authentication updates.
- `settings_router` / `notification_router`: For user preferences.

**Output/Result**: Updated user profile, changed security settings, and refined notification filters.
