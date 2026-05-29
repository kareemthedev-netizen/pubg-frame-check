import json
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import random

print("🚀 AI Smart Device Manager (5 devices per day) -", datetime.now())

# ========================================
# تحميل قاعدة البيانات
# ========================================

def load_device_database():
    try:
        with open('scraper/devices_db.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('devices', [])
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return []

# ========================================
# الاتصال بـ Firebase
# ========================================

def get_firebase():
    try:
        cred_json = os.environ.get('FIREBASE_CREDENTIALS')
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        else:
            print("⚠️ No Firebase credentials found")
            return None
    except Exception as e:
        print(f"❌ Firebase init error: {e}")
        return None

# ========================================
# جلب الأجهزة الموجودة في Firebase
# ========================================

def get_existing_device_keys(db):
    """جلب أسماء الأجهزة الموجودة في Firebase"""
    existing = set()
    try:
        docs = db.collection('devices').stream()
        for doc in docs:
            data = doc.to_dict()
            key = f"{data.get('brand', '')}_{data.get('model', '')}"
            existing.add(key)
    except Exception as e:
        print(f"❌ Error: {e}")
    return existing

# ========================================
# إضافة جهاز جديد إلى Firebase
# ========================================

def add_device(db, device):
    try:
        graphics = {
            "smooth": device["maxFPS"],
            "balanced": 60 if device["maxFPS"] >= 60 else 40,
            "hd": 60 if device["maxFPS"] >= 60 else 40,
            "hdr": 40 if device["maxFPS"] >= 90 else "غير مدعوم",
            "ultraHDR": "غير مدعوم",
            "extremeHDR": "غير مدعوم"
        }
        
        device_data = {
            "brand": device["brand"],
            "model": device["model"],
            "screenHz": device["screenHz"],
            "maxFPS": device["maxFPS"],
            "priceEGP": device.get("priceEGP", 0),
            "category": device.get("category", "midrange"),
            "priceCategory": device.get("priceCategory", "mid"),
            "image": device["image"],
            "views": 0,  # views تبدأ من صفر
            "addedDate": datetime.now().isoformat(),
            "graphics": graphics
        }
        
        db.collection("devices").add(device_data)
        print(f"✅ Added: {device['brand']} {device['model']} ({device['maxFPS']} FPS)")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

# ========================================
# الوظيفة الرئيسية (تضيف 5 أجهزة بس كل يوم)
# ========================================

def main():
    print("=" * 50)
    print("🤖 AI Device Manager (5 devices per day)")
    print("=" * 50)
    
    # تحميل كل الأجهزة من قاعدة البيانات
    all_devices = load_device_database()
    if not all_devices:
        print("❌ No devices found in database")
        return
    
    print(f"📚 Total devices in database: {len(all_devices)}")
    
    # الاتصال بـ Firebase
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    # جلب الأجهزة الموجودة حالياً
    existing_keys = get_existing_device_keys(db)
    print(f"📱 Existing devices in Firebase: {len(existing_keys)}")
    
    # تصفية الأجهزة اللي لسة مش موجودة
    new_devices = [d for d in all_devices if f"{d['brand']}_{d['model']}" not in existing_keys]
    print(f"🆕 New devices waiting to be added: {len(new_devices)}")
    
    if not new_devices:
        print("✅ No new devices to add today")
        return
    
    # اختيار 5 أجهزة عشوائية من الجدد (أو كلهم لو أقل من 5)
    devices_to_add = random.sample(new_devices, min(5, len(new_devices)))
    
    print(f"📊 Today's batch: {len(devices_to_add)} devices")
    print("=" * 50)
    
    # إضافة الأجهزة
    added_count = 0
    for device in devices_to_add:
        if add_device(db, device):
            added_count += 1
    
    print("=" * 50)
    print(f"✅ Added {added_count} new devices today")
    print(f"📊 Total devices now: {len(existing_keys) + added_count}")
    print(f"⏳ Remaining devices in queue: {len(new_devices) - added_count}")
    print("🏁 Finished at:", datetime.now())

if __name__ == "__main__":
    main()
