import requests
import json
import os
import re
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

print("🖼️ AI Image Fixer Started -", datetime.now())

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
# التحقق من صحة الصورة
# ========================================

def check_image(url):
    """تتأكد إذا كانت الصورة شغالة ولا لأ"""
    if not url:
        return False
    if 'placehold' in url:
        return False
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

# ========================================
# البحث عن صورة من GSMarena
# ========================================

def search_gsmarena(brand, model):
    """تبحث عن صورة الجهاز في GSMarena"""
    
    brand_clean = brand.lower().strip()
    model_clean = model.lower().strip()
    
    # تنظيف الموديل
    model_search = re.sub(r'[^a-z0-9]', '-', model_clean)
    
    urls = [
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_clean}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}_{model_search}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search}-5g.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search}-plus.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search}-pro.jpg",
    ]
    
    for url in urls:
        if check_image(url):
            print(f"   ✅ Found on GSMarena: {url}")
            return url
    return None

# ========================================
# البحث عن صورة من Google (Tavily)
# ========================================

def search_tavily(brand, model):
    """تبحث عن صورة الجهاز من Google باستخدام Tavily API"""
    
    API_KEY = os.environ.get('TAVILY_API_KEY')
    if not API_KEY:
        return None
    
    query = f"{brand} {model} phone"
    
    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    data = {
        "api_key": API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": 3,
        "include_images": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        # جلب الصور من النتائج
        if "images" in result and result["images"]:
            for img in result["images"]:
                if check_image(img):
                    print(f"   ✅ Found on Google: {img[:80]}...")
                    return img
        
        # البحث في المحتوى
        if "results" in result:
            for item in result["results"]:
                content = item.get("content", "")
                img_urls = re.findall(r'https?://[^\s]+\.(jpg|jpeg|png|webp)', content)
                for img_url in img_urls:
                    full_url = img_url if img_url.startswith('http') else f"https:{img_url}"
                    if check_image(full_url):
                        print(f"   ✅ Found in content: {full_url[:80]}...")
                        return full_url
                        
    except Exception as e:
        print(f"   ⚠️ Tavily error: {e}")
    
    return None

# ========================================
# البحث عن صورة من DuckDuckGo (بديل مجاني)
# ========================================

def search_duckduckgo(brand, model):
    """تبحث عن صورة الجهاز من DuckDuckGo"""
    
    query = f"{brand} {model} phone"
    url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "RelatedTopics" in data:
            for topic in data["RelatedTopics"]:
                if "Icon" in topic and "URL" in topic["Icon"]:
                    img_url = topic["Icon"]["URL"]
                    if img_url and check_image(img_url):
                        print(f"   ✅ Found on DuckDuckGo: {img_url}")
                        return img_url
    except Exception as e:
        print(f"   ⚠️ DuckDuckGo error: {e}")
    
    return None

# ========================================
# إصلاح الصور لجميع الأجهزة
# ========================================

def fix_all_images(db):
    """إصلاح الصور المفقودة لكل الأجهزة"""
    
    devices_ref = db.collection('devices')
    docs = devices_ref.stream()
    
    fixed_count = 0
    total_count = 0
    tavily_used = 0
    
    for doc in docs:
        total_count += 1
        device = doc.to_dict()
        image_url = device.get('image', '')
        
        if not check_image(image_url):
            print(f"\n📱 {device.get('brand')} {device.get('model')}")
            if image_url:
                print(f"   Old image: {image_url[:80]}...")
            else:
                print(f"   Old image: None")
            
            # 1. GSMarena (مجاني)
            new_image = search_gsmarena(device.get('brand'), device.get('model'))
            
            # 2. DuckDuckGo (مجاني، بديل)
            if not new_image:
                new_image = search_duckduckgo(device.get('brand'), device.get('model'))
            
            # 3. Tavily (يستهلك كريدت)
            if not new_image:
                new_image = search_tavily(device.get('brand'), device.get('model'))
                if new_image:
                    tavily_used += 1
            
            if new_image:
                doc.reference.update({'image': new_image})
                print(f"   ✅ Fixed!")
                fixed_count += 1
            else:
                print(f"   ❌ No image found anywhere")
    
    return fixed_count, total_count, tavily_used

# ========================================
# التشغيل الرئيسي
# ========================================

def main():
    print("=" * 50)
    print("🖼️ AI Image Fixer (Multi-Source)")
    print("=" * 50)
    
    # الاتصال بـ Firebase
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    # إصلاح الصور
    fixed, total, tavily_used = fix_all_images(db)
    
    print("=" * 50)
    print(f"📊 Total devices: {total}")
    print(f"✅ Fixed images: {fixed}")
    print(f"❌ Still broken: {total - fixed}")
    print(f"📡 Tavily credits used: {tavily_used}")
    print("🏁 Finished at:", datetime.now())

if __name__ == "__main__":
    main()
