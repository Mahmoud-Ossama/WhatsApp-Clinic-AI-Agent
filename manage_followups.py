from pymongo import MongoClient
from datetime import datetime
import argparse

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['dr_wasim_db']

def show_pending_followups():
    """Display all pending follow-ups"""
    pending = db.followups.find({
        'status': 'pending',
        'message_sent': False
    }).sort('scheduled_date', 1)

    print("\nPending Follow-ups:")
    print("-" * 80)
    for f in pending:
        print(f"Patient: {f['patient_name']}")
        print(f"Scheduled: {f['scheduled_date'].strftime('%Y-%m-%d %H:%M')}")
        print(f"Phone: {f.get('patient_phone', 'N/A')}")
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description='Manage follow-up messages')
    parser.add_argument('--show-pending', action='store_true', help='Show pending follow-ups')
    
    args = parser.parse_args()
    
    if args.show_pending:
        show_pending_followups()

if __name__ == '__main__':
    main()
