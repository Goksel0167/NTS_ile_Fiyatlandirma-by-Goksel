import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)  # CORS'u aktif et

# --- DOSYALAR ---
PRODUCT_FILE = 'urun_fiyat_db.csv'
SHIPPING_FILE = 'lokasyonlar.csv'
EXCHANGE_RATES_FILE = 'exchange_rates.json'

# --- Helper Functions ---
def load_products():
    try:
        df = pd.read_csv(PRODUCT_FILE)
        df['Kayit_Tarihi'] = pd.to_datetime(df['Kayit_Tarihi'], format='%d.%m.%Y', errors='coerce')
        return df
    except Exception:
        return pd.DataFrame(columns=['Urun_Adi', 'Fabrika', 'NTS_Maliyet_TL', 'Kayit_Tarihi'])

def load_shipping():
    try:
        return pd.read_csv(SHIPPING_FILE)
    except Exception:
        return pd.DataFrame(columns=['Sehir', 'Firma', 'Fabrika', 'Arac_Tipi', 'Fiyat_TL_KG'])

def load_exchange_rates():
    if os.path.exists(EXCHANGE_RATES_FILE):
        with open(EXCHANGE_RATES_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {'TL': 1.0, 'USD': 36.50, 'EUR': 38.20, 'CHF': 41.10}

# --- API Endpoints ---

@app.route('/api/products', methods=['GET'])
def get_products():
    """Tüm ürünleri döndür"""
    df = load_products()
    if not df.empty:
        df['Kayit_Tarihi'] = df['Kayit_Tarihi'].astype(str)
        return jsonify(df.to_dict('records'))
    return jsonify([])

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Tüm şehirleri döndür"""
    df = load_shipping()
    if not df.empty:
        cities = sorted(df['Sehir'].unique().tolist())
        return jsonify(cities)
    return jsonify([])

@app.route('/api/shipping', methods=['GET'])
def get_shipping():
    """Belirli bir şehir için nakliye seçeneklerini döndür"""
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City parameter required'}), 400
    
    df = load_shipping()
    filtered = df[df['Sehir'] == city]
    
    if not filtered.empty:
        return jsonify(filtered.to_dict('records'))
    return jsonify([])

@app.route('/api/rates', methods=['GET'])
def get_rates():
    """Güncel döviz kurlarını döndür"""
    rates = load_exchange_rates()
    return jsonify(rates)

@app.route('/api/calculate', methods=['POST'])
def calculate_price():
    """Fiyat hesaplama"""
    data = request.json
    
    product = data.get('product')
    city = data.get('city')
    profit_margin = data.get('profit_margin', 15.0)
    factory = data.get('factory')
    shipping_company = data.get('shipping_company')
    vehicle_type = data.get('vehicle_type')
    
    if not product or not city:
        return jsonify({'error': 'Product and city are required'}), 400
    
    df_products = load_products()
    df_shipping = load_shipping()
    rates = load_exchange_rates()
    
    # Manuel seçim varsa
    if factory and shipping_company and vehicle_type:
        # Ürün maliyeti
        product_data = df_products[
            (df_products['Urun_Adi'] == product) & 
            (df_products['Fabrika'] == factory)
        ].sort_values('Kayit_Tarihi', ascending=False)
        
        if product_data.empty:
            return jsonify({'error': 'Product not found'}), 404
        
        nts_cost = product_data.iloc[0]['NTS_Maliyet_TL']
        
        # Nakliye maliyeti
        shipping_data = df_shipping[
            (df_shipping['Sehir'] == city) &
            (df_shipping['Fabrika'] == factory) &
            (df_shipping['Firma'] == shipping_company) &
            (df_shipping['Arac_Tipi'] == vehicle_type)
        ]
        
        if shipping_data.empty:
            return jsonify({'error': 'Shipping option not found'}), 404
        
        shipping_cost = shipping_data.iloc[0]['Fiyat_TL_KG']
        
        # Hesaplama
        total_cost = nts_cost + shipping_cost
        sale_price_tl = total_cost * (1 + profit_margin / 100)
        
        result = {
            'Fabrika': factory,
            'Firma': shipping_company,
            'Arac': vehicle_type,
            'NTS_TL': float(nts_cost),
            'Nakliye_TL': float(shipping_cost),
            'Toplam_Maliyet_TL': float(total_cost),
            'Satis_TL': float(sale_price_tl),
            'Satis_USD_KG': float(sale_price_tl / rates.get('USD', 36.50)),
            'Satis_EUR_KG': float(sale_price_tl / rates.get('EUR', 38.20)),
            'Satis_CHF_KG': float(sale_price_tl / rates.get('CHF', 41.10)),
            'is_cheapest': True
        }
        
        return jsonify(result)
    
    # Otomatik - en ucuz seçeneği bul
    all_factories = ['TR14', 'TR15', 'TR16']
    cheapest = None
    min_price = float('inf')
    
    for fab in all_factories:
        product_data = df_products[
            (df_products['Urun_Adi'] == product) & 
            (df_products['Fabrika'] == fab)
        ].sort_values('Kayit_Tarihi', ascending=False)
        
        if product_data.empty:
            continue
        
        nts_cost = product_data.iloc[0]['NTS_Maliyet_TL']
        
        shipping_options = df_shipping[
            (df_shipping['Sehir'] == city) &
            (df_shipping['Fabrika'] == fab)
        ]
        
        for _, shipping in shipping_options.iterrows():
            shipping_cost = shipping['Fiyat_TL_KG']
            total_cost = nts_cost + shipping_cost
            sale_price_tl = total_cost * (1 + profit_margin / 100)
            
            if sale_price_tl < min_price:
                min_price = sale_price_tl
                cheapest = {
                    'Fabrika': fab,
                    'Firma': shipping['Firma'],
                    'Arac': shipping['Arac_Tipi'],
                    'NTS_TL': float(nts_cost),
                    'Nakliye_TL': float(shipping_cost),
                    'Toplam_Maliyet_TL': float(total_cost),
                    'Satis_TL': float(sale_price_tl),
                    'Satis_USD_KG': float(sale_price_tl / rates.get('USD', 36.50)),
                    'Satis_EUR_KG': float(sale_price_tl / rates.get('EUR', 38.20)),
                    'Satis_CHF_KG': float(sale_price_tl / rates.get('CHF', 41.10)),
                    'is_cheapest': True
                }
    
    if cheapest:
        return jsonify(cheapest)
    
    return jsonify({'error': 'No valid calculation found'}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'NTS Backend API'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
