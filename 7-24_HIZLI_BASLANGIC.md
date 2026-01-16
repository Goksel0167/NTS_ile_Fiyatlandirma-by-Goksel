# 🚀 NTS Mobil - 7/24 Otomatik Servis

## ⚡ Hızlı Kurulum (3 Adım)

### 1️⃣ Kurulum Dosyasına Sağ Tıklayın
📁 `KURULUM_7-24.bat`

### 2️⃣ "Yönetici Olarak Çalıştır" Seçin
🔐 Admin yetkisi gerekli

### 3️⃣ Tamamlandı! 
✅ Bilgisayar her açıldığında NTS otomatik başlayacak

---

## 🌐 Erişim

**Tarayıcıdan:**
```
http://localhost:8501
```

**Ağdan (diğer cihazlar):**
```
http://[BILGISAYAR-IP]:8501
```

---

## 🎮 Yönetim Komutları

### Servisi Başlat
```
Start-NTSService.ps1
```

### Servisi Durdur
```
Stop-NTSService.ps1
```

### Otomatik Başlatmayı Kaldır
```
KURULUM_KALDIR.bat (YÖNETİCİ)
```

---

## 📊 Durum Kontrol

### Çalışıyor mu?
```powershell
Get-NetTCPConnection -LocalPort 8501
```

### Logları Görüntüle
```
logs\service_*.log
```

---

## 🔥 Özellikler

✅ Windows başlangıcında otomatik açılma  
✅ Hata durumunda otomatik yeniden başlatma  
✅ Arka planda sessiz çalışma  
✅ Pil modunda bile çalışma  
✅ Ağ üzerinden erişim  
✅ Detaylı log kayıtları  

---

## 📞 Sorun mu var?

1. **Başlamıyor?**
   - `logs/` klasöründeki logları kontrol edin
   - `start_nts_service.bat` ile manuel başlatın

2. **Port kullanımda?**
   - `Stop-NTSService.ps1` çalıştırın
   - Tekrar başlatın

3. **Görev çalışmıyor?**
   - Windows + R → `taskschd.msc`
   - "NTS_Mobil_AutoStart" görevini kontrol edin

---

## 📁 Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `KURULUM_7-24.bat` | ⚡ TEK TIKLA KURULUM |
| `Install-AutoStart.ps1` | Otomatik başlatma kur |
| `Uninstall-AutoStart.ps1` | Otomatik başlatma kaldır |
| `Start-NTSService.ps1` | Servisi başlat |
| `Stop-NTSService.ps1` | Servisi durdur |
| `start_nts_service.bat` | Manuel başlatma (pencere ile) |
| `24-7_SERVIS_REHBERI.md` | 📖 Detaylı rehber |

---

## 🔒 Güvenlik

Ağ erişimi için firewall'da port açın:
```powershell
New-NetFirewallRule -DisplayName "NTS Mobil" -Direction Inbound -LocalPort 8501 -Protocol TCP -Action Allow
```

---

## 💡 İpucu

Kurulumdan sonra bilgisayarı **yeniden başlatın** ve otomatik açılışı test edin!

**Erişim:** http://localhost:8501

---

**NTS Mobil v7.5** | 7/24 Aktif | Windows Otomatik Servis
