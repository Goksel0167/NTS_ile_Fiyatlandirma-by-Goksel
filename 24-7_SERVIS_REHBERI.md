# NTS Projesi - 7/24 Servis Kurulumu ve Yönetim Rehberi

## 🚀 Otomatik Başlatma Kurulumu

NTS uygulamasını Windows başlangıcında otomatik olarak başlatmak için:

### Adım 1: Otomatik Başlatmayı Kur

1. **PowerShell'i Yönetici Olarak Aç**
   - Windows tuşu + X
   - "Windows PowerShell (Yönetici)" seçeneğini tıklayın

2. **Kurulum Script'ini Çalıştır**
   ```powershell
   cd "c:\Github Projelerim\NTS_Proje"
   .\Install-AutoStart.ps1
   ```

3. **Kurulum Tamamlandı!**
   - Windows Task Scheduler'da "NTS_Mobil_AutoStart" görevi oluşturuldu
   - Bilgisayar her açıldığında uygulama otomatik başlayacak
   - 2 dakika gecikme ile başlar (sistem tam açılması için)

### Adım 2: Test Et

Hemen test etmek için:
```powershell
.\Start-NTSService.ps1
```

Tarayıcıda aç: http://localhost:8501

---

## 🛠️ Servis Yönetimi

### Servisi Durdur
```powershell
.\Stop-NTSService.ps1
```

### Servisi Manuel Başlat
```powershell
.\Start-NTSService.ps1
```

### Otomatik Başlatmayı Kaldır
```powershell
.\Uninstall-AutoStart.ps1
```
(Yönetici olarak çalıştırın)

---

## 📊 Durum Kontrolü

### Servis Çalışıyor mu?

**PowerShell ile:**
```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen
```

**Tarayıcı ile:**
- http://localhost:8501 adresini açın

### Log Dosyalarını İncele

```powershell
cd logs
Get-Content service_*.log -Tail 50
```

---

## 🔧 Ayarlar

### Port Değiştirme

`Start-NTSService.ps1` dosyasında:
```powershell
$port = 8501  # İstediğiniz port numarası
```

### Başlangıç Gecikmesi

`Install-AutoStart.ps1` dosyasında:
```powershell
$trigger.Delay = "PT2M"  # 2 dakika -> "PT5M" = 5 dakika
```

---

## 📁 Dosya Yapısı

```
NTS_Proje/
├── Install-AutoStart.ps1      # Otomatik başlatma KURULUM
├── Uninstall-AutoStart.ps1    # Otomatik başlatma KALDIRMA
├── Start-NTSService.ps1       # Servisi BAŞLAT
├── Stop-NTSService.ps1        # Servisi DURDUR
├── start_nts_service.bat      # Görsel başlatma (pencere ile)
├── start_background.bat       # Gizli başlatma
└── logs/                      # Log dosyaları
    ├── service_*.log
    ├── streamlit_*.log
    └── startup.log
```

---

## 🌐 Erişim

### Yerel (Aynı Bilgisayar)
```
http://localhost:8501
```

### Ağ Üzerinden (Diğer Cihazlar)
```
http://[BILGISAYAR-IP]:8501
```

IP adresinizi öğrenmek için:
```powershell
ipconfig
```
(IPv4 Address satırına bakın)

### Güvenlik Duvarı Ayarları

Ağ erişimi için Windows Firewall'da port 8501'i açın:

```powershell
New-NetFirewallRule -DisplayName "NTS Mobil - Streamlit" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow
```

---

## 🔄 Otomatik Yeniden Başlatma

Task Scheduler ayarları:
- ✅ Hata durumunda 3 kez yeniden başlatma
- ✅ 1 dakika aralıklarla deneme
- ✅ Pil modunda çalışma
- ✅ Uyku modundan çıkınca devam etme

---

## 📞 Sorun Giderme

### Uygulama Başlamıyor

1. **Log dosyalarını kontrol edin:**
   ```powershell
   cd logs
   Get-Content -Tail 100 service_*.log
   ```

2. **Port kullanımda mı?**
   ```powershell
   Get-NetTCPConnection -LocalPort 8501
   ```

3. **Manuel başlatmayı deneyin:**
   ```powershell
   .\start_nts_service.bat
   ```

### Task Scheduler Görevi Çalışmıyor

1. **Görev Zamanlayıcı'yı açın:**
   - Windows + R
   - `taskschd.msc` yazın
   - "NTS_Mobil_AutoStart" görevini bulun

2. **Görev geçmişini kontrol edin:**
   - Göreve sağ tıklayın
   - "Geçmiş" sekmesi

3. **Görevi manuel çalıştırın:**
   - Göreve sağ tıklayın
   - "Çalıştır"

---

## 💡 İpuçları

1. **İlk kurulumdan sonra bilgisayarı yeniden başlatın**
   - Otomatik başlatmanın çalıştığını görmek için

2. **Log dosyalarını düzenli kontrol edin**
   - Disk doluluk problemlerini önlemek için

3. **Güncelleme sonrası servisi yeniden başlatın**
   - Kod değişikliklerinin yansıması için

4. **Yedekleme yapın**
   - Önemli dosyalar: users.json, *.csv, *.json

---

## 📧 Destek

Sorun yaşarsanız:
1. `logs/` klasöründeki log dosyalarını kontrol edin
2. Task Scheduler geçmişine bakın
3. Manuel başlatmayı deneyin

---

**Son Güncelleme:** 17 Ocak 2026
**Versiyon:** 7.5
