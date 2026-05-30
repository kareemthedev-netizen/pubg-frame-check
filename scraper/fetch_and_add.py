import requests
import json
import os
import sys
import re
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

search_query = sys.argv[1] if len(sys.argv) > 1 else ""

print(f"🔍 Fetching device: {search_query}")
print(f"🚀 Started at: {datetime.now()}")

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
# جلب البيانات من Apify Actor
# ========================================

def fetch_from_apify(query):
    """جلب بيانات الجهاز من Apify Actor"""
    
    API_TOKEN = os.environ.get('APIFY_API_KEY')
    if not API_TOKEN:
        print("❌ No APIFY_API_KEY found")
        return None
    
    # Actor ID (Google Shopping Scraper)
    ACTOR_ID = "lucky1~google-shopping-scraper"
    
    # إعدادات التشغيل
    input_data = {
        "searchQueries": [query],
        "maxResults": 1,
        "country": "EG",
        "language": "en"
    }
    
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={API_TOKEN}"
    
    try:
        print(f"   🚀 Starting Actor...")
        response = requests.post(url, json=input_data)
        run_data = response.json()
        
        if 'data' not in run_data:
            print(f"   ❌ API Error: {run_data}")
            return None
        
        run_id = run_data['data']['id']
        print(f"   ⏳ Run ID: {run_id}, waiting for results...")
        
        # انتظار النتيجة (15-20 ثانية)
        time.sleep(20)
        
        # جلب النتائج
        dataset_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}/dataset/items?token={API_TOKEN}"
        dataset_response = requests.get(dataset_url)
        items = dataset_response.json()
        
        if items and len(items) > 0:
            item = items[0]
            print(f"   ✅ Found: {item.get('title', query)}")
            return {
                "name": item.get("title", query),
                "price": item.get("price", 0),
                "image": item.get("image", ""),
                "rating": item.get("rating", 0),
                "seller": item.get("seller", ""),
                "link": item.get("url", "")
            }
        else:
            print(f"   ❌ No results found")
            
    except Exception as e:
        print(f"   ❌ Apify error: {e}")
    
    return None

# ========================================
# تنظيف السعر
# ========================================

def clean_price(price_str):
    if not price_str:
        return 0
    if isinstance(price_str, (int, float)):
        return int(price_str)
    numbers = re.findall(r'\d+', str(price_str))
    if numbers:
        return int(''.join(numbers))
    return 0

# ========================================
# إضافة جهاز إلى Firebase
# ========================================

def add_device_to_firebase(db, device_data, search_query):
    """إضافة الجهاز الجديد إلى Firebase"""
    
    # استخراج الماركة والموديل
    name_parts = device_data["name"].split()
    brand = name_parts[0] if name_parts else "Unknown"
    model = " ".join(name_parts[1:]) if len(name_parts) > 1 else search_query
    
    # تنظيف السعر
    price = clean_price(device_data.get("price", 0))
    name_lower = device_data["name"].lower()
    
    # تحديد الفريمات بناءً على الاسم
    if "ultra" in name_lower or "pro max" in name_lower or "rog" in name_lower:
        max_fps = 120
        screen_hz = 120
        category = "flagship"
        price_category = "premium" if price > 30000 else "mid"
    elif "pro" in name_lower or "plus" in name_lower:
        max_fps = 90
        screen_hz = 120
        category = "flagship" if price > 20000 else "midrange"
        price_category = "premium" if price > 30000 else ("mid" if price > 10000 else "budget")
    else:
        max_fps = 60
        screen_hz = 90
        category = "midrange"
        price_category = "budget" if price < 10000 else "mid"
    
    # بناء الجهاز
    new_device = {
        "brand": brand,
        "model": model,
        "screenHz": screen_hz,
        "maxFPS": max_fps,
        "priceEGP": price,
        "category": category,
        "priceCategory": price_category,
        "image": device_data.get("image", ""),
        "addedDate": datetime.now().isoformat(),
        "source": "apify",
        "search_query": search_query,
        "graphics": {
            "smooth": max_fps,
            "balanced": 60 if max_fps >= 60 else 40,
            "hd": 60 if max_fps >= 60 else 40,
            "hdr": 40 if max_fps >= 90 else "غير مدعوم",
            "ultraHDR": "غير مدعوم",
            "extremeHDR": "غير مدعوم"
        }
    }
    
    try:
        doc_ref = db.collection("devices").add(new_device)
        print(f"   ✅ Device added! ID: {doc_ref[1].id}")
        print(f"   📱 {brand} {model}")
        print(f"   💰 {price} EGP")
        print(f"   ⚡ {max_fps} FPS")
        return doc_ref[1].id
    except Exception as e:
        print(f"   ❌ Failed to add device: {e}")
        return None

# ========================================
# التشغيل الرئيسي
# ========================================

def main():
    print("=" * 50)
    print("📱 AI Device Fetcher (Apify)")
    print("=" * 50)
    
    if not search_query:
        print("❌ No search query provided")
        return
    
    # الاتصال بـ Firebase
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    # جلب البيانات من Apify
    device_data = fetch_from_apify(search_query)
    
    if device_data:
        # إضافة الجهاز إلى Firebase
        device_id = add_device_to_firebase(db, device_data, search_query)
        
        if device_id:
            print("=" * 50)
            print(f"✅ Device added successfully!")
            print(f"📱 Name: {device_data['name']}")
            print(f"🆔 Firebase ID: {device_id}")
        else:
            print("❌ Failed to add device to Firebase")
    else:
        print("❌ Could not fetch device data from Apify")
        print("   ⚠️ Try running the Actor manually from Apify Console first")
    
    print("🏁 Finished at:", datetime.now())

if __name__ == "__main__":
    main()
