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
    year = date_obj.year
    month = f"{date_obj.month:02d}"
    url = f"https://www.tcmb.gov.tr/kurlar/{year}{month}/{date_str}.xml"
    try:
        response = requests.get(url, timeout=10)
    except Exception:
        return None
    if response.status_code != 200:
        return None
    try:
        root = ET.fromstring(response.content)
    except Exception:
        return None
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


def get_tcmb_rates(target_date=None):
    """
    TCMB'den döviz satış kurlarını çek.
    
    Args:
        target_date: datetime.date veya None. None ise bugünün tarihi kullanılır.
    
    Returns:
        dict: Kurlar ve tarih bilgisi
    """
    if target_date is None:
        target_date = datetime.now().date()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()
    
    attempts = 0
    for back in range(0, 15):  # 15 güne kadar geriye git
        candidate = target_date - timedelta(days=back)
        if candidate.weekday() >= 5:  # Hafta sonu ise atla
            continue
        attempts += 1
        if attempts > 10:  # Maksimum 10 iş günü dene
            break
        fetched = fetch_tcmb_for_date(candidate)
        if fetched:
            fetched['is_fallback'] = back > 0
            fetched['fallback_days'] = back
            fetched['target_date'] = target_date.strftime('%Y-%m-%d')
            if back > 0:
                fetched['used_date'] = candidate.strftime('%Y-%m-%d')
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


def get_selected_product_price(df_products, urun_adi, fabrika, secili_fiyatlar):
    """Kullanıcının seçtiği fiyatı döndür, yoksa en son fiyatı kullan"""
    if fabrika in secili_fiyatlar:
        return secili_fiyatlar[fabrika]
    return get_latest_product_price(df_products, urun_adi, fabrika)

def get_all_product_prices(df_products, urun_adi, fabrika):
    filtered = df_products[(df_products['Urun_Adi'] == urun_adi) & (df_products['Fabrika'] == fabrika)]
    return filtered.sort_values('Kayit_Tarihi', ascending=False)

def find_cheapest_route(df_products, df_shipping, urun_adi, sehir, kar_marji, exchange_rates, secili_fiyatlar=None, manuel_nakliye=None):
    if secili_fiyatlar is None:
        secili_fiyatlar = {}
    calculated_rows = []
    display_rows = []
    usd_rate = exchange_rates.get('USD', 36.50) or 36.50
    eur_rate = exchange_rates.get('EUR', 38.20) or 38.20
    chf_rate = exchange_rates.get('CHF', 41.10) or 41.10

    ilgili_nakliye = df_shipping[(df_shipping['Sehir'] == sehir)]
    tum_fabrikalar = ['TR14', 'TR15', 'TR16']
    
    # Manuel nakliye seçimi varsa, sadece o seçeneği hesapla
    if manuel_nakliye:
        fabrika = manuel_nakliye['fabrika']
        nts_tl = get_selected_product_price(df_products, urun_adi, fabrika, secili_fiyatlar)
        
        if nts_tl is not None:
            nakliye_tl = manuel_nakliye['fiyat']
            toplam_maliyet_tl = nts_tl + nakliye_tl
            satis_tl = toplam_maliyet_tl * (1 + kar_marji / 100)
            
            satis_usd_kg = satis_tl / usd_rate
            satis_eur_kg = satis_tl / eur_rate
            satis_chf_kg = satis_tl / chf_rate
            
            manuel_row = {
                'Fabrika': fabrika,
                'Firma': manuel_nakliye['firma'],
                'Arac': manuel_nakliye['arac'],
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
            }
            
            # Tüm fabrikalar için display göster ama sadece seçili manuel hesaplama
            for fab in tum_fabrikalar:
                if fab == fabrika:
                    display_rows.append(manuel_row)
                    calculated_rows.append(manuel_row)
                else:
                    # Diğer fabrikalar için boş gösterim
                    fab_nts = get_selected_product_price(df_products, urun_adi, fab, secili_fiyatlar)
                    display_rows.append({
                        'Fabrika': fab,
                        'Firma': '-',
                        'Arac': '-',
                        'NTS_TL': fab_nts if fab_nts is not None else '-',
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
            
            return manuel_row, display_rows, exchange_rates

    # Otomatik mod - tüm seçenekleri hesapla

    for fabrika in tum_fabrikalar:
        nts_tl = get_selected_product_price(df_products, urun_adi, fabrika, secili_fiyatlar)
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

def save_new_product(urun_adi, fabrika, nts_maliyet, tarih, para_birimi='TL', giris_fiyat=None, kur_usd=None, kur_eur=None, kur_chf=None, kur_tarihi=None):
    """Ürün kaydını genişletilmiş bilgilerle kaydet"""
    df = load_products()
    
    # Yeni kayıt
    new_row_data = {
        'Urun_Adi': urun_adi,
        'Fabrika': fabrika,
        'NTS_Maliyet_TL': nts_maliyet,
        'Giris_Para_Birimi': para_birimi,
        'Giris_Fiyat': giris_fiyat if giris_fiyat is not None else nts_maliyet,
        'Kayit_Tarihi': tarih.strftime('%d.%m.%Y'),
        'Kur_USD': kur_usd if kur_usd is not None else '',
        'Kur_EUR': kur_eur if kur_eur is not None else '',
        'Kur_CHF': kur_chf if kur_chf is not None else '',
        'Kur_Tarihi': kur_tarihi if kur_tarihi else ''
    }
    
    new_row = pd.DataFrame([new_row_data])
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
    page = st.radio("🔀 Menü", ["Fiyat Hesaplama", "Yeni Ürün Ekle", "📈 Ürün Fiyat Artışı", "Lojistik Fiyat Güncelleme", "� Bayi Müşteri Yönetimi", "�📜 Hesaplama Geçmişi"])
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
        
        # 1. Müşteri Adı (Ana Müşteri / Bayi)
        musteri_adi = st.text_input("👤 Müşteri Adı (Bayi) - Zorunlu", key="musteri_adi", placeholder="Örn: ABC İnşaat Ltd.")
        
        # 2. Bayi Müşteri Seçimi
        st.markdown("#### 🏢 Bayi Müşteri Seçimi")
        BAYI_MUSTERI_FILE = "bayi_musterileri.json"
        bayi_musteri_adi = ""
        
        if os.path.exists(BAYI_MUSTERI_FILE):
            with open(BAYI_MUSTERI_FILE, 'r', encoding='utf-8') as f:
                bayi_musteriler = json.load(f)
            
            current_user = st.session_state.username
            if current_user in bayi_musteriler and bayi_musteriler[current_user]:
                col_bayi1, col_bayi2 = st.columns([1, 1])
                with col_bayi1:
                    musteri_listesi = ["Manuel Giriş"] + [m['adi'] for m in bayi_musteriler[current_user]]
                    musteri_secim = st.selectbox("📋 Kayıtlı Müşterilerden Seç", musteri_listesi, key="musteri_sec")
                
                with col_bayi2:
                    if musteri_secim == "Manuel Giriş":
                        bayi_musteri_adi = st.text_input("✍️ Bayi Müşteri Adı", key="bayi_musteri_manuel", placeholder="Örn: XYZ Yapı A.Ş.")
                    else:
                        bayi_musteri_adi = musteri_secim
                        st.text_input("✅ Seçili Müşteri", value=musteri_secim, key="bayi_musteri_selected", disabled=True)
            else:
                bayi_musteri_adi = st.text_input("🏢 Bayi Müşteri Adı (Opsiyonel)", key="bayi_musteri_adi", placeholder="Örn: DEF Proje Ltd.")
        else:
            bayi_musteri_adi = st.text_input("🏢 Bayi Müşteri Adı (Opsiyonel)", key="bayi_musteri_adi", placeholder="Örn: DEF Proje Ltd.")
        
        st.markdown("---")
        
        urun_listesi = [''] + sorted(df_products['Urun_Adi'].unique().tolist())
        secili_urun = st.selectbox("🔹 Ürün Seçin", urun_listesi, index=0)
        
        if secili_urun:
            sehir_listesi = sorted(df_shipping['Sehir'].unique())
            secili_sehir = st.selectbox("📍 Varış Şehri", sehir_listesi)
            
            # Nakliye seçeneklerini göster
            st.markdown("### 🚛 Nakliye Seçimi")
            
            # Seçili şehir için mevcut nakliye seçenekleri
            sehir_nakliye = df_shipping[df_shipping['Sehir'] == secili_sehir].copy()
            
            if not sehir_nakliye.empty:
                # Nakliye modu: Otomatik veya Manuel
                nakliye_modu = st.radio("Nakliye Seçim Modu", 
                                       ["🤖 Otomatik (En Ucuz)", "✋ Manuel Seçim"], 
                                       key="nakliye_modu")
                
                if nakliye_modu == "✋ Manuel Seçim":
                    st.info("💡 Nakliyeci, araç ve fiyatı kendiniz seçin")
                    
                    # Fabrika seçimi
                    fabrika_listesi = sorted(sehir_nakliye['Fabrika'].unique().tolist())
                    secili_fabrika = st.selectbox("🏭 Fabrika", fabrika_listesi, key="manuel_fabrika")
                    
                    # Seçili fabrika için firma listesi
                    fabrika_nakliye = sehir_nakliye[sehir_nakliye['Fabrika'] == secili_fabrika]
                    firma_listesi = sorted(fabrika_nakliye['Firma'].unique().tolist())
                    secili_firma = st.selectbox("🚚 Nakliyeci Firma", firma_listesi, key="manuel_firma")
                    
                    # Seçili firma için araç listesi
                    firma_arac = fabrika_nakliye[fabrika_nakliye['Firma'] == secili_firma]
                    arac_listesi = sorted(firma_arac['Arac_Tipi'].unique().tolist())
                    secili_arac = st.selectbox("🚗 Araç Tipi", arac_listesi, key="manuel_arac")
                    
                    # Seçili kombinasyonun fiyatını göster
                    secili_nakliye = firma_arac[firma_arac['Arac_Tipi'] == secili_arac]
                    if not secili_nakliye.empty:
                        nakliye_fiyat = secili_nakliye.iloc[0]['Fiyat_TL_KG']
                        st.success(f"📦 Nakliye Fiyatı: **{nakliye_fiyat:.4f} TL/Kg**")
                        
                        # Manuel seçimleri session state'e kaydet
                        st.session_state['manuel_nakliye'] = {
                            'fabrika': secili_fabrika,
                            'firma': secili_firma,
                            'arac': secili_arac,
                            'fiyat': nakliye_fiyat
                        }
                else:
                    # Otomatik mod - manuel seçimi temizle
                    if 'manuel_nakliye' in st.session_state:
                        del st.session_state['manuel_nakliye']
            
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

                    # Manuel nakliye seçimi varsa kullan
                    manuel_nakliye = st.session_state.get('manuel_nakliye')
                    
                    en_ucuz, tum_secenekler, kullanilan_kurlar = find_cheapest_route(
                        df_products, df_shipping, secili_urun, secili_sehir, st.session_state.kar_marji, kurlar,
                        st.session_state.get('secili_fiyatlar', {}),
                        manuel_nakliye
                    )
                    
                    if tum_secenekler:
                        st.session_state['hesaplama_yapildi'] = True
                        st.session_state['en_ucuz'] = en_ucuz
                        st.session_state['tum_secenekler'] = tum_secenekler
                        st.session_state['secili_urun'] = secili_urun
                        st.session_state['secili_sehir'] = secili_sehir
                        st.session_state['kullanilan_kurlar'] = kullanilan_kurlar
                        st.session_state['musteri_adi_kayit'] = musteri_adi_clean
                        st.session_state['bayi_musteri_kayit'] = bayi_musteri_adi.strip() if bayi_musteri_adi else ""
                        try:
                            st.session_state['urun_kayit_tarihi'] = urun_kayit_tarih.strftime('%Y-%m-%d') if urun_kayit_tarih is not None and pd.notna(urun_kayit_tarih) else None
                        except:
                            st.session_state['urun_kayit_tarihi'] = None
                        st.rerun()
                    else:
                        st.error("❌ Bu ürün veya şehir için veri bulunamadı!")
    
    with col_right:
        st.subheader("📋 Ürün Geçmişi")
        if secili_urun:
            if 'secili_fiyatlar' not in st.session_state:
                st.session_state.secili_fiyatlar = {}
            
            # Tüm fabrikaları göster
            for fabrika in ['TR14', 'TR15', 'TR16']:
                fab_adi = {"TR14": "GEBZE", "TR15": "TRABZON", "TR16": "ADANA"}[fabrika]
                fab_emoji = {"TR14": "🟩", "TR15": "🟦", "TR16": "🟧"}[fabrika]
                
                # Container ile her fabrikayı çerçevele
                with st.container():
                    st.markdown(f"### {fab_emoji} {fab_adi}")
                    
                    # Bu fabrika için tüm fiyatları getir
                    gecmis = get_all_product_prices(df_products, secili_urun, fabrika)
                    
                    if not gecmis.empty:
                        # Birden fazla fiyat varsa dropdown ile seçim
                        if len(gecmis) > 1:
                            st.info(f"📊 {len(gecmis)} adet fiyat kaydı bulundu")
                            
                            tarih_secenekleri = []
                            for idx, row in gecmis.iterrows():
                                try:
                                    tarih_str = row['Kayit_Tarihi'].strftime('%d.%m.%Y') if pd.notna(row['Kayit_Tarihi']) else 'Tarih Yok'
                                except:
                                    tarih_str = 'Tarih Yok'
                                fiyat = row['NTS_Maliyet_TL']
                                tarih_secenekleri.append(f"{tarih_str} → {fiyat:.4f} TL/Kg")
                            
                            secili = st.selectbox(
                                f"{fab_adi} Fiyat Seçimi",
                                tarih_secenekleri,
                                key=f"fiyat_sec_{fabrika}",
                                help=f"{fab_adi} fabrikası için kullanılacak fiyatı seçin"
                            )
                            secili_index = tarih_secenekleri.index(secili)
                            secili_fiyat = gecmis.iloc[secili_index]['NTS_Maliyet_TL']
                            st.session_state.secili_fiyatlar[fabrika] = secili_fiyat
                            st.success(f"✅ Seçili: **{secili_fiyat:.4f} TL/Kg**")
                            
                        # Tek fiyat varsa direkt göster
                        else:
                            row = gecmis.iloc[0]
                            try:
                                tarih_str = row['Kayit_Tarihi'].strftime('%d.%m.%Y') if pd.notna(row['Kayit_Tarihi']) else 'Tarih Yok'
                            except:
                                tarih_str = 'Tarih Yok'
                            fiyat = row['NTS_Maliyet_TL']
                            st.success(f"💰 **{fiyat:.4f} TL/Kg**")
                            st.caption(f"📅 Kayıt Tarihi: {tarih_str}")
                            st.session_state.secili_fiyatlar[fabrika] = fiyat
                    
                    # Fiyat yoksa boş göster
                    else:
                        st.warning("❌ Fiyat kaydı bulunamadı")
                        st.caption("Bu fabrikada henüz ürün fiyatı girilmemiş")
                        if fabrika in st.session_state.secili_fiyatlar:
                            del st.session_state.secili_fiyatlar[fabrika]
                    
                    st.markdown("---")
        else:
            st.info("👆 Lütfen önce bir ürün seçin")
    
    if 'hesaplama_yapildi' in st.session_state and st.session_state['hesaplama_yapildi']:
        st.markdown("---")
        st.markdown("## 📊 DETAYLI FİYAT KARŞILAŞTIRMA TABLOSU")

        en_ucuz = st.session_state['en_ucuz']
        tum_secenekler = st.session_state['tum_secenekler']
        kullanilan_kurlar = st.session_state.get('kullanilan_kurlar', kurlar)
        
        # Döviz kurları
        usd_kur = kullanilan_kurlar.get('USD', 36.50) or 36.50
        eur_kur = kullanilan_kurlar.get('EUR', 38.20) or 38.20
        chf_kur = kullanilan_kurlar.get('CHF', 41.10) or 41.10
        kur_tarihi = kullanilan_kurlar.get('source_date', 'Bilinmiyor')
        
        # Kur bilgisi
        st.info(f"💱 Döviz Kurları (Tarih: {kur_tarihi}) → USD: {usd_kur:.4f} ₺ | EUR: {eur_kur:.4f} ₺ | CHF: {chf_kur:.4f} ₺ | Kar Marjı: %{st.session_state.get('kar_marji', 0):.1f}")

        if en_ucuz:
            # EN UCUZ SEÇENEK VURGUSU
            st.success("🏆 **EN UYGUN SEÇENEK**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fabrika", {"TR14": "GEBZE", "TR15": "TRABZON", "TR16": "ADANA"}.get(en_ucuz['Fabrika'], '-'))
                st.metric("Firma", f"{en_ucuz['Firma']}")
                st.metric("Araç", en_ucuz['Arac'])
            
            with col2:
                st.markdown("**💰 Maliyet**")
                st.metric("NTS", f"{en_ucuz['NTS_TL']:.2f} ₺/Kg")
                st.metric("Nakliye", f"{en_ucuz.get('Nakliye_TL', 0):.2f} ₺/Kg")
                st.metric("**Toplam**", f"**{en_ucuz.get('Toplam_Maliyet_TL', 0):.2f} ₺/Kg**")
            
            with col3:
                st.markdown("**📦 Satış Fiyatı (Birim)**")
                st.metric("TL/Kg", f"{en_ucuz['Satis_TL']:.2f} ₺")
                st.metric("USD/Kg", f"${en_ucuz['Satis_USD_KG']:.4f}")
                st.metric("EUR/Kg", f"€{en_ucuz['Satis_EUR_KG']:.4f}")
                st.metric("CHF/Kg", f"₣{en_ucuz['Satis_CHF_KG']:.4f}")
            
            st.markdown("---")
        
        # TÜM FABRİKALARIN FİYATLARINI GÖSTER
        st.markdown("### 🏭 Tüm Fabrikalar İçin Fiyat Karşılaştırması")
        st.caption(f"Ürün: **{st.session_state.get('secili_urun')}** | Varış Şehri: **{st.session_state.get('secili_sehir')}**")
        
        df_sonuc = pd.DataFrame(tum_secenekler)
        
        if not df_sonuc.empty:
            # Sadece fiyatı olan kayıtları al
            df_sonuc = df_sonuc[df_sonuc['Satis_TL'].notna()]
            
            if not df_sonuc.empty:
                # Fabrika bazında gruplama
                fabrika_isimleri = {"TR14": "🟩 GEBZE", "TR15": "🟦 TRABZON", "TR16": "🟧 ADANA"}
                
                for fabrika_kod in df_sonuc['Fabrika'].unique():
                    fab_data = df_sonuc[df_sonuc['Fabrika'] == fabrika_kod].copy()
                    
                    if not fab_data.empty:
                        with st.expander(f"{fabrika_isimleri.get(fabrika_kod, fabrika_kod)} - {len(fab_data)} nakliye seçeneği", expanded=True):
                            
                            # En ucuz bu fabrikadan
                            en_ucuz_fab = fab_data.loc[fab_data['Satis_TL'].idxmin()]
                            
                            st.info(f"💰 **En Ucuz Nakliye:** {en_ucuz_fab['Firma']} ({en_ucuz_fab['Arac']}) → **{en_ucuz_fab['Satis_TL']:.2f} ₺/Kg**")
                            
                            # Tablo için hazırlık
                            display_fab = fab_data[['Firma', 'Arac', 'NTS_TL', 'Nakliye_TL', 'Toplam_Maliyet_TL', 'Satis_TL', 'Satis_USD_KG', 'Satis_EUR_KG', 'Satis_CHF_KG']].copy()
                            
                            # Kolon isimlerini değiştir
                            display_fab.columns = ['Nakliye Firması', 'Araç Tipi', 'NTS (₺/Kg)', 'Nakliye (₺/Kg)', 'Toplam Maliyet (₺/Kg)', 'Satış TL/Kg', 'Satış $/Kg', 'Satış €/Kg', 'Satış ₣/Kg']
                            
                            # En ucuz satırı vurgula
                            def highlight_min(s):
                                is_min = s == s.min()
                                return ['background-color: lightgreen' if v else '' for v in is_min]
                            
                            st.dataframe(
                                display_fab.style.apply(highlight_min, subset=['Satış TL/Kg']).format({
                                    'NTS (₺/Kg)': '{:.2f}',
                                    'Nakliye (₺/Kg)': '{:.4f}',
                                    'Toplam Maliyet (₺/Kg)': '{:.2f}',
                                    'Satış TL/Kg': '{:.2f}',
                                    'Satış $/Kg': '{:.4f}',
                                    'Satış €/Kg': '{:.4f}',
                                    'Satış ₣/Kg': '{:.4f}'
                                }),
                                use_container_width=True,
                                hide_index=True
                            )
            else:
                st.warning("❌ Hesaplanabilir fiyat bulunamadı.")
        else:
            st.warning("❌ Sonuç verisi bulunamadı.")

        # Hesaplama kaydı butonu
        kayit_en_ucuz = st.session_state.get('en_ucuz')
        if kayit_en_ucuz:
            st.markdown("---")
            st.info("✅ Hesaplama tamamlandı. Kaydetmek için butona basın.")
            if st.button("💾 Hesaplamayı Kaydet", type="primary", key="kaydet_btn"):
                kayit_kurlar = st.session_state.get('kullanilan_kurlar', kurlar)
                
                # Kur tarihini kayıt tarihi olarak al
                kur_tarihi_str = kayit_kurlar.get('source_date', datetime.now().strftime('%Y-%m-%d'))
                
                record = {
                    'timestamp': kur_tarihi_str + ' ' + datetime.now().strftime('%H:%M:%S'),  # Kur tarihi + saat
                    'username': st.session_state.username,
                    'musteri': st.session_state.get('musteri_adi_kayit', ''),
                    'bayi_musteri': st.session_state.get('bayi_musteri_kayit', ''),
                    'urun': st.session_state.get('secili_urun', ''),
                    'sehir': st.session_state.get('secili_sehir', ''),
                    'fabrika': kayit_en_ucuz['Fabrika'],
                    'firma': kayit_en_ucuz['Firma'],
                    'arac': kayit_en_ucuz['Arac'],
                    'kar_marji': st.session_state.get('kar_marji', 0),
                    'nts_tl': kayit_en_ucuz.get('NTS_TL'),
                    'nakliye_tl': kayit_en_ucuz.get('Nakliye_TL'),
                    'toplam_maliyet_tl': kayit_en_ucuz.get('Toplam_Maliyet_TL'),
                    'satis_tl_kg': kayit_en_ucuz.get('Satis_TL'),
                    'satis_usd_kg': kayit_en_ucuz.get('Satis_TL') / kayit_kurlar.get('USD', 1),
                    'satis_eur_kg': kayit_en_ucuz.get('Satis_TL') / kayit_kurlar.get('EUR', 1),
                    'satis_chf_kg': kayit_en_ucuz.get('Satis_TL') / kayit_kurlar.get('CHF', 1),
                    'satis_tl_ton': kayit_en_ucuz.get('Satis_TL') * 1000,
                    'satis_usd_ton': (kayit_en_ucuz.get('Satis_TL') / kayit_kurlar.get('USD', 1)) * 1000,
                    'satis_eur_ton': (kayit_en_ucuz.get('Satis_TL') / kayit_kurlar.get('EUR', 1)) * 1000,
                    'satis_chf_ton': (kayit_en_ucuz.get('Satis_TL') / kayit_kurlar.get('CHF', 1)) * 1000,
                    'usd_kur': kayit_kurlar.get('USD', 0),
                    'eur_kur': kayit_kurlar.get('EUR', 0),
                    'chf_kur': kayit_kurlar.get('CHF', 0),
                    'kur_tarihi': kur_tarihi_str,
                    'urun_kayit_tarihi': st.session_state.get('urun_kayit_tarihi', '')
                }
                append_calc_record(record)
                
                # Bayi müşteri hesaplama sayısını güncelle
                BAYI_MUSTERI_FILE = "bayi_musterileri.json"
                if os.path.exists(BAYI_MUSTERI_FILE):
                    with open(BAYI_MUSTERI_FILE, 'r', encoding='utf-8') as f:
                        bayi_musteriler = json.load(f)
                    
                    current_user = st.session_state.username
                    bayi_musteri_kayit = st.session_state.get('bayi_musteri_kayit', '')
                    
                    if current_user in bayi_musteriler and bayi_musteri_kayit:
                        for musteri in bayi_musteriler[current_user]:
                            if musteri['adi'] == bayi_musteri_kayit:
                                musteri['toplam_hesaplama'] = musteri.get('toplam_hesaplama', 0) + 1
                                break
                        
                        with open(BAYI_MUSTERI_FILE, 'w', encoding='utf-8') as f:
                            json.dump(bayi_musteriler, f, indent=2, ensure_ascii=False)
                
                st.success("📜 Hesaplama kaydedildi!")
                st.balloons()

# =========================================================
# SAYFA 2: YENİ ÜRÜN EKLE
# =========================================================
elif page == "Yeni Ürün Ekle":
    st.header("➕ Yeni Ürün / NTS Maliyeti Ekle")
    
    # Kayıt tarihi için session state
    if 'secili_kayit_tarihi' not in st.session_state:
        st.session_state.secili_kayit_tarihi = datetime.now()
    
    # Kur bilgileri - kayıt tarihine göre
    usd_kur = kurlar.get('USD', 0)
    eur_kur = kurlar.get('EUR', 0)
    chf_kur = kurlar.get('CHF', 0)
    kur_tarihi = kurlar.get('source_date', 'Bilinmiyor')
    
    # Kur bilgilerini göster
    col_kur1, col_kur2, col_kur3, col_kur4 = st.columns(4)
    with col_kur1:
        st.metric("💵 USD", f"{usd_kur:.4f} ₺")
    with col_kur2:
        st.metric("💶 EUR", f"{eur_kur:.4f} ₺")
    with col_kur3:
        st.metric("💷 CHF", f"{chf_kur:.4f} ₺")
    with col_kur4:
        st.info(f"📅 Kur Tarihi\n\n{kur_tarihi}")
    
    if kurlar.get('is_fallback'):
        fallback_info = f"⚠️ "
        if kurlar.get('used_date'):
            fallback_info += f"Seçili tarih için kur bulunamadı. {kurlar.get('used_date')} tarihli kur kullanılıyor."
        else:
            fallback_info += "Hafta sonu/tatil nedeniyle önceki iş günü kuru kullanılıyor."
        st.warning(fallback_info)
    
    st.markdown("---")
    
    # Tarih seçimi ve kur güncelleme
    col_tarih1, col_tarih2 = st.columns([3, 1])
    with col_tarih1:
        secilen_tarih = st.date_input("📅 Kur ve Kayıt Tarihi Seçin", value=datetime.now(), key="kayit_tarihi_sec")
    with col_tarih2:
        st.write("")
        st.write("")
        if st.button("🔄 Bu Tarihin Kurlarını Getir", type="secondary"):
            # Seçilen tarihe göre kurları yeniden çek
            yeni_kurlar = get_tcmb_rates(secilen_tarih)
            st.session_state.secili_kayit_tarihi = secilen_tarih
            st.session_state.yeni_urun_kurlar = yeni_kurlar
            st.rerun()
    
    st.caption("💡 Seçilen tarih hem kur tarihi hem de kayıt tarihi olarak kullanılacaktır.")
    
    # Kayıt tarihi değişti mi kontrol et
    if 'yeni_urun_kurlar' in st.session_state:
        kurlar_kayit = st.session_state.yeni_urun_kurlar
        usd_kur = kurlar_kayit.get('USD', 0)
        eur_kur = kurlar_kayit.get('EUR', 0)
        chf_kur = kurlar_kayit.get('CHF', 0)
        
        # Güncellenen kurları göster
        st.success(f"✅ {secilen_tarih.strftime('%d.%m.%Y')} tarihine göre kurlar yüklendi")
        col_k1, col_k2, col_k3 = st.columns(3)
        with col_k1:
            st.info(f"💵 USD: {usd_kur:.4f} ₺")
        with col_k2:
            st.info(f"💶 EUR: {eur_kur:.4f} ₺")
        with col_k3:
            st.info(f"💷 CHF: {chf_kur:.4f} ₺")
        
        if kurlar_kayit.get('is_fallback') and kurlar_kayit.get('used_date'):
            st.warning(f"⚠️ Seçili tarih için kur bulunamadı. {kurlar_kayit.get('used_date')} tarihli kur kullanılıyor.")
    
    st.markdown("---")
    
    # Tek form ile tüm girişler
    with st.form("yeni_urun_form"):
        st.markdown("### 📝 Ürün Bilgileri")
        st.caption("Aynı üründen birden çok kayıt ekleyebilirsiniz (fiyat güncellemeleri için).")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            yeni_urun_adi = st.text_input("Ürün Adı *", key="urun_adi")
        with col2:
            yeni_fabrika = st.selectbox("Fabrika *", ["TR14", "TR15", "TR16"], key="fabrika")
        with col3:
            form_tarih = st.date_input("Kayıt Tarihi", value=secilen_tarih, key="tarih", disabled=True)
            st.caption("↑ Kur tarihiyle aynı")
        
        # Form içinde kullanılacak kurlar
        if 'yeni_urun_kurlar' in st.session_state:
            form_usd_kur = st.session_state.yeni_urun_kurlar.get('USD', usd_kur)
            form_eur_kur = st.session_state.yeni_urun_kurlar.get('EUR', eur_kur)
            form_chf_kur = st.session_state.yeni_urun_kurlar.get('CHF', chf_kur)
        else:
            form_usd_kur = usd_kur
            form_eur_kur = eur_kur
            form_chf_kur = chf_kur
        
        st.markdown("---")
        st.markdown("### 💰 Fiyat Girişi")
        
        # Hangi para biriminde gireceğini seç
        para_birimi = st.radio(
            "Fiyat Hangi Para Biriminde?",
            ["TL", "USD", "EUR", "CHF"],
            horizontal=True,
            key="para_birimi"
        )
        
        st.caption(f"💡 Fiyatı **{para_birimi}** cinsinden girin. Diğer döviz karşılıkları otomatik hesaplanacaktır.")
        
        # Seçilen para birimine göre input göster
        col_input, col_spacer = st.columns([1, 3])
        
        with col_input:
            if para_birimi == "TL":
                girilen_fiyat = st.number_input("💵 TL/Kg *", min_value=0.0, step=0.01, format="%.4f", key="fiyat_input")
                tl_karsilik = girilen_fiyat
            elif para_birimi == "USD":
                girilen_fiyat = st.number_input("💲 USD/Kg *", min_value=0.0, step=0.01, format="%.4f", key="fiyat_input")
                tl_karsilik = girilen_fiyat * form_usd_kur
            elif para_birimi == "EUR":
                girilen_fiyat = st.number_input("💶 EUR/Kg *", min_value=0.0, step=0.01, format="%.4f", key="fiyat_input")
                tl_karsilik = girilen_fiyat * form_eur_kur
            else:  # CHF
                girilen_fiyat = st.number_input("💷 CHF/Kg *", min_value=0.0, step=0.01, format="%.4f", key="fiyat_input")
                tl_karsilik = girilen_fiyat * form_chf_kur
                tl_karsilik = girilen_fiyat * chf_kur
        
        # Tüm döviz karşılıklarını göster
        if girilen_fiyat > 0:
            st.markdown("#### 💱 Döviz Karşılıkları")
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            
            with col_d1:
                if para_birimi == "TL":
                    st.metric("💵 TL/Kg", f"{girilen_fiyat:.4f}", delta="Girilen")
                else:
                    st.metric("💵 TL/Kg", f"{tl_karsilik:.4f}")
            
            with col_d2:
                if para_birimi == "USD":
                    st.metric("💲 USD/Kg", f"{girilen_fiyat:.4f}", delta="Girilen")
                else:
                    usd_karsilik = tl_karsilik / form_usd_kur if form_usd_kur > 0 else 0
                    st.metric("💲 USD/Kg", f"{usd_karsilik:.4f}")
            
            with col_d3:
                if para_birimi == "EUR":
                    st.metric("💶 EUR/Kg", f"{girilen_fiyat:.4f}", delta="Girilen")
                else:
                    eur_karsilik = tl_karsilik / form_eur_kur if form_eur_kur > 0 else 0
                    st.metric("💶 EUR/Kg", f"{eur_karsilik:.4f}")
            
            with col_d4:
                if para_birimi == "CHF":
                    st.metric("💷 CHF/Kg", f"{girilen_fiyat:.4f}", delta="Girilen")
                else:
                    chf_karsilik = tl_karsilik / form_chf_kur if form_chf_kur > 0 else 0
                    st.metric("💷 CHF/Kg", f"{chf_karsilik:.4f}")
            
            st.success(f"✅ **Veritabanına kaydedilecek:** {tl_karsilik:.4f} TL/Kg")
            
            # Kullanılan kur bilgisini göster
            if 'yeni_urun_kurlar' in st.session_state:
                kur_bilgi = st.session_state.yeni_urun_kurlar.get('source_date', '')
                if kur_bilgi:
                    st.caption(f"📅 Hesaplama Tarihi: {kur_bilgi}")
        
        st.markdown("---")
        
        submitted = st.form_submit_button("💾 ÜRÜNÜ KAYDET", type="primary", use_container_width=True)
        
        if submitted:
            if not yeni_urun_adi:
                st.error("❌ Ürün adı zorunludur!")
            elif girilen_fiyat <= 0:
                st.error("❌ Fiyat 0'dan büyük olmalıdır!")
            else:
                # Kur bilgilerini hazırla
                kur_tarihi_kayit = None
                if 'yeni_urun_kurlar' in st.session_state:
                    kur_tarihi_kayit = st.session_state.yeni_urun_kurlar.get('source_date', '')
                
                # Kaydet - Tüm bilgilerle
                save_new_product(
                    urun_adi=yeni_urun_adi,
                    fabrika=yeni_fabrika,
                    nts_maliyet=tl_karsilik,
                    tarih=secilen_tarih,
                    para_birimi=para_birimi,
                    giris_fiyat=girilen_fiyat,
                    kur_usd=form_usd_kur,
                    kur_eur=form_eur_kur,
                    kur_chf=form_chf_kur,
                    kur_tarihi=kur_tarihi_kayit
                )
                
                # Kur bilgisini göster
                kur_info = ""
                if kur_tarihi_kayit:
                    kur_info = f" (Kur Tarihi: {kur_tarihi_kayit})"
                
                st.success(f"🎉 **{yeni_urun_adi}** ({yeni_fabrika}) → {girilen_fiyat:.4f} {para_birimi}/Kg = **{tl_karsilik:.4f} TL/Kg** olarak kaydedildi!{kur_info}")
                st.balloons()
                st.rerun()

    st.markdown("---")
    st.subheader("� Excel/CSV Dosyasından Toplu Ekleme")
    
    with st.expander("📋 Dosya Formatı Hakkında Bilgi"):
        st.info("""
        **Gerekli Kolonlar:**
        - `Urun_Adi` veya `Ürün Adı`
        - `Fabrika` (TR14, TR15, TR16)
        - `NTS_Maliyet_TL` veya `Maliyet` veya `Fiyat`
        
        **Desteklenen Formatlar:** Excel (.xlsx, .xls) veya CSV (.csv)
        
        **Not:** Kayıt tarihi otomatik olarak eklenecektir.
        """)
        
        # Örnek şablon göster
        sample_df = pd.DataFrame({
            'Urun_Adi': ['Örnek Ürün 1', 'Örnek Ürün 2'],
            'Fabrika': ['TR14', 'TR15'],
            'NTS_Maliyet_TL': [12.50, 15.75]
        })
        st.dataframe(sample_df, use_container_width=True, hide_index=True)
    
    uploaded_file = st.file_uploader("📁 Excel veya CSV Dosyası Seçin", type=['xlsx', 'xls', 'csv'], key="excel_upload")
    
    if uploaded_file is not None:
        try:
            # Dosya tipine göre okuma
            if uploaded_file.name.endswith('.csv'):
                uploaded_df = pd.read_csv(uploaded_file)
            else:
                uploaded_df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Dosya yüklendi: {len(uploaded_df)} satır bulundu")
            
            # Kolon isimleri eşleştirme
            column_mapping = {}
            for col in uploaded_df.columns:
                col_lower = col.lower().strip()
                if 'urun' in col_lower or 'ürün' in col_lower:
                    column_mapping[col] = 'Urun_Adi'
                elif 'fabrika' in col_lower:
                    column_mapping[col] = 'Fabrika'
                elif 'maliyet' in col_lower or 'fiyat' in col_lower or 'tl' in col_lower:
                    column_mapping[col] = 'NTS_Maliyet_TL'
            
            uploaded_df = uploaded_df.rename(columns=column_mapping)
            
            # Gerekli kolonları kontrol et
            required_cols = ['Urun_Adi', 'Fabrika', 'NTS_Maliyet_TL']
            missing_cols = [col for col in required_cols if col not in uploaded_df.columns]
            
            if missing_cols:
                st.error(f"❌ Eksik kolonlar: {', '.join(missing_cols)}")
                st.warning("Lütfen dosyanızın gerekli kolonları içerdiğinden emin olun.")
            else:
                # Veri önizleme
                st.subheader("📊 Veri Önizleme")
                preview_df = uploaded_df[required_cols].head(10)
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
                
                # İstatistikler
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("📦 Toplam Kayıt", len(uploaded_df))
                with col_stat2:
                    st.metric("🏭 Fabrika Sayısı", uploaded_df['Fabrika'].nunique())
                with col_stat3:
                    st.metric("🔢 Benzersiz Ürün", uploaded_df['Urun_Adi'].nunique())
                
                # Fabrika dağılımı
                fab_counts = uploaded_df['Fabrika'].value_counts()
                st.write("**Fabrika Dağılımı:**")
                for fab, count in fab_counts.items():
                    st.write(f"- {fab}: {count} kayıt")
                
                # Import butonu
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    if st.button("✅ ÜRÜNLER İ EKLE", type="primary", use_container_width=True):
                        # Tarih ekle
                        uploaded_df['Kayit_Tarihi'] = datetime.now().strftime('%d.%m.%Y')
                        
                        # Sadece gerekli kolonları al
                        new_products = uploaded_df[['Urun_Adi', 'Fabrika', 'NTS_Maliyet_TL', 'Kayit_Tarihi']].copy()
                        
                        # Mevcut verilere ekle
                        df_products = pd.concat([df_products, new_products], ignore_index=True)
                        df_products.to_csv(PRODUCT_FILE, index=False)
                        
                        st.success(f"🎉 {len(new_products)} ürün başarıyla eklendi!")
                        st.balloons()
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ Dosya okuma hatası: {str(e)}")
            st.warning("Lütfen dosya formatını kontrol edin.")

    st.markdown("---")
    st.subheader("�📂 Mevcut Ürünler")
    
    # Arama ve filtreleme
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_term = st.text_input("🔍 Ürün Ara", placeholder="Ürün adı yazın...", key="urun_ara")
    with col_search2:
        fab_filter = st.selectbox("🏭 Fabrika Filtrele", ["Tümü", "TR14", "TR15", "TR16"], key="fab_filtre")
    
    # Filtreleme uygula
    display_products = df_products.copy()
    if search_term:
        display_products = display_products[display_products['Urun_Adi'].str.contains(search_term, case=False, na=False)]
    if fab_filter != "Tümü":
        display_products = display_products[display_products['Fabrika'] == fab_filter]
    
    display_products = display_products.sort_values('Kayit_Tarihi', ascending=False)
    
    st.info(f"📊 Toplam {len(display_products)} kayıt bulundu")
    
    # Ürün silme alanı (sadece yönetici için)
    if st.session_state.username == ADMIN_USERNAME:
        with st.expander("🗑️ Ürün Silme İşlemleri (YÖNETİCİ)"):
            st.warning("⚠️ Dikkat! Bu işlem geri alınamaz.")
            
            delete_col1, delete_col2, delete_col3 = st.columns(3)
            with delete_col1:
                delete_urun = st.selectbox("Silinecek Ürün", sorted(df_products['Urun_Adi'].unique()), key="sil_urun")
            with delete_col2:
                delete_fabrika = st.selectbox("Fabrika", ["Tümü", "TR14", "TR15", "TR16"], key="sil_fabrika")
            with delete_col3:
                st.write("")
                st.write("")
                if delete_fabrika == "Tümü":
                    if st.button("🗑️ TÜM FABRİKALARDAN SİL", type="secondary"):
                        df_products = df_products[df_products['Urun_Adi'] != delete_urun]
                        df_products.to_csv(PRODUCT_FILE, index=False)
                        st.success(f"✅ '{delete_urun}' tüm fabrikalardan silindi!")
                        st.balloons()
                        st.rerun()
                else:
                    if st.button(f"🗑️ {delete_fabrika}'dan SİL", type="secondary"):
                        df_products = df_products[~((df_products['Urun_Adi'] == delete_urun) & (df_products['Fabrika'] == delete_fabrika))]
                        df_products.to_csv(PRODUCT_FILE, index=False)
                        st.success(f"✅ '{delete_urun}' ({delete_fabrika}) silindi!")
                        st.balloons()
                        st.rerun()
            
            # Toplu silme
            st.markdown("---")
            st.markdown("##### 🗂️ Toplu Silme")
            st.warning("⚠️ Aşağıdaki işlemler çok sayıda kaydı etkileyebilir!")
            
            toplu_col1, toplu_col2 = st.columns(2)
            with toplu_col1:
                toplu_fabrika = st.selectbox("Fabrika Seç", ["TR14", "TR15", "TR16"], key="toplu_sil_fab")
            with toplu_col2:
                st.write("")
                st.write("")
                if st.button(f"🗑️ {toplu_fabrika} FABRİKADAKİ TÜM ÜRÜNLERİ SİL", type="secondary"):
                    etkilenen = len(df_products[df_products['Fabrika'] == toplu_fabrika])
                    df_products = df_products[df_products['Fabrika'] != toplu_fabrika]
                    df_products.to_csv(PRODUCT_FILE, index=False)
                    st.success(f"✅ {toplu_fabrika} fabrikasından {etkilenen} kayıt silindi!")
                    st.rerun()
    
    # Döviz karşılıklarını hesapla ve ekle
    display_products_with_currencies = display_products.copy()
    
    # Kayıt Tarihini datetime formatına çevir
    if 'Kayit_Tarihi' in display_products_with_currencies.columns:
        display_products_with_currencies['Kayit_Tarihi'] = pd.to_datetime(
            display_products_with_currencies['Kayit_Tarihi'], 
            format='%d.%m.%Y', 
            errors='coerce'
        )
    
    # Index'i kaydet (silme için gerekli)
    display_products_with_currencies = display_products_with_currencies.reset_index(drop=False)
    display_products_with_currencies = display_products_with_currencies.rename(columns={'index': 'original_index'})
    
    # Yeni kolonları ekle - Girilen para birimi ve orijinal fiyat
    if 'Giris_Para_Birimi' not in display_products_with_currencies.columns:
        display_products_with_currencies['Giris_Para_Birimi'] = 'TL'
    if 'Giris_Fiyat' not in display_products_with_currencies.columns:
        display_products_with_currencies['Giris_Fiyat'] = display_products_with_currencies['NTS_Maliyet_TL']
    if 'Kur_USD' not in display_products_with_currencies.columns:
        display_products_with_currencies['Kur_USD'] = ''
    if 'Kur_EUR' not in display_products_with_currencies.columns:
        display_products_with_currencies['Kur_EUR'] = ''
    if 'Kur_CHF' not in display_products_with_currencies.columns:
        display_products_with_currencies['Kur_CHF'] = ''
    if 'Kur_Tarihi' not in display_products_with_currencies.columns:
        display_products_with_currencies['Kur_Tarihi'] = ''
    
    # Döviz karşılıklarını hesapla - KAYDEDİLEN KURLARA GÖRE
    # Eğer kayıtlı kur varsa onu kullan, yoksa güncel kuru kullan (eski kayıtlar için)
    def calculate_currency(row):
        tl_value = row['NTS_Maliyet_TL']
        
        # Kayıtlı kurları kontrol et
        try:
            saved_usd = float(row['Kur_USD']) if row['Kur_USD'] and str(row['Kur_USD']).strip() else None
            saved_eur = float(row['Kur_EUR']) if row['Kur_EUR'] and str(row['Kur_EUR']).strip() else None
            saved_chf = float(row['Kur_CHF']) if row['Kur_CHF'] and str(row['Kur_CHF']).strip() else None
        except:
            saved_usd = None
            saved_eur = None
            saved_chf = None
        
        # Güncel kurlar (fallback)
        current_usd = kurlar.get('USD', 1)
        current_eur = kurlar.get('EUR', 1)
        current_chf = kurlar.get('CHF', 1)
        
        # Kurları seç (kayıtlı varsa onu, yoksa güncel)
        use_usd = saved_usd if saved_usd else current_usd
        use_eur = saved_eur if saved_eur else current_eur
        use_chf = saved_chf if saved_chf else current_chf
        
        return pd.Series({
            'USD/Kg': round(tl_value / use_usd, 4) if use_usd > 0 else 0,
            'EUR/Kg': round(tl_value / use_eur, 4) if use_eur > 0 else 0,
            'CHF/Kg': round(tl_value / use_chf, 4) if use_chf > 0 else 0
        })
    
    # Döviz karşılıklarını hesapla
    currency_cols = display_products_with_currencies.apply(calculate_currency, axis=1)
    display_products_with_currencies[['USD/Kg', 'EUR/Kg', 'CHF/Kg']] = currency_cols
    
    # Kolon sırasını düzenle
    display_products_with_currencies = display_products_with_currencies[[
        'original_index', 'Urun_Adi', 'Fabrika', 
        'Giris_Para_Birimi', 'Giris_Fiyat',
        'NTS_Maliyet_TL', 'USD/Kg', 'EUR/Kg', 'CHF/Kg', 
        'Kayit_Tarihi', 'Kur_Tarihi'
    ]]
    
    # Kur bilgisi
    st.info(f"💡 **Döviz karşılıkları her ürünün KENDİ kayıt tarihindeki kurla hesaplanmıştır.** Güncel kur ({kur_tarihi}): USD={kurlar.get('USD', 0):.4f}, EUR={kurlar.get('EUR', 0):.4f}, CHF={kurlar.get('CHF', 0):.4f}")
    
    # Tablo görünümü - data_editor ile satır silme özelliği
    st.markdown("##### 📊 Ürün Listesi (Satırları düzenleyebilir veya silebilirsiniz)")
    st.caption(f"📊 Toplam **{len(display_products_with_currencies)}** kayıt gösteriliyor")
    
    edited_df = st.data_editor(
        display_products_with_currencies,
        use_container_width=True,
        hide_index=True,
        height=500,
        num_rows="dynamic",  # Satır ekleme/silme aktif
        disabled=['original_index', 'USD/Kg', 'EUR/Kg', 'CHF/Kg', 'Kur_Tarihi'],  # Otomatik hesaplananlar salt okunur
        column_config={
            "original_index": None,  # Gizle
            "Urun_Adi": st.column_config.TextColumn("Ürün Adı", width="large", required=True),
            "Fabrika": st.column_config.SelectboxColumn("Fabrika", options=["TR14", "TR15", "TR16"], width="small", required=True),
            "Giris_Para_Birimi": st.column_config.SelectboxColumn("💱 Para Birimi", options=["TL", "USD", "EUR", "CHF"], width="small", help="Girilen para birimi"),
            "Giris_Fiyat": st.column_config.NumberColumn("📝 Girilen Fiyat", format="%.4f", width="medium", help="Orijinal girilen fiyat"),
            "NTS_Maliyet_TL": st.column_config.NumberColumn("💵 TL/Kg", format="%.4f", width="medium", required=True),
            "USD/Kg": st.column_config.NumberColumn("💲 USD/Kg", format="%.4f", width="medium"),
            "EUR/Kg": st.column_config.NumberColumn("💶 EUR/Kg", format="%.4f", width="medium"),
            "CHF/Kg": st.column_config.NumberColumn("💷 CHF/Kg", format="%.4f", width="medium"),
            "Kayit_Tarihi": st.column_config.DateColumn("📅 Kayıt Tarihi", format="DD.MM.YYYY", width="medium"),
            "Kur_Tarihi": st.column_config.TextColumn("📅 Kur Tarihi", width="medium", help="Kullanılan kur tarihi")
        },
        key="products_editor"
    )
    
    # Değişiklikleri kaydet butonu
    col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
    with col_save2:
        if st.button("💾 DEĞİŞİKLİKLERİ KAYDET", type="primary", use_container_width=True):
            # Silinen satırları tespit et
            original_indices = set(display_products_with_currencies['original_index'].tolist())
            edited_indices = set(edited_df['original_index'].tolist())
            deleted_indices = original_indices - edited_indices
            
            # Silinen satırları ana dataframe'den çıkar
            if deleted_indices:
                df_products_filtered = df_products.drop(index=list(deleted_indices))
                df_products_filtered.to_csv(PRODUCT_FILE, index=False)
                st.success(f"✅ {len(deleted_indices)} satır silindi ve değişiklikler kaydedildi!")
                st.balloons()
                st.rerun()
            else:
                # Düzenlenmiş verileri güncelle
                degisiklik_sayisi = 0
                for idx, row in edited_df.iterrows():
                    orig_idx = row['original_index']
                    if orig_idx in df_products.index:
                        # Değişiklikleri kontrol et ve kaydet
                        if df_products.loc[orig_idx, 'Urun_Adi'] != row['Urun_Adi']:
                            df_products.loc[orig_idx, 'Urun_Adi'] = row['Urun_Adi']
                            degisiklik_sayisi += 1
                        if df_products.loc[orig_idx, 'Fabrika'] != row['Fabrika']:
                            df_products.loc[orig_idx, 'Fabrika'] = row['Fabrika']
                            degisiklik_sayisi += 1
                        if df_products.loc[orig_idx, 'NTS_Maliyet_TL'] != row['NTS_Maliyet_TL']:
                            df_products.loc[orig_idx, 'NTS_Maliyet_TL'] = row['NTS_Maliyet_TL']
                            degisiklik_sayisi += 1
                        if df_products.loc[orig_idx, 'Giris_Para_Birimi'] != row['Giris_Para_Birimi']:
                            df_products.loc[orig_idx, 'Giris_Para_Birimi'] = row['Giris_Para_Birimi']
                            degisiklik_sayisi += 1
                        if df_products.loc[orig_idx, 'Giris_Fiyat'] != row['Giris_Fiyat']:
                            df_products.loc[orig_idx, 'Giris_Fiyat'] = row['Giris_Fiyat']
                            degisiklik_sayisi += 1
                        
                        # Tarihi düzgün formatta kaydet
                        if pd.notna(row['Kayit_Tarihi']):
                            if isinstance(row['Kayit_Tarihi'], str):
                                tarih_str = row['Kayit_Tarihi']
                            else:
                                tarih_str = row['Kayit_Tarihi'].strftime('%d.%m.%Y')
                            df_products.loc[orig_idx, 'Kayit_Tarihi'] = tarih_str
                
                df_products.to_csv(PRODUCT_FILE, index=False)
                if degisiklik_sayisi > 0:
                    st.success(f"✅ {degisiklik_sayisi} değişiklik kaydedildi!")
                else:
                    st.info("ℹ️ Hiçbir değişiklik yapılmadı.")
                st.rerun()
    
    st.info("💡 **İpucu:** Tabloda istediğiniz hücreyi tıklayarak düzenleyebilirsiniz. Satır silmek için soldaki ❌ butonuna tıklayın. Tüm değişiklikler için 'Değişiklikleri Kaydet' butonuna basın.")

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

elif page == "� Bayi Müşteri Yönetimi":
    st.header("👥 Bayi Müşteri Yönetimi")
    
    # Bayi müşteri dosyası
    BAYI_MUSTERI_FILE = "bayi_musterileri.json"
    
    # Bayi müşteri verilerini yükle
    def load_bayi_musteriler():
        if os.path.exists(BAYI_MUSTERI_FILE):
            with open(BAYI_MUSTERI_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_bayi_musteriler(data):
        with open(BAYI_MUSTERI_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    bayi_musteriler = load_bayi_musteriler()
    current_user = st.session_state.username
    
    # Kullanıcının müşteri listesi
    if current_user not in bayi_musteriler:
        bayi_musteriler[current_user] = []
    
    st.markdown(f"### 🏢 {current_user} - Müşteri Listesi")
    
    # Yeni müşteri ekleme
    with st.expander("➕ Yeni Müşteri Ekle", expanded=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            yeni_musteri_adi = st.text_input("👤 Müşteri Adı", key="yeni_musteri_adi", placeholder="Örn: ABC İnşaat Ltd.")
        
        with col2:
            yeni_musteri_tel = st.text_input("📞 Telefon", key="yeni_musteri_tel", placeholder="0555 555 55 55")
        
        with col3:
            st.write("")
            st.write("")
            if st.button("✅ EKLE", type="primary"):
                if yeni_musteri_adi.strip():
                    # Müşteri zaten var mı kontrol et
                    musteri_varmi = any(m['adi'] == yeni_musteri_adi.strip() for m in bayi_musteriler[current_user])
                    
                    if musteri_varmi:
                        st.error(f"❌ '{yeni_musteri_adi}' zaten kayıtlı!")
                    else:
                        yeni_musteri = {
                            "adi": yeni_musteri_adi.strip(),
                            "telefon": yeni_musteri_tel.strip() if yeni_musteri_tel.strip() else "-",
                            "kayit_tarihi": datetime.now().strftime('%d.%m.%Y %H:%M'),
                            "toplam_hesaplama": 0
                        }
                        bayi_musteriler[current_user].append(yeni_musteri)
                        save_bayi_musteriler(bayi_musteriler)
                        st.success(f"✅ '{yeni_musteri_adi}' müşterisi eklendi!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Müşteri adı boş olamaz!")
    
    st.markdown("---")
    
    # Müşteri listesi
    if bayi_musteriler[current_user]:
        st.subheader(f"📋 Müşterilerim ({len(bayi_musteriler[current_user])} adet)")
        
        # Arama
        search_musteri = st.text_input("🔍 Müşteri Ara", placeholder="Müşteri adı yazın...", key="musteri_ara")
        
        # Filtreleme
        filtered_musteriler = bayi_musteriler[current_user]
        if search_musteri:
            filtered_musteriler = [m for m in filtered_musteriler if search_musteri.lower() in m['adi'].lower()]
        
        if filtered_musteriler:
            # DataFrame formatında göster
            musteri_df = pd.DataFrame(filtered_musteriler)
            musteri_df = musteri_df[['adi', 'telefon', 'kayit_tarihi', 'toplam_hesaplama']]
            musteri_df.columns = ['Müşteri Adı', 'Telefon', 'Kayıt Tarihi', 'Toplam Hesaplama']
            
            st.dataframe(musteri_df, use_container_width=True, hide_index=True, height=400)
            
            # Müşteri silme
            if st.session_state.username == ADMIN_USERNAME or True:  # Tüm bayiler kendi müşterilerini silebilir
                with st.expander("🗑️ Müşteri Silme İşlemleri"):
                    st.warning("⚠️ Dikkat! Silinen müşteri geri getirilemez.")
                    
                    col_del1, col_del2 = st.columns([3, 1])
                    with col_del1:
                        silinecek_musteri = st.selectbox(
                            "Silinecek Müşteri",
                            [m['adi'] for m in bayi_musteriler[current_user]],
                            key="sil_musteri"
                        )
                    with col_del2:
                        st.write("")
                        st.write("")
                        if st.button("🗑️ SİL", type="secondary"):
                            bayi_musteriler[current_user] = [
                                m for m in bayi_musteriler[current_user] if m['adi'] != silinecek_musteri
                            ]
                            save_bayi_musteriler(bayi_musteriler)
                            st.success(f"✅ '{silinecek_musteri}' silindi!")
                            st.rerun()
        else:
            st.info("🔍 Arama sonucu bulunamadı")
    
    else:
        st.info("📭 Henüz müşteri eklemediniz. Yukarıdan yeni müşteri ekleyebilirsiniz.")
    
    # İstatistikler
    st.markdown("---")
    st.subheader("📊 İstatistikler")
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("👥 Toplam Müşteri", len(bayi_musteriler[current_user]))
    with col_stat2:
        toplam_hesap = sum(m.get('toplam_hesaplama', 0) for m in bayi_musteriler[current_user])
        st.metric("📊 Toplam Hesaplama", toplam_hesap)
    with col_stat3:
        if bayi_musteriler[current_user]:
            ort_hesap = toplam_hesap / len(bayi_musteriler[current_user])
            st.metric("📈 Ortalama Hesaplama", f"{ort_hesap:.1f}")
        else:
            st.metric("📈 Ortalama Hesaplama", "0")

elif page == "�📜 Hesaplama Geçmişi":
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
            f_musteri = st.selectbox("Müşteri (Bayi)", [''] + sorted(df_hist['musteri'].dropna().unique().tolist()))
        with col_f2:
            f_bayi_musteri = st.selectbox("Bayi Müşteri", [''] + sorted(df_hist['bayi_musteri'].dropna().unique().tolist()) if 'bayi_musteri' in df_hist.columns else [''])
        with col_f3:
            f_urun = st.selectbox("Ürün", [''] + sorted(df_hist['urun'].dropna().unique().tolist()))
        
        col_f4, col_f5, col_f6 = st.columns(3)
        with col_f4:
            f_user = st.selectbox("Kullanıcı", [''] + sorted(df_hist['username'].dropna().unique().tolist()))
        with col_f5:
            st.write("")
        with col_f6:
            st.write("")

        if f_musteri:
            df_hist = df_hist[df_hist['musteri'] == f_musteri]
        if f_bayi_musteri and 'bayi_musteri' in df_hist.columns:
            df_hist = df_hist[df_hist['bayi_musteri'] == f_bayi_musteri]
        if f_urun:
            df_hist = df_hist[df_hist['urun'] == f_urun]
        if f_user:
            df_hist = df_hist[df_hist['username'] == f_user]

        st.metric("Kayıt Sayısı", len(df_hist))

        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ CSV Olarak İndir", csv_data, "hesaplama_gecmisi.csv", mime="text/csv")

        st.markdown("---")
        st.markdown("##### 📊 Hesaplama Kayıtları (Satırları silebilirsiniz)")
        
        # Index'i ekle
        df_hist_display = df_hist.reset_index(drop=False)
        df_hist_display = df_hist_display.rename(columns={'index': 'original_index'})
        
        # Düzenlenebilir tablo
        edited_hist = st.data_editor(
            df_hist_display,
            use_container_width=True,
            hide_index=True,
            height=500,
            num_rows="dynamic",
            disabled=[col for col in df_hist_display.columns if col != 'original_index'],  # Tüm kolonlar salt okunur
            column_config={
                "original_index": None,  # Gizle
                "timestamp": st.column_config.DatetimeColumn("Tarih/Saat", format="DD.MM.YYYY HH:mm:ss"),
            },
            key="history_editor"
        )
        
        # Kaydet butonu
        col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
        with col_save2:
            if st.button("💾 SİLİNEN SATIRLARI KALDIR", type="primary", use_container_width=True):
                # Tüm geçmişi oku
                df_all_hist = pd.read_csv(CALC_HISTORY_FILE)
                
                # Silinen satırları tespit et
                original_indices = set(df_hist_display['original_index'].tolist())
                edited_indices = set(edited_hist['original_index'].tolist())
                deleted_indices = original_indices - edited_indices
                
                if deleted_indices:
                    # Silinen satırları çıkar
                    df_all_hist = df_all_hist.drop(index=list(deleted_indices))
                    df_all_hist.to_csv(CALC_HISTORY_FILE, index=False)
                    st.success(f"✅ {len(deleted_indices)} kayıt silindi!")
                    st.balloons()
                    st.rerun()
                else:
                    st.info("ℹ️ Silinecek kayıt bulunamadı.")
        
        st.info("💡 **İpucu:** Satırı silmek için soldaki ❌ butonuna tıklayın, ardından 'Silinen Satırları Kaldır' butonuna basın.")
