@echo off
rem Khoi dong TradeFlow tren Windows. Viet khong dau de tranh loi font trong cua so lenh.
cd /d "%~dp0"
set PY=
py -3 --version >nul 2>nul && set PY=py -3
if not defined PY python --version >nul 2>nul && set PY=python
if not defined PY (
  echo Chua tim thay Python. Hay cai Python 3.10 tro len tai https://www.python.org/downloads/
  echo Khi cai, nho tick vao o "Add python.exe to PATH". Sau do chay lai file nay.
  pause
  exit /b 1
)
if not exist .venv (
  echo Dang chuan bi moi truong cho TradeFlow - chi lam o lan dau...
  %PY% -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt
python run.py
pause
