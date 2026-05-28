import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
import sys

print("🚀 AI Auto Device Manager with Web Scraping -", datetime.now())

# ========================================
# 1. إعدادات Firebase
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

# ========================================
# 2. قاعدة بيانات الأجهزة المضمونة (بدون Scraping)
# ========================================

# دي قائمة الأجهزة المعروفة اللي بتدعم فريمات عالية
# الـ AI هيضيفهم لو مش موجودين
DEVICES_FALLBACK = [
    # 120 FPS
    {"brand": "OnePlus", "model": "11 5G", "screenHz": 120, "maxFPS": 120, "priceEGP": 29999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/oneplus-11-5g.jpg"},
    {"brand": "ASUS", "model": "ROG Phone 8", "screenHz": 165, "maxFPS": 120, "priceEGP": 45000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/asus-rog-phone-8.jpg"},
    {"brand": "Nubia", "model": "RedMagic 9 Pro", "screenHz": 120, "maxFPS": 120, "priceEGP": 38000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/nubia-redmagic-9-pro.jpg"},
    {"brand": "Google", "model": "Pixel 8 Pro", "screenHz": 120, "maxFPS": 120, "priceEGP": 40000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/google-pixel-8-pro.jpg"},
    
    # 90 FPS
    {"brand": "OnePlus", "model": "10 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 22999, "category": "flagship", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/oneplus-10-pro.jpg"},
    {"brand": "Poco", "model": "F4 GT", "screenHz": 120, "maxFPS": 90, "priceEGP": 15999, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-f4-gt.jpg"},
    {"brand": "Poco", "model": "F5", "screenHz": 120, "maxFPS": 90, "priceEGP": 18999, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-f5.jpg"},
    {"brand": "Poco", "model": "X6 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 18500, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-x6-pro.jpg"},
    {"brand": "Samsung", "model": "Galaxy S23 Ultra", "screenHz": 120, "maxFPS": 90, "priceEGP": 59999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s23-ultra-5g.jpg"},
    {"brand": "Samsung", "model": "Galaxy S24 Ultra", "screenHz": 120, "maxFPS": 90, "priceEGP": 65000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s24-ultra.jpg"},
    {"brand": "Samsung", "model": "Galaxy S24 Plus", "screenHz": 120, "maxFPS": 90, "priceEGP": 45000, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-s24-plus.jpg"},
    {"brand": "Xiaomi", "model": "13T Pro", "screenHz": 144, "maxFPS": 90, "priceEGP": 26900, "category": "flagship", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-13t-pro.jpg"},
    {"brand": "Xiaomi", "model": "12T Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 20999, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-12t-pro.jpg"},
    {"brand": "Xiaomi", "model": "14", "screenHz": 120, "maxFPS": 90, "priceEGP": 35000, "category": "flagship", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-14.jpg"},
    {"brand": "Realme", "model": "GT Neo 3", "screenHz": 120, "maxFPS": 90, "priceEGP": 13999, "category": "midrange", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/realme-gt-neo-3.jpg"},
    {"brand": "Realme", "model": "GT 5G", "screenHz": 120, "maxFPS": 90, "priceEGP": 24999, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/realme-gt-5g.jpg"},
    {"brand": "iPhone", "model": "14 Pro Max", "screenHz": 120, "maxFPS": 90, "priceEGP": 72999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-14-pro-max.jpg"},
    {"brand": "iPhone", "model": "15 Pro Max", "screenHz": 120, "maxFPS": 90, "priceEGP": 79999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-15-pro-max.jpg"},
    {"brand": "iPhone", "model": "15 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 69999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/apple-iphone-15-pro.jpg"},
    {"brand": "Nothing", "model": "Phone 2", "screenHz": 120, "maxFPS": 90, "priceEGP": 30000, "category": "midrange", "priceCategory": "mid", "image": "https://fdn2.gsmarena.com/vv/bigpic/nothing-phone-2.jpg"},
    {"brand": "Honor", "model": "Magic 5 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 32999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/honor-magic5-pro.jpg"},
    {"brand": "Vivo", "model": "X90 Pro", "screenHz": 120, "maxFPS": 90, "priceEGP": 37999, "category": "flagship", "priceCategory": "premium", "image": "https://fdn2.gsmarena.com/vv/bigpic/vivo-x90-pro.jpg"},
    
    # 60 FPS
    {"brand": "Samsung", "model": "Galaxy A73", "screenHz": 120, "maxFPS": 60, "priceEGP": 11999, "category": "midrange", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-a73-5g.jpg"},
    {"brand": "Samsung", "model": "Galaxy A54", "screenHz": 120, "maxFPS": 60, "priceEGP": 10999, "category": "midrange", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/samsung-galaxy-a54.jpg"},
    {"brand": "Poco", "model": "M5", "screenHz": 90, "maxFPS": 60, "priceEGP": 8999, "category": "budget", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/xiaomi-poco-m5.jpg"},
    {"brand": "Realme", "model": "C55", "screenHz": 90, "maxFPS": 60, "priceEGP": 6999, "category": "budget", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/realme-c55.jpg"},
    {"brand": "Infinix", "model": "Note 30", "screenHz": 120, "maxFPS": 60, "priceEGP": 7999, "category": "budget", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/infinix-note-30.jpg"},
    {"brand": "Tecno", "model": "Pova 5", "screenHz": 120, "maxFPS": 60, "priceEGP": 7499, "category": "budget", "priceCategory": "budget", "image": "https://fdn2.gsmarena.com/vv/bigpic/tecno-pova-5.jpg"},
]

# ========================================
# 3. تحديث Firebase
# ========================================

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

def add_device(db, device_data):
    try:
        graphics = {
            "smooth": device_data["maxFPS"],
            "balanced": 60 if device_data["maxFPS"] >= 60 else 40,
            "hd": 60 if device_data["maxFPS"] >= 60 else 40,
            "hdr": 40 if device_data["maxFPS"] >= 90 else "غير مدعوم",
            "ultraHDR": "غير مدعوم",
            "extremeHDR": "غير مدعوم"
        }
        
        new_device = {
            "brand": device_data["brand"],
            "model": device_data["model"],
            "screenHz": device_data["screenHz"],
            "maxFPS": device_data["maxFPS"],
            "priceEGP": device_data["priceEGP"],
            "category": device_data["category"],
            "priceCategory": device_data["priceCategory"],
            "image": device_data["image"],
            "addedDate": datetime.now().isoformat(),
            "graphics": graphics
        }
        
        db.collection("devices").add(new_device)
        print(f"✅ Added: {device_data['brand']} {device_data['model']} ({device_data['maxFPS']} FPS)")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def update_device_price(db, device_id, new_price):
    try:
        db.collection('devices').document(device_id).update({
            'priceEGP': new_price,
            'last_price_update': datetime.now().isoformat()
        })
        print(f"💰 Price updated: {device_id} → {new_price} EGP")
    except Exception as e:
        print(f"❌ Update error: {e}")

def update_device_image(db, device_id, new_image):
    try:
        db.collection('devices').document(device_id).update({
            'image': new_image,
            'last_image_update': datetime.now().isoformat()
        })
        print(f"🖼️ Image updated: {device_id}")
    except Exception as e:
        print(f"❌ Image error: {e}")

# ========================================
# 4. الوظيفة الرئيسية
# ========================================

def main():
    print("=" * 50)
    print("🤖 AI Auto Device Manager")
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
    
    for device in DEVICES_FALLBACK:
        key = f"{device['brand']}_{device['model']}"
        
        if key in existing:
            # الجهاز موجود - نتحقق من الصورة
            current_image = existing[key]['data'].get('image', '')
            if current_image != device['image'] and 'placehold' not in device['image']:
                update_device_image(db, existing[key]['id'], device['image'])
                fixed_count += 1
        else:
            # جهاز جديد
            if add_device(db, device):
                new_count += 1
    
    print("=" * 50)
    print(f"📱 New devices added: {new_count}")
    print(f"🖼️ Images fixed: {fixed_count}")
    print(f"📊 Total devices now: {len(existing) + new_count}")
    print("=" * 50)
    print("✅ AI Auto Device Manager finished!")
    print("🏁 Completed at:", datetime.now())

if __name__ == "__main__":
    main()
