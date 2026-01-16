@echo off
title NTS Mobil - 7/24 Kurulum
color 0A
cls

echo ========================================
echo    NTS MOBIL - 7/24 SERViS KURULUMU
echo ========================================
echo.
echo Bu kurulum ile NTS uygulamasi:
echo   - Windows baslangicinda otomatik acilir
echo   - Arka planda surekli calisir  
echo   - 7/24 erisime hazir olur
echo.
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

echo [1/3] Admin yetkisi onaylandi...
echo.

REM PowerShell kurulum scriptini calistir
echo [2/3] Otomatik baslat gorevi olusturuluyor...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0Install-AutoStart.ps1"

if %errorLevel% equ 0 (
    echo.
    echo [3/3] Kurulum tamamlandi!
    echo.
    echo ========================================
    echo   KURULUM BASARILI!
    echo ========================================
    echo.
    echo Bilgisayariniz her acildiginda NTS uygulamasi
    echo otomatik olarak baslatilacak.
    echo.
    echo Erisim adresi: http://localhost:8501
    echo.
    echo Yonetim:
    echo   - Durdur: Stop-NTSService.ps1
    echo   - Baslat: Start-NTSService.ps1
    echo.
) else (
    echo.
    echo HATA: Kurulum tamamlanamadi!
    echo.
)

pause
