# NTS Projesi - Windows Task Scheduler Kurulum Script
# Bu script Windows başlangıcında otomatik çalışacak bir görev oluşturur

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "NTS Projesi - Otomatik Başlatma Kurulumu"
Write-Host "========================================"
Write-Host ""

# Admin kontrolü
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (!$isAdmin) {
    Write-Host "HATA: Bu script yönetici olarak çalıştırılmalıdır!" -ForegroundColor Red
    Write-Host "Sağ tıklayıp 'Yönetici olarak çalıştır' seçeneğini kullanın." -ForegroundColor Yellow
    pause
    exit 1
}

$ProjectPath = "c:\Github Projelerim\NTS_Proje"
$ScriptPath = "$ProjectPath\Start-NTSService.ps1"
$TaskName = "NTS_Mobil_AutoStart"

Write-Host "Proje dizini: $ProjectPath" -ForegroundColor Cyan
Write-Host "Script: $ScriptPath" -ForegroundColor Cyan
Write-Host ""

# Script varlığını kontrol et
if (!(Test-Path $ScriptPath)) {
    Write-Host "HATA: Start-NTSService.ps1 dosyası bulunamadı!" -ForegroundColor Red
    Write-Host "Yol: $ScriptPath" -ForegroundColor Yellow
    pause
    exit 1
}

# Eski görevi sil (varsa)
Write-Host "Mevcut görev kontrol ediliyor..." -ForegroundColor Yellow
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Eski görev bulundu, siliniyor..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✓ Eski görev silindi" -ForegroundColor Green
}

# Yeni görev oluştur
Write-Host ""
Write-Host "Yeni Windows görevi oluşturuluyor..." -ForegroundColor Yellow

# Eylem: PowerShell script'ini çalıştır
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $ProjectPath

# Tetikleyici: Sistem başlangıcında (2 dakika gecikme ile)
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = "PT2M"  # 2 dakika bekleme

# Ayarlar
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # Sınırsız

# Principal: SYSTEM hesabı ile çalıştır (en yüksek ayrıcalık)
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Görevi kaydet
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "NTS Mobil - Fiyat Hesaplama Sistemi otomatik başlatma servisi. Sistem başlangıcında Streamlit uygulamasını başlatır." `
        -Force | Out-Null
    
    Write-Host ""
    Write-Host "✓ Windows görevi başarıyla oluşturuldu!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Görev Bilgileri:" -ForegroundColor Cyan
    Write-Host "  - Görev Adı: $TaskName"
    Write-Host "  - Tetikleyici: Sistem başlangıcında (2 dakika gecikme)"
    Write-Host "  - Çalışma Hesabı: SYSTEM"
    Write-Host "  - Otomatik Yeniden Başlatma: Evet (3 deneme)"
    Write-Host ""
    
    # Görevi test et
    Write-Host "Görevi şimdi test etmek ister misiniz? (E/H)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "E" -or $response -eq "e") {
        Write-Host ""
        Write-Host "Görev başlatılıyor..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 3
        
        Write-Host "✓ Görev başlatıldı!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Tarayıcınızda http://localhost:8501 adresini açın" -ForegroundColor Cyan
        Write-Host "Log dosyaları: $ProjectPath\logs" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "========================================"
    Write-Host "KURULUM TAMAMLANDI!"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "Artık bilgisayarınız her açıldığında NTS uygulaması" -ForegroundColor Green
    Write-Host "otomatik olarak arka planda başlayacak." -ForegroundColor Green
    Write-Host ""
    Write-Host "Yönetim Komutları:" -ForegroundColor Cyan
    Write-Host "  - Servisi Durdur: .\Stop-NTSService.ps1" -ForegroundColor White
    Write-Host "  - Servisi Başlat: .\Start-NTSService.ps1" -ForegroundColor White
    Write-Host "  - Görev Ayarları: taskschd.msc (Görev Zamanlayıcı)" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "HATA: Görev oluşturulamadı!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}

pause
