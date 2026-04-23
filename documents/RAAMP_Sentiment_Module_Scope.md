**RAAMP --- New Module Proposal**

**Sentiment Analysis & Competitive Intelligence Engine**

Final Year Project --- Module Scope Document (Revised MVP)

**1. Module Overview**

  --------------------- -------------------------------------------------
  **Module Name**       Sentiment Analysis & Competitive Intelligence
                        Engine

  **Module Code**       RAAMP-16

  **Purpose**           Extract and analyze sentiment from customer
                        reviews and social media comments for both the
                        client restaurant and its local competitors, then
                        surface actionable marketing recommendations.

  **Data Sources**      Google Places API (reviews), Instagram Graph API
                        (comments), Facebook Graph API (comments),
                        SerpAPI (competitor discovery)

  **ML Components**     Supervised: Sentiment Classification (TF-IDF +
                        Logistic Regression) | Rule-Based: Keyword
                        Extraction & Insight Detection

  **Integration         Competitor Benchmarking Radar (Module 4), AI
  Points**              Creative Studio (Module 1), Performance Dashboard
                        (Module 10)

  **Training Data**     Yelp Open Dataset (Kaggle) --- 6M+ labeled
                        restaurant reviews
  --------------------- -------------------------------------------------

**2. Problem Statement**

Restaurant owners currently have no structured way to understand what
customers are saying about them or their competitors across Google and
social media. They act on instinct rather than data when creating
marketing campaigns.

This module solves that by:

-   Automatically reading and classifying reviews and comments as
    positive, negative, or neutral

-   Identifying the specific keywords driving praise or complaints (food
    quality, delivery, pricing, etc.)

-   Comparing the client restaurant's sentiment profile against local
    competitors

-   Translating those insights into concrete campaign suggestions inside
    RAAMP's existing Creative Studio

**3. Data Sources & Availability**

**3.1 Own Restaurant Data**

  ------------------ ---------------------- ------------------------------
  **Source**         **What It Provides**   **Volume / Limit**

  Google Places API  Review text, star      Max 5 reviews per request ---
                     rating, date           acknowledged limitation

  Instagram Graph    Post comments, reply   No hard cap --- volume depends
  API                threads                on account activity

  Facebook Graph API Page comments, post    No hard cap --- volume depends
                     reactions              on account activity
  ------------------ ---------------------- ------------------------------

**3.2 Competitor Data**

  ------------------ ---------------------- ------------------------------
  **Source**         **What It Provides**   **Volume / Limit**

  SerpAPI (Google    Full review text per   10--20 reviews per business on
  Reviews)           competitor, star       paid plan
                     ratings                

  Google Places API  Competitor             5 reviews per business ---
                     identification         same limitation applies
                     (already used in       
                     Module 4)              
  ------------------ ---------------------- ------------------------------

**3.3 Training Data**

  ------------------ ---------------------- ------------------------------
  **Dataset**        **Source**             **Why It Is Used**

  Yelp Open Dataset  Kaggle (free, public)  6M+ real restaurant reviews
                                            with star ratings used as
                                            sentiment labels. Removes need
                                            for synthetic data.
  ------------------ ---------------------- ------------------------------

**Expected Data Volume:** 70-100 total reviews per restaurant (aggregated
across all 4 sources), sufficient for sentiment classification and keyword
analysis.

**4. ML Training Pipeline**

The module contains one supervised ML component for sentiment
classification and a rule-based system for insight extraction.

**4.1 Component 1 --- Sentiment Classifier (Supervised)**

  --------------------- -------------------------------------------------
  **Goal**              Label each review or comment as Positive,
                        Negative, or Neutral

  **Input Features**    Raw review text

  **Feature             Text cleaning (lowercasing, punctuation removal,
  Engineering**         stopword removal) → TF-IDF vectorization
                        (unigrams + bigrams, max 10,000 features)

  **Model**             Logistic Regression (primary) with Random Forest
                        as comparison baseline

  **Training Labels**   Yelp star ratings mapped: 4--5 stars = Positive,
                        3 stars = Neutral, 1--2 stars = Negative

  **Train/Test Split**  80% train, 20% test --- stratified by sentiment
                        class

  **Evaluation          Accuracy, Precision, Recall, F1-Score (per
  Metrics**             class), Confusion Matrix

  **Inference**         Trained model serialized with joblib, loaded at
                        runtime to score live reviews
  --------------------- -------------------------------------------------

**4.2 Component 2 --- Keyword Insight Extractor (Rule-Based)**

  --------------------- -------------------------------------------------
  **Goal**              Identify recurring keywords and themes in
                        positive vs negative reviews (e.g., food quality,
                        delivery speed, pricing)

  **Input**             Preprocessed review text corpus, separated by
                        sentiment class

  **Method**            Domain-specific keyword dictionaries + frequency
                        analysis. No training required.

  **Keyword             Food Quality: [delicious, fresh, tasty,
  Categories**          amazing], Delivery: [late, slow, cold,
                        delivered], Service: [friendly, rude, attentive,
                        waited], Pricing: [expensive, cheap, value,
                        overpriced], Ambiance: [cozy, clean, noisy,
                        atmosphere]

  **Evaluation**        Human validation of extracted keywords. Sample
                        review inspection.

  **Output**            Top 5-10 keywords per sentiment class (positive,
                        negative) with frequency counts and percentage
                        mentions
  --------------------- -------------------------------------------------

**Rationale for Rule-Based Approach:** LDA topic modeling requires 100+
documents per topic for statistical stability. With typical review volumes
of 70-100 total reviews, LDA would produce unstable topics. Rule-based
keyword extraction is more appropriate for small sample sizes and provides
interpretable results.

**4.3 Pipeline Flow**

  ---------- ----------------------- -----------------------------------------
  **Step**   **Stage**               **Description**

  **1**      Data Ingestion          Pull reviews from Google Places + SerpAPI
                                     for own restaurant and competitors

  **2**      Preprocessing           Clean text, remove noise, tokenize,
                                     remove stopwords

  **3**      Sentiment Scoring       Run each review through trained Logistic
                                     Regression classifier

  **4**      Keyword Extraction      Extract frequent keywords from positive
                                     and negative review sets using domain
                                     dictionaries

  **5**      Aggregation             Compute per-business sentiment scores,
                                     keyword frequencies, and sample size

  **6**      Comparison              Diff own restaurant vs competitor
                                     sentiment scores and ranking

  **7**      Action Generation       Map keyword patterns to campaign
                                     templates in Creative Studio
  ---------- ----------------------- -----------------------------------------

**5. Feature Output --- What the User Sees**

**5.1 Sentiment Overview Panel**

-   Overall sentiment score for own restaurant (0--100 scale)

-   Last scan timestamp (e.g., "Last updated: 2 days ago")

-   Sample size display (e.g., "Based on 87 reviews")

-   Breakdown: % Positive / Neutral / Negative

**5.2 Keyword Insights Panel**

-   **Top Praise Keywords:** Most frequent words in positive reviews
    (e.g., "delicious" - mentioned in 34% of positive reviews,
    "friendly" - 28%, "fresh" - 21%)

-   **Top Complaint Keywords:** Most frequent words in negative reviews
    (e.g., "slow" - mentioned in 45% of negative reviews, "cold" - 30%,
    "expensive" - 25%)

-   Keyword category detection: highlights if delivery, service, food,
    or pricing issues dominate

**5.3 Competitor Comparison Panel**

-   Side-by-side sentiment score: own restaurant vs top 3 competitors
    (bar chart format)

-   Competitive ranking: "You rank #2 among 4 local competitors"

-   Sentiment gap highlights: where you are ahead or behind in overall
    positive percentage

**5.4 Campaign Recommendation Engine**

-   If "delivery" or "slow" keywords dominate negative reviews →
    suggest 'We Improved Our Delivery' campaign in Creative Studio

-   If "expensive" or "price" keywords appear frequently → suggest
    discount/value campaign

-   If "delicious" or "amazing" keywords dominate positive reviews →
    suggest 'Our Customers Love Our Food' social proof campaign

-   Each recommendation is one-click to generate content in the existing
    AI Creative Studio

**6. Integration with Existing RAAMP Modules**

  ---------------------- ---------------- -------------------------------
  **Existing Module**    **Integration    **How It Connects**
                         Type**           

  Module 4 ---           Consumes         Reuses competitor list already
  Competitor                              identified by SerpAPI. No
  Benchmarking Radar                      duplicate discovery needed.

  Module 1 --- AI        Feeds into       Campaign recommendations
  Creative Studio                         pre-fill the Creative Studio
                                          with a brief based on detected
                                          sentiment issues.

  Module 10 ---          Adds widget      Sentiment score and top
  Performance Dashboard                   complaint keyword appear as new
                                          KPI cards on the existing
                                          dashboard.

  Module 13 --- Social   Data source      Pulls Instagram and Facebook
  Media Integration                       comments via
                                          already-authenticated Graph API
                                          connection.
  ---------------------- ---------------- -------------------------------

**7. Known Limitations & Mitigations**

  --------------------------- -------------------------------------------
  **Limitation**              **Mitigation / Acknowledgment**

  Google Places API returns   SerpAPI Google Reviews endpoint used as
  max 5 reviews per business  supplement for competitor data (10--20
                              reviews). Aggregate across 4 sources (Google,
                              SerpAPI, Instagram, Facebook) to reach
                              70-100+ reviews total. Limitation
                              acknowledged in FYP documentation.

  Small restaurants may have  Module shows 'insufficient data' state
  low comment volume on       gracefully. Sentiment scores require
  social media                minimum 10 data points to render. Sample
                              size is displayed prominently to users.

  No time-series trend data   Google Places API does not provide
                              continuous review streams. System displays
                              "last scanned" timestamp instead of trend
                              lines. Weekly scan schedule implemented to
                              capture new reviews over time.

  Keyword extraction is       Deliberate design choice: rule-based keyword
  rule-based, not learned     detection is interpretable, requires no
                              training, and works reliably with small
                              sample sizes. LDA topic modeling requires
                              100+ documents per topic and would be
                              unstable with typical review volumes
                              (70-100 reviews).

  Yelp training data may not  Acknowledged as a generalization
  fully represent             limitation. Scope is English-language
  Pakistani/South Asian       reviews. Future work: fine-tune on local
  restaurant language         data.
  patterns                    

  Sentiment model trained on  Domain mismatch is a documented learning
  Yelp but inference on       outcome --- similar to the Kaggle
  Google/Instagram data       experiment noted in Module 11.
  --------------------------- -------------------------------------------

**8. Technical Stack**

  --------------------- -------------------------------------------------
  **Backend Language**  Python (FastAPI --- consistent with existing
                        RAAMP backend)

  **ML Libraries**      scikit-learn (TF-IDF, Logistic Regression),
                        pandas, numpy, joblib (model serialization),
                        nltk (stopwords, tokenization)

  **New Router**        sentiment_router.py --- prefix /api/sentiment

  **New Service**       sentiment_service.py --- orchestrates ingestion,
                        scoring, keyword extraction, comparison

  **Model Storage**     Trained sentiment classifier saved as .pkl file,
                        loaded at startup

  **Frontend**          New SentimentDashboard.tsx page +
                        SentimentWidget.tsx for dashboard KPI strip

  **Database**          MongoDB --- stores aggregated sentiment scores,
                        keyword frequencies, and scan metadata per
                        business

  **External APIs**     Google Places API (existing), SerpAPI (existing),
                        Instagram Graph API (existing), Facebook Graph
                        API (existing)
  --------------------- -------------------------------------------------

**9. Deliverables**

  -------- ------------------------ ---------------------- -------------------
  **#**    **Deliverable**          **Type**               **Status**

  **1**    Trained Sentiment        ML Model               To be built
           Classifier (.pkl)                               

  **2**    Keyword extraction       Backend Code           To be built
           module (rule-based)                             

  **3**    sentiment_router.py +    Backend Code           To be built
           sentiment_service.py                            

  **4**    SentimentDashboard.tsx   Frontend Code          To be built
           frontend page                                   

  **5**    Model training notebook  Documentation          To be built
           (Jupyter)                                       

  **6**    Evaluation report        Documentation          To be built
           (metrics + confusion                            
           matrix + keyword                                
           validation)                                     
  -------- ------------------------ ---------------------- -------------------

**10. FYP Defense Talking Points**

These are the questions your supervisor or examiner is most likely to
ask, and how to answer them.

**Q: Why Logistic Regression and not a deep learning model?**

Logistic Regression with TF-IDF is interpretable, fast to train, and
well-suited to this domain. Deep learning (BERT etc.) would require
significantly more compute and training data with minimal accuracy gain
for the restaurant review domain. This is a deliberate engineering
trade-off, not a limitation.

**Q: Is your training data representative?**

The Yelp dataset is 6M+ real restaurant reviews in English with genuine
star-rating labels. It is the industry standard for restaurant sentiment
research. The domain mismatch between training (Yelp) and inference
(Google/Instagram) is acknowledged and documented as a known limitation.

**Q: How is this different from just showing star ratings?**

Star ratings give an aggregate score. This module tells you WHY the
score is what it is, which specific keywords are driving it, how it
compares to competitors, and what marketing action to take in response.
That is the value add.

**Q: What is the ML pipeline exactly?**

Data ingestion from APIs → text preprocessing → TF-IDF feature
extraction → Logistic Regression inference (supervised) → keyword
extraction (rule-based) → aggregation and comparison → campaign action
mapping. One trained ML model (sentiment classifier) plus rule-based
keyword detection, with documented evaluation metrics.

**Q: Why didn't you use topic modeling (LDA)?**

Initial scope included LDA, but after analyzing API data volume
constraints (5 reviews from Google Places, 10-20 from SerpAPI), I
determined that topic modeling requires 100+ documents per topic for
statistical stability. With typical volumes of 70-100 total reviews
across 6-8 topics, LDA would produce unstable, unreliable topics that
change on every retrain. Rule-based keyword extraction provides
interpretable insights without overfitting to small samples, and is more
appropriate for the available data volume.

**Q: How do you handle new reviews over time?**

The system runs a weekly scan and stores sentiment snapshots in MongoDB.
While individual restaurants don't get many new Google reviews, social
media comments refresh more frequently. Each scan displays "Last updated:
X days ago" and sample size to set user expectations. Over multiple
weeks, the system builds a historical record of sentiment changes.

---

RAAMP --- Final Year Project

Module Scope Document | Sentiment Analysis & Competitive Intelligence
Engine (MVP)