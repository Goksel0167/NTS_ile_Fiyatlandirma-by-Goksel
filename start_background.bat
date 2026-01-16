@echo off
REM NTS Projesi - Arkaplan Servisi (Gizli Mod)
REM Bu script Windows başlangıcında otomatik çalışır

cd /d "c:\Github Projelerim\NTS_Proje"

REM Log klasörü oluştur
if not exist "logs" mkdir logs

REM Tarih damgası
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%

REM Log'a yaz
echo [%date% %time%] NTS Service basladi >> logs\service.log

REM Streamlit'i başlat (konsol penceresi OLMADAN)
start /B "" "c:\Github Projelerim\NTS_Proje\.venv\Scripts\python.exe" -m streamlit run "c:\Github Projelerim\NTS_Proje\app.py" --server.port=8501 --server.headless=true > "c:\Github Projelerim\NTS_Proje\logs\streamlit_%timestamp%.log" 2>&1

exit
