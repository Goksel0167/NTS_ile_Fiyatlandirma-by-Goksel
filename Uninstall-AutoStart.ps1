# NTS Projesi - Otomatik Başlatma Kaldırma Script

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "NTS Projesi - Otomatik Başlatma Kaldırma"
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

$TaskName = "NTS_Mobil_AutoStart"

# Görevi bul
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "Görev bulundu: $TaskName" -ForegroundColor Yellow
    Write-Host "Durum: $($task.State)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Bu görevi kaldırmak istediğinizden emin misiniz? (E/H)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -eq "E" -or $response -eq "e") {
        # Önce çalışan servisi durdur
        Write-Host ""
        Write-Host "Çalışan servis durdruluyor..." -ForegroundColor Yellow
        & "$PSScriptRoot\Stop-NTSService.ps1"
        
        # Görevi sil
        Write-Host ""
        Write-Host "Windows görevi kaldırılıyor..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        
        Write-Host ""
        Write-Host "✓ Otomatik başlatma kaldırıldı!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Artık bilgisayar başlangıcında NTS uygulaması" -ForegroundColor Cyan
        Write-Host "otomatik olarak başlamayacak." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Manuel başlatmak için: .\start_nts_service.bat" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "İşlem iptal edildi." -ForegroundColor Yellow
    }
} else {
    Write-Host "Otomatik başlatma görevi bulunamadı." -ForegroundColor Yellow
    Write-Host "Görev adı: $TaskName" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Zaten kaldırılmış olabilir." -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================"
pause
