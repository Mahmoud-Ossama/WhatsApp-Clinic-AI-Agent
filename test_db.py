from pymongo import MongoClient

def test_connection():
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['dr_wasim_db']
        
        # Test connection by listing collections
        collections = db.list_collection_names()
        print("Connected successfully!")
        print("Collections:", collections)
        
        # Test user collection
        admin_user = db.users.find_one({'username': 'admin'})
        if admin_user:
            print("Admin user exists!")
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

if __name__ == '__main__':
    test_connection()
