import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re

# Firebase imports
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    if not cred_json:
        print("❌ FIREBASE_CREDENTIALS not found in environment")
        return None
    
    try:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"❌ Firebase init error: {e}")
        return None

def clean_price(price_text):
    if not price_text:
        return None
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch: {response.status_code}")
            return devices
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        phones = soup.find_all('div', class_='product-item')
        print(f"📱 Found {len(phones)} phones in HTML")
        
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
                print(f"✅ Found: {name_elem.text.strip()} - {price_elem.text.strip()}")
    except Exception as e:
        print(f"❌ Error fetching: {e}")
    return devices

def main():
    print(f"🚀 AI Scraper Started - {datetime.now()}")
    
    # Test without Firebase first
    print("📱 Fetching devices from Mobizil...")
    devices = fetch_from_mobizil()
    print(f"📊 Found {len(devices)} devices")
    
    for device in devices:
        print(f"  - {device['name']}: {device['priceEGP']} EGP")
    
    # Try to connect to Firebase
    print("\n🔌 Connecting to Firebase...")
    db = init_firebase()
    
    if db:
        print("✅ Firebase connected successfully!")
    else:
        print("⚠️ Firebase not configured. Run with real data only.")
    
    print("🏁 Finished")

if __name__ == "__main__":
    main()
