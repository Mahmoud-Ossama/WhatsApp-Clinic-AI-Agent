from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB Atlas using environment variables
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB_NAME', 'dr_wasim_db')]

def init_remote_db():
    print(f"Connecting to MongoDB Atlas: {os.getenv('MONGODB_URI')}")
    print(f"Using database: {os.getenv('MONGODB_DB_NAME', 'dr_wasim_db')}")
    
    # Create collections if they don't exist
    collections = ['users', 'patients', 'injections', 'followups', 'message_history']
    existing_collections = db.list_collection_names()
    
    for collection in collections:
        try:
            if collection not in existing_collections:
                db.create_collection(collection)
                print(f"Created collection: {collection}")
            else:
                print(f"Collection already exists: {collection}")
        except Exception as e:
            print(f"Error with collection {collection}: {str(e)}")

    # Create indexes
    try:
        db.patients.create_index('phone', unique=True)
        db.injections.create_index('patient_id')
        db.followups.create_index([('patient_id', 1), ('scheduled_date', 1)])
        db.message_history.create_index([('phone', 1), ('timestamp', -1)])
        print("Indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")

    # Create admin user if doesn't exist
    try:
        if not db.users.find_one({'username': 'admin'}):
            db.users.insert_one({
                'username': 'admin',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'created_at': datetime.utcnow()
            })
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
            
        # Print all users for verification
        users = list(db.users.find({}, {'_id': 0, 'username': 1, 'role': 1}))
        print(f"Users in database: {users}")
        
    except Exception as e:
        print(f"Error with admin user: {str(e)}")

if __name__ == '__main__':
    print("Initializing remote MongoDB Atlas database...")
    init_remote_db()
    print("Remote database initialization completed!")
