@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Sanal ortam bulunamadi. Once README kurulum adimlarini uygulayin.
  pause
  exit /b 1
)
call venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
