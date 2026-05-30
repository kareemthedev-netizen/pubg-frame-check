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
# جلب البيانات من Tavily API
# ========================================

def fetch_from_tavily(query):
    """جلب بيانات الجهاز من Tavily API"""
    
    API_KEY = os.environ.get('TAVILY_API_KEY')
    if not API_KEY:
        print("❌ No TAVILY_API_KEY found")
        return None
    
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "api_key": API_KEY,
        "query": f"{query} price Egypt specification",
        "search_depth": "basic",
        "include_answer": True,
        "include_raw_content": False,
        "max_results": 3
    }
    
    try:
        print(f"   🚀 Searching Tavily for: {query}")
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if "results" in result and len(result["results"]) > 0:
            item = result["results"][0]
            
            # استخراج السعر من النص
            price = extract_price_from_text(item.get("content", ""))
            
            # استخراج صورة (لو موجودة)
            image = extract_image_from_text(item.get("content", ""))
            
            print(f"   ✅ Found: {item.get('title', query)}")
            print(f"   💰 Price: {price} EGP")
            
            return {
                "name": item.get("title", query),
                "price": price,
                "image": image,
                "description": item.get("content", ""),
                "url": item.get("url", "")
            }
        else:
            print(f"   ❌ No results found")
            
    except Exception as e:
        print(f"   ❌ Tavily error: {e}")
    
    return None

# ========================================
# استخراج السعر من النص
# ========================================

def extract_price_from_text(text):
    """استخراج السعر من النص"""
    if not text:
        return 15000
    
    # البحث عن أسعار بالجنيه المصري
    patterns = [
        r'(\d+[\d,]*)\s*جنيه',
        r'(\d+[\d,]*)\s*EGP',
        r'(\d+[\d,]*)\s*جنية',
        r'سعر[\s:]*(\d+[\d,]*)',
        r'(\d+[\d,]*)\s*جنيه مصري'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            return int(price_str)
    
    # البحث عن أي رقم كبير (احتمال يكون السعر)
    numbers = re.findall(r'\d+', text)
    if numbers:
        for num in numbers:
            if int(num) > 5000:
                return int(num)
    
    # تقدير السعر حسب الاسم
    query_lower = text.lower()
    if "ultra" in query_lower or "pro max" in query_lower:
        return 35000
    elif "pro" in query_lower or "plus" in query_lower:
        return 25000
    else:
        return 15000

# ========================================
# استخراج صورة من النص (بديل)
# ========================================

def extract_image_from_text(text):
    """محاولة استخراج رابط صورة من النص"""
    # بحث عن روابط صور
    patterns = [
        r'https?://[^\s]+\.(jpg|jpeg|png|webp)',
        r'src=["\']([^"\']+\.(jpg|jpeg|png|webp))'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "https://placehold.co/400x200/1a1a2e/e74c3c?text=Device"

# ========================================
# إضافة جهاز إلى Firebase
# ========================================

def add_device_to_firebase(db, device_data, search_query):
    """إضافة الجهاز الجديد إلى Firebase"""
    
    # استخراج الماركة والموديل
    name_parts = device_data["name"].split()
    brand = name_parts[0] if name_parts else "Unknown"
    model = " ".join(name_parts[1:]) if len(name_parts) > 1 else search_query
    
    price = device_data.get("price", 15000)
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
        "source": "tavily",
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
    print("📱 AI Device Fetcher (Tavily)")
    print("=" * 50)
    
    if not search_query:
        print("❌ No search query provided")
        return
    
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    device_data = fetch_from_tavily(search_query)
    
    if device_data:
        add_device_to_firebase(db, device_data, search_query)
    else:
        print("❌ Could not fetch device data from Tavily")
        print("   💡 Trying fallback data...")
        # بيانات تقديرية كبديل
        fallback_data = {
            "name": search_query.title(),
            "price": 15000,
            "image": f"https://placehold.co/400x200/1a1a2e/e74c3c?text={search_query.replace(' ', '+')}"
        }
        add_device_to_firebase(db, fallback_data, search_query)

if __name__ == "__main__":
    main()
