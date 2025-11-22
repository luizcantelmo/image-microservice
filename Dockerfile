FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs temp_processed_images fonts

# Expor porta
EXPOSE 5001

# Comando para iniciar
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
