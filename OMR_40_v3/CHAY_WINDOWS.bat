@echo off
cd /d "%~dp0"
echo ===== OMR 40 V3 - START =====
py -m pip install -r requirements.txt
if errorlevel 1 (
 echo Python launcher not available or dependency installation failed.
 echo Try: python -m pip install -r requirements.txt
 pause
 exit /b 1
)
py -m streamlit run app.py
pause
