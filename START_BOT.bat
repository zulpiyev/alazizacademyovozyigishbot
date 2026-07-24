@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo   AL-AZIZ VOTING BOT - SQLITE
ECHO ==========================================

set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py"
if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
    echo [XATO] Python topilmadi.
    echo Python 3.11 yoki undan yangi versiyani o'rnating va "Add Python to PATH" ni belgilang.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Virtual muhit yaratilmoqda...
    if "%PY_CMD%"=="py" (
        py -3.11 -m venv .venv 2>nul
        if errorlevel 1 py -m venv .venv
    ) else (
        python -m venv .venv
    )
    if errorlevel 1 (
        echo [XATO] Virtual muhit yaratilmadi.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

if not exist ".venv\.requirements_installed" (
    echo [2/3] Kerakli kutubxonalar o'rnatilmoqda...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [XATO] Kutubxonalarni o'rnatishda xato yuz berdi.
        pause
        exit /b 1
    )
    type nul > ".venv\.requirements_installed"
)

if not exist ".env" (
    echo [3/3] .env fayli yaratilmoqda...
    copy /Y ".env.example" ".env" >nul
    echo.
    echo Notepad ochiladi. BOT_TOKEN, ADMIN_IDS va 2 ta kanal ma'lumotini kiriting.
    echo Saqlang va Notepadni yoping - bot avtomatik ishga tushadi.
    start /wait notepad ".env"
)

echo.
echo Bot ishga tushmoqda...
echo SQLite baza avtomatik: data\alaziz_voting.db
echo To'xtatish uchun CTRL+C bosing.
echo.
python bot.py

if errorlevel 1 (
    echo.
    echo [XATO] Bot to'xtadi. Yuqoridagi xatoni tekshiring.
    pause
)
