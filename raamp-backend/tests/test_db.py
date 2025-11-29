from pymongo import MongoClient

client = MongoClient(
    "mongodb+srv://username:password@ac-1oyk1hi-shard-00-00.vtcx7x1.mongodb.net/test?retryWrites=true&w=majority&tls=true"
)
db = client.get_database("your_db_name")
print(db.list_collection_names())
