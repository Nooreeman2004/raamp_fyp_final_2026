"""
Query business information for a specific user email
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('.env')

# Get MongoDB URI from environment
mongodb_uri = os.getenv('MONGODB_URL') or os.getenv('MONGODB_URI') or 'mongodb://localhost:27017'
db_name = 'raamp_db'

user_email = 'abdullah@gmail.com'

print('='*70)
print(f'CHECKING BUSINESS FOR: {user_email}')
print('='*70)
print(f'\nConnecting to: {mongodb_uri[:50]}...')
print(f'Database: {db_name}\n')

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    print('✅ Connected to MongoDB\n')
    
    db = client[db_name]
    
    # 1. Find user
    print('1. USER INFORMATION:')
    print('-'*70)
    user = db.users.find_one({'email': user_email})
    
    if not user:
        print(f'❌ User not found: {user_email}')
    else:
        print(f'✅ User found:')
        print(f'  Email: {user.get("email")}')
        print(f'  Name: {user.get("name", "N/A")}')
        print(f'  User ID: {user.get("_id")}')
        print(f'  Created: {user.get("created_at", "N/A")}')
        print(f'  Verified: {user.get("is_verified", False)}')
        
        # 2. Find business locations
        print('\n2. BUSINESS LOCATIONS:')
        print('-'*70)
        businesses = list(db.business_locations.find({'user_email': user_email}))
        
        if not businesses:
            print(f'❌ No business locations found for {user_email}')
        else:
            print(f'✅ Found {len(businesses)} business location(s):\n')
            
            for i, business in enumerate(businesses, 1):
                print(f'Business {i}:')
                print(f'  Business Name: {business.get("business_name", "N/A")}')
                print(f'  Business ID: {business.get("_id")}')
                print(f'  Industry: {business.get("industry", "N/A")}')
                print(f'  Address: {business.get("address", "N/A")}')
                print(f'  City: {business.get("city", "N/A")}')
                print(f'  Country: {business.get("country", "N/A")}')
                
                # Location coordinates
                location = business.get("location", {})
                if location:
                    coords = location.get("coordinates", [])
                    if coords:
                        print(f'  Coordinates: [{coords[0]}, {coords[1]}]')
                
                print(f'  Confirmed: {business.get("is_confirmed", False)}')
                print(f'  Created: {business.get("created_at", "N/A")}')
                print()
        
        # 3. Check trend signals
        print('3. TREND SIGNALS:')
        print('-'*70)
        signals = list(db.trend_signals.find({'user_email': user_email}).sort('created_at', -1).limit(5))
        
        if not signals:
            print(f'No trend signals found for {user_email}')
        else:
            print(f'Found {len(signals)} trend signal(s):\n')
            for i, signal in enumerate(signals, 1):
                print(f'Signal {i}:')
                print(f'  Niche: {signal.get("niche")}')
                print(f'  Location: {signal.get("location")}')
                print(f'  Status: {signal.get("fetch_status")}')
                print(f'  Created: {signal.get("created_at")}')
                print()
    
    print('='*70)
    print('QUERY COMPLETE')
    print('='*70)
    
except Exception as e:
    print(f'\n❌ ERROR: {e}')
    print(f'\nCurrent MONGODB_URI: {mongodb_uri}')

