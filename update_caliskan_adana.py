import pandas as pd

# Yeni Çalışkan Adana fiyatları
yeni_fiyatlar = {
    'ADANA': 0.84, 'ADIYAMAN': 1.55, 'AFYON': 2.52, 'AGRI': 4.00, 'AKSARAY': 1.34,
    'ALANYA': 1.77, 'AMASYA': 2.79, 'ANKARA': 2.52, 'ANTALYA': 2.90, 'ARDAHAN': 3.96,
    'ARTVIN': 3.76, 'AYDIN': 3.44, 'BALIKESİR': 3.53, 'BARTIN': 3.01, 'BATMAN': 2.64,
    'BAYBURT': 3.40, 'BİLECİK': 2.82, 'BİNGÖL': 2.77, 'BİNGÖL- SOLHAN': 2.81, 'BİTLİS': 3.12,
    'BOLU': 2.80, 'BURDUR': 2.50, 'BURSA': 3.23, 'ÇANAKKALE': 4.41, 'ÇANKIRI': 2.50,
    'ÇORUM': 2.50, 'DENİZLİ': 2.90, 'DİYARBAKIR': 2.28, 'DÜZCE': 3.04, 'EDİRNE': 4.78,
    'ELAZIĞ': 2.17, 'ERZİNCAN': 3.13, 'ERZURUM': 3.44, 'ESKİŞEHİR': 2.69, 'GAZİANTEP': 1.08,
    'GİRESUN': 3.66, 'GÜMÜŞHANE': 3.31, 'HAKKARİ': 3.97, 'HATAY': 0.96, 'IĞDIR': 3.74,
    'ISPARTA': 2.56, 'İSTANBUL ANADOLU': 3.65, 'İSTANBUL AVRUPA': 4.19, 'İZMİR': 3.49,
    'KAHRAMANMARAŞ': 1.19, 'KARABÜK': 2.99, 'KARAMAN': 1.55, 'KARS': 3.89, 'KASTAMONU': 2.90,
    'KAYSERİ': 1.55, 'KAYSERİ- YAHYALI MADEN': 1.34, 'KIRIKKALE': 2.41, 'KIRŞEHİR': 1.70,
    'KİLİS': 1.34, 'KOCAELI': 3.24, 'KONYA': 1.55, 'KÜTAHYA': 2.72, 'MALATYA': 1.74,
    'MANİSA': 3.44, 'MARDİN': 2.52, 'MERSİN': 0.84, 'MERSİN DOĞANÇAY BARAJI': 0.84,
    'MERSİN ERDEMLI TÜNEL PROJESİ': 0.84, 'MERSİN GÜLNAR AKKUYU ŞANTİYESİ': 0.88,
    'MERSİN SİLİFKE': 0.84, 'MUĞLA': 3.64, 'MUŞ': 3.11, 'NEVŞEHİR': 1.42, 'NİĞDE': 1.08,
    'ORDU': 3.54, 'OSMANİYE': 0.73, 'RİZE': 3.85, 'SAKARYA': 3.32, 'SAMSUN': 3.04,
    'SİİRT': 3.12, 'SİNOP': 3.42, 'SİVAS': 2.41, 'SİVAS- DİVRİĞİ ÇİFTÇAY MADEN': 2.44,
    'ŞANLIURFA': 1.55, 'ŞIRNAK': 3.24, 'TEKİRDAĞ': 3.73, 'TOKAT': 2.70, 'TRABZON': 3.57,
    'TUNCELİ': 2.68, 'UŞAK': 2.77, 'VAN': 3.74, 'YALOVA': 3.87, 'YOZGAT': 2.41,
    'YOZGAT YERKÖY MADEN': 2.17, 'ZONGULDAK': 3.13
}

# CSV'yi oku
df = pd.read_csv('lokasyonlar.csv')

# Çalışkan + TR16 satırlarını güncelle
for sehir, fiyat in yeni_fiyatlar.items():
    mask = (df['Firma'] == 'CALISKAN') & (df['Fabrika'] == 'TR16') & (df['Sehir'] == sehir)
    if mask.any():
        df.loc[mask, 'Fiyat_TL_KG'] = fiyat
        print(f"✓ {sehir}: {fiyat} TL güncellendi")
    else:
        # Yoksa ekle
        new_row = pd.DataFrame([{
            'Sehir': sehir,
            'Firma': 'CALISKAN',
            'Fabrika': 'TR16',
            'Arac_Tipi': 'TIR',
            'Fiyat_TL_KG': fiyat
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"+ {sehir}: {fiyat} TL eklendi")

# Kaydet
df.to_csv('lokasyonlar.csv', index=False)
print("\n✅ Çalışkan Adana fiyatları güncellendi!")
