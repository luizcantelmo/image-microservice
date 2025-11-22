"""
WSGI Entry Point para Produção
Use com Gunicorn: gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
"""
import os
from app.main import app, create_app

# Criar instância da aplicação
create_app()

if __name__ == "__main__":
    app.run()
