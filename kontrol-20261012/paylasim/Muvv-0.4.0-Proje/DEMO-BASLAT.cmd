@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1
set "MUVV_PY=%~dp0.venv\Scripts\python.exe"
if exist "%MUVV_PY%" goto check_python
where py.exe >nul 2>nul
if errorlevel 1 goto python_fallback
py -3 -m venv "%~dp0.venv"
if errorlevel 1 goto failed
goto check_python
:python_fallback
python -m venv "%~dp0.venv"
if errorlevel 1 goto failed
:check_python
"%MUVV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto version_failed
"%MUVV_PY%" -c "import gui,cli,hid,tkinter,customtkinter; from app_version import __version__; raise SystemExit(0 if __version__ == '0.4.0' else 1)" >nul 2>nul
if not errorlevel 1 goto ready
echo Muvv bagimliliklari bu klasordeki .venv ortamina kuruluyor...
"%MUVV_PY%" -m pip install --disable-pip-version-check --require-hashes -r "%~dp0Muvv\requirements-lock.txt"
if errorlevel 1 goto failed
"%MUVV_PY%" -m pip install --disable-pip-version-check --no-deps "%~dp0paketler\muvv-0.4.0-py3-none-any.whl"
if errorlevel 1 goto failed
"%MUVV_PY%" -m pip check
if errorlevel 1 goto failed
:ready
if /I "%~1"=="--check" goto verification
echo Demo aciliyor. Fiziksel fareye veri gonderilmez.
"%MUVV_PY%" -m gui --demo
if errorlevel 1 goto failed
exit /b 0
:verification
"%MUVV_PY%" -m cli --version
if errorlevel 1 goto failed
"%MUVV_PY%" -m pip check
if errorlevel 1 goto failed
exit /b 0
:version_failed
echo Python 3.10 veya daha yeni bir surum gereklidir.
goto failed
:failed
echo Baslatma tamamlanamadi. Yukaridaki hata mesajini kontrol edin.
echo Python 3.10+ ve ilk kurulum icin internet gerekir. Ayrintilar BASLANGIC.md dosyasinda.
if /I not "%~1"=="--check" pause
exit /b 1
