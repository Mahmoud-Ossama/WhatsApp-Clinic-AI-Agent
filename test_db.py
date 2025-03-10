from pymongo import MongoClient
import os
from dotenv import load_dotenv

def test_atlas_connection():
    try:
        load_dotenv()
        print("Testing MongoDB Atlas connection...")
        print(f"Using URI: {os.getenv('MONGODB_URI')}")
        
        # Connect to MongoDB Atlas
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client[os.getenv('MONGODB_DB_NAME', 'dr_wasim_db')]
        
        # Test connection by listing collections
        collections = db.list_collection_names()
        print("\nConnection successful!")
        print(f"Available collections: {collections}")
        
        # Test read operations
        print("\nTesting collections:")
        for collection in ['users', 'patients', 'followups']:
            count = db[collection].count_documents({})
            print(f"{collection}: {count} documents")
            
        client.close()
        print("\nConnection test completed successfully!")
        
    except Exception as e:
        print(f"\nError connecting to MongoDB Atlas: {str(e)}")
        print("\nPlease check:")
        print("1. Internet connection")
        print("2. MongoDB Atlas whitelist (your IP address)")
        print("3. Username and password in connection string")
        print("4. Database name")

if __name__ == '__main__':
    test_atlas_connection()
