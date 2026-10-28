@echo off
cd /d "%~dp0"
echo ===== OMR 40 V3 - AUTOMATED TESTS =====
py -m pip install -r requirements-dev.txt
if errorlevel 1 (
 echo Cannot install test requirements.
 pause
 exit /b 1
)
py -m pytest -q
pause
