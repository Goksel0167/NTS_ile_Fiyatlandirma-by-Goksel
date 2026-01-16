@echo off
echo ====================================
echo NTS Proje - Baslat
echo ====================================
echo.
echo [1/2] Streamlit Web UI Baslatiliyor...
start cmd /k "cd /d %~dp0 && .venv\Scripts\streamlit.exe run app.py"
timeout /t 2 >nul

echo [2/2] REST API Sunucusu Baslatiliyor...
start cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe api_server.py"
timeout /t 2 >nul

echo.
echo ====================================
echo BASARILI!
echo ====================================
echo.
echo Streamlit Web UI: http://localhost:8501
echo REST API Server: http://localhost:5000
echo.
echo Kapamak icin CTRL+C basin (her iki terminalde)
echo.
pause
