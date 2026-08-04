@echo off
title REURB - Instalador de Dependencias
echo ===================================================
echo   INSTALANDO DEPENDENCIAS DO SISTEMA REURB
echo ===================================================
echo.
echo Aguarde... O sistema esta validando as ferramentas necessarias.
echo.
py -m pip install --upgrade pip
py -m pip install streamlit pandas reportlab validate-docbr fpdf2
echo.
echo ===================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo ===================================================
pause