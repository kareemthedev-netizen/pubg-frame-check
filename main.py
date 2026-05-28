import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from datetime import datetime
import re

def init_firebase():
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate('service-account-key.json')
    firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

def clean_price(price_text):
    numbers = re.findall(r'\d+', price_text)
    if numbers:
        return int(''.join(numbers))
    return None

def extract_brand(full_name):
    brands = ['Samsung', 'Apple', 'iPhone', 'Xiaomi', 'Poco', 'Realme', 
              'OnePlus', 'Huawei', 'Google', 'ASUS', 'Nubia', 'RedMagic']
    for brand in brands:
        if brand.lower() in full_name.lower():
            return brand
    return "Other"

def extract_model(full_name):
    return full_name[:50]

def fetch_from_mobizil():
    devices = []
    try:
        url = "https://mobizil.com/category/xiaomi-phones/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        phones = soup.find_all('div', class_='product-item')
        for phone in phones:
            name_elem = phone.find('h3')
            price_elem = phone.find('span', class_='price')
            if name_elem and price_elem:
                devices.append({
                    'name': name_elem.text.strip(),
                    'priceEGP': clean_price(price_elem.text),
                    'source': 'mobizil',
                    'last_updated': datetime.now().isoformat()
                })
    except Exception as e:
        print(f"Error: {e}")
    return devices

def get_existing_devices():
    existing = {}
    docs = db.collection('devices').stream()
    for doc in docs:
        data = doc.to_dict()
        key = f"{data.get('brand', '')}_{data.get('model', '')}"
        existing[key] = {'id': doc.id, 'data': data}
    return existing

def add_new_device(device_data):
    try:
        new_device = {
            'brand': extract_brand(device_data['name']),
            'model': extract_model(device_data['name']),
            'priceEGP': device_data['priceEGP'],
            'screenHz': 90,
            'maxFPS': 90,
            'category': 'midrange',
            'priceCategory': 'mid',
            'image': 'https://placehold.co/400x200/1a1a2e/e74c3c?text=📱',
            'addedDate': datetime.now().isoformat(),
            'source': device_data.get('source', 'auto_scraper'),
            'graphics': {
                'smooth': 90, 'balanced': 60, 'hd': 60,
                'hdr': 'غير مدعوم', 'ultraHDR': 'غير مدعوم', 'extremeHDR': 'غير مدعوم'
            }
        }
        db.collection('devices').add(new_device)
        print(f"✅ Added: {device_data['name']}")
    except Exception as e:
        print(f"❌ Error: {e}")

def update_device_price(device_id, new_price):
    try:
        db.collection('devices').document(device_id).update({
            'priceEGP': new_price,
            'last_price_update': datetime.now().isoformat()
        })
        print(f"💰 Price updated: {device_id}")
    except Exception as e:
        print(f"❌ Update error: {e}")

def compare_and_update():
    print("🔄 Fetching data...")
    all_new_devices = fetch_from_mobizil()
    print(f"📱 Found {len(all_new_devices)} devices")
    
    existing = get_existing_devices()
    print(f"📚 Existing: {len(existing)} devices")
    
    for device in all_new_devices:
        key = f"{extract_brand(device['name'])}_{extract_model(device['name'])}"
        if key in existing:
            existing_price = existing[key]['data'].get('priceEGP')
            if existing_price != device['priceEGP']:
                update_device_price(existing[key]['id'], device['priceEGP'])
        else:
            add_new_device(device)
    
    print("✅ Done!")

def main():
    print(f"🚀 AI Scraper Started - {datetime.now()}")
    compare_and_update()
    print("🏁 Finished")

if __name__ == "__main__":
    main()