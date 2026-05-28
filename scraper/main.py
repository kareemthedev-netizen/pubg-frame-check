import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# 2. جلب الأجهزة من مواقع مختلفة
# ========================================

def scrape_mobizil_category(url, brand):
    """جلب الأجهزة من موبيزل حسب العلامة التجارية"""
    devices = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to fetch {url}: {response.status_code}")
            return devices
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # البحث عن المنتجات
        products = soup.find_all('div', class_='product-item')
        if not products:
            products = soup.find_all('div', class_='product')
        
        for product in products:
            try:
                name_elem = product.find('h3')
                if not name_elem:
                    name_elem = product.find('a', class_='product-name')
                
                price_elem = product.find('span', class_='price')
                if not price_elem:
                    price_elem = product.find('span', class_='amount')
                
                if name_elem and price_elem:
                    name = name_elem.text.strip()
                    price_text = price_elem.text.strip()
                    price = re.findall(r'\d+', price_text)
                    
                    if price:
                        devices.append({
                            'name': name,
                            'brand': brand,
                            'priceEGP': int(''.join(price)),
                            'source': 'mobizil'
                        })
                        print(f"✅ Found: {name} - {price[0]} EGP")
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
    
    return devices

def scrape_all_sources():
    """جلب الأجهزة من كل المصادر"""
    all_devices = []
    
    # قائمة بمواقع الموبايلات
    sources = [
        ("https://mobizil.com/category/xiaomi-phones/", "Xiaomi"),
        ("https://mobizil.com/category/samsung-phones/", "Samsung"),
        ("https://mobizil.com/category/oneplus-phones/", "OnePlus"),
        ("https://mobizil.com/category/realme-phones/", "Realme"),
        ("https://mobizil.com/category/poco-phones/", "Poco"),
    ]
    
    print("📱 Fetching devices from online sources...")
    
    # استخدام ThreadPoolExecutor للجلب المتوازي (أسرع)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scrape_mobizil_category, url, brand): (url, brand) 
                   for url, brand in sources}
        
        for future in as_completed(futures):
            devices = future.result()
            all_devices.extend(devices)
    
    print(f"📊 Total devices found: {len(all_devices)}")
    return all_devices

# ========================================
# 3. تصنيف الأجهزة (فريمات)
# ========================================

def classify_device_by_name(name, brand):
    """تحديد إعدادات الجهاز بناءً على اسمه وفئته"""
    name_lower = name.lower()
    
    # تحديد الفريمات بناءً على الموديل
    if 'snapdragon 8 gen' in name_lower or 'dimensity 9000' in name_lower:
        max_fps = 120
        screen_hz = 120
        category = 'flagship'
        price_category = 'premium'
    elif 'ultra' in name_lower or 'pro max' in name_lower:
        max_fps = 90
        screen_hz = 120
        category = 'flagship'
        price_category = 'premium'
    elif 'pro' in name_lower and ('xiaomi' in name_lower or 'realme' in name_lower):
        max_fps = 90
        screen_hz = 120
        category = 'flagship'
        price_category = 'mid'
    elif 'poco f' in name_lower or 'gt neo' in name_lower:
        max_fps = 90
        screen_hz = 120
        category = 'midrange'
        price_category = 'mid'
    else:
        max_fps = 60
        screen_hz = 90
        category = 'midrange'
        price_category = 'budget'
    
    return max_fps, screen_hz, category, price_category

def get_image_url(brand, model):
    """توليد رابط صورة من GSMarena"""
    model_clean = model.replace(' ', '-').replace('/', '-')
    brand_clean = brand.lower()
    
    # روابط GSMarena الصحيحة
    image_map = {
        'xiaomi': f'https://fdn2.gsmarena.com/vv/bigpic/xiaomi-{model_clean.lower()}.jpg',
        'samsung': f'https://fdn2.gsmarena.com/vv/bigpic/samsung-{model_clean.lower()}.jpg',
        'oneplus': f'https://fdn2.gsmarena.com/vv/bigpic/oneplus-{model_clean.lower()}.jpg',
        'poco': f'https://fdn2.gsmarena.com/vv/bigpic/xiaomi-{model_clean.lower()}.jpg',
        'realme': f'https://fdn2.gsmarena.com/vv/bigpic/realme-{model_clean.lower()}.jpg',
    }
    
    return image_map.get(brand_clean, f'https://placehold.co/400x200/1a1a2e/e74c3c?text={brand}+{model}')

# ========================================
# 4. تحديث Firebase
# ========================================

def get_existing_devices(db):
    """جلب الأجهزة الموجودة"""
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
    """إضافة جهاز جديد"""
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
            "source": device_data.get("source", "auto_scraper"),
            "graphics": graphics
        }
        
        db.collection("devices").add(new_device)
        print(f"✅ Added: {device_data['brand']} {device_data['model']} ({device_data['maxFPS']} FPS) - {device_data['priceEGP']} EGP")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def update_device_price(db, device_id, new_price):
    """تحديث سعر جهاز"""
    try:
        db.collection('devices').document(device_id).update({
            'priceEGP': new_price,
            'last_price_update': datetime.now().isoformat()
        })
        print(f"💰 Updated price: {device_id} → {new_price} EGP")
    except Exception as e:
        print(f"❌ Update error: {e}")

def update_device_image(db, device_id, new_image):
    """تحديث صورة جهاز"""
    try:
        db.collection('devices').document(device_id).update({
            'image': new_image,
            'last_image_update': datetime.now().isoformat()
        })
        print(f"🖼️ Updated image: {device_id}")
    except Exception as e:
        print(f"❌ Image update error: {e}")

# ========================================
# 5. الوظيفة الرئيسية
# ========================================

def main():
    print("=" * 50)
    print("🤖 AI Auto Device Scraper")
    print("=" * 50)
    
    # الاتصال بـ Firebase
    db = get_firebase()
    if not db:
        print("❌ Cannot continue without Firebase")
        return
    
    print("✅ Firebase connected")
    
    # جلب البيانات من الإنترنت
    scraped_devices = scrape_all_sources()
    
    if not scraped_devices:
        print("⚠️ No devices found from scraping")
        return
    
    # جلب الأجهزة الموجودة
    existing = get_existing_devices(db)
    print(f"📚 Existing devices: {len(existing)}")
    
    # معالجة كل جهاز
    new_count = 0
    price_updates = 0
    image_updates = 0
    
    for device in scraped_devices:
        max_fps, screen_hz, category, price_category = classify_device_by_name(device['name'], device['brand'])
        image_url = get_image_url(device['brand'], device['name'].replace(device['brand'], '').strip())
        
        model_name = device['name'].replace(device['brand'], '').strip()
        if not model_name:
            model_name = device['name']
        
        key = f"{device['brand']}_{model_name}"
        
        if key in existing:
            # الجهاز موجود - نتحقق من السعر والصورة
            existing_price = existing[key]['data'].get('priceEGP')
            existing_image = existing[key]['data'].get('image', '')
            
            if existing_price != device['priceEGP']:
                update_device_price(db, existing[key]['id'], device['priceEGP'])
                price_updates += 1
            
            if existing_image != image_url and 'placehold' not in image_url:
                update_device_image(db, existing[key]['id'], image_url)
                image_updates += 1
        else:
            # جهاز جديد
            new_device = {
                "brand": device['brand'],
                "model": model_name,
                "maxFPS": max_fps,
                "screenHz": screen_hz,
                "priceEGP": device['priceEGP'],
                "category": category,
                "priceCategory": price_category,
                "image": image_url,
                "source": device.get('source', 'auto_scraper')
            }
            add_device(db, new_device)
            new_count += 1
    
    print("=" * 50)
    print(f"📱 New devices added: {new_count}")
    print(f"💰 Prices updated: {price_updates}")
    print(f"🖼️ Images updated: {image_updates}")
    print(f"📊 Total devices in DB: {len(existing) + new_count}")
    print("=" * 50)
    print("✅ AI Auto Device Scraper finished!")
    print("🏁 Completed at:", datetime.now())

if __name__ == "__main__":
    main()
