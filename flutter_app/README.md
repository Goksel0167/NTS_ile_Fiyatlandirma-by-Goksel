# NTS Mobil Projesi

Bu proje, hazır beton ve yapı kimyasalları sektöründe NTS (Net Fabrika Teslim) maliyet hesaplaması yapan bir sistemdir.

## 🎯 Proje Yapısı

### Backend
- **Streamlit Web UI**: `app.py` - Ana web arayüzü (http://localhost:8501)
- **REST API**: `api_server.py` - Flutter mobil uygulama için API (http://localhost:5000)
- **Veri Dosyaları**: CSV/JSON formatında ürün, nakliye ve kur verileri

### Frontend (Mobil)
- **Flutter App**: `flutter_app/` klasöründe modern mobil uygulama
- API servisleri, model sınıfları ve optimize edilmiş UI

## 🚀 Kurulum ve Çalıştırma

### Python Backend

```bash
# Virtual environment'i aktif et (zaten yapılandırılmış)
# Gerekli paketler yüklü

# Streamlit Web UI'yi başlat
streamlit run app.py

# REST API sunucusunu başlat (ayrı terminal)
python api_server.py
```

### Flutter Mobil Uygulama

```bash
cd flutter_app

# Paketleri yükle
flutter pub get

# Uygulamayı çalıştır
flutter run
```

## ✨ Optimizasyonlar

### Backend Optimizasyonları
1. ✅ Flask REST API eklendi
2. ✅ CORS desteği aktif
3. ✅ Efficient veri yükleme
4. ✅ Caching mekanizması
5. ✅ Error handling iyileştirildi

### Frontend Optimizasyonları
1. ✅ Clean architecture (services, models, screens)
2. ✅ Paralel veri yükleme
3. ✅ Proper state management
4. ✅ Responsive design
5. ✅ Loading states ve error handling
6. ✅ Modal bottom sheets
7. ✅ Optimized widget building

## 📊 API Endpoints

- `GET /api/products` - Tüm ürünleri getir
- `GET /api/cities` - Tüm şehirleri getir
- `GET /api/shipping?city=ISTANBUL` - Şehir için nakliye seçenekleri
- `GET /api/rates` - Güncel döviz kurları
- `POST /api/calculate` - Fiyat hesaplama
- `GET /health` - Health check

## 🔧 Teknolojiler

**Backend:**
- Python 3.13
- Streamlit (Web UI)
- Flask (REST API)
- Pandas (Veri işleme)

**Frontend:**
- Flutter/Dart
- HTTP (API istekleri)
- Material Design 3

## 📱 Özellikler

- 🏭 3 Fabrika (Gebze, Trabzon, Adana)
- 🚚 2 Nakliye Firması (Baykan, Çalışkan)
- 💰 Otomatik en ucuz rota hesaplama
- 💱 4 Döviz desteği (TL, USD, EUR, CHF)
- 📈 Fiyat geçmişi takibi
- 📊 Hesaplama geçmişi
- 🔐 Kullanıcı yönetimi
- 📱 Mobil uyumlu

## 👨‍💻 Geliştirici

Göksel Çapkın

## 📄 Lisans

Telif hakkı korumalıdır. İzinsiz kullanım yasaktır.
