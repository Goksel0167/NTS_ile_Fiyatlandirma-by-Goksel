# NTS Proje - Hızlı Başlangıç Kılavuzu

## 🎯 Projeye Genel Bakış

NTS Mobil, hazır beton ve yapı kimyasalları sektörü için maliyet optimizasyonu yapan bir sistemdir.

### Sistem Bileşenleri

1. **Streamlit Web UI** - Ana yönetim arayüzü
2. **Flask REST API** - Mobil uygulama backend'i
3. **Flutter Mobil App** - iOS/Android uygulaması

## 🚀 Hızlı Başlatma

### Windows

Çift tıklayın: `start.bat`

Bu otomatik olarak:
- Streamlit Web UI'yi başlatır (port 8501)
- REST API sunucusunu başlatır (port 5000)

### Manuel Başlatma

#### 1. Backend Başlatma

**Terminal 1 - Streamlit Web UI:**
```bash
cd "C:\Github Projelerim\NTS_Proje"
.venv\Scripts\streamlit.exe run app.py
```

**Terminal 2 - REST API:**
```bash
cd "C:\Github Projelerim\NTS_Proje"
.venv\Scripts\python.exe api_server.py
```

#### 2. Flutter Mobil App

```bash
cd flutter_app
flutter pub get
flutter run
```

## 📱 Erişim Noktaları

| Servis | URL | Açıklama |
|--------|-----|----------|
| Web UI | http://localhost:8501 | Streamlit arayüzü |
| API | http://localhost:5000 | REST API |
| Health Check | http://localhost:5000/health | API durumu |

## 🔑 Varsayılan Giriş Bilgileri

**Web UI için:**
- Kullanıcı: `goksel`
- Şifre: `NTS2025!`

**Not:** İlk girişte kullanıcı sözleşmesini kabul etmeniz gerekir.

## 📊 API Kullanımı

### Temel Endpoints

```bash
# Tüm ürünleri getir
curl http://localhost:5000/api/products

# Şehirleri listele
curl http://localhost:5000/api/cities

# Nakliye seçenekleri
curl http://localhost:5000/api/shipping?city=ISTANBUL

# Döviz kurları
curl http://localhost:5000/api/rates

# Fiyat hesaplama
curl -X POST http://localhost:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "product": "Sika Viscocrete HT 2541",
    "city": "DIYARBAKIR",
    "profit_margin": 15.0
  }'
```

## 🗂 Proje Yapısı

```
NTS_Proje/
├── app.py                 # Streamlit web uygulaması
├── api_server.py          # Flask REST API
├── requirements.txt       # Python dependencies
├── start.bat             # Windows başlatma scripti
├── *.csv                 # Veri dosyaları
├── *.json                # Konfigürasyon
└── flutter_app/          # Flutter mobil uygulama
    ├── lib/
    │   ├── main.dart
    │   ├── models/       # Veri modelleri
    │   ├── services/     # API servisleri
    │   └── ui/           # Ekranlar
    └── pubspec.yaml
```

## 🛠 Veri Dosyaları

| Dosya | Açıklama |
|-------|----------|
| `urun_fiyat_db.csv` | Ürün fiyat veritabanı |
| `lokasyonlar.csv` | Nakliye bilgileri |
| `exchange_rates.json` | Döviz kurları |
| `users.json` | Kullanıcı veritabanı |
| `hesaplama_gecmisi.csv` | Hesaplama kayıtları |

## 🔧 Sorun Giderme

### Port Zaten Kullanımda

```bash
# Windows'ta port'u kullanan process'i bul
netstat -ano | findstr :8501
netstat -ano | findstr :5000

# Process'i sonlandır
taskkill /PID <PID> /F
```

### Virtual Environment Sorunu

```bash
# Yeniden oluştur
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Flutter Paket Sorunları

```bash
cd flutter_app
flutter clean
flutter pub get
flutter pub upgrade
```

## 📈 Kullanım Senaryoları

### 1. Yeni Ürün Ekleme

1. Web UI'ye giriş yap
2. Sol menüden "Yeni Ürün Ekle" seç
3. Ürün bilgilerini gir
4. Kaydet

### 2. Fiyat Hesaplama

1. "Fiyat Hesaplama" sekmesi
2. Ürün ve şehir seç
3. Kâr marjını ayarla
4. "Fiyat Hesapla" butonuna bas
5. En ucuz rotayı gör

### 3. Mobil Uygulamadan Kullanım

1. Flutter app'i çalıştır
2. Ürün seç
3. Varış noktasını seç
4. Nakliye firması seç
5. Hesapla ve sonuçları gör

## 🎓 İleri Düzey Özellikler

### Toplu Fiyat Güncellemesi

Web UI'de:
- "Ürün Fiyat Artışı" sekmesi
- Tüm ürünlere %X artış uygula
- Fabrika bazlı güncelleme

### Lojistik Yönetimi

- Nakliye fiyatlarını düzenle
- Toplu zam uygula
- Yeni nakliye firması ekle

### Hesaplama Geçmişi

- Tüm hesaplamaları görüntüle
- Müşteri/ürün bazlı filtrele
- CSV olarak indir

## 📚 Ek Kaynaklar

- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - Detaylı optimizasyon raporu
- [flutter_app/README.md](flutter_app/README.md) - Flutter app dokümantasyonu
- [README.md](README.md) - Ana proje dokümantasyonu

## 💡 İpuçları

1. **Performans**: İlk yüklemede döviz kurları internetten çekilir, sonraki kullanımlarda cache kullanılır
2. **Veri Güvenliği**: Düzenli olarak CSV dosyalarını yedekleyin
3. **Güncellemeler**: requirements.txt'i güncel tutun
4. **Mobil Test**: Flutter app'i gerçek cihazda test edin

## 🐛 Hata Bildirimi

Sorun yaşarsanız:
1. Terminal çıktılarını kontrol edin
2. Log dosyalarını inceleyin
3. Geliştirici ile iletişime geçin

## ✨ Katkıda Bulunma

Bu proje aktif geliştirme aşamasındadır. Önerilerinizi geliştirici ile paylaşabilirsiniz.

---

**Son Güncelleme:** 16 Ocak 2026  
**Versiyon:** 8.0  
**Geliştirici:** Göksel Çapkın
