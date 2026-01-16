@echo off
title NTS Mobil - Otomatik Baslatmayi Kaldir
color 0C
cls

echo ========================================
echo   NTS MOBIL - OTOMATIK BASLATMA KALDIR
echo ========================================
echo.

REM Admin kontrolu
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo HATA: Bu script yonetici olarak calistirilmalidir!
    echo.
    echo Sag tiklayip "Yonetici olarak calistir" secin.
    echo.
    pause
    exit /b 1
)

echo Admin yetkisi onaylandi...
echo.
echo UYARI: Bu islem NTS uygulamasinin otomatik baslatilmasini
echo        bilgisayar acilisinda devre disi birakacak.
echo.
echo Devam etmek istiyor musunuz? (E/H)
set /p onay=

if /i "%onay%" neq "E" (
    echo.
    echo Islem iptal edildi.
    pause
    exit /b 0
)

echo.
echo Otomatik baslatma kaldirilIyor...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0Uninstall-AutoStart.ps1"

echo.
echo ========================================
echo   ISLEM TAMAMLANDI
echo ========================================
echo.
echo Artik bilgisayar acilisinda NTS uygulamasi
echo otomatik olarak baslamayacak.
echo.
echo Manuel baslatmak icin: start_nts_service.bat
echo.

pause
