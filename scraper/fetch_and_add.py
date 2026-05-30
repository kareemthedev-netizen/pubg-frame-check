import requests
import json
import os
import sys
import re
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

search_query = sys.argv[1] if len(sys.argv) > 1 else ""

print(f"🔍 Fetching device: {search_query}")

def get_firebase():
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    return None

def fetch_from_apify(query):
    """جلب بيانات الجهاز من Apify (مجاني)"""
    
    API_TOKEN = os.environ.get('APIFY_API_KEY')
    if not API_TOKEN:
        print("❌ No APIFY_API_KEY found")
        return None
    
    # استخدام Actor مجاني
    ACTOR_ID = "pear_fight~google-shopping-scraper"
    
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={API_TOKEN}"
    
    input_data = {
        "searchQueries": [query],
        "maxResults": 1,
        "country": "EG",
        "currency": "EGP"
    }
    
    try:
        # تشغيل الـ Actor
        response = requests.post(url, json=input_data)
        run_data = response.json()
        
        if 'data' not in run_data:
            print("❌ Failed to start Actor")
            return None
        
        run_id = run_data['data']['id']
        
        # انتظار النتيجة
        import time
        time.sleep(15)
        
        # جلب النتائج
        dataset_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}/dataset/items?token={API_TOKEN}"
        dataset_response = requests.get(dataset_url)
        items = dataset_response.json()
        
        if items and len(items) > 0:
            item = items[0]
            return {
                "name": item.get("title", query),
                "price": item.get("price", 0),
                "image": item.get("image", ""),
                "rating": item.get("rating", 0),
                "seller": item.get("seller", "")
            }
    except Exception as e:
        print(f"❌ Apify error: {e}")
    
    return None

def clean_price(price_str):
    """تحويل السعر من نص لرقم"""
    if not price_str:
        return 0
    numbers = re.findall(r'\d+', str(price_str))
    if numbers:
        return int(''.join(numbers))
    return 0

def add_device_to_firebase(db, device_data, search_query):
    """إضافة الجهاز إلى Firebase"""
    
    # استخراج الماركة والموديل
    name_parts = device_data["name"].split()
    brand = name_parts[0] if name_parts else "Unknown"
    model = " ".join(name_parts[1:]) if len(name_parts) > 1 else search_query
    
    # تحديد الفريمات
    price = clean_price(device_data.get("price", 0))
    name_lower = device_data["name"].lower()
    
    if "ultra" in name_lower or "pro max" in name_lower or "rog" in name_lower:
        max_fps, screen_hz = 120, 120
    elif "pro" in name_lower or "plus" in name_lower:
        max_fps, screen_hz = 90, 120
    else:
        max_fps, screen_hz = 60, 90
    
    new_device = {
        "brand": brand,
        "model": model,
        "screenHz": screen_hz,
        "maxFPS": max_fps,
        "priceEGP": price,
        "category": "flagship" if price > 20000 else "midrange",
        "priceCategory": "premium" if price > 30000 else ("mid" if price > 10000 else "budget"),
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
        print(f"✅ Device added! ID: {doc_ref[1].id}")
        print(f"   📱 {brand} {model}")
        print(f"   💰 {price} EGP")
        print(f"   ⚡ {max_fps} FPS")
        return doc_ref[1].id
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def main():
    print("=" * 50)
    print("📱 AI Device Fetcher (Apify)")
    print("=" * 50)
    
    if not search_query:
        print("❌ No search query")
        return
    
    db = get_firebase()
    if not db:
        print("❌ Firebase connection failed")
        return
    
    print("✅ Firebase connected")
    
    device_data = fetch_from_apify(search_query)
    
    if device_data:
        add_device_to_firebase(db, device_data, search_query)
    else:
        print("❌ Could not fetch device data")
        # استخدام بيانات تقديرية كبديل
        print("   ⚠️ Using fallback data...")
        fallback_data = {
            "name": search_query.title(),
            "price": 15000,
            "image": f"https://placehold.co/400x200/1a1a2e/e74c3c?text={search_query.replace(' ', '+')}"
        }
        add_device_to_firebase(db, fallback_data, search_query)

if __name__ == "__main__":
    main()
