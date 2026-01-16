# NTS Projesi - PowerShell Servis Başlatıcı
# Windows başlangıcında otomatik çalışır ve arkaplanda servisi yönetir

$ErrorActionPreference = "Continue"
$ProjectPath = "c:\Github Projelerim\NTS_Proje"
$LogPath = "$ProjectPath\logs"

# Log klasörü oluştur
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

# Timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$LogPath\service_$timestamp.log"

# Log fonksiyonu
function Write-Log {
    param($Message)
    $logMessage = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "========================================"
Write-Log "NTS Mobil - Otomatik Servis Başlatıcı"
Write-Log "========================================"

# Proje dizinine geç
Set-Location $ProjectPath
Write-Log "Çalışma dizini: $ProjectPath"

# Python virtual environment yolu
$pythonExe = "$ProjectPath\.venv\Scripts\python.exe"

if (!(Test-Path $pythonExe)) {
    Write-Log "HATA: Python virtual environment bulunamadı!"
    Write-Log "Yol: $pythonExe"
    exit 1
}

# Önceki Streamlit process'lerini kontrol et ve temizle
Write-Log "Önceki Streamlit süreçleri kontrol ediliyor..."
$existingProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*" }
if ($existingProcesses) {
    Write-Log "Eski süreçler bulundu, temizleniyor..."
    $existingProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Port kontrolü
$port = 8501
$portInUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Log "UYARI: Port $port kullanımda!"
    $process = Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Log "Port $port kullanan süreç: $($process.ProcessName) (PID: $($process.Id))"
        Write-Log "Süreç sonlandırılıyor..."
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Streamlit'i başlat
Write-Log "Streamlit uygulaması başlatılıyor..."
Write-Log "Port: $port"
Write-Log "URL: http://localhost:$port"

try {
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $pythonExe
    $processInfo.Arguments = "-m streamlit run app.py --server.port=$port --server.headless=true"
    $processInfo.WorkingDirectory = $ProjectPath
    $processInfo.UseShellExecute = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    
    # Output ve error handling
    $stdOutBuilder = New-Object System.Text.StringBuilder
    $stdErrBuilder = New-Object System.Text.StringBuilder
    
    $stdOutEvent = Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action {
        if ($EventArgs.Data) {
            [System.IO.File]::AppendAllText($Event.MessageData, "$($EventArgs.Data)`n")
        }
    } -MessageData "$LogPath\streamlit_output_$timestamp.log"
    
    $stdErrEvent = Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action {
        if ($EventArgs.Data) {
            [System.IO.File]::AppendAllText($Event.MessageData, "$($EventArgs.Data)`n")
        }
    } -MessageData "$LogPath\streamlit_error_$timestamp.log"
    
    $process.Start() | Out-Null
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()
    
    Write-Log "Streamlit başlatıldı! (PID: $($process.Id))"
    Write-Log "Process ID dosyaya kaydediliyor..."
    
    # PID'yi dosyaya kaydet
    $process.Id | Out-File "$ProjectPath\nts_service.pid" -Force
    
    # Başlangıç kontrolü (5 saniye bekle)
    Write-Log "Başlangıç kontrolü yapılıyor..."
    Start-Sleep -Seconds 5
    
    if (!$process.HasExited) {
        Write-Log "Servis basariyla calisiyor!"
        Write-Log "Web arayuzu: http://localhost:$port"
        $localIP = ([System.Net.Dns]::GetHostAddresses($env:COMPUTERNAME) | Where-Object { $_.AddressFamily -eq 'InterNetwork' })[0].IPAddressToString
        Write-Log "Network arayuzu: http://${localIP}:$port"
    } else {
        Write-Log "HATA: Servis baslatilamadi!"
        Write-Log "Cikis kodu: $($process.ExitCode)"
    }
    
} catch {
    Write-Log "HATA: $($_.Exception.Message)"
    Write-Log $_.ScriptStackTrace
    exit 1
}

Write-Log "========================================"
Write-Log "Servis baslatma islemi tamamlandi"
Write-Log "========================================"
