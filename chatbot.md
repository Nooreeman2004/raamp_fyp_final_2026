# RAAMP Assistant: Chatbot & AI Architecture

This document provides a technical overview of the RAAMP Assistant (Chatbot) and the underlying AI infrastructure supporting the platform's intelligence layers.

---

## 🏗️ Core Architecture: Hybrid Intelligence

The RAAMP Assistant uses a **Retrieval-Augmented Generation (RAG)** architecture enhanced with **Business-Aware Context Injection**. Unlike standard chatbots, it combines three separate intelligence layers to generate responses:

### 1. The Knowledge Layer (Static/FAQ)
*   **Vector Store**: Pinecone (Index: `raamp`).
*   **Embeddings**: `text-embedding-3-large` (1024-3072 dimensions).
*   **Source**: FAQ data and platform documentation.
*   **Role**: Handles specific Q&A about RAAMP features, pricing, and troubleshooting.

### 2. The Context Layer (Dynamic/Awareness)
*   **Business Profile**: Fetches the user's `BusinessModel` (Niche, Location, Specialties) and injects it into the system prompt.
*   **Trend Intelligence**: Fetches the last 3 `TrendAIAnalysis` records linked to the session to provide trend-aware strategy advice.
*   **Caching**: Uses an in-memory `TTLCache` (10-minute TTL) for business profiles to ensure sub-millisecond context retrieval.

### 3. The Memory Layer (Session Management)
*   **History**: Conversation history is stored in MongoDB via the `ChatSessionModel`.
*   **Window**: The assistant "remembers" the last 10 messages to maintain linear context in multi-turn conversations.

---

## 🚀 Smart Interaction Flow

When a user sends a message, it follows this logic:

1.  **Smart Pattern Detection (Deterministic)**:
    *   Regex matches for `file complaint`, `bug`, `report issue`, etc.
    *   **Result**: Instant redirection to the **Support Center** ([/dashboard/complaints](/dashboard/complaints)) without LLM delay.
    *   **Support Info**: Surfacing support email and phone numbers automatically.

2.  **Retrieval (Semantic)**:
    *   Query is vectorized and matched against Pinecone documentation.
    *   Business and Trend contexts are fetched from MongoDB.

3.  **Synthesis (Generative)**:
    *   LLM (GPT-4o) processes the query + documentation + business context + trends.
    *   Generates a professional, emoji-rich response tailored to the user's specific store location and niche.

4.  **Audit Trail (Logging)**:
    *   Every interaction (Query + Response) is logged in `ChatInteractionModel` for analytics and quality control.

---

## 🧠 Model Specifications

| Component | Model / Provider | Details |
| :--- | :--- | :--- |
| **Generative Brain** | `gpt-4o` / `gpt-4o-mini` | High-reasoning model for strategy and natural conversation. |
| **Embeddings** | `text-embedding-3-large` | 1024-dimensional vectors for semantic grounding. |
| **Orchestration** | **LangChain** | Manages the conversation flow and prompt templates. |
| **Vector Store** | **Pinecone** | Serverless vector database optimized for real-time RAG. |

---

## 🛡️ Guardrails & Security

- **knowledge Threshold**: The `RAAMPRetriever` requires a similarity score of >0.3. Below this, it uses general marketing knowledge while notifying the user.
- **Strict Guardrails**: `RAAMP_SYSTEM_PROMPT` enforces a professional tone and prevents the bot from discussing competitors or unrelated topics.
- **Support Redirects**: If a user exhibits frustration or reports a technical failure, the LLM is instructed to provide a direct link to the formal complaints module.

---

## 📊 Feature Integration

### 1. Trend Arbitrage Strategy
*   Synthesizes signals from **Spotify API** (Viral Audio) and **SerpAPI** (Competitor Saturation).
*   Chatbot can interpret these signals: *"Based on the high urgency score of the 'Vegan Leather' trend, I recommend..."*

### 2. Complaints Integration
*   The chatbot detects support intent and acts as a triage layer, guiding users to the `/dashboard/complaints` module for formal tracking.

---

## 🛠️ Data Storage Architecture

- **MongoDB**: Source of truth for `UserModel`, `BusinessModel`, `ChatSessionModel`, and `ComplaintModel`.
- **Pinecone**: High-performance index for all platform and FAQ documentation.
- **Cloudinary**: Storage for complaint attachments and generated media assets.
