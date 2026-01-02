import streamlit as st
import pandas as pd
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="NTS Mobil - Yönetim Paneli", page_icon="🚛", layout="wide")

# --- CSS: BUTONLARI GÜZELLEŞTİRME ---
st.markdown("""
<style>
div.stButton > button:first-child {
    border-radius: 8px;
    font-weight: bold;
    height: 45px;
}
</style>
""", unsafe_allow_html=True)

# --- DOSYA İSİMLERİ ---
PRODUCT_FILE = 'urunler.csv'
SHIPPING_FILE = 'nakliye_db.csv' # Artık tüm nakliye verisi burada

# --- VARSAYILAN VERİLER (İLK KURULUM İÇİN) ---
DEFAULT_PRODUCTS = [
    {"Ürün Adı": "Sika Viscocrete HT 2541", "Fabrika": "TR16"},
    {"Ürün Adı": "Sikaviscocrete PC-15 TR dökme KG", "Fabrika": "TR16"},
    {"Ürün Adı": "Sika Viscocrete PC 61 Dökme", "Fabrika": "TR16"},
    {"Ürün Adı": "Sika Paver HC-1", "Fabrika": "TR14"},
    {"Ürün Adı": "Sika Viscocrete GL 3113", "Fabrika": "TR15"}
]

# BAZ NAKLİYE VERİSİ (İLK ÇALIŞMADA CSV'YE DÖNÜŞECEK)
BAZ_NAKLIYE_DICT = {
    "ADANA": [{"Fabrika": "TR16", "Firma": "BAYKAN", "Araç": "TIR", "Fiyat": 0.89}, {"Fabrika": "TR16", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 0.84}],
    "DIYARBAKIR": [{"Fabrika": "TR16", "Firma": "BAYKAN", "Araç": "TIR", "Fiyat": 2.69}, {"Fabrika": "TR16", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 2.27}, {"Fabrika": "TR14", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 2.27}, {"Fabrika": "TR15", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 2.75}],
    "BATMAN": [{"Fabrika": "TR16", "Firma": "BAYKAN", "Araç": "TIR", "Fiyat": 2.50}, {"Fabrika": "TR16", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 2.64}],
    "TRABZON": [{"Fabrika": "TR15", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 0.50}, {"Fabrika": "TR14", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 3.95}, {"Fabrika": "TR16", "Firma": "BAYKAN", "Araç": "TIR", "Fiyat": 3.99}],
    "ISTANBUL": [{"Fabrika": "TR14", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 0.99}, {"Fabrika": "TR16", "Firma": "BAYKAN", "Araç": "TIR", "Fiyat": 3.32}],
    "ANTALYA": [{"Fabrika": "TR16", "Firma": "BAYKAN", "Araç": "TIR", "Fiyat": 3.03}, {"Fabrika": "TR14", "Firma": "ÇALIŞKAN", "Araç": "TIR", "Fiyat": 2.88}]
}

# --- FONKSİYONLAR ---

def init_shipping_db():
    """İlk çalışmada hardcoded veriyi CSV'ye çevirir."""
    if not os.path.exists(SHIPPING_FILE):
        data_list = []
        for sehir, rotalar in BAZ_NAKLIYE_DICT.items():
            for rota in rotalar:
                data_list.append({
                    "Varis_Yeri": sehir,
                    "Cikis_Fabrikasi": rota["Fabrika"],
                    "Firma": rota["Firma"],
                    "Arac": rota["Araç"],
                    "Fiyat": rota["Fiyat"]
                })
        df = pd.DataFrame(data_list)
        df.to_csv(SHIPPING_FILE, index=False)

def load_shipping_data():
    init_shipping_db() # Dosya yoksa oluştur
    return pd.read_csv(SHIPPING_FILE)

def save_shipping_data(df):
    df.to_csv(SHIPPING_FILE, index=False)

def apply_bulk_raise(percentage):
    """Tüm fiyatlara yüzde oranında zam yapar."""
    df = load_shipping_data()
    # Fiyatı güncelle: Eski Fiyat * (1 + oran/100)
    df['Fiyat'] = df['Fiyat'] * (1 + percentage / 100)
    # Virgülden sonra 2 hane yuvarla
    df['Fiyat'] = df['Fiyat'].round(2)
    save_shipping_data(df)

def load_products():
    if not os.path.exists(PRODUCT_FILE):
        pd.DataFrame(DEFAULT_PRODUCTS).to_csv(PRODUCT_FILE, index=False)
    return pd.read_csv(PRODUCT_FILE)

# --- UYGULAMA BAŞLANGICI ---
init_shipping_db() # Veritabanını kontrol et/oluştur

# --- SOL MENÜ (NAVİGASYON) ---
with st.sidebar:
    st.title("NTS Mobil v5.0")
    page = st.radio("Menü", ["Hesaplama & Analiz", "Lojistik Yönetimi (ZAM)"])
    st.markdown("---")
    
    # --- ORTAK AYARLAR (SOL TARAFTA HEP GÖRÜNSÜN) ---
    if page == "Hesaplama & Analiz":
        df_urunler = load_products()
        urun = st.selectbox("Ürün Seç", df_urunler["Ürün Adı"])
        fabrika_varsayilan = df_urunler[df_urunler["Ürün Adı"] == urun].iloc[0]["Fabrika"]
        
        fabrika = st.selectbox("Fabrika", ["TR16", "TR14", "TR15"], 
                             index=["TR16", "TR14", "TR15"].index(fabrika_varsayilan) if fabrika_varsayilan in ["TR16", "TR14", "TR15"] else 0)
        
        if fabrika == "TR16": st.warning("🟧 ADANA")
        elif fabrika == "TR14": st.success("🟩 GEBZE")
        else: st.info("🟦 TRABZON")
        
        st.markdown("---")
        maliyet = st.number_input("Maliyet (KG)", value=0.0000, step=0.0001, format="%.4f")
        para = st.selectbox("Döviz", ["EUR", "USD", "TL", "CHF"])
        
        st.markdown("### Kâr Marjı")
        if 'marj' not in st.session_state: st.session_state.marj = 15
        c1, c2, c3 = st.columns([1,4,1])
        if c1.button("➖"): st.session_state.marj -= 1
        st.session_state.marj = c2.slider("", 0, 100, st.session_state.marj, label_visibility="collapsed")
        if c3.button("➕"): st.session_state.marj += 1
        st.caption(f"Marj: %{st.session_state.marj}")

# =========================================================
# SAYFA 1: HESAPLAMA VE ANALİZ (ESKİ ANA EKRAN)
# =========================================================
if page == "Hesaplama & Analiz":
    st.header("🏭 Fiyat Hesaplama")
    
    # Veritabanından Şehirleri Çek
    df_ship = load_shipping_data()
    sehirler = sorted(df_ship["Varis_Yeri"].unique())
    
    varis = st.selectbox("Varış Şehri", sehirler)
    
    # Şehir Verisini Filtrele
    sehir_df = df_ship[df_ship["Varis_Yeri"] == varis]
    
    # Analiz Kartları
    cols = st.columns(3)
    kurlar = {"TL": 1.0, "USD": 36.50, "EUR": 38.20, "CHF": 41.10}
    ham_tl = maliyet * kurlar[para] if para != "TL" else maliyet
    
    fabs = [("TR14", "GEBZE", "green", "🟩"), ("TR15", "TRABZON", "blue", "🟦"), ("TR16", "ADANA", "orange", "🟧")]
    
    for i, (kod, ad, renk, icon) in enumerate(fabs):
        f_data = sehir_df[sehir_df["Cikis_Fabrikasi"] == kod]
        with cols[i]:
            if not f_data.empty:
                min_row = f_data.loc[f_data["Fiyat"].idxmin()]
                toplam = ham_tl + min_row["Fiyat"]
                st.markdown(f"**{icon} {ad}**")
                st.caption(f"{min_row['Firma']} ({min_row['Arac']})")
                st.metric("Toplam", f"{toplam:.2f} TL")
            else:
                st.markdown(f"**{icon} {ad}**")
                st.caption("Sevkiyat Yok")
                
    st.markdown("---")
    
    # Nakliye Seçimi
    f_data_secili = sehir_df[sehir_df["Cikis_Fabrikasi"] == fabrika]
    
    nakliye_fiyat = 0.0
    if not f_data_secili.empty:
        st.subheader(f"🚛 {fabrika} -> {varis} Nakliye Seçimi")
        min_f = f_data_secili["Fiyat"].min()
        
        # Seçenekleri hazırla
        secenekler = f_data_secili.to_dict('records')
        secim = st.radio("Firma", range(len(secenekler)), 
                         format_func=lambda i: f"{secenekler[i]['Firma']} | {secenekler[i]['Arac']} | {secenekler[i]['Fiyat']} TL {'⭐' if secenekler[i]['Fiyat']==min_f else ''}")
        nakliye_fiyat = secenekler[secim]['Fiyat']
    else:
        st.warning("Bu rota için kayıtlı fiyat yok. Manuel giriniz.")
        nakliye_fiyat = st.number_input("Manuel Nakliye (TL)", step=0.1)

    # Sonuç
    if nakliye_fiyat > 0 or ham_tl > 0:
        satis_tl = (ham_tl + nakliye_fiyat) * (1 + st.session_state.marj / 100)
        st.success(f"💰 {urun} Satış Fiyatı")
        c1, c2, c3, c4 = st.columns(4)
        def show(c, t, s, k):
            v = satis_tl / k
            c.metric(t, f"{v:.4f} {s}", f"{(v*1000):,.0f}/Ton")
        show(c1, "TL", "₺", 1.0)
        show(c2, "USD", "$", kurlar["USD"])
        show(c3, "EUR", "€", kurlar["EUR"])
        show(c4, "CHF", "₣", kurlar["CHF"])

# =========================================================
# SAYFA 2: LOJİSTİK YÖNETİMİ (YENİ ÖZELLİK)
# =========================================================
elif page == "Lojistik Yönetimi (ZAM)":
    st.header("⚙️ Lojistik Veritabanı Yönetimi")
    st.info("Buradan nakliye fiyatlarına toplu zam yapabilir veya tek tek düzenleyebilirsiniz.")
    
    # --- BÖLÜM 1: TOPLU ZAM ---
    with st.container():
        st.subheader("📈 Toplu Zam Uygula")
        col_zam1, col_zam2 = st.columns([1, 2])
        
        with col_zam1:
            zam_orani = st.number_input("Zam Oranı (%)", value=0.0, step=1.0, help="Örn: 10 yazarsanız %10 zam gelir.")
        
        with col_zam2:
            st.write("") # Boşluk
            st.write("") 
            if st.button("🚀 Tüm Fiyatlara Uygula", type="primary"):
                if zam_orani != 0:
                    apply_bulk_raise(zam_orani)
                    st.success(f"Tüm fiyatlara %{zam_orani} zam yapıldı!")
                    st.rerun()
                else:
                    st.warning("Lütfen 0'dan farklı bir oran girin.")
    
    st.markdown("---")
    
    # --- BÖLÜM 2: EXCEL GİBİ DÜZENLEME ---
    st.subheader("📝 Fiyat Listesi (Düzenle)")
    
    df_current = load_shipping_data()
    
    # Streamlit Data Editor: Excel gibi çalışır
    edited_df = st.data_editor(
        df_current, 
        num_rows="dynamic", # Satır eklemeye izin ver
        use_container_width=True,
        column_config={
            "Fiyat": st.column_config.NumberColumn(
                "Birim Fiyat (TL/Kg)",
                format="%.2f TL"
            ),
            "Varis_Yeri": "Varış Şehri",
            "Cikis_Fabrikasi": "Fabrika",
        }
    )
    
    # Kaydet Butonu
    if st.button("💾 Değişiklikleri Kaydet"):
        save_shipping_data(edited_df)
        st.success("Veritabanı güncellendi!")
        st.rerun()