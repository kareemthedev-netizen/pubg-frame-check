import json
import os
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

print("🚀 AI Smart Device Manager Started -", datetime.now())

# ========================================
# تحميل قاعدة البيانات من ملف JSON
# ========================================

def load_device_database():
    """قراءة قاعدة البيانات من ملف JSON"""
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
# جلب الأسعار من السوق المصري (API تجريبي)
# ========================================

def fetch_egyptian_price(device):
    """محاولة جلب السعر من السوق المصري"""
    # هذه مرحلة مستقبلية: ربط بـ API حقيقي (أمازون مصر، سوق.كوم)
    # حالياً نرجع السعر الافتراضي من قاعدة البيانات
    return device.get('priceEGP', None)

# ========================================
# إضافة أو تحديث جهاز في Firebase
# ========================================

def add_or_update_device(db, device):
    try:
        # البحث عن الجهاز في Firebase
        existing = db.collection('devices').where('brand', '==', device['brand']).where('model', '==', device['model']).get()
        
        # تحضير البيانات
        device_data = {
            "brand": device["brand"],
            "model": device["model"],
            "screenHz": device["screenHz"],
            "maxFPS": device["maxFPS"],
            "category": device["category"],
            "priceCategory": device["priceCategory"],
            "image": device["image"],
            "graphics": device["graphics"],
            "last_updated": datetime.now().isoformat(),
            "verified": True,
            "source": "official_database"
        }
        
        # جلب السعر الحقيقي من السوق
        price = fetch_egyptian_price(device)
        if price:
            device_data["priceEGP"] = price
        
        if existing:
            # تحديث الجهاز الموجود
            doc_id = existing[0].id
            db.collection('devices').document(doc_id).update(device_data)
            print(f"🔄 Updated: {device['brand']} {device['model']}")
        else:
            # إضافة جهاز جديد
            db.collection('devices').add(device_data)
            print(f"✅ Added: {device['brand']} {device['model']} ({device['maxFPS']} FPS)")
            
    except Exception as e:
        print(f"❌ Failed: {device['brand']} {device['model']} - {e}")

# ========================================
# الوظيفة الرئيسية
# ========================================

def main():
    print("=" * 50)
    print("🤖 AI Smart Device Manager")
    print("=" * 50)
    
    # تحميل قاعدة البيانات
    devices = load_device_database()
    if not devices:
        print("❌ No devices found in database")
        return
    
    print(f"📚 Loaded {len(devices)} devices from database")
    
    # الاتصال بـ Firebase
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    # إضافة أو تحديث كل جهاز
    count = 0
    for device in devices:
        add_or_update_device(db, device)
        count += 1
    
    print("=" * 50)
    print(f"✅ Processed {count} devices")
    print("🏁 Finished at:", datetime.now())

if __name__ == "__main__":
    main()
