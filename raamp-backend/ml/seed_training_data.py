"""
seed_training_data.py — RAAMP ML Training Data Seeder
=====================================================
Populates caption_logs.engagement_rate with heuristic synthetic values,
then immediately trains the ML model.

Usage:
    python seed_training_data.py            # seed + train
    python seed_training_data.py --dry-run  # preview only, no DB writes
    python seed_training_data.py --force    # re-seed even already-seeded docs
"""

import argparse
import asyncio
import os
import random
import sys
# Add the backend root (one level up) to sys.path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from pymongo import UpdateOne

load_dotenv()

# ── Warning banner ─────────────────────────────────────────────────────────────
print("""⚠️  SYNTHETIC DATA MODE: engagement rates are heuristic estimates.
 This seeds the ML model for demo/FYP purposes.
 Retrain with real data once Instagram ROI metrics populate.
""")

# ── CLI flags ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Seed synthetic engagement data + train ML")
parser.add_argument("--dry-run", action="store_true", help="Preview what would be seeded — no DB writes or training")
parser.add_argument("--force", action="store_true", help="Re-seed docs that already have engagement_rate (overwrites)")
args = parser.parse_args()

DRY_RUN = args.dry_run
FORCE = args.force

# ── CTA keywords ───────────────────────────────────────────────────────────────
CTA_KEYWORDS = ["click", "link in bio", "shop", "buy", "dm", "order", "book", "reserve", "visit"]


# ── Heuristic engagement rate calculator ──────────────────────────────────────
def compute_engagement_rate(
    caption_text: str,
    tone: str,
    hashtags: list,
    published_at: datetime | None,
    industry: str | None
) -> float:
    rate = 0.03  # base rate

    # TONE multipliers
    tone_lower = (tone or "").lower()
    if "professional" in tone_lower: rate += 0.005
    elif "casual" in tone_lower: rate += 0.012
    elif "humorous" in tone_lower: rate += 0.018
    elif "inspirational" in tone_lower: rate += 0.015
    elif "urgent" in tone_lower: rate += 0.008

    # HASHTAG COUNT multipliers
    n_tags = len(hashtags) if isinstance(hashtags, list) else 0
    if 0 <= n_tags <= 3: rate += -0.005
    elif 4 <= n_tags <= 7: rate += 0.008
    elif 8 <= n_tags <= 12: rate += 0.015
    elif n_tags >= 13: rate += 0.005

    # CAPTION LENGTH multipliers
    length = len(caption_text or "")
    if length < 50: rate += -0.003
    elif 50 <= length <= 150: rate += 0.010
    elif 151 <= length <= 300: rate += 0.007
    elif length > 300: rate += -0.002

    # TIME OF DAY multipliers (published_at hour UTC)
    if published_at:
        hour = published_at.hour
        if 6 <= hour <= 9: rate += 0.012
        elif 11 <= hour <= 13: rate += 0.008
        elif 18 <= hour <= 21: rate += 0.018

    # CTA BONUS
    text_lower = (caption_text or "").lower()
    if any(kw in text_lower for kw in CTA_KEYWORDS):
        rate += 0.010

    # INDUSTRY multipliers
    ind_lower = (industry or "").lower()
    if "restaurant" in ind_lower: rate += 0.005
    elif "fashion" in ind_lower: rate += 0.008
    elif "fitness" in ind_lower: rate += 0.006

    # NOISE
    rate += random.uniform(-0.005, 0.005)

    # CLAMP
    return round(max(0.005, min(0.15, rate)), 6)


# ── Main seeding + training function ──────────────────────────────────────────
async def main():
    # ── 1. Connect to MongoDB ──────────────────────────────────────────────────
    print("🔗 Connecting to MongoDB...")
    from infrastructure.database.database import connect_to_mongo, init_db
    await connect_to_mongo()
    await init_db()

    from infrastructure.database.models.caption_log_model import CaptionLogModel

    # ── 2. Pull target documents ──────────────────────────────────────────────
    if FORCE:
        docs = await CaptionLogModel.find(CaptionLogModel.caption_text != None).to_list()
    else:
        docs = await CaptionLogModel.find(
            CaptionLogModel.engagement_rate == None,
            CaptionLogModel.caption_text != None
        ).to_list()

    total = len(docs)
    if total == 0:
        print("✅ All captions already have engagement_rate" if not FORCE else "No captions found to seed.")
        return

    print(f"✅ Connected. Found {total} captions to seed.")

    if DRY_RUN:
        for doc in docs[:3]:
            pub_at = getattr(doc, 'published_at', getattr(doc, 'last_used_at', getattr(doc, 'created_at', None)))
            ind = getattr(doc, 'industry', None)
            er = compute_engagement_rate(doc.caption_text, doc.tone, doc.hashtags, pub_at, ind)
            print(f"DRY RUN: tone={doc.tone}, text={doc.caption_text[:30]}... -> ER={er}")
        print("🚫 Dry run complete. No changes made.")
        return


    # ── 4. Update MongoDB documents ───────────────────────────────────────
    from motor.motor_asyncio import AsyncIOMotorClient
    from infrastructure.database.database import client as motor_client
    db = motor_client["raamp_db"]
    collection = db["caption_logs"]

    bulk_ops = []
    for i, doc in enumerate(docs, start=1):
        # Use last_used_at or created_at as fallback for published_at
        pub_at = getattr(doc, 'published_at', getattr(doc, 'last_used_at', getattr(doc, 'created_at', None)))
        ind = getattr(doc, 'industry', None)
        
        er = compute_engagement_rate(
            caption_text=doc.caption_text, 
            tone=doc.tone, 
            hashtags=doc.hashtags, 
            published_at=pub_at, 
            industry=ind
        )
        bulk_ops.append(UpdateOne({"_id": doc.id}, {"$set": {"engagement_rate": er}}))
        
        if i % 10 == 0 or i == total:
            print(f"Seeded {i}/{total}...")


    if bulk_ops:
        await collection.bulk_write(bulk_ops)
        print(f"✅ Seeded {total} documents successfully.")

    # ── 5. Run training automatically ──────────────────────────────────────────
    print("🤖 Training ML model...")
    from ml.model_trainer import train_models, ColdStartError

    try:
        metrics = await train_models()
        print(f"📊 Training complete:")
        print(f"   R²:               {metrics['r2']}")
        print(f"   RMSE:             {metrics['rmse']}")
        print(f"   MAE:              {metrics['mae']}")
        print(f"   Training samples: {metrics['sample_size']}")
        print("🎉 Done! Model ready. Test with POST /api/ml/score-post")
    except ColdStartError as e:
        print(f"❌ ColdStartError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
