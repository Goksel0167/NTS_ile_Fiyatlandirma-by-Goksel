@echo off
REM NTS Projesi - 7/24 Otomatik Başlatma Script
echo ========================================
echo NTS Mobil - Fiyat Hesaplama Sistemi
echo Otomatik Baslama Modu
echo ========================================
echo.

REM Proje dizinine git
cd /d "c:\Github Projelerim\NTS_Proje"

REM Log klasörü oluştur
if not exist "logs" mkdir logs

REM Tarih ve saat bilgisi
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%

echo [%date% %time%] NTS Uygulamasi baslatiiliyor... >> logs\startup.log

REM Virtual environment'i aktif et ve Streamlit'i başlat
echo Virtual environment aktif ediliyor...
call .venv\Scripts\activate.bat

echo Streamlit uygulamasi baslatiliyor...
echo Tarayicinizda http://localhost:8501 adresini acin
echo.
echo Uygulamayi durdurmak icin bu pencereyi kapatabilirsiniz.
echo.

REM Streamlit'i başlat (port 8501)
start "NTS-Streamlit" /B .venv\Scripts\python.exe -m streamlit run app.py --server.port=8501 --server.headless=true >> logs\streamlit_%timestamp%.log 2>&1

REM Flask API'yi başlat (port 5000) - opsiyonel
REM start "NTS-API" /B .venv\Scripts\python.exe api_server.py >> logs\api_%timestamp%.log 2>&1

echo.
echo ========================================
echo Uygulama basariyla baslatildi!
echo Web: http://localhost:8501
echo ========================================
echo.
echo Bu pencereyi acik tutun veya minimize edin.
echo Kapattiginizda uygulama duracaktir.
echo.

REM Pencereyi açık tut
pause
