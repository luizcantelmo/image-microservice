@echo off
REM Script de inicialização para Windows

echo ================================
echo Image Processing Microservice
echo ================================

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Erro: Python não está instalado
    exit /b 1
)

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual
call venv\Scripts\activate.bat

REM Instalar dependências
echo Instalando dependências...
pip install -r requirements.txt

REM Criar diretórios necessários
if not exist "logs" mkdir logs
if not exist "temp_processed_images" mkdir temp_processed_images
if not exist "fonts" mkdir fonts

echo.
echo ================================
echo Configuração Concluída!
echo ================================
echo.
echo Próximos passos:
echo 1. Coloque um arquivo .ttf (ex: arial.ttf) na pasta 'fonts\'
echo 2. Configure variáveis de ambiente em '.env' (veja .env.example)
echo 3. Inicie o servidor:
echo    python -m app.main      (desenvolvimento)
echo    gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app  (produção)
echo.
echo Para testes:
echo    python dev_test.py --full
echo.
pause
