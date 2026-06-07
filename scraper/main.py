import json
import os
import random
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

print("🚀 AI Device Manager Started -", datetime.now())

# ========== التاريخ المطلوب ==========
CUTOFF_DATE = datetime(2025, 1, 1)  # هضيف بس الأجهزة اللي تاريخها >= 1 يناير 2025

def get_firebase():
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    return None

def load_device_database():
    try:
        with open('scraper/devices_db.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            devices = data.get('devices', [])
            print(f"📂 Total devices in JSON: {len(devices)}")
            
            # تصفية: بس الأجهزة اللي ليها تاريخ إضافة (من الـ JSON) >= CUTOFF_DATE
            filtered = []
            for d in devices:
                added = d.get('addedDate', '')
                if added:
                    try:
                        added_date = datetime.fromisoformat(added.replace('Z', '+00:00'))
                        if added_date >= CUTOFF_DATE:
                            filtered.append(d)
                        else:
                            print(f"   🗑️ Skipping old device: {d.get('brand')} {d.get('model')} ({added})")
                    except:
                        filtered.append(d)  # لو التاريخ مش واضح، سيبه عادي
                else:
                    # لو مفيش addedDate، نضيفه (الأجهزة الجديدة اللي هتضاف بعدين)
                    filtered.append(d)
            
            print(f"✅ Kept (added after {CUTOFF_DATE.date()}): {len(filtered)} devices")
            return filtered
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return []

def get_existing_devices(db):
    existing = {}
    try:
        docs = db.collection('devices').stream()
        for doc in docs:
            data = doc.to_dict()
            key = f"{data.get('brand', '')}_{data.get('model', '')}"
            existing[key] = True
        print(f"📚 Found {len(existing)} devices in Firebase")
    except Exception as e:
        print(f"❌ Error: {e}")
    return existing

def add_device(db, device):
    try:
        max_fps = device.get("maxFPS", 60)
        graphics = {
            "smooth": max_fps,
            "balanced": 60 if max_fps >= 60 else 40,
            "hd": 60 if max_fps >= 60 else 40,
            "hdr": 40 if max_fps >= 90 else "غير مدعوم",
            "ultraHDR": "غير مدعوم",
            "extremeHDR": "غير مدعوم"
        }
        
        device_data = {
            "brand": device["brand"],
            "model": device["model"],
            "screenHz": device.get("screenHz", 90),
            "maxFPS": max_fps,
            "priceEGP": device.get("priceEGP", 0),
            "category": device.get("category", "midrange"),
            "priceCategory": device.get("priceCategory", "mid"),
            "image": device.get("image", ""),
            "addedDate": datetime.now().isoformat(),
            "graphics": graphics
        }
        
        db.collection("devices").add(device_data)
        print(f"   ✅ Added: {device['brand']} {device['model']}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def main():
    db = get_firebase()
    if not db:
        print("❌ Cannot continue")
        return
    
    all_devices = load_device_database()
    if not all_devices:
        print("❌ No devices to add")
        return
    
    existing = get_existing_devices(db)
    
    new_devices = []
    for device in all_devices:
        key = f"{device['brand']}_{device['model']}"
        if key not in existing:
            new_devices.append(device)
    
    print(f"🆕 New devices to add: {len(new_devices)}")
    
    if len(new_devices) == 0:
        print("✅ All devices already in Firebase")
        return
    
    devices_to_add = random.sample(new_devices, min(5, len(new_devices)))
    print(f"📊 Today's batch: {len(devices_to_add)} devices")
    
    added = 0
    for device in devices_to_add:
        if add_device(db, device):
            added += 1
    
    print(f"✅ Added {added} new devices today")

if __name__ == "__main__":
    main()
