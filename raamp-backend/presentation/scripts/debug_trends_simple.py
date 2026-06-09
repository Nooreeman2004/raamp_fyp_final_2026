import asyncio
from pymongo import MongoClient

def check():
    client = MongoClient('mongodb://localhost:27017')
    db = client.raamp
    collection = db.TrendDetectionModel
    
    count = collection.count_documents({})
    print(f"TOTAL_TRENDS: {count}")
    
    for t in collection.find().limit(5):
        print(f"TREND: {t.get('keyword')} | USER: {t.get('user_id')} | NICHE: {t.get('niche')}")

if __name__ == "__main__":
    check()
