#!/usr/bin/env python
"""
Script wrapper para iniciar a aplicação Flask
Resolve problemas de importação de módulos
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Agora importar e executar
if __name__ == "__main__":
    from app.main import app
    
    # Configurações
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5001"))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    
    print(f"🚀 Iniciando Flask...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print()
    
    app.run(host=host, port=port, debug=debug)
