# NTS Projesi - Servis Durdurma Script

$ErrorActionPreference = "Continue"
$ProjectPath = "c:\Github Projelerim\NTS_Proje"
$LogPath = "$ProjectPath\logs"
$pidFile = "$ProjectPath\nts_service.pid"

function Write-Log {
    param($Message)
    $logMessage = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $logMessage
    if (Test-Path $LogPath) {
        Add-Content -Path "$LogPath\service_stop.log" -Value $logMessage
    }
}

Write-Log "========================================"
Write-Log "NTS Servisini Durdurma"
Write-Log "========================================"

# PID dosyasından process ID'yi oku
if (Test-Path $pidFile) {
    $pid = Get-Content $pidFile
    Write-Log "PID dosyasından okunan: $pid"
    
    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
        Write-Log "Process bulundu: $($process.ProcessName) (PID: $pid)"
        Stop-Process -Id $pid -Force
        Write-Log "✓ Process sonlandırıldı"
        Remove-Item $pidFile -Force
        Write-Log "✓ PID dosyası silindi"
    } catch {
        Write-Log "Process bulunamadı (zaten kapanmış olabilir)"
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Log "PID dosyası bulunamadı"
}

# Port 8501'i kullanan tüm process'leri bul ve durdur
Write-Log "Port 8501 kontrol ediliyor..."
$connections = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $connections) {
    $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Log "Port 8501 kullanan process: $($process.ProcessName) (PID: $($process.Id))"
        Stop-Process -Id $process.Id -Force
        Write-Log "✓ Process sonlandırıldı"
    }
}

# Streamlit içeren tüm Python process'lerini bul
Write-Log "Streamlit process'leri aranıyor..."
$allProcesses = Get-Process python* -ErrorAction SilentlyContinue
foreach ($proc in $allProcesses) {
    $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
    if ($cmdLine -like "*streamlit*") {
        Write-Log "Streamlit process bulundu: PID $($proc.Id)"
        Stop-Process -Id $proc.Id -Force
        Write-Log "✓ Process sonlandırıldı"
    }
}

Write-Log "========================================"
Write-Log "Durdurma işlemi tamamlandı"
Write-Log "========================================"
