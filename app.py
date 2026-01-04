import streamlit as st
import pandas as pd
from datetime import datetime
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

# --- DÖVİZ KURU FONKSİYONLARI ---

def get_tcmb_rates():
    """TCMB'den güncel döviz satış kurlarını çek"""
    try:
        today = datetime.now().strftime('%d%m%Y')
        url = f"https://www.tcmb.gov.tr/kurlar/{today[:4]}{today[2:4]}/{today}.xml"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            rates = {}
            
            for currency in root.findall('Currency'):
                code = currency.get('CurrencyCode')
                if code in ['USD', 'EUR', 'CHF']:
                    forex_selling = currency.find('ForexSelling')
                    if forex_selling is not None and forex_selling.text:
                        rates[code] = float(forex_selling.text)
            
            if rates:
                rates['TL'] = 1.0
                rates['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_exchange_rates(rates)
                return rates
    except:
        pass
    
    # Hata durumunda kayıtlı kurları kullan
    return load_exchange_rates()

def save_exchange_rates(rates):
    """Döviz kurlarını kaydet"""
    with open(EXCHANGE_RATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

def load_exchange_rates():
    """Kayıtlı döviz kurlarını yükle"""
    if os.path.exists(EXCHANGE_RATES_FILE):
        with open(EXCHANGE_RATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Varsayılan kurlar
    return {'TL': 1.0, 'USD': 36.50, 'EUR': 38.20, 'CHF': 41.10, 'date': 'Varsayılan'}

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
    except:
        return pd.DataFrame(columns=['Urun_Adi', 'Fabrika', 'NTS_Maliyet_TL', 'Kayit_Tarihi'])

def load_shipping():
    try:
        return pd.read_csv(SHIPPING_FILE)
    except:
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
    results = []
    urun_fabrikalari = df_products[df_products['Urun_Adi'] == urun_adi]['Fabrika'].unique()
    
    usd_rate = exchange_rates.get('USD', 36.50)
    
    for fabrika in urun_fabrikalari:
        nts_tl = get_latest_product_price(df_products, urun_adi, fabrika)
        if nts_tl is None:
            continue
        
        nakliye_options = df_shipping[(df_shipping['Sehir'] == sehir) & (df_shipping['Fabrika'] == fabrika)]
        
        for _, nakliye in nakliye_options.iterrows():
            nakliye_tl = nakliye['Fiyat_TL_KG']
            toplam_maliyet_tl = nts_tl + nakliye_tl
            satis_tl = toplam_maliyet_tl * (1 + kar_marji / 100)
            
            # USD hesaplamaları
            satis_usd_kg = satis_tl / usd_rate
            satis_usd_ton = satis_usd_kg * 1000
            satis_tl_ton = satis_tl * 1000
            
            results.append({
                'Fabrika': fabrika,
                'Firma': nakliye['Firma'],
                'Arac': nakliye['Arac_Tipi'],
                'NTS_TL': nts_tl,
                'Nakliye_TL': nakliye_tl,
                'Toplam_Maliyet_TL': toplam_maliyet_tl,
                'Satis_TL': satis_tl,
                'Satis_USD_KG': satis_usd_kg,
                'Satis_USD_TON': satis_usd_ton,
                'Satis_TL_TON': satis_tl_ton
            })
    
    if not results:
        return None, [], exchange_rates
    
    en_ucuz = min(results, key=lambda x: x['Satis_TL'])
    return en_ucuz, results, exchange_rates

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

# --- GİRİŞ SAYFASI ---
if not st.session_state.logged_in:
    st.title("🔐 NTS Mobil - Giriş")
    
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
                users['admin'] = {
                    'password': hash_password('admin123'),
                    'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'created_by': 'system',
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

with st.sidebar:
    st.title("📊 NTS Mobil v6.5")
    st.caption(f"👤 Kullanıcı: **{st.session_state.username}**")
    page = st.radio("🔀 Menü", ["Fiyat Hesaplama", "Yeni Ürün Ekle", "Lojistik Yönetimi"])
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
    
    # TCMB kurlarını çek
    kurlar = get_tcmb_rates()
    
    # Kur bilgisini göster
    with st.expander("💱 Güncel Döviz Kurları (TCMB Satış)"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("USD", f"{kurlar.get('USD', 0):.4f} ₺")
        col2.metric("EUR", f"{kurlar.get('EUR', 0):.4f} ₺")
        col3.metric("CHF", f"{kurlar.get('CHF', 0):.4f} ₺")
        col4.info(f"📅 {kurlar.get('date', 'Bilinmiyor')}")
    
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("🔧 Seçimler")
        
        urun_listesi = [''] + sorted(df_products['Urun_Adi'].unique().tolist())
        secili_urun = st.selectbox("🔹 Ürün Seçin", urun_listesi, index=0)
        
        if secili_urun:
            sehir_listesi = sorted(df_shipping['Sehir'].unique())
            secili_sehir = st.selectbox("📍 Varış Şehri", sehir_listesi)
            
            secili_doviz = st.selectbox("💵 Döviz", ["TL", "USD", "EUR", "CHF"], index=0)
            
            st.markdown("### 📈 Kâr Marjı")
            if 'kar_marji' not in st.session_state:
                st.session_state.kar_marji = 30
            
            c1, c2, c3 = st.columns([1, 4, 1])
            if c1.button("➖"):
                st.session_state.kar_marji = max(0, st.session_state.kar_marji - 1)
            st.session_state.kar_marji = c2.slider("Marj", 0, 100, st.session_state.kar_marji, label_visibility="collapsed")
            if c3.button("➕"):
                st.session_state.kar_marji = min(100, st.session_state.kar_marji + 1)
            st.caption(f"**Marj: %{st.session_state.kar_marji}**")
            
            st.markdown("---")
            
            if st.button("🚀 FİYAT HESAPLA", type="primary"):
                en_ucuz, tum_secenekler, kullanilan_kurlar = find_cheapest_route(
                    df_products, df_shipping, secili_urun, secili_sehir, st.session_state.kar_marji, kurlar
                )
                
                if en_ucuz:
                    st.session_state['hesaplama_yapildi'] = True
                    st.session_state['en_ucuz'] = en_ucuz
                    st.session_state['tum_secenekler'] = tum_secenekler
                    st.session_state['secili_urun'] = secili_urun
                    st.session_state['secili_sehir'] = secili_sehir
                    st.session_state['secili_doviz'] = secili_doviz
                    st.session_state['kullanilan_kurlar'] = kullanilan_kurlar
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
        
        st.success(f"🏆 **EN UYGUN SEÇENEK**")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fabrika", {"TR14": "GEBZE", "TR15": "TRABZON", "TR16": "ADANA"}[en_ucuz['Fabrika']])
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
        show_price(c2, "USD", "$", kurlar["USD"])
        show_price(c3, "EUR", "€", kurlar["EUR"])
        show_price(c4, "CHF", "₣", kurlar["CHF"])
        
        with st.expander("🔍 Tüm Fabrika & Nakliye Seçenekleri"):
            df_sonuc = pd.DataFrame(tum_secenekler)
            df_sonuc = df_sonuc.sort_values('Satis_TL')
            df_sonuc['Fabrika_Adi'] = df_sonuc['Fabrika'].map({"TR14": "GEBZE", "TR15": "TRABZON", "TR16": "ADANA"})
            
            # Formatlama
            df_sonuc['NTS_TL'] = df_sonuc['NTS_TL'].round(2)
            df_sonuc['Nakliye_TL'] = df_sonuc['Nakliye_TL'].round(2)
            df_sonuc['Toplam_Maliyet_TL'] = df_sonuc['Toplam_Maliyet_TL'].round(2)
            df_sonuc['Satis_USD_KG'] = df_sonuc['Satis_USD_KG'].round(4)
            df_sonuc['Satis_USD_TON'] = df_sonuc['Satis_USD_TON'].round(2)
            df_sonuc['Satis_TL_TON'] = df_sonuc['Satis_TL_TON'].round(2)
            
            # Renklendirme için normalize et (0-1 arası)
            min_val = df_sonuc['Satis_TL'].min()
            max_val = df_sonuc['Satis_TL'].max()
            
            def color_scale(val):
                if max_val == min_val:
                    return 'background-color: #90EE90'
                normalized = (val - min_val) / (max_val - min_val)
                # Yeşilden (#90EE90) kırmızıya (#FFB6C6) gradient
                r = int(144 + (255 - 144) * normalized)
                g = int(238 - (238 - 182) * normalized)
                b = int(144 - (144 - 198) * normalized)
                return f'background-color: rgb({r}, {g}, {b})'
            
            # Gösterilecek kolonlar
            display_df = df_sonuc[['Fabrika_Adi', 'Firma', 'Arac', 'NTS_TL', 'Nakliye_TL', 
                                    'Toplam_Maliyet_TL', 'Satis_USD_KG', 'Satis_USD_TON', 'Satis_TL_TON']]
            
            # Style uygula
            styled_df = display_df.style.applymap(
                color_scale,
                subset=['Toplam_Maliyet_TL', 'Satis_USD_KG', 'Satis_USD_TON', 'Satis_TL_TON']
            ).format({
                'NTS_TL': '{:.2f}',
                'Nakliye_TL': '{:.2f}',
                'Toplam_Maliyet_TL': '{:.2f}',
                'Satis_USD_KG': '${:.4f}',
                'Satis_USD_TON': '${:,.2f}',
                'Satis_TL_TON': '{:,.2f} ₺'
            })
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Hesaplama tarihindeki kur bilgisi
            if 'kullanilan_kurlar' in st.session_state:
                kur_tarihi = st.session_state['kullanilan_kurlar'].get('date', 'Bilinmiyor')
                kur_usd = st.session_state['kullanilan_kurlar'].get('USD', 0)
                st.caption(f"💱 Hesaplama Tarihi: {kur_tarihi} | USD Satış Kuru: {kur_usd:.4f} ₺")

# =========================================================
# SAYFA 2: YENİ ÜRÜN EKLE
# =========================================================
elif page == "Yeni Ürün Ekle":
    st.header("➕ Yeni Ürün / NTS Maliyeti Ekle")
    
    with st.form("yeni_urun_form"):
        st.markdown("Aynı üründen birden çok kayıt ekleyebilirsiniz (fiyat güncellemeleri için).")
        
        col1, col2 = st.columns(2)
        with col1:
            yeni_urun_adi = st.text_input("Ürün Adı")
            yeni_fabrika = st.selectbox("Fabrika", ["TR14", "TR15", "TR16"])
        with col2:
            yeni_nts_maliyet = st.number_input("NTS Maliyet (TL/Kg)", min_value=0.0, step=0.01, format="%.4f")
            yeni_tarih = st.date_input("Kayıt Tarihi", value=datetime.now())
        
        submitted = st.form_submit_button("💾 Kaydet")
        
        if submitted:
            if yeni_urun_adi and yeni_nts_maliyet > 0:
                save_new_product(yeni_urun_adi, yeni_fabrika, yeni_nts_maliyet, yeni_tarih)
                st.success(f"✅ **{yeni_urun_adi}** ({yeni_fabrika}) başarıyla eklendi!")
                st.rerun()
            else:
                st.error("❌ Lütfen tüm alanları doldurun!")
    
    st.markdown("---")
    st.subheader("📂 Mevcut Ürünler")
    st.dataframe(df_products.sort_values('Kayit_Tarihi', ascending=False), use_container_width=True, hide_index=True)

# =========================================================
# SAYFA 3: LOJİSTİK YÖNETİMİ
# =========================================================
elif page == "Lojistik Yönetimi":
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
