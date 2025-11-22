# Guia de Deploy na Hostinger VPS

## Pré-requisitos

- VPS Linux (Ubuntu 20.04 LTS ou superior recomendado)
- Acesso SSH com permissões de sudo
- Domínio próprio (opcional, mas recomendado)

## 1. Preparação Inicial do Servidor

### 1.1 Conectar ao VPS via SSH

```bash
ssh root@seu_ip_vps
```

### 1.2 Atualizar o Sistema

```bash
apt update && apt upgrade -y
```

### 1.3 Instalar Dependências Básicas

```bash
apt install -y \
    build-essential \
    python3 python3-pip python3-venv \
    nginx \
    redis-server \
    git \
    curl \
    wget \
    certbot \
    python3-certbot-nginx
```

### 1.4 Criar Usuário de Aplicação (Opcional, mas Recomendado)

```bash
# Criar usuário
useradd -m -s /bin/bash appuser

# Adicionar ao grupo sudo
usermod -aG sudo appuser

# Mudar para o novo usuário
su - appuser
```

## 2. Instalação da Aplicação

### 2.1 Clonar ou Copiar o Repositório

```bash
# Via Git (se usar repositório)
cd /opt
sudo git clone https://seu-repo.git image-processing

# Ou copiar manualmente (via SFTP/SCP)
# scp -r ./image_processing_microservice appuser@seu_ip:/opt/image-processing
```

### 2.2 Configurar Permissões

```bash
sudo chown -R appuser:appuser /opt/image-processing
cd /opt/image-processing
chmod +x setup.sh
```

### 2.3 Executar Setup

```bash
./setup.sh
```

Ou manualmente:

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Criar diretórios
mkdir -p logs temp_processed_images fonts
```

### 2.4 Configurar Variáveis de Ambiente

```bash
# Copiar arquivo .env
cp .env.example .env

# Editar configurações
nano .env
```

Configure com seus valores (Redis, debug, etc).

### 2.5 Adicionar Fonte TrueType

Copie um arquivo `.ttf` para a pasta `fonts/`:

```bash
# Opção 1: Usar fonte padrão do sistema
sudo cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf fonts/arial.ttf

# Opção 2: Copiar via SCP do seu PC
# scp ./arial.ttf appuser@seu_ip:/opt/image-processing/fonts/
```

## 3. Configurar Redis

```bash
# Iniciar Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verificar status
sudo systemctl status redis-server

# Teste de conexão
redis-cli ping
# Resposta esperada: PONG
```

## 4. Configurar Systemd Service

```bash
# Copiar arquivo de serviço
sudo cp image-processing.service /etc/systemd/system/

# Editar o arquivo se necessário
sudo nano /etc/systemd/system/image-processing.service

# Atualizar systemd
sudo systemctl daemon-reload

# Ativar serviço
sudo systemctl enable image-processing

# Iniciar serviço
sudo systemctl start image-processing

# Verificar status
sudo systemctl status image-processing

# Ver logs
sudo journalctl -u image-processing -f
```

## 5. Configurar Nginx

### 5.1 Copiar Configuração

```bash
# Copiar arquivo de configuração
sudo cp nginx-config.conf /etc/nginx/sites-available/image-processing

# Editar para seu domínio
sudo nano /etc/nginx/sites-available/image-processing
# Altere "seu.dominio.com" para seu domínio real
```

### 5.2 Ativar Site

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/image-processing /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

## 6. Configurar HTTPS com Let's Encrypt

```bash
# Gerar certificado SSL
sudo certbot --nginx -d seu.dominio.com

# Seguir as instruções interativas (aceitar termos, email, etc)

# Testar renovação automática
sudo certbot renew --dry-run
```

## 7. Configurar Firewall

```bash
# Ativar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP
sudo ufw allow 80/tcp

# Permitir HTTPS
sudo ufw allow 443/tcp

# Verificar regras
sudo ufw status
```

## 8. Verificar Instalação

### 8.1 Health Check Local

```bash
# No servidor
curl http://localhost:5001/health

# Resposta esperada:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   ...
# }
```

### 8.2 Health Check Remoto

```bash
# Do seu PC
curl https://seu.dominio.com/health

# Ou
curl https://seu_ip/health
```

### 8.3 Testar Processamento

```bash
# Enviar requisição de teste
curl -X POST https://seu.dominio.com/api/v1/process-image \
  -H "Content-Type: application/json" \
  -d @payload_example.json

# Verificar logs do servidor
sudo tail -f /opt/image-processing/logs/app.log
```

## 9. Monitoramento

### 9.1 Verificar Status do Serviço

```bash
# Status da aplicação
sudo systemctl status image-processing

# Logs recentes
sudo journalctl -u image-processing -n 50

# Logs em tempo real
sudo journalctl -u image-processing -f
```

### 9.2 Verificar Recursos

```bash
# Uso de CPU e memória
ps aux | grep gunicorn

# Espaço em disco
df -h

# Uso de memória
free -h

# Conectar ao Redis
redis-cli
> INFO
```

### 9.3 Limpar Arquivos Temporários

```bash
# Limpar manualmente
curl -X POST https://seu.dominio.com/api/v1/cleanup?max_age_hours=24

# Agendar limpeza automática (cron)
sudo crontab -e

# Adicionar linha:
0 * * * * curl -X POST http://localhost:5001/api/v1/cleanup?max_age_hours=24
```

## 10. Backup e Manutenção

### 10.1 Backup da Aplicação

```bash
# Criar tarball
sudo tar -czf image-processing-backup-$(date +%Y%m%d).tar.gz /opt/image-processing/

# Copiar para seu PC
scp appuser@seu_ip:/opt/image-processing-backup-*.tar.gz ./
```

### 10.2 Atualizar Aplicação

```bash
# Pull das alterações
cd /opt/image-processing
sudo git pull

# Ou copiar nova versão
scp -r ./image_processing_microservice/* appuser@seu_ip:/opt/image-processing/

# Instalar dependências novas
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar serviço
sudo systemctl restart image-processing
```

### 10.3 Logs de Rotação

Logs são rotacionados automaticamente pelo Python logging (10MB max, 10 backups).

Você também pode adicionar ao `/etc/logrotate.d/`:

```bash
# Criar arquivo
sudo nano /etc/logrotate.d/image-processing

# Adicionar:
/opt/image-processing/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 appuser appuser
    sharedscripts
    postrotate
        systemctl reload image-processing > /dev/null 2>&1 || true
    endscript
}
```

## 11. Troubleshooting

### Problema: "Connection refused"

```bash
# Verificar se porta 5001 está aberta
sudo netstat -tlpn | grep 5001

# Verificar se aplicação está rodando
ps aux | grep gunicorn

# Reiniciar serviço
sudo systemctl restart image-processing
```

### Problema: "502 Bad Gateway (Nginx)"

```bash
# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Verificar logs da aplicação
sudo journalctl -u image-processing -f

# Verificar status
sudo systemctl status image-processing
```

### Problema: "Redis connection error"

```bash
# Verificar se Redis está rodando
sudo systemctl status redis-server

# Reiniciar Redis
sudo systemctl restart redis-server

# Testar conexão
redis-cli ping
```

### Problema: "Font not found"

```bash
# Verificar se fonte existe
ls -la /opt/image-processing/fonts/

# Copiar fonte
sudo cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /opt/image-processing/fonts/arial.ttf

# Reiniciar aplicação
sudo systemctl restart image-processing
```

### Problema: "Disco cheio"

```bash
# Verificar espaço
df -h

# Limpar arquivos temporários
sudo rm -f /opt/image-processing/temp_processed_images/*

# Limpar tarefas antigas
curl -X POST http://localhost:5001/api/v1/cleanup?max_age_hours=12
```

## 12. Performance e Scaling

### 12.1 Aumentar Workers Gunicorn

Editar `/etc/systemd/system/image-processing.service`:

```ini
ExecStart=/opt/image-processing/venv/bin/gunicorn \
    --workers 8 \
    --worker-class sync \
    ...
```

### 12.2 Usar Processos Separados com RQ

Para escalar o processamento de imagens:

```bash
# Instalar RQ
pip install rq==1.15.1

# Ativar RQ em config.py
# USE_REDIS=True

# Criar worker systemd service para RQ
# (veja rq-worker.service abaixo)
```

**Arquivo: `/etc/systemd/system/rq-worker.service`**

```ini
[Unit]
Description=RQ Worker for Image Processing
After=redis-server.service
Requires=redis-server.service

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/image-processing
Environment="PATH=/opt/image-processing/venv/bin"
ExecStart=/opt/image-processing/venv/bin/rq worker \
    -c app.config \
    --with-scheduler

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Ativar:

```bash
sudo systemctl enable rq-worker
sudo systemctl start rq-worker
```

### 12.3 Load Balancing (Múltiplos Servidores)

Para múltiplos VPS, use Nginx como load balancer:

```nginx
upstream image_processing_backend {
    server vps1.ip:5001;
    server vps2.ip:5001;
    server vps3.ip:5001;
}

server {
    listen 80;
    server_name seu.dominio.com;
    
    location / {
        proxy_pass http://image_processing_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 13. Segurança

### 13.1 Desabilitar Debug em Produção

```bash
# Em .env:
DEBUG=False
```

### 13.2 Habilitar Autenticação (Opcional)

Adicione um header de autenticação em `app/main.py`:

```python
@app.before_request
def check_auth():
    if request.path.startswith('/api/'):
        token = request.headers.get('X-API-Key')
        if token != os.getenv('API_KEY'):
            return jsonify({"error": "Unauthorized"}), 401
```

### 13.3 Rate Limiting

Instale Flask-Limiter:

```bash
pip install Flask-Limiter
```

Use em `app/main.py`:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/v1/process-image', methods=['POST'])
@limiter.limit("10 per minute")
def process_image_request():
    ...
```

### 13.4 Manter Dependências Atualizadas

```bash
# Checar pacotes desatualizados
pip list --outdated

# Atualizar individual
pip install --upgrade package_name

# Verificar vulnerabilidades
pip install safety
safety check
```

## Resumo de Comandos Úteis

```bash
# Status geral
sudo systemctl status image-processing redis-server nginx

# Reiniciar todos os serviços
sudo systemctl restart image-processing redis-server nginx

# Ver logs
sudo journalctl -u image-processing -f
sudo tail -f /opt/image-processing/logs/app.log

# Testar API
curl https://seu.dominio.com/health

# SSH para servidor
ssh appuser@seu_ip

# Conectar ao Redis
redis-cli

# Editar configurações
sudo nano /opt/image-processing/.env
sudo nano /etc/nginx/sites-available/image-processing
sudo nano /etc/systemd/system/image-processing.service
```

## Próximos Passos

1. Configure seu domínio com DNS apontando para o IP do VPS
2. Acesse `https://seu.dominio.com/health` para verificar se está funcionando
3. Configure integração com sua Supabase Edge Function
4. Monitore logs e performance
5. Configure backups automáticos

Boa sorte com o deploy! 🚀
