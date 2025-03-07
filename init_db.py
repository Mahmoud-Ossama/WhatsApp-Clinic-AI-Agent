from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['dr_wasim_db']

def init_db():
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
    except Exception as e:
        print(f"Error with admin user: {str(e)}")

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialization completed!")
