**RAAMP --- New Module Proposal**

**Sentiment Analysis & Competitive Intelligence Engine**

Final Year Project --- Module Scope Document

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
                        Logistic Regression) \| Unsupervised: Topic
                        Extraction (LDA)

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

-   Identifying the specific topics driving praise or complaints (food
    quality, delivery, pricing, etc.)

-   Comparing the client restaurant\'s sentiment profile against local
    competitors

-   Translating those insights into concrete campaign suggestions inside
    RAAMP\'s existing Creative Studio

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

**4. ML Training Pipeline**

The module contains two distinct ML components, each with its own
training and inference pipeline.

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

**4.2 Component 2 --- Topic Extractor (Unsupervised)**

  --------------------- -------------------------------------------------
  **Goal**              Identify recurring themes in reviews (e.g., food
                        quality, delivery speed, pricing, ambiance)

  **Input**             Preprocessed review text corpus

  **Model**             Latent Dirichlet Allocation (LDA) --- sklearn
                        implementation

  **Configuration**     Number of topics: 6--8 (tuned using coherence
                        score). Topics manually labeled after training
                        based on top keywords.

  **Evaluation**        Topic coherence score (UMass / CV). Human
                        validation of topic labels.

  **Output**            Per-review topic distribution → aggregated into
                        restaurant-level topic scores
  --------------------- -------------------------------------------------

**4.3 Pipeline Flow**

  ---------- ----------------------- -----------------------------------------
  **Step**   **Stage**               **Description**

  **1**      Data Ingestion          Pull reviews from Google Places + SerpAPI
                                     for own restaurant and competitors

  **2**      Preprocessing           Clean text, remove noise, tokenize,
                                     remove stopwords

  **3**      Sentiment Scoring       Run each review through trained Logistic
                                     Regression classifier

  **4**      Topic Extraction        Run LDA on review corpus, assign dominant
                                     topic per review

  **5**      Aggregation             Compute per-business sentiment scores and
                                     topic distribution percentages

  **6**      Comparison              Diff own restaurant vs competitor
                                     averages per topic

  **7**      Action Generation       Map complaint/praise patterns to campaign
                                     templates in Creative Studio
  ---------- ----------------------- -----------------------------------------

**5. Feature Output --- What the User Sees**

**5.1 Sentiment Overview Panel**

-   Overall sentiment score for own restaurant (0--100 scale)

-   Trend line: sentiment over last 30 / 60 / 90 days

-   Breakdown: % Positive / Neutral / Negative

**5.2 Topic Intelligence Panel**

-   Top 3 praise topics this week (e.g., \'Food Quality 78% positive\')

-   Top 3 complaint topics this week (e.g., \'Delivery Speed 61%
    negative\')

-   Topic sentiment trend over time

**5.3 Competitor Comparison Panel**

-   Side-by-side sentiment score: own restaurant vs top 3 competitors

-   Topic-level comparison table --- where you are ahead, where you are
    behind

-   \'Competitive gap\' highlight: topics where you outperform
    competitors

**5.4 Campaign Recommendation Engine**

-   If delivery complaints spike → suggest \'We Improved Our Delivery\'
    campaign in Creative Studio

-   If pricing sentiment drops vs competitors → suggest discount/value
    campaign

-   If food quality praise is high → suggest \'Our Customers Love Our
    Food\' social proof campaign

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
  Performance Dashboard                   complaint topic appear as new
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
                              reviews). Limitation acknowledged in FYP
                              documentation.

  Small restaurants may have  Module shows \'insufficient data\' state
  low comment volume on       gracefully. Sentiment scores require
  social media                minimum 10 data points to render.

  LDA topic labels require    Topics are pre-labeled after training based
  manual interpretation       on top keywords. Labels are hardcoded to
                              restaurant-domain themes.

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

  **ML Libraries**      scikit-learn (TF-IDF, Logistic Regression, LDA),
                        pandas, numpy, joblib (model serialization)

  **New Router**        sentiment_router.py --- prefix /api/sentiment

  **New Service**       sentiment_service.py --- orchestrates ingestion,
                        scoring, topic extraction, comparison

  **Model Storage**     Trained models saved as .pkl files, loaded at
                        startup

  **Frontend**          New SentimentDashboard.tsx page +
                        SentimentWidget.tsx for dashboard KPI strip

  **Database**          MongoDB --- stores aggregated sentiment scores
                        and topic distributions per business per scan

  **External APIs**     Google Places API (existing), SerpAPI (existing),
                        Instagram Graph API (existing), Facebook Graph
                        API (existing)
  --------------------- -------------------------------------------------

**9. Deliverables**

  -------- ------------------------ ---------------------- -------------------
  **\#**   **Deliverable**          **Type**               **Status**

  **1**    Trained Sentiment        ML Model               To be built
           Classifier (.pkl)                               

  **2**    Trained LDA Topic Model  ML Model               To be built
           (.pkl)                                          

  **3**    sentiment_router.py +    Backend Code           To be built
           sentiment_service.py                            

  **4**    SentimentDashboard.tsx   Frontend Code          To be built
           frontend page                                   

  **5**    Model training notebook  Documentation          To be built
           (Jupyter)                                       

  **6**    Evaluation report        Documentation          To be built
           (metrics + confusion                            
           matrix)                                         
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
score is what it is, which specific topics are driving it, how it
compares to competitors on each topic, and what marketing action to take
in response. That is the value add.

**Q: What is the ML pipeline exactly?**

Data ingestion from APIs → text preprocessing → TF-IDF feature
extraction → Logistic Regression inference (supervised) → LDA topic
modeling (unsupervised) → aggregation and comparison → campaign action
mapping. Two distinct ML models, both trained on real data, with
documented evaluation metrics.

RAAMP --- Final Year Project

Module Scope Document \| Sentiment Analysis & Competitive Intelligence
Engine
