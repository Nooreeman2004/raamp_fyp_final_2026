"""
Fix abdullah@gmail.com business niche/type in database
"""
import os
import asyncio
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv('.env')

# Try to get MongoDB URI from environment or use default
mongodb_uri = os.getenv('MONGODB_URL') or os.getenv('MONGODB_URI') or os.getenv('MONGO_URI') or 'mongodb://localhost:27017'
db_name = 'raamp_db'

print('='*70)
print('FIX ABDULLAH NICHE - DATABASE UPDATE')
print('='*70)
print(f'\nConnecting to: {mongodb_uri[:50]}...')
print(f'Database: {db_name}')

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    print('✅ Connected to MongoDB\n')
    
    db = client[db_name]
    
    # 1. Find user abdullah@gmail.com
    print('1. FINDING USER:')
    print('-'*70)
    user = db.users.find_one({'email': 'abdullah@gmail.com'})
    
    if not user:
        print('❌ User abdullah@gmail.com not found')
        exit(1)
    
    print(f'✅ Found user: {user.get("email")}')
    print(f'   User ID: {user.get("_id")}')
    print(f'   Username: {user.get("username")}')
    print(f'   business_domain: {user.get("business_domain")}')
    print(f'   business_domain_name: {user.get("business_domain_name")}')
    
    user_id = str(user.get('_id'))
    
    # 2. Find business record
    print('\n2. FINDING BUSINESS RECORD:')
    print('-'*70)
    business = db.businesses.find_one({'user_id': user_id})
    
    if not business:
        print('❌ Business record not found')
        exit(1)
    
    print(f'✅ Found business:')
    print(f'   Business ID: {business.get("_id")}')
    print(f'   Business Name: {business.get("business_name")}')
    print(f'   Business Type: {business.get("business_type")}')
    print(f'   Tagline: {business.get("tagline")}')
    print(f'   City: {business.get("city")}')
    print(f'   Country: {business.get("country")}')
    
    # 3. Check if update is needed
    current_type = business.get('business_type')
    
    if current_type and current_type.lower() in ['cafe', 'restaurant']:
        print(f'\n✅ Business type is already correct: {current_type}')
        print('No update needed.')
    else:
        print(f'\n⚠️  Business type needs update: "{current_type}" -> "cafe"')
        
        # Ask for confirmation
        response = input('\nDo you want to update business_type to "cafe"? (yes/no): ')
        
        if response.lower() == 'yes':
            # Update business record
            result = db.businesses.update_one(
                {'_id': business.get('_id')},
                {'$set': {'business_type': 'cafe'}}
            )
            
            if result.modified_count > 0:
                print('✅ Successfully updated business_type to "cafe"')
            else:
                print('⚠️  No changes made (value might already be correct)')
        else:
            print('❌ Update cancelled')
    
    # 4. Check user fields that might interfere
    print('\n3. CHECKING USER FIELDS:')
    print('-'*70)
    
    if user.get('business_domain') or user.get('business_domain_name'):
        print(f'⚠️  User has business_domain fields:')
        print(f'   business_domain: {user.get("business_domain")}')
        print(f'   business_domain_name: {user.get("business_domain_name")}')
        print('\nNote: These fields might override business_type in frontend.')
        print('Consider removing them if they contain incorrect values.')
        
        response = input('\nDo you want to remove these fields? (yes/no): ')
        
        if response.lower() == 'yes':
            result = db.users.update_one(
                {'_id': user.get('_id')},
                {'$unset': {'business_domain': '', 'business_domain_name': ''}}
            )
            
            if result.modified_count > 0:
                print('✅ Successfully removed business_domain fields from user')
            else:
                print('⚠️  No changes made')
        else:
            print('❌ Update cancelled')
    else:
        print('✅ User has no conflicting business_domain fields')
    
    print('\n' + '='*70)
    print('DIAGNOSTIC AND FIX COMPLETE')
    print('='*70)
    print('\nNext steps:')
    print('1. Refresh the frontend page')
    print('2. Check console logs for "deriveBusinessNiche"')
    print('3. Verify that niche is now "cafe" instead of "fashion"')
    
except Exception as e:
    print(f'\n❌ ERROR: {e}')
    import traceback
    traceback.print_exc()
