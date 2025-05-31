@echo off
REM Script para executar o Sistema AURALIS no Windows

echo ======================================
echo   AURALIS - Sistema Inteligente
echo ======================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale Python 3.8 ou superior
    pause
    exit /b 1
)

REM Verificar/criar ambiente virtual
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Verificar/instalar dependencias
echo Verificando dependencias...
python -m pip install --quiet --upgrade pip

if not exist ".deps_installed" (
    echo Instalando dependencias...
    pip install -r requirements.txt
    echo. > .deps_installed
) else (
    echo Dependencias ja instaladas
)

REM Criar diretorios necessarios
echo Criando diretorios...
if not exist "logs" mkdir logs
if not exist "recordings" mkdir recordings
if not exist "auralis_memoria" mkdir auralis_memoria
if not exist "update_conhecimento" mkdir update_conhecimento
if not exist "update_historico" mkdir update_historico

REM Verificar arquivo .env
if not exist ".env" (
    echo.
    echo AVISO: Arquivo .env nao encontrado!
    echo Por favor, configure as credenciais em .env
    pause
    exit /b 1
)

REM Executar aplicacao
echo.
echo Iniciando AURALIS...
echo.
python main.py

REM Pausar ao final
pause