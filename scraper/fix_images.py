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
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

# ========================================
# البحث عن صورة بديلة من GSMarena
# ========================================

def search_gsmarena_image(brand, model):
    """تبحث عن صورة الجهاز في GSMarena"""
    
    # تنظيف الأسماء
    brand_clean = brand.lower().strip()
    model_clean = model.lower().strip()
    
    # إزالة كلمات زي "5g", "plus", "ultra" من الموديل للبحث
    model_search = model_clean.replace('5g', '').replace('plus', '').replace('ultra', '').replace('pro', '').strip()
    model_search = re.sub(r'[^a-z0-9]', '-', model_search)
    
    # تجربة الروابط المختلفة
    possible_urls = [
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_clean}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}_{model_search}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search}-5g.jpg",
    ]
    
    for url in possible_urls:
        if check_image(url):
            print(f"   ✅ Found: {url}")
            return url
    
    # لو لسة مش موجود، نجرب البحث العام
    try:
        search_url = f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_search[:20]}.jpg"
        if check_image(search_url):
            return search_url
    except:
        pass
    
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
    
    for doc in docs:
        total_count += 1
        device = doc.to_dict()
        image_url = device.get('image', '')
        
        # لو الصورة مش موجودة أو بايظة
        if not image_url or 'placehold' in image_url or not check_image(image_url):
            print(f"\n🔍 Device: {device.get('brand')} {device.get('model')}")
            print(f"   Old image: {image_url[:80] if image_url else 'None'}...")
            
            # البحث عن صورة جديدة
            new_image = search_gsmarena_image(device.get('brand'), device.get('model'))
            
            if new_image:
                doc.reference.update({'image': new_image})
                print(f"   ✅ Updated!")
                fixed_count += 1
            else:
                print(f"   ❌ No alternative found")
    
    return fixed_count, total_count

# ========================================
# التشغيل الرئيسي
# ========================================

def main():
    print("=" * 50)
    print("🖼️ AI Image Fixer")
    print("=" * 50)
    
    # الاتصال بـ Firebase
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    # إصلاح الصور
    fixed, total = fix_all_images(db)
    
    print("=" * 50)
    print(f"📊 Total devices: {total}")
    print(f"✅ Fixed images: {fixed}")
    print(f"❌ Still broken: {total - fixed}")
    print("🏁 Finished at:", datetime.now())

if __name__ == "__main__":
    main()
