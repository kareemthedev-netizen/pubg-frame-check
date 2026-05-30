import requests
import json
import os
import sys
import re
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from apify_client import ApifyClient

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

def fetch_from_google_shopping(query):
    api_key = os.environ.get('APIFY_API_KEY')
    if not api_key:
        return None
    
    try:
        client = ApifyClient(api_key)
        run_input = {
            "searchTerms": [query],
            "maxResults": 1,
            "country": "EG",
            "currency": "EGP"
        }
        run = client.actor("compass/google-shopping-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if items:
            item = items[0]
            return {
                "name": item.get("title", query),
                "price": item.get("price", 0),
                "image": item.get("image", ""),
                "link": item.get("link", "")
            }
    except Exception as e:
        print(f"Apify error: {e}")
    return None

def add_device_to_firebase(db, device_data, search_query):
    name_parts = device_data["name"].split()
    brand = name_parts[0] if name_parts else "Unknown"
    model = " ".join(name_parts[1:]) if len(name_parts) > 1 else search_query
    
    # تقدير الفريمات
    price = device_data.get("price", 0)
    if "iphone" in model.lower() or "samsung" in model.lower():
        max_fps, screen_hz = 90, 120
    elif price > 45000:
        max_fps, screen_hz = 120, 120
    elif price > 25000:
        max_fps, screen_hz = 90, 120
    else:
        max_fps, screen_hz = 60, 90
    
    new_device = {
        "brand": brand,
        "model": model,
        "screenHz": screen_hz,
        "maxFPS": max_fps,
        "priceEGP": int(price) if price else 0,
        "category": "flagship" if price > 20000 else "midrange",
        "priceCategory": "premium" if price > 30000 else ("mid" if price > 10000 else "budget"),
        "image": device_data.get("image", ""),
        "addedDate": datetime.now().isoformat(),
        "source": "google_shopping",
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
        return doc_ref[1].id
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def main():
    print("=" * 50)
    print("📱 AI Device Fetcher (On-Demand)")
    print("=" * 50)
    
    if not search_query:
        print("❌ No search query")
        return
    
    db = get_firebase()
    if not db:
        print("❌ Firebase connection failed")
        return
    
    print("✅ Firebase connected")
    
    device_data = fetch_from_google_shopping(search_query)
    if device_data:
        device_id = add_device_to_firebase(db, device_data, search_query)
        if device_id:
            print(f"✅ Device added successfully: {device_data['name']}")
        else:
            print("❌ Failed to add device")
    else:
        print("❌ Could not fetch device data")

if __name__ == "__main__":
    main()
