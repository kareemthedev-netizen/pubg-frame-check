import requests
import json
import os
from datetime import datetime
import sys

print("🚀 AI Auto Device Manager Started -", datetime.now())

# ========================================
# كل الأجهزة (موبايلات + تابلت)
# ========================================

DEVICES_LIST = [
    # ========== موبايلات 120 FPS ==========
    {"brand": "OnePlus", "model": "11 5G", "screenHz": 120, "maxFPS": 120, "priceEGP": 29999, "category": "flagship", "priceCategory": "premium", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/oneplus-11-5g.jpg"},
    {"brand": "ASUS", "model": "ROG Phone 8", "screenHz": 165, "maxFPS": 120, "priceEGP": 45000, "category": "flagship", "priceCategory": "premium", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/asus-rog-phone-8.jpg"},
    {"brand": "Nubia", "model": "RedMagic 9 Pro", "screenHz": 120, "maxFPS": 120, "priceEGP": 38000, "category": "flagship", "priceCategory": "premium", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/nubia-redmagic-9-pro.jpg"},
    
    # ========== موبايلات 90 FPS ==========
    {"brand": "OnePlus", "model": "10 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 22999, "category": "flagship", "priceCategory": "mid", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/oneplus-10-pro.jpg"},
    {"brand": "Poco", "model": "F4 GT", "screenHz": 120, "maxFPS": 90, "priceEGP": 15999, "category": "midrange", "priceCategory": "mid", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-f4-gt.jpg"},
    {"brand": "Poco", "model": "F5", "screenHz": 120, "maxFPS": 90, "priceEGP": 18999, "category": "midrange", "priceCategory": "mid", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-f5.jpg"},
    {"brand": "Poco", "model": "X6 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 18500, "category": "midrange", "priceCategory": "mid", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-x6-pro.jpg"},
    {"brand": "Samsung", "model": "Galaxy S23 Ultra", "screenHz": 120, "maxFPS": 90, "priceEGP": 59999, "category": "flagship", "priceCategory": "premium", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s23-ultra-5g.jpg"},
    {"brand": "Samsung", "model": "Galaxy S24 Ultra", "screenHz": 120, "maxFPS": 90, "priceEGP": 65000, "category": "flagship", "priceCategory": "premium", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s24-ultra.jpg"},
    {"brand": "Xiaomi", "model": "13T Pro", "screenHz": 144, "maxFPS": 90, "priceEGP": 26900, "category": "flagship", "priceCategory": "mid", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-13t-pro.jpg"},
    {"brand": "Xiaomi", "model": "12T Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 20999, "category": "midrange", "priceCategory": "mid", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-12t-pro.jpg"},
    {"brand": "Realme", "model": "GT Neo 3", "screenHz": 120, "maxFPS": 90, "priceEGP": 13999, "category": "midrange", "priceCategory": "budget", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/realme-gt-neo-3.jpg"},
    {"brand": "iPhone", "model": "14 Pro Max", "screenHz": 120, "maxFPS": 90, "priceEGP": 72999, "category": "flagship", "priceCategory": "premium", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-14-pro-max.jpg"},
    {"brand": "iPhone", "model": "15 Pro Max", "screenHz": 120, "maxFPS": 90, "priceEGP": 79999, "category": "flagship", "priceCategory": "premium", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-15-pro-max.jpg"},
    
    # ========== موبايلات 60 FPS ==========
    {"brand": "Samsung", "model": "Galaxy A73", "screenHz": 120, "maxFPS": 60, "priceEGP": 11999, "category": "midrange", "priceCategory": "budget", "type": "phone", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-a73-5g.jpg"},
    
    # ========== تابلت ==========
    {"brand": "Apple", "model": "iPad Pro 12.9 (2024)", "screenHz": 120, "maxFPS": 120, "priceEGP": 65000, "category": "tablet", "priceCategory": "premium", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-ipad-pro-12-9-2022.jpg"},
    {"brand": "Apple", "model": "iPad Pro 11 (2024)", "screenHz": 120, "maxFPS": 120, "priceEGP": 49000, "category": "tablet", "priceCategory": "premium", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-ipad-pro-11-2022.jpg"},
    {"brand": "Apple", "model": "iPad Air (2024)", "screenHz": 60, "maxFPS": 90, "priceEGP": 32000, "category": "tablet", "priceCategory": "mid", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-ipad-air-2022.jpg"},
    {"brand": "Apple", "model": "iPad mini (2024)", "screenHz": 60, "maxFPS": 60, "priceEGP": 24000, "category": "tablet", "priceCategory": "mid", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-ipad-mini-2021.jpg"},
    {"brand": "Samsung", "model": "Galaxy Tab S9 Ultra", "screenHz": 120, "maxFPS": 120, "priceEGP": 55000, "category": "tablet", "priceCategory": "premium", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-tab-s9-ultra.jpg"},
    {"brand": "Samsung", "model": "Galaxy Tab S9+", "screenHz": 120, "maxFPS": 90, "priceEGP": 40000, "category": "tablet", "priceCategory": "mid", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-tab-s9-plus.jpg"},
    {"brand": "Samsung", "model": "Galaxy Tab A9+", "screenHz": 90, "maxFPS": 60, "priceEGP": 15000, "category": "tablet", "priceCategory": "budget", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-tab-a9-plus.jpg"},
    {"brand": "Xiaomi", "model": "Pad 6 Pro", "screenHz": 144, "maxFPS": 90, "priceEGP": 25000, "category": "tablet", "priceCategory": "mid", "type": "tablet", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-pad-6-pro.jpg"},
]

# ========================================
# الاتصال بـ Firebase
# ========================================

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
        print(f"❌ Error: {e}")
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
            "type": device.get("type", "phone"),
            "image": device["image"],
            "addedDate": datetime.now().isoformat(),
            "graphics": graphics
        }
        
        db.collection("devices").add(device_data)
        print(f"✅ Added: {device['brand']} {device['model']} ({device['maxFPS']} FPS) - {device.get('type', 'phone')}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def main():
    print("=" * 50)
    print("🤖 AI Device Manager (Phones + Tablets)")
    print("=" * 50)
    
    phones = [d for d in DEVICES_LIST if d.get('type') == 'phone']
    tablets = [d for d in DEVICES_LIST if d.get('type') == 'tablet']
    
    print(f"📱 Phones: {len(phones)}")
    print(f"📟 Tablets: {len(tablets)}")
    print(f"📊 Total: {len(DEVICES_LIST)}")
    
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    existing = get_existing_devices(db)
    print(f"📚 Existing devices: {len(existing)}")
    
    new_count = 0
    for device in DEVICES_LIST:
        key = f"{device['brand']}_{device['model']}"
        if key not in existing:
            if add_device(db, device):
                new_count += 1
        else:
            print(f"⏭️ Skipping: {device['brand']} {device['model']}")
    
    print("=" * 50)
    print(f"📱 Added {new_count} new devices")
    print(f"📊 Total: {len(existing) + new_count}")
    print("🏁 Finished at:", datetime.now())

if __name__ == "__main__":
    main()
