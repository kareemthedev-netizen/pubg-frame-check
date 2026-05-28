import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import sys
import re

print("🚀 AI Auto Device Manager Started -", datetime.now())

# قائمة الأجهزة مع روابط صور GSMarena الصحيحة
DEVICES_DATABASE = [
    # 120 FPS
    {"brand": "OnePlus", "model": "11 5G", "screenHz": 120, "maxFPS": 120, "priceEGP": 29999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/oneplus-11-5g.jpg"},
    {"brand": "ASUS", "model": "ROG Phone 8", "screenHz": 165, "maxFPS": 120, "priceEGP": 45000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/asus-rog-phone-8.jpg"},
    {"brand": "Nubia", "model": "RedMagic 9 Pro", "screenHz": 120, "maxFPS": 120, "priceEGP": 38000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/nubia-redmagic-9-pro.jpg"},
    
    # 90 FPS
    {"brand": "OnePlus", "model": "10 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 22999, "category": "flagship", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/oneplus-10-pro.jpg"},
    {"brand": "Poco", "model": "F4 GT", "screenHz": 120, "maxFPS": 90, "priceEGP": 15999, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-f4-gt.jpg"},
    {"brand": "Poco", "model": "F5", "screenHz": 120, "maxFPS": 90, "priceEGP": 18999, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-f5.jpg"},
    {"brand": "Poco", "model": "X6 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 18500, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-x6-pro.jpg"},
    {"brand": "Samsung", "model": "Galaxy S23 Ultra", "screenHz": 120, "maxFPS": 90, "priceEGP": 59999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s23-ultra-5g.jpg"},
    {"brand": "Samsung", "model": "Galaxy S24 Ultra", "screenHz": 120, "maxFPS": 90, "priceEGP": 65000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s24-ultra.jpg"},
    {"brand": "Xiaomi", "model": "13T Pro", "screenHz": 144, "maxFPS": 90, "priceEGP": 26900, "category": "flagship", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-13t-pro.jpg"},
    {"brand": "Xiaomi", "model": "12T Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 20999, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-12t-pro.jpg"},
    {"brand": "Realme", "model": "GT Neo 3", "screenHz": 120, "maxFPS": 90, "priceEGP": 13999, "category": "midrange", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/realme-gt-neo-3.jpg"},
    {"brand": "iPhone", "model": "14 Pro Max", "screenHz": 120, "maxFPS": 90, "priceEGP": 72999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-14-pro-max.jpg"},
    {"brand": "iPhone", "model": "15 Pro Max", "screenHz": 120, "maxFPS": 90, "priceEGP": 79999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-15-pro-max.jpg"},
    
    # 60 FPS
    {"brand": "Samsung", "model": "Galaxy A73", "screenHz": 120, "maxFPS": 60, "priceEGP": 11999, "category": "midrange", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-a73-5g.jpg"},
]

def get_firebase():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        import json
        
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

def get_existing_devices(db):
    existing = {}
    try:
        docs = db.collection('devices').stream()
        for doc in docs:
            data = doc.to_dict()
            key = f"{data.get('brand', '')}_{data.get('model', '')}"
            existing[key] = {'id': doc.id, 'data': data}
    except Exception as e:
        print(f"❌ Error getting devices: {e}")
    return existing

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
            "priceEGP": device["priceEGP"],
            "category": device["category"],
            "priceCategory": device["priceCategory"],
            "image": device["image"],
            "addedDate": datetime.now().isoformat(),
            "graphics": graphics
        }
        
        db.collection("devices").add(device_data)
        print(f"✅ Added: {device['brand']} {device['model']} ({device['maxFPS']} FPS)")
        return True
    except Exception as e:
        print(f"❌ Failed to add {device['brand']} {device['model']}: {e}")
        return False

def fix_device_image(db, device_id, correct_image):
    """تحديث صورة جهاز موجود"""
    try:
        db.collection('devices').document(device_id).update({'image': correct_image})
        print(f"🖼️ Fixed image for device: {device_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to fix image: {e}")
        return False

def main():
    print("=" * 50)
    print("🤖 AI Auto Device Manager (with image fix)")
    print("=" * 50)
    
    stats = {120: 0, 90: 0, 60: 0}
    for d in DEVICES_DATABASE:
        stats[d["maxFPS"]] += 1
    
    print(f"📊 Devices in database:")
    print(f"   ⚡ 120 FPS: {stats[120]} devices")
    print(f"   🎯 90 FPS: {stats[90]} devices")
    print(f"   🟢 60 FPS: {stats[60]} devices")
    print(f"   📱 Total: {len(DEVICES_DATABASE)} devices")
    print("=" * 50)
    
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    existing = get_existing_devices(db)
    print(f"📚 Existing devices: {len(existing)}")
    
    # إضافة الأجهزة الجديدة وتحديث الصور
    new_count = 0
    fixed_count = 0
    
    for device in DEVICES_DATABASE:
        key = f"{device['brand']}_{device['model']}"
        
        if key in existing:
            # الجهاز موجود - نتحقق من الصورة
            current_image = existing[key]['data'].get('image', '')
            correct_image = device['image']
            
            if current_image != correct_image and 'placehold' not in correct_image:
                fix_device_image(db, existing[key]['id'], correct_image)
                fixed_count += 1
        else:
            # جهاز جديد
            if add_device(db, device):
                new_count += 1
    
    print("=" * 50)
    print(f"📱 Added {new_count} new devices")
    print(f"🖼️ Fixed images for {fixed_count} devices")
    print(f"📊 Total devices now: {len(existing) + new_count}")
    print("=" * 50)
    print("✅ AI Auto Device Manager finished!")
    print("🏁 Completed at:", datetime.now())

if __name__ == "__main__":
    main()
