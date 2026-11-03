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
echo Checking optional live camera dependencies...
py -m pip install -r requirements-camera.txt
if errorlevel 1 (
 echo WARNING: Auto-scan camera libraries were not installed.
 echo Normal photo upload and manual camera capture will still work.
 echo You can try: py -m pip install -r requirements-camera.txt
)
py -m streamlit run app.py
pause
