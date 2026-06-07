import json
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

print("🗑️ Old Device Cleaner Started -", datetime.now())

CUTOFF_DATE = datetime(2025, 1, 1)

def get_firebase():
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    return None

def clean_old_devices(db):
    devices_ref = db.collection('devices')
    docs = devices_ref.stream()
    
    deleted = 0
    for doc in docs:
        data = doc.to_dict()
        added_date_str = data.get('addedDate', '')
        
        if added_date_str:
            try:
                added_date = datetime.fromisoformat(added_date_str.replace('Z', '+00:00'))
                if added_date < CUTOFF_DATE:
                    print(f"   🗑️ Deleting: {data.get('brand')} {data.get('model')} ({added_date.date()})")
                    doc.reference.delete()
                    deleted += 1
            except:
                pass
    
    return deleted

def main():
    db = get_firebase()
    if not db:
        print("❌ Cannot continue")
        return
    
    print("✅ Firebase connected")
    deleted = clean_old_devices(db)
    print(f"🗑️ Deleted {deleted} old devices (before 2025)")

if __name__ == "__main__":
    main()
