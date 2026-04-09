"""
One-shot training script — run from raamp-backend/ directory.
Usage: python train_ml.py
"""
import asyncio
import sys
import os

# Add the backend root (one level up) to sys.path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def main():
    print("🔌 Connecting to MongoDB...")
    from infrastructure.database.database import connect_to_mongo, init_db
    await connect_to_mongo()
    await init_db()
    print("✅ MongoDB connected.\n")

    print("🤖 Starting ML training pipeline...")
    from ml.model_trainer import train_models, ColdStartError
    try:
        metrics = await train_models()
        print("\n" + "="*55)
        print("✅  TRAINING COMPLETE")
        print("="*55)
        print(f"  Sample size     : {metrics['sample_size']}")
        print(f"  R²              : {metrics['r2']}")
        print(f"  RMSE            : {metrics['rmse']}")
        print(f"  MAE             : {metrics['mae']}")
        print(f"  Clusters        : {metrics['n_clusters']}")
        print(f"  Silhouette      : {metrics['silhouette']}")
        print(f"  Trained at      : {metrics['trained_at']}")
        print("="*55)
        print(f"\n📁 Models saved to: raamp-backend/ml/models/")
    except ColdStartError as e:
        print("\n" + "="*55)
        print("❄️   COLD START — NOT ENOUGH DATA")
        print("="*55)
        print(f"\n{e}\n")
        print("ℹ️  To fix this: ensure caption_logs documents have")
        print("   'engagement_rate' populated (non-null) on at least 50 records.")
        print("   This field is set when Instagram ROI metrics are fetched.")

asyncio.run(main())
