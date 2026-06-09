import os
from dotenv import load_dotenv

load_dotenv('.env')

print('Checking environment variables...')
mongodb = os.getenv('MONGODB_URI')
gemini = os.getenv('GEMINI_API_KEY')
openai = os.getenv('OPENAI_API_KEY')

print(f'MONGODB_URI: {"SET" if mongodb else "NOT SET"}')
print(f'GEMINI_API_KEY: {"SET" if gemini else "NOT SET"}')
print(f'OPENAI_API_KEY: {"SET" if openai else "NOT SET"}')

if not mongodb:
    print('\n❌ MONGODB_URI is not set - cannot connect to database')
if not gemini and not openai:
    print('\n❌ No AI API keys set - AI analysis will fail')
