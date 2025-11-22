#!/bin/bash
# Script de inicialização da aplicação

set -e

echo "================================"
echo "Image Processing Microservice"
echo "================================"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não está instalado"
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Criar diretórios necessários
mkdir -p logs
mkdir -p temp_processed_images
mkdir -p fonts

echo ""
echo "================================"
echo "Configuração Concluída!"
echo "================================"
echo ""
echo "Próximos passos:"
echo "1. Coloque um arquivo .ttf (ex: arial.ttf) na pasta 'fonts/'"
echo "2. Configure variáveis de ambiente em '.env' (veja .env.example)"
echo "3. Inicie o servidor:"
echo "   python -m app.main      (desenvolvimento)"
echo "   gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app  (produção)"
echo ""
echo "Para testes:"
echo "   python dev_test.py --full"
echo ""
