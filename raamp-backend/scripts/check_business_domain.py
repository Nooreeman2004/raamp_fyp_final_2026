"""
Check what the business_domain ObjectId was pointing to
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv('.env')

mongodb_uri = os.getenv('MONGODB_URL') or os.getenv('MONGODB_URI') or os.getenv('MONGO_URI') or 'mongodb://localhost:27017'
db_name = 'raamp_db'

print('='*70)
print('CHECK BUSINESS DOMAIN REFERENCE')
print('='*70)

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    print('✅ Connected to MongoDB\n')
    
    db = client[db_name]
    
    # The business_domain ObjectId that was stored
    domain_id = '6925f43ab14d8328c6ede40c'
    
    print(f'Looking for business_domain with ID: {domain_id}\n')
    
    # Check if there's a business_domains collection
    collections = db.list_collection_names()
    print(f'Available collections: {[c for c in collections if "domain" in c.lower() or "business" in c.lower()]}\n')
    
    # Try to find in various possible collections
    for collection_name in ['business_domains', 'domains', 'niches', 'categories']:
        if collection_name in collections:
            print(f'Checking {collection_name} collection...')
            try:
                doc = db[collection_name].find_one({'_id': ObjectId(domain_id)})
                if doc:
                    print(f'✅ Found in {collection_name}:')
                    print(f'   {doc}')
                else:
                    print(f'   Not found in {collection_name}')
            except Exception as e:
                print(f'   Error: {e}')
            print()
    
    print('='*70)
    
except Exception as e:
    print(f'\n❌ ERROR: {e}')
    import traceback
    traceback.print_exc()
