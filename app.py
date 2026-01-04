import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import json
import os
import requests
import xml.etree.ElementTree as ET

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="NTS Mobil - Fiyat Hesaplama", page_icon="🚛", layout="wide")

st.markdown("""
<style>
div.stButton > button:first-child {
    border-radius: 8px;
    font-weight: bold;
    height: 45px;
}
</style>
""", unsafe_allow_html=True)

# --- DOSYALAR ---
PRODUCT_FILE = 'urun_fiyat_db.csv'
SHIPPING_FILE = 'lokasyonlar.csv'
USERS_FILE = 'users.json'
EXCHANGE_RATES_FILE = 'exchange_rates.json'
TCMB_HISTORY_FILE = 'tcmb_kur_gecmisi.json'
CALC_HISTORY_FILE = 'hesaplama_gecmisi.csv'
OWNER_NAME = "Göksel Çapkın"
ADMIN_USERNAME = "goksel"
ADMIN_DEFAULT_PASSWORD = "NTS2025!"

# --- DÖVİZ KURU FONKSİYONLARI ---

def load_tcmb_history():
    if os.path.exists(TCMB_HISTORY_FILE):
        with open(TCMB_HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_tcmb_history(date_key, rates):
    history = load_tcmb_history()
    history[date_key] = rates
    with open(TCMB_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def fetch_tcmb_for_date(date_obj):
    date_str = date_obj.strftime('%d%m%Y')
    url = f"https://www.tcmb.gov.tr/kurlar/{date_str[:4]}{date_str[2:4]}/{date_str}.xml"
    try:
        response = requests.get(url, timeout=5)
    except Exception:
        return None
    if response.status_code != 200:
        return None
    root = ET.fromstring(response.content)
    rates = {}
    for currency in root.findall('Currency'):
        code = currency.get('CurrencyCode')
        if code in ['USD', 'EUR', 'CHF']:
            forex_selling = currency.find('ForexSelling')
            if forex_selling is not None and forex_selling.text:
                rates[code] = float(forex_selling.text)
    if not rates:
        return None
    rates['TL'] = 1.0
    rates['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rates['source_date'] = date_obj.strftime('%Y-%m-%d')
    return rates


def get_tcmb_rates():
    """TCMB'den güncel döviz satış kurlarını çek, gerekirse son 10 iş gününe kadar geriye git."""
    today = datetime.now().date()
    for back in range(0, 10):
        candidate = today - timedelta(days=back)
        if candidate.weekday() >= 5:  # Hafta sonu ise atla
            continue
        fetched = fetch_tcmb_for_date(candidate)
        if fetched:
            fetched['is_fallback'] = back > 0
            save_exchange_rates(fetched)
            save_tcmb_history(candidate.strftime('%Y-%m-%d'), fetched)
            return fetched
    fallback = load_exchange_rates()
    fallback['is_fallback'] = True
    fallback.setdefault('source_date', 'Varsayılan')
    return fallback


def save_exchange_rates(rates):
    """Döviz kurlarını kaydet"""
    with open(EXCHANGE_RATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)


def load_exchange_rates():
    """Kayıtlı döviz kurlarını yükle"""
    if os.path.exists(EXCHANGE_RATES_FILE):
        with open(EXCHANGE_RATES_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    # Varsayılan kurlar
    return {'TL': 1.0, 'USD': 36.50, 'EUR': 38.20, 'CHF': 41.10, 'date': 'Varsayılan', 'source_date': 'Varsayılan', 'is_fallback': True}


def get_rates_for_date(date_obj):
    """Kaydedilmiş TCMB geçmişinde verilen tarih için kur arar."""
    history = load_tcmb_history()
    key = date_obj.strftime('%Y-%m-%d')
    return history.get(key)


# --- HESAPLAMA GEÇMİŞİ ---

CALC_COLUMNS = [
    'timestamp', 'username', 'musteri', 'urun', 'sehir', 'fabrika', 'firma', 'arac',
    'kar_marji', 'nts_tl', 'nakliye_tl', 'toplam_maliyet_tl',
    'satis_tl_kg', 'satis_usd_kg', 'satis_eur_kg', 'satis_chf_kg',
    'satis_tl_ton', 'satis_usd_ton', 'satis_eur_ton', 'satis_chf_ton',
    'usd_kur', 'eur_kur', 'chf_kur', 'kur_tarihi', 'urun_kayit_tarihi'
]


def ensure_calc_history_file():
    if not os.path.exists(CALC_HISTORY_FILE):
        df = pd.DataFrame(columns=CALC_COLUMNS)
        df.to_csv(CALC_HISTORY_FILE, index=False)


def append_calc_record(record):
    ensure_calc_history_file()
    df = pd.read_csv(CALC_HISTORY_FILE) if os.path.exists(CALC_HISTORY_FILE) else pd.DataFrame(columns=CALC_COLUMNS)
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(CALC_HISTORY_FILE, index=False)

# --- KULLANICI YÖNETİMİ ---

def hash_password(password):
    """Şifreyi hash'le"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Kullanıcıları yükle"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Kullanıcıları kaydet"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def ensure_owner_user():
    """Sistem sahibi için varsayılan yönetici hesabını yoksa ekle."""
    users = load_users()
    if ADMIN_USERNAME not in users:
        users[ADMIN_USERNAME] = {
            'password': hash_password(ADMIN_DEFAULT_PASSWORD),
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': OWNER_NAME,
            'agreement_accepted': True
        }
        save_users(users)

def create_user(username, password, created_by="admin"):
    """Yeni kullanıcı oluştur"""
    users = load_users()
    if username in users:
        return False, "Kullanıcı adı zaten mevcut!"
    
    users[username] = {
        'password': hash_password(password),
        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'created_by': created_by,
        'agreement_accepted': False
    }
    save_users(users)
    return True, "Kullanıcı başarıyla oluşturuldu!"

def verify_user(username, password):
    """Kullanıcı doğrula"""
    users = load_users()
    if username not in users:
        return False
    return users[username]['password'] == hash_password(password)

def accept_agreement(username):
    """Sözleşme onayını kaydet"""
    users = load_users()
    if username in users:
        users[username]['agreement_accepted'] = True
        users[username]['agreement_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_users(users)

def user_accepted_agreement(username):
    """Sözleşme onayını kontrol et"""
    users = load_users()
    if username in users:
        return users[username].get('agreement_accepted', False)
    return False

# --- FONKSİYONLAR ---

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

def get_latest_product_price(df_products, urun_adi, fabrika):
    filtered = df_products[(df_products['Urun_Adi'] == urun_adi) & (df_products['Fabrika'] == fabrika)]
    if filtered.empty:
        return None
    latest = filtered.sort_values('Kayit_Tarihi', ascending=False).iloc[0]
    return latest['NTS_Maliyet_TL']

def get_all_product_prices(df_products, urun_adi, fabrika):
    filtered = df_products[(df_products['Urun_Adi'] == urun_adi) & (df_products['Fabrika'] == fabrika)]
    return filtered.sort_values('Kayit_Tarihi', ascending=False)

def find_cheapest_route(df_products, df_shipping, urun_adi, sehir, kar_marji, exchange_rates):
    calculated_rows = []
    display_rows = []
    usd_rate = exchange_rates.get('USD', 36.50) or 36.50
    eur_rate = exchange_rates.get('EUR', 38.20) or 38.20
    chf_rate = exchange_rates.get('CHF', 41.10) or 41.10

    ilgili_nakliye = df_shipping[(df_shipping['Sehir'] == sehir)]
    tum_fabrikalar = ['TR14', 'TR15', 'TR16']

    for fabrika in tum_fabrikalar:
        nts_tl = get_latest_product_price(df_products, urun_adi, fabrika)
        nakliye_options = ilgili_nakliye[ilgili_nakliye['Fabrika'] == fabrika]

        # Eğer nakliye kaydı yoksa bile satır ekle (boş gösterim)
        if nakliye_options.empty:
            display_rows.append({
                'Fabrika': fabrika,
                'Firma': '-',
                'Arac': '-',
                'NTS_TL': nts_tl if nts_tl is not None else '-',
                'Nakliye_TL': '-',
                'Toplam_Maliyet_TL': '-',
                'Satis_USD_KG': '-',
                'Satis_EUR_KG': '-',
                'Satis_CHF_KG': '-',
                'Satis_TL_TON': '-',
                'Satis_USD_TON': '-',
                'Satis_EUR_TON': '-',
                'Satis_CHF_TON': '-',
                'Satis_TL': None,
                'HasPrice': False
            })
            continue

        if nts_tl is None:
            for _, nakliye in nakliye_options.iterrows():
                display_rows.append({
                    'Fabrika': fabrika,
                    'Firma': nakliye['Firma'],
                    'Arac': nakliye['Arac_Tipi'],
                    'NTS_TL': '-',
                    'Nakliye_TL': '-',
                    'Toplam_Maliyet_TL': '-',
                    'Satis_USD_KG': '-',
                    'Satis_EUR_KG': '-',
                    'Satis_CHF_KG': '-',
                    'Satis_TL_TON': '-',
                    'Satis_USD_TON': '-',
                    'Satis_EUR_TON': '-',
                    'Satis_CHF_TON': '-',
                    'Satis_TL': None,
                    'HasPrice': False
                })
            continue

        for _, nakliye in nakliye_options.iterrows():
            nakliye_tl = nakliye['Fiyat_TL_KG']
            toplam_maliyet_tl = nts_tl + nakliye_tl
            satis_tl = toplam_maliyet_tl * (1 + kar_marji / 100)

            satis_usd_kg = satis_tl / usd_rate
            satis_eur_kg = satis_tl / eur_rate
            satis_chf_kg = satis_tl / chf_rate

            display_rows.append({
                'Fabrika': fabrika,
                'Firma': nakliye['Firma'],
                'Arac': nakliye['Arac_Tipi'],
                'NTS_TL': nts_tl,
                'Nakliye_TL': nakliye_tl,
                'Toplam_Maliyet_TL': toplam_maliyet_tl,
                'Satis_USD_KG': satis_usd_kg,
                'Satis_EUR_KG': satis_eur_kg,
                'Satis_CHF_KG': satis_chf_kg,
                'Satis_TL_TON': satis_tl * 1000,
                'Satis_USD_TON': satis_usd_kg * 1000,
                'Satis_EUR_TON': satis_eur_kg * 1000,
                'Satis_CHF_TON': satis_chf_kg * 1000,
                'Satis_TL': satis_tl,
                'HasPrice': True
            })

            calculated_rows.append({
                'Fabrika': fabrika,
                'Firma': nakliye['Firma'],
                'Arac': nakliye['Arac_Tipi'],
                'NTS_TL': nts_tl,
                'Nakliye_TL': nakliye_tl,
                'Toplam_Maliyet_TL': toplam_maliyet_tl,
                'Satis_TL': satis_tl,
                'Satis_USD_KG': satis_usd_kg,
                'Satis_EUR_KG': satis_eur_kg,
                'Satis_CHF_KG': satis_chf_kg,
                'Satis_USD_TON': satis_usd_kg * 1000,
                'Satis_EUR_TON': satis_eur_kg * 1000,
                'Satis_CHF_TON': satis_chf_kg * 1000,
                'Satis_TL_TON': satis_tl * 1000
            })

    en_ucuz = None
    if calculated_rows:
        en_ucuz = min(calculated_rows, key=lambda x: x['Satis_TL'])

    return en_ucuz, display_rows, exchange_rates

def save_new_product(urun_adi, fabrika, nts_maliyet, tarih):
    df = load_products()
    new_row = pd.DataFrame([{
        'Urun_Adi': urun_adi,
        'Fabrika': fabrika,
        'NTS_Maliyet_TL': nts_maliyet,
        'Kayit_Tarihi': tarih.strftime('%d.%m.%Y')
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(PRODUCT_FILE, index=False)

# --- SESSION STATE KONTROLÜ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'musteri_adi' not in st.session_state:
    st.session_state.musteri_adi = ''
if 'musteri_adi_kayit' not in st.session_state:
    st.session_state.musteri_adi_kayit = ''

# --- GİRİŞ SAYFASI ---
if not st.session_state.logged_in:
    st.title("🔐 NTS Mobil - Giriş")
    st.info(f"Proje Sahibi ve Sistem Yöneticisi: {OWNER_NAME} ({ADMIN_USERNAME})")
    ensure_owner_user()
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Yönetici: Yeni Kullanıcı"])
    
    with tab1:
        st.subheader("Kullanıcı Girişi")
        login_username = st.text_input("Kullanıcı Adı", key="login_user")
        login_password = st.text_input("Şifre", type="password", key="login_pass")
        
        if st.button("Giriş Yap", type="primary"):
            if verify_user(login_username, login_password):
                st.session_state.logged_in = True
                st.session_state.username = login_username
                st.rerun()
            else:
                st.error("❌ Hatalı kullanıcı adı veya şifre!")
    
    with tab2:
        st.subheader("Yeni Kullanıcı Oluştur")
        st.warning("⚠️ Bu alan sadece yöneticiler içindir.")
        
        admin_username = st.text_input("Yönetici Kullanıcı Adı", key="admin_user")
        admin_password = st.text_input("Yönetici Şifre", type="password", key="admin_pass")
        
        new_username = st.text_input("Yeni Kullanıcı Adı", key="new_user")
        new_password = st.text_input("Yeni Kullanıcı Şifre", type="password", key="new_pass")
        new_password_confirm = st.text_input("Şifre Tekrar", type="password", key="new_pass_confirm")
        
        if st.button("Kullanıcı Oluştur"):
            users = load_users()
            if not users:
                users[ADMIN_USERNAME] = {
                    'password': hash_password(ADMIN_DEFAULT_PASSWORD),
                    'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'created_by': OWNER_NAME,
                    'agreement_accepted': True
                }
                save_users(users)
            
            if verify_user(admin_username, admin_password):
                if new_password == new_password_confirm and len(new_password) >= 6:
                    success, message = create_user(new_username, new_password, admin_username)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Şifreler eşleşmiyor veya 6 karakterden kısa!")
            else:
                st.error("❌ Yönetici girişi başarısız!")
    
    st.stop()

# --- KULLANICI SÖZLEŞMESİ KONTROLÜ ---
if not user_accepted_agreement(st.session_state.username):
    st.title("📜 Kullanıcı Sözleşmesi")
    
    st.markdown("""
    ## NTS Mobil Uygulaması Kullanım Sözleşmesi
    
    **Hoş geldiniz!** Bu uygulamayı kullanmadan önce lütfen aşağıdaki şartları dikkatlice okuyunuz.
    
    ### 1. Telif Hakları
    - Bu uygulama ve içerdiği tüm veriler, algoritmalar ve hesaplamalar telif hakkı ile korunmaktadır.
    - Uygulamanın kaynak kodunu, veritabanını veya herhangi bir bölümünü kopyalamak, dağıtmak veya 
      üçüncü şahıslarla paylaşmak **kesinlikle yasaktır**.
    
    ### 2. Rekabet Yasağı
    - Bu uygulamadan elde ettiğiniz bilgileri, rakip firmalarla paylaşmayacağınızı,
    - Benzer bir sistem geliştirmek için kullanmayacağınızı,
    - Fiyatlandırma stratejilerini ve nakliye rotalarını gizli tutacağınızı kabul edersiniz.
    
    ### 3. Gizlilik ve Güvenlik
    - Kullanıcı adı ve şifrenizi **kimseyle paylaşmayacağınızı**,
    - Hesabınızdan yapılan tüm işlemlerden sorumlu olduğunuzu,
    - Şüpheli aktivite fark ettiğinizde hemen yöneticiyi bilgilendireceğinizi taahhüt edersiniz.
    
    ### 4. Yasal Sorumluluk
    - Bu sözleşmeyi ihlal etmeniz durumunda yasal işlem başlatılabilir.
    - Uygulamadan elde edilen verilerin yanlış kullanımından doğan zararlar kullanıcının sorumluluğundadır.
    
    ---
    
    **Devam ederek yukarıdaki şartları okuduğunuzu ve kabul ettiğinizi beyan edersiniz.**
    """)
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("✅ KABUL EDİYORUM", type="primary", use_container_width=True):
            accept_agreement(st.session_state.username)
            st.success("Sözleşme kabul edildi! Yönlendiriliyorsunuz...")
            st.rerun()
    
    st.stop()

# --- ANA UYGULAMA ---
df_products = load_products()
df_shipping = load_shipping()
kurlar = get_tcmb_rates()

with st.sidebar:
    st.title("📊 NTS Mobil v7.5")
    st.caption(f"👤 Kullanıcı: **{st.session_state.username}**")
    st.caption(f"🏢 Proje Sahibi / Yönetici: **{OWNER_NAME} ({ADMIN_USERNAME})**")
    page = st.radio("🔀 Menü", ["Fiyat Hesaplama", "Yeni Ürün Ekle", "📈 Ürün Fiyat Artışı", "Lojistik Fiyat Güncelleme", "📜 Hesaplama Geçmişi"])
    st.markdown("---")
    if st.button("🚪 Çıkış Yap"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

# =========================================================
# SAYFA 1: FİYAT HESAPLAMA
# =========================================================
if page == "Fiyat Hesaplama":
    st.header("💰 Fiyat Hesaplama Sistemi")
    kur_tarih = kurlar.get('source_date', kurlar.get('date', 'Bilinmiyor'))
    with st.expander("💱 Güncel Döviz Kurları (TCMB Satış)"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("USD", f"{kurlar.get('USD', 0):.4f} ₺")
        col2.metric("EUR", f"{kurlar.get('EUR', 0):.4f} ₺")
        col3.metric("CHF", f"{kurlar.get('CHF', 0):.4f} ₺")
        col4.info(f"📅 Kur Tarihi: {kur_tarih}")
        if kurlar.get('is_fallback'):
            st.warning("Bugün için kur bulunamadı; en yakın iş günü kullanıldı.")
    
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("🔧 Seçimler")
        musteri_adi = st.text_input("👤 Müşteri Adı (zorunlu)", key="musteri_adi")
        
        urun_listesi = [''] + sorted(df_products['Urun_Adi'].unique().tolist())
        secili_urun = st.selectbox("🔹 Ürün Seçin", urun_listesi, index=0)
        
        if secili_urun:
            sehir_listesi = sorted(df_shipping['Sehir'].unique())
            secili_sehir = st.selectbox("📍 Varış Şehri", sehir_listesi)
            
            st.markdown("### 📈 Kâr Marjı")
            if 'kar_marji' not in st.session_state:
                st.session_state.kar_marji = 30.0
            st.session_state.kar_marji = st.number_input("Marj (%)", min_value=-100.0, max_value=1000.0, value=float(st.session_state.kar_marji), step=1.0)
            st.caption(f"Girilen Marj: %{st.session_state.kar_marji}")
            
            st.markdown("---")
            
            if st.button("🚀 FİYAT HESAPLA", type="primary"):
                if not musteri_adi.strip():
                    st.error("❌ Müşteri adı zorunludur.")
                else:
                    musteri_adi_clean = musteri_adi.strip()
                    urun_kayit_tarih = None
                    urun_gecmis = df_products[df_products['Urun_Adi'] == secili_urun]
                    if not urun_gecmis.empty:
                        urun_kayit_tarih = urun_gecmis.sort_values('Kayit_Tarihi', ascending=False).iloc[0]['Kayit_Tarihi']

                    en_ucuz, tum_secenekler, kullanilan_kurlar = find_cheapest_route(
                        df_products, df_shipping, secili_urun, secili_sehir, st.session_state.kar_marji, kurlar
                    )
                    
                    if tum_secenekler:
                        st.session_state['hesaplama_yapildi'] = True
                        st.session_state['en_ucuz'] = en_ucuz
                        st.session_state['tum_secenekler'] = tum_secenekler
                        st.session_state['secili_urun'] = secili_urun
                        st.session_state['secili_sehir'] = secili_sehir
                        st.session_state['kullanilan_kurlar'] = kullanilan_kurlar
                        st.session_state['musteri_adi_kayit'] = musteri_adi_clean
                        st.session_state['urun_kayit_tarihi'] = urun_kayit_tarih.strftime('%Y-%m-%d') if urun_kayit_tarih is not None else None
                    else:
                        st.error("❌ Bu ürün veya şehir için veri bulunamadı!")
    
    with col_right:
        st.subheader("📋 Ürün Geçmişi")
        if secili_urun:
            for fabrika in ['TR14', 'TR15', 'TR16']:
                gecmis = get_all_product_prices(df_products, secili_urun, fabrika)
                if not gecmis.empty:
                    fab_adi = {"TR14": "🟩 GEBZE", "TR15": "🟦 TRABZON", "TR16": "🟧 ADANA"}[fabrika]
                    st.markdown(f"**{fab_adi}**")
                    for _, row in gecmis.iterrows():
                        tarih_str = row['Kayit_Tarihi'].strftime('%d.%m.%Y')
                        fiyat = row['NTS_Maliyet_TL']
                        st.caption(f"• {tarih_str}: **{fiyat:.2f} TL/Kg**")
        else:
            st.info("Lütfen ürün seçin")
    
    if 'hesaplama_yapildi' in st.session_state and st.session_state['hesaplama_yapildi']:
        st.markdown("---")
        st.subheader("✅ HESAPLAMA SONUÇLARI")

        en_ucuz = st.session_state['en_ucuz']
        tum_secenekler = st.session_state['tum_secenekler']
        urun_kayit_tarihi = st.session_state.get('urun_kayit_tarihi')
        urun_kayit_dt = datetime.strptime(urun_kayit_tarihi, '%Y-%m-%d').date() if urun_kayit_tarihi else None
        urun_kayit_kurlari = get_rates_for_date(urun_kayit_dt) if urun_kayit_dt else None

        if urun_kayit_tarihi:
            st.info(f"Ürün son kayıt tarihi: {urun_kayit_tarihi}")
            if urun_kayit_kurlari:
                st.caption(f"Kayıt tarihindeki kurlar → USD: {urun_kayit_kurlari.get('USD', 0):.4f} ₺ | EUR: {urun_kayit_kurlari.get('EUR', 0):.4f} ₺ | CHF: {urun_kayit_kurlari.get('CHF', 0):.4f} ₺")
            else:
                st.warning("Kayıt tarihi için kur bulunamadı; güncel kurlar gösterildi.")

        if en_ucuz:
            st.success("🏆 **EN UYGUN SEÇENEK**")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Fabrika", {"TR14": "GEBZE", "TR15": "TRABZON", "TR16": "ADANA"}.get(en_ucuz['Fabrika'], '-'))
            col2.metric("Firma", f"{en_ucuz['Firma']}")
            col3.metric("Araç", en_ucuz['Arac'])
            col4.metric("NTS Maliyet", f"{en_ucuz['NTS_TL']:.2f} TL")

            st.markdown("### 💰 Satış Fiyatı")
            c1, c2, c3, c4 = st.columns(4)

            def show_price(col, baslik, simge, kur):
                deger = en_ucuz['Satis_TL'] / kur
                ton_fiyat = deger * 1000
                col.metric(baslik, f"{deger:.4f} {simge}/Kg", f"{ton_fiyat:,.0f} {simge}/Ton")

            show_price(c1, "TL", "₺", 1.0)
            show_price(c2, "USD", "$", kurlar.get("USD", 36.50) or 36.50)
            show_price(c3, "EUR", "€", kurlar.get("EUR", 38.20) or 38.20)
            show_price(c4, "CHF", "₣", kurlar.get("CHF", 41.10) or 41.10)
        else:
            st.warning("Bu şehir/ürün için NTS maliyeti olmayan fabrikalar mevcut. Fiyat hesaplanamadı.")

        with st.expander("🔍 Tüm Fabrika & Nakliye Seçenekleri"):
            df_sonuc = pd.DataFrame(tum_secenekler)
            if not df_sonuc.empty:
                df_sonuc['Fabrika_Adi'] = df_sonuc['Fabrika'].map({"TR14": "GEBZE", "TR15": "TRABZON", "TR16": "ADANA"})
                df_sonuc['Siralama'] = df_sonuc.apply(lambda r: r['Satis_TL'] if r['HasPrice'] else float('inf'), axis=1)
                df_sonuc = df_sonuc.sort_values(['HasPrice', 'Siralama'], ascending=[False, True])

                def color_scale(val, min_val, max_val):
                    if pd.isna(val) or max_val == min_val:
                        return ''
                    normalized = (val - min_val) / (max_val - min_val)
                    r = int(144 + (255 - 144) * normalized)
                    g = int(238 - (238 - 182) * normalized)
                    b = int(144 - (144 - 198) * normalized)
                    return f'background-color: rgb({r}, {g}, {b})'

                value_cols = ['Toplam_Maliyet_TL', 'Satis_USD_KG', 'Satis_EUR_KG', 'Satis_CHF_KG', 'Satis_TL_TON', 'Satis_USD_TON', 'Satis_EUR_TON', 'Satis_CHF_TON']
                min_val = df_sonuc.loc[df_sonuc['HasPrice'], 'Satis_TL'].min()
                max_val = df_sonuc.loc[df_sonuc['HasPrice'], 'Satis_TL'].max()

                def row_style(row):
                    if not row['HasPrice']:
                        return ['background-color: #f0f0f0'] * len(row)
                    return [''] * len(row)

                display_df = df_sonuc[['Fabrika_Adi', 'Firma', 'Arac', 'NTS_TL', 'Nakliye_TL', 'Toplam_Maliyet_TL', 'Satis_TL', 'Satis_USD_KG', 'Satis_EUR_KG', 'Satis_CHF_KG', 'Satis_TL_TON', 'Satis_USD_TON', 'Satis_EUR_TON', 'Satis_CHF_TON', 'HasPrice']]

                styled_df = display_df.style.apply(row_style, axis=1).applymap(
                    lambda v: color_scale(v, min_val, max_val), subset=value_cols
                ).format({
                    'NTS_TL': lambda v: '-' if pd.isna(v) else f"{v:.2f}",
                    'Nakliye_TL': lambda v: '-' if pd.isna(v) else f"{v:.2f}",
                    'Toplam_Maliyet_TL': lambda v: '-' if pd.isna(v) else f"{v:.2f}",
                    'Satis_TL': lambda v: '-' if pd.isna(v) else f"{v:.2f}",
                    'Satis_USD_KG': lambda v: '-' if pd.isna(v) else f"${v:.4f}",
                    'Satis_EUR_KG': lambda v: '-' if pd.isna(v) else f"€{v:.4f}",
                    'Satis_CHF_KG': lambda v: '-' if pd.isna(v) else f"₣{v:.4f}",
                    'Satis_TL_TON': lambda v: '-' if pd.isna(v) else f"{v:,.2f} ₺",
                    'Satis_USD_TON': lambda v: '-' if pd.isna(v) else f"${v:,.2f}",
                    'Satis_EUR_TON': lambda v: '-' if pd.isna(v) else f"€{v:,.2f}",
                    'Satis_CHF_TON': lambda v: '-' if pd.isna(v) else f"₣{v:,.2f}",
                    'HasPrice': lambda v: ''
                })

                st.dataframe(styled_df, use_container_width=True, hide_index=True)

                if 'kullanilan_kurlar' in st.session_state:
                    kur_tarihi = st.session_state['kullanilan_kurlar'].get('source_date', st.session_state['kullanilan_kurlar'].get('date', 'Bilinmiyor'))
                    kur_usd = st.session_state['kullanilan_kurlar'].get('USD', 0)
                    st.caption(f"💱 Hesaplama Kur Tarihi: {kur_tarihi} | USD: {kur_usd:.4f} ₺")

        if en_ucuz:
            if st.button("💾 Hesaplamayı Kaydet", type="primary"):
                record = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'username': st.session_state.username,
                    'musteri': st.session_state.get('musteri_adi_kayit', ''),
                    'urun': st.session_state.get('secili_urun', ''),
                    'sehir': st.session_state.get('secili_sehir', ''),
                    'fabrika': en_ucuz['Fabrika'],
                    'firma': en_ucuz['Firma'],
                    'arac': en_ucuz['Arac'],
                    'kar_marji': st.session_state.get('kar_marji', 0),
                    'nts_tl': en_ucuz.get('NTS_TL'),
                    'nakliye_tl': en_ucuz.get('Nakliye_TL'),
                    'toplam_maliyet_tl': en_ucuz.get('Toplam_Maliyet_TL'),
                    'satis_tl_kg': en_ucuz.get('Satis_TL'),
                    'satis_usd_kg': en_ucuz.get('Satis_TL') / kurlar.get('USD', 1),
                    'satis_eur_kg': en_ucuz.get('Satis_TL') / kurlar.get('EUR', 1),
                    'satis_chf_kg': en_ucuz.get('Satis_TL') / kurlar.get('CHF', 1),
                    'satis_tl_ton': en_ucuz.get('Satis_TL') * 1000,
                    'satis_usd_ton': (en_ucuz.get('Satis_TL') / kurlar.get('USD', 1)) * 1000,
                    'satis_eur_ton': (en_ucuz.get('Satis_TL') / kurlar.get('EUR', 1)) * 1000,
                    'satis_chf_ton': (en_ucuz.get('Satis_TL') / kurlar.get('CHF', 1)) * 1000,
                    'usd_kur': kurlar.get('USD', 0),
                    'eur_kur': kurlar.get('EUR', 0),
                    'chf_kur': kurlar.get('CHF', 0),
                    'kur_tarihi': kur_tarih,
                    'urun_kayit_tarihi': urun_kayit_tarihi or ''
                }
                append_calc_record(record)
                st.success("📜 Hesaplama kaydedildi!")

# =========================================================
# SAYFA 2: YENİ ÜRÜN EKLE
# =========================================================
elif page == "Yeni Ürün Ekle":
    st.header("➕ Yeni Ürün / NTS Maliyeti Ekle")

    tab_tl, tab_usd, tab_eur = st.tabs(["💵 TL Girişi", "💲 USD Girişi", "💶 EUR / CHF Girişi"])

    with tab_tl:
        with st.form("yeni_urun_form_tl"):
            st.markdown("Aynı üründen birden çok kayıt ekleyebilirsiniz (fiyat güncellemeleri için).")
            col1, col2 = st.columns(2)
            with col1:
                yeni_urun_adi = st.text_input("Ürün Adı", key="tl_urun")
                yeni_fabrika = st.selectbox("Fabrika", ["TR14", "TR15", "TR16"], key="tl_fabrika")
            with col2:
                yeni_nts_maliyet = st.number_input("NTS Maliyet (TL/Kg)", min_value=0.0, step=0.01, format="%.4f", key="tl_nts")
                yeni_tarih = st.date_input("Kayıt Tarihi", value=datetime.now(), key="tl_tarih")

            submitted = st.form_submit_button("💾 Kaydet (TL)")
            if submitted:
                if yeni_urun_adi and yeni_nts_maliyet > 0:
                    save_new_product(yeni_urun_adi, yeni_fabrika, yeni_nts_maliyet, yeni_tarih)
                    st.success(f"✅ {yeni_urun_adi} ({yeni_fabrika}) {yeni_nts_maliyet:.4f} TL/Kg olarak eklendi")
                    st.rerun()
                else:
                    st.error("❌ Lütfen tüm alanları doldurun!")

    with tab_usd:
        usd_kur = kurlar.get('USD', 0)
        kur_tarih_usd = kurlar.get('source_date', 'Bilinmiyor')
        st.info(f"USD kuru: {usd_kur:.4f} ₺ | Kur tarihi: {kur_tarih_usd}")
        if kurlar.get('is_fallback'):
            st.warning("Hafta sonu/tatil nedeniyle önceki iş günü kuru kullanılıyor.")

        with st.form("yeni_urun_form_usd"):
            col1, col2 = st.columns(2)
            with col1:
                usd_urun = st.text_input("Ürün Adı", key="usd_urun")
                usd_fabrika = st.selectbox("Fabrika", ["TR14", "TR15", "TR16"], key="usd_fabrika")
            with col2:
                usd_fiyat = st.number_input("USD Fiyat (Kg)", min_value=0.0, step=0.01, format="%.4f", key="usd_fiyat")
                usd_tarih = st.date_input("Kayıt Tarihi", value=datetime.now(), key="usd_tarih")

            tl_karsilik = usd_fiyat * usd_kur
            st.caption(f"Anlık TL karşılığı: {tl_karsilik:.4f} TL/Kg")

            submit_usd = st.form_submit_button("💾 Kaydet (USD→TL)")
            if submit_usd:
                if usd_urun and usd_fiyat > 0:
                    save_new_product(usd_urun, usd_fabrika, tl_karsilik, usd_tarih)
                    st.success(f"✅ {usd_urun} ({usd_fabrika}) {usd_fiyat:.4f} $/Kg ({tl_karsilik:.4f} TL/Kg) olarak kaydedildi")
                    st.rerun()
                else:
                    st.error("❌ Lütfen tüm alanları doldurun!")

    with tab_eur:
        eur_chf_secim = st.selectbox("Döviz", ["EUR", "CHF"], key="eur_secim")
        secili_kur = kurlar.get(eur_chf_secim, 0)
        kur_tarih_eur = kurlar.get('source_date', 'Bilinmiyor')
        st.info(f"{eur_chf_secim} kuru: {secili_kur:.4f} ₺ | Kur tarihi: {kur_tarih_eur}")
        if kurlar.get('is_fallback'):
            st.warning("Hafta sonu/tatil nedeniyle önceki iş günü kuru kullanılıyor.")

        with st.form("yeni_urun_form_eur"):
            col1, col2 = st.columns(2)
            with col1:
                eur_urun = st.text_input("Ürün Adı", key="eur_urun")
                eur_fabrika = st.selectbox("Fabrika", ["TR14", "TR15", "TR16"], key="eur_fabrika")
            with col2:
                eur_fiyat = st.number_input(f"{eur_chf_secim} Fiyat (Kg)", min_value=0.0, step=0.01, format="%.4f", key="eur_fiyat")
                eur_tarih = st.date_input("Kayıt Tarihi", value=datetime.now(), key="eur_tarih")

            tl_karsilik_eur = eur_fiyat * secili_kur
            st.caption(f"Anlık TL karşılığı: {tl_karsilik_eur:.4f} TL/Kg")

            submit_eur = st.form_submit_button("💾 Kaydet (Döviz→TL)")
            if submit_eur:
                if eur_urun and eur_fiyat > 0:
                    save_new_product(eur_urun, eur_fabrika, tl_karsilik_eur, eur_tarih)
                    st.success(f"✅ {eur_urun} ({eur_fabrika}) {eur_fiyat:.4f} {eur_chf_secim}/Kg ({tl_karsilik_eur:.4f} TL/Kg) olarak kaydedildi")
                    st.rerun()
                else:
                    st.error("❌ Lütfen tüm alanları doldurun!")

    st.markdown("---")
    st.subheader("📂 Mevcut Ürünler")
    st.dataframe(df_products.sort_values('Kayit_Tarihi', ascending=False), use_container_width=True, hide_index=True)

# =========================================================
# SAYFA 3: LOJİSTİK YÖNETİMİ
# =========================================================
elif page == "📈 Ürün Fiyat Artışı":
    st.header("📈 Ürün Fiyat Artışı")

    def latest_price_info(urun, fabrika):
        subset = df_products[(df_products['Urun_Adi'] == urun) & (df_products['Fabrika'] == fabrika)]
        if subset.empty:
            return None, None
        latest = subset.sort_values('Kayit_Tarihi', ascending=False).iloc[0]
        return latest['NTS_Maliyet_TL'], latest['Kayit_Tarihi']

    st.markdown("### 🎯 A) Belirli Ürüne Artış")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        a_urun = st.selectbox("Ürün", sorted(df_products['Urun_Adi'].unique()), key="a_urun")
    with col_a2:
        a_fabrika = st.selectbox("Fabrika", ["TR14", "TR15", "TR16"], key="a_fabrika")
    with col_a3:
        a_oran = st.number_input("Artış (%)", min_value=-100.0, max_value=1000.0, value=0.0, step=1.0, key="a_oran")

    if a_urun:
        mevcut_fiyat, mevcut_tarih = latest_price_info(a_urun, a_fabrika)
        if mevcut_fiyat is not None:
            yeni_fiyat = mevcut_fiyat * (1 + a_oran / 100)
            st.metric("Mevcut Fiyat", f"{mevcut_fiyat:.4f} TL/Kg", help=f"Kayıt tarihi: {mevcut_tarih.strftime('%d.%m.%Y') if pd.notna(mevcut_tarih) else '-'}")
            st.metric("Yeni Fiyat", f"{yeni_fiyat:.4f} TL/Kg", delta=f"{yeni_fiyat - mevcut_fiyat:+.4f}")
            if st.button("Artışı Uygula ve Kaydet", key="btn_a"):
                save_new_product(a_urun, a_fabrika, yeni_fiyat, datetime.now())
                st.success(f"✅ {a_urun} ({a_fabrika}) için {a_oran}% uygulandı → {yeni_fiyat:.4f} TL/Kg")
                st.balloons()
                st.rerun()
        else:
            st.warning("Bu ürün için seçilen fabrikada fiyat bulunamadı.")

    st.markdown("---")
    st.markdown("### 🌐 B) Tüm Ürünlere Toplu Artış")
    b_oran = st.number_input("Toplu Artış (%)", min_value=-100.0, max_value=1000.0, value=0.0, step=1.0, key="b_oran")
    b_onay = st.checkbox("Tüm ürünlerde son fiyatları güncellemeyi onaylıyorum", key="b_onay")

    latest_all = df_products.sort_values('Kayit_Tarihi').groupby(['Urun_Adi', 'Fabrika'], as_index=False).tail(1)
    etkilenecek = len(latest_all)
    ort_fiyat = latest_all['NTS_Maliyet_TL'].mean() if not latest_all.empty else 0
    yeni_ort = ort_fiyat * (1 + b_oran / 100)
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.metric("Etkilenecek Kayıt", etkilenecek)
    col_b2.metric("Mevcut Ortalama", f"{ort_fiyat:.4f} TL/Kg")
    col_b3.metric("Yeni Ortalama", f"{yeni_ort:.4f} TL/Kg", delta=f"{yeni_ort - ort_fiyat:+.4f}")

    if st.button("🚀 Tüm Ürünleri Güncelle", type="primary", key="btn_b"):
        if b_oran == 0:
            st.warning("0 oranı için işlem yapılmadı.")
        elif not b_onay:
            st.error("Onay kutusunu işaretleyin.")
        else:
            for _, row in latest_all.iterrows():
                yeni_fiyat = row['NTS_Maliyet_TL'] * (1 + b_oran / 100)
                save_new_product(row['Urun_Adi'], row['Fabrika'], yeni_fiyat, datetime.now())
            st.success(f"✅ {etkilenecek} kayıt güncellendi. %{b_oran} uygulandı.")
            st.balloons()
            st.rerun()

    st.markdown("---")
    st.markdown("### 🏭 C) Fabrika Bazlı Toplu Artış")
    c_fabrika = st.selectbox("Fabrika Seç", ["TR14", "TR15", "TR16"], key="c_fabrika")
    c_oran = st.number_input("Artış (%)", min_value=-100.0, max_value=1000.0, value=0.0, step=1.0, key="c_oran")
    c_onay = st.checkbox("Bu fabrika için toplu güncellemeyi onaylıyorum", key="c_onay")

    factory_latest = latest_all[latest_all['Fabrika'] == c_fabrika]
    col_c1, col_c2 = st.columns(2)
    col_c1.metric("Ürün Sayısı", len(factory_latest))
    col_c2.metric("Mevcut Ortalama", f"{factory_latest['NTS_Maliyet_TL'].mean():.4f} TL/Kg" if not factory_latest.empty else "-")

    st.dataframe(factory_latest[['Urun_Adi', 'NTS_Maliyet_TL']].rename(columns={'Urun_Adi': 'Ürün', 'NTS_Maliyet_TL': 'Fiyat TL/Kg'}), use_container_width=True)

    if st.button("🏭 Fabrika Ürünlerini Güncelle", key="btn_c"):
        if c_oran == 0:
            st.warning("0 oranı için işlem yapılmadı.")
        elif not c_onay:
            st.error("Onay kutusunu işaretleyin.")
        else:
            for _, row in factory_latest.iterrows():
                yeni_fiyat = row['NTS_Maliyet_TL'] * (1 + c_oran / 100)
                save_new_product(row['Urun_Adi'], row['Fabrika'], yeni_fiyat, datetime.now())
            st.success(f"✅ {c_fabrika} fabrikasında {len(factory_latest)} kayıt güncellendi. %{c_oran} uygulandı.")
            st.balloons()
            st.rerun()

elif page == "Lojistik Fiyat Güncelleme":
    st.header("🚚 Lojistik Veritabanı Yönetimi")
    
    st.info("Nakliye fiyatlarını düzenleyebilir veya toplu zam uygulayabilirsiniz.")
    
    with st.container():
        st.subheader("📈 Toplu Zam Uygula")
        col_z1, col_z2 = st.columns([1, 2])
        
        with col_z1:
            zam_orani = st.number_input("Zam Oranı (%)", value=0.0, step=1.0)
        
        with col_z2:
            st.write("")
            st.write("")
            if st.button("🚀 Tüm Fiyatlara Uygula", type="primary"):
                if zam_orani != 0:
                    df_shipping['Fiyat_TL_KG'] = df_shipping['Fiyat_TL_KG'] * (1 + zam_orani / 100)
                    df_shipping['Fiyat_TL_KG'] = df_shipping['Fiyat_TL_KG'].round(2)
                    df_shipping.to_csv(SHIPPING_FILE, index=False)
                    st.success(f"✅ Tüm fiyatlara %{zam_orani} zam uygulandı!")
                    st.rerun()
                else:
                    st.warning("⚠️ Lütfen 0'dan farklı bir oran girin.")
    
    st.markdown("---")
    st.subheader("📝 Nakliye Fiyat Listesi")
    
    edited_df = st.data_editor(
        df_shipping,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Fiyat_TL_KG": st.column_config.NumberColumn("Fiyat (TL/Kg)", format="%.2f TL")
        }
    )
    
    if st.button("💾 Değişiklikleri Kaydet"):
        edited_df.to_csv(SHIPPING_FILE, index=False)
        st.success("✅ Nakliye veritabanı güncellendi!")
        st.rerun()

elif page == "📜 Hesaplama Geçmişi":
    st.header("📜 Hesaplama Geçmişi")
    ensure_calc_history_file()
    df_hist = pd.read_csv(CALC_HISTORY_FILE)
    if df_hist.empty:
        st.info("Henüz kayıt yok.")
    else:
        df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'])
        df_hist = df_hist.sort_values('timestamp', ascending=False)

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            f_musteri = st.selectbox("Müşteri", [''] + sorted(df_hist['musteri'].dropna().unique().tolist()))
        with col_f2:
            f_urun = st.selectbox("Ürün", [''] + sorted(df_hist['urun'].dropna().unique().tolist()))
        with col_f3:
            f_user = st.selectbox("Kullanıcı", [''] + sorted(df_hist['username'].dropna().unique().tolist()))

        if f_musteri:
            df_hist = df_hist[df_hist['musteri'] == f_musteri]
        if f_urun:
            df_hist = df_hist[df_hist['urun'] == f_urun]
        if f_user:
            df_hist = df_hist[df_hist['username'] == f_user]

        st.metric("Kayıt Sayısı", len(df_hist))

        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ CSV Olarak İndir", csv_data, "hesaplama_gecmisi.csv", mime="text/csv")

        st.dataframe(df_hist, use_container_width=True, hide_index=True)
