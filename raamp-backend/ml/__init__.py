"""
ml/ — RAAMP Machine Learning Enrichment Layer
==============================================
This package provides ML capabilities that plug into the caption generation pipeline.

Modules:
    model_trainer        — Trains GradientBoosting + TF-IDF/KMeans from MongoDB data
    caption_scorer       — Loads trained model and scores a caption in real-time
    hashtag_recommender  — Recommends hashtags based on content cluster similarity
    comment_analyser     — Multi-stage sentiment, intent and auto-reply analysis
"""
