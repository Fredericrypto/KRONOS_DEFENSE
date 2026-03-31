@echo off
title INSTALADOR KRONOS DEFENSE V1.0
echo -------------------------------------------------------
echo   PREPARANDO AMBIENTE PARA KRONOS DEFENSE V1.0
echo -------------------------------------------------------
echo.
echo [1/2] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado! Instale o Python 3.10 ou superior primeiro.
    pause
    exit
)
echo [2/2] Instalando bibliotecas (isso pode demorar alguns minutos)...
pip install -r requirements.txt
echo.
echo -------------------------------------------------------
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo -------------------------------------------------------
pause
