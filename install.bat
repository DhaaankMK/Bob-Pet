@echo off
echo ============================================
echo      Bob Desktop Mascot - Instalador
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado! Instale Python 3.10+ e tente novamente.
    pause
    exit /b 1
)

echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo ============================================
echo  Instalacao completa! Execute launcher.py
echo ============================================
pause
