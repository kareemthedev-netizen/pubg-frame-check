import requests
import json
import os
import re
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

print("🖼️ AI Image Fixer (with Tavily) Started -", datetime.now())

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

def check_image(url):
    if not url or 'placehold' in url:
        return False
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def search_gsmarena(brand, model):
    brand_clean = brand.lower().strip()
    model_clean = model.lower().strip()
    model_search = re.sub(r'[^a-z0-9]', '-', model_clean)
    
    urls = [
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_clean}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}_{model_search}.jpg",
    ]
    for url in urls:
        if check_image(url):
            return url
    return None

def search_tavily_image(brand, model):
    API_KEY = os.environ.get('TAVILY_API_KEY')
    if not API_KEY:
        return None
    
    query = f"{brand} {model} phone image"
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    data = {
        "api_key": API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": 1
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if "results" in result and len(result["results"]) > 0:
            content = result["results"][0].get("content", "")
            # البحث عن رابط صورة في النص
            img_match = re.search(r'https?://[^\s]+\.(jpg|jpeg|png|webp)', content)
            if img_match:
                return img_match.group(0)
    except Exception as e:
        print(f"   ⚠️ Tavily error: {e}")
    return None

def fix_all_images(db):
    devices_ref = db.collection('devices')
    docs = devices_ref.stream()
    
    fixed_count = 0
    total_count = 0
    
    for doc in docs:
        total_count += 1
        device = doc.to_dict()
        image_url = device.get('image', '')
        
        if not check_image(image_url):
            print(f"\n📱 {device.get('brand')} {device.get('model')}")
            
            # 1. حاول من GSMarena
            new_image = search_gsmarena(device.get('brand'), device.get('model'))
            
            # 2. لو مفيش، حاول من Tavily
            if not new_image:
                new_image = search_tavily_image(device.get('brand'), device.get('model'))
            
            if new_image:
                doc.reference.update({'image': new_image})
                print(f"   ✅ Fixed!")
                fixed_count += 1
            else:
                print(f"   ❌ No image found")
    
    return fixed_count, total_count

def main():
    print("=" * 50)
    print("🖼️ AI Image Fixer (GSMarena + Tavily)")
    print("=" * 50)
    
    db = get_firebase()
    if not db:
        print("❌ Cannot continue")
        return
    
    print("✅ Firebase connected")
    fixed, total = fix_all_images(db)
    
    print("=" * 50)
    print(f"📊 Total: {total}")
    print(f"✅ Fixed: {fixed}")
    print(f"❌ Broken: {total - fixed}")
    print("🏁 Finished")

if __name__ == "__main__":
    main()
