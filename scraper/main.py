import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import re
import sys

print("🚀 AI Scraper Started -", datetime.now())
print("Python version:", sys.version)

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
    print("📱 Fetching from Mobizil...")
    devices = []
    try:
        url = "https://mobizil.com/category/xiaomi-phones/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch: {response.status_code}")
            return devices
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # جرب selectors مختلفة
        phones = soup.find_all('div', class_='product-item')
        if not phones:
            phones = soup.find_all('div', class_='product')
        if not phones:
            phones = soup.find_all('li', class_='product-item')
            
        print(f"📱 Found {len(phones)} phones in HTML")
        
        for phone in phones:
            name_elem = phone.find('h3')
            price_elem = phone.find('span', class_='price')
            
            if not name_elem:
                name_elem = phone.find('a', class_='product-name')
            if not price_elem:
                price_elem = phone.find('span', class_='amount')
            
            if name_elem and price_elem:
                name = name_elem.text.strip()
                price = clean_price(price_elem.text)
                if name and price:
                    devices.append({
                        'name': name,
                        'priceEGP': price,
                        'source': 'mobizil',
                        'last_updated': datetime.now().isoformat()
                    })
                    print(f"✅ Found: {name} - {price} EGP")
                    
    except Exception as e:
        print(f"❌ Error fetching: {e}")
    
    return devices

def main():
    print("=" * 50)
    
    # جلب البيانات
    devices = fetch_from_mobizil()
    
    print("=" * 50)
    print(f"📊 Total devices found: {len(devices)}")
    
    if devices:
        print("\n📱 First 5 devices:")
        for i, device in enumerate(devices[:5]):
            print(f"  {i+1}. {device['name']}: {device['priceEGP']} EGP")
    else:
        print("⚠️ No devices found - website structure may have changed")
    
    print("=" * 50)
    print("🏁 Finished")

if __name__ == "__main__":
    main()
