import requests
from bs4 import BeautifulSoup

def check_image_exists(url):
    """تتأكد إذا كانت الصورة شغالة ولا لأ"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def search_gsmarena_image(brand, model):
    """تدور على صورة الجهاز في موقع GSMarena"""
    
    # تنظيف الأسماء
    brand_clean = brand.lower().strip()
    model_clean = model.lower().strip().replace(' ', '-').replace('/', '-')
    
    # تجربة الروابط المختلفة
    possible_urls = [
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_clean}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}_{model_clean}.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_clean}-5g.jpg",
        f"https://fdn2.gsmarena.com/vv/bigpic/{brand_clean}-{model_clean}-pro.jpg",
    ]
    
    for url in possible_urls:
        if check_image_exists(url):
            return url
    
    return None

def fix_missing_images(db, devices_collection):
    """تصلح الصور المفقودة لجميع الأجهزة"""
    
    fixed_count = 0
    docs = devices_collection.stream()
    
    for doc in docs:
        device = doc.to_dict()
        image_url = device.get('image', '')
        
        # لو الصورة مش موجودة أو عبارة عن placehold
        if not image_url or 'placehold' in image_url or not check_image_exists(image_url):
            print(f"🔍 Searching image for: {device['brand']} {device['model']}")
            
            # دور على صورة جديدة
            new_image = search_gsmarena_image(device['brand'], device['model'])
            
            if new_image:
                # حدث الصورة في Firebase
                doc.reference.update({'image': new_image})
                print(f"✅ Fixed: {device['brand']} {device['model']} → {new_image}")
                fixed_count += 1
            else:
                print(f"❌ No image found for: {device['brand']} {device['model']}")
    
    return fixed_count
