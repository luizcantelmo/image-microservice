# 🚀 DEPLOY NA VPS HOSTINGER - PASSO A PASSO

## 📋 RESUMO DO DEPLOY

```
VPS: 212.85.13.64
Serviço: Image Microservice (Python Flask)
Porta: 5001
Runtime: Gunicorn + PM2
Servidor Web: Nginx (proxy reverso)
SSL: Let's Encrypt
```

---

## ✅ PASSO 1: Conectar na VPS via SSH

No PuTTY já conectado, você está pronto. Se precisar reconectar:

```bash
ssh seu_usuario@212.85.13.64
```

Confirme que está conectado (você deve ver o terminal da VPS).

---

## ✅ PASSO 2: Criar Diretório do Microservice

```bash
mkdir -p ~/microservice
cd ~/microservice
```

---

## ✅ PASSO 3: Clone do GitHub (ou Upload SFTP)

### Opção A: Git Clone (Recomendado)

```bash
git clone https://github.com/luizcantelmo/image-microservice.git .
cd ~/microservice
```

### Opção B: Upload via SFTP

1. Abra WinSCP
2. Faça login (IP: 212.85.13.64)
3. Arraste todos os arquivos de `d:\Repositorio\image-microservice\` para `/home/seu_usuario/microservice/`
4. No PuTTY:
```bash
cd ~/microservice
```

---

## ✅ PASSO 4: Instalar Python e Dependências

```bash
# Atualizar sistema
sudo apt update
sudo apt upgrade -y

# Instalar Python3 e pip
sudo apt install -y python3 python3-pip python3-venv

# Criar virtualenv
python3 -m venv venv

# Ativar virtualenv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
```

⏳ Isso pode levar 2-5 minutos. Aguarde até ver a mensagem de sucesso.

---

## ✅ PASSO 5: Testar a Aplicação

```bash
# Ter certeza que ainda está na pasta microservice
cd ~/microservice

# Ativar virtualenv novamente (se perdeu)
source venv/bin/activate

# Testar com Python
python3 wsgi.py
```

Você deve ver algo como:
```
 * Running on http://0.0.0.0:5001
 * Press CTRL+C to quit
```

**Teste a saúde da API em outro terminal:**
```bash
curl http://localhost:5001/health
```

Se vir `{"status":"ok"}` = ✅ Funcionando!

Volte para o PuTTY original e pressione `CTRL+C` para parar.

---

## ✅ PASSO 6: Instalar PM2 (Gerenciador de Processos)

```bash
# Instalar Node.js (necessário para PM2)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Instalar PM2 globalmente
sudo npm install -g pm2

# Ativar PM2 no startup
sudo pm2 startup
sudo pm2 save
```

---

## ✅ PASSO 7: Iniciar o Microservice com PM2

```bash
cd ~/microservice

# Ativar virtualenv
source venv/bin/activate

# Iniciar com PM2
pm2 start "gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app" --name microservice

# Salvar para reiniciar após reboot
pm2 save

# Ver status
pm2 status
```

Você deve ver:
```
┌─────────────────────────────────────────────────────────────────┐
│ id  │ name          │ namespace   │ version │ mode    │ pid     │
├─────────────────────────────────────────────────────────────────┤
│ 0   │ microservice  │ default     │ 1.0.0   │ fork    │ 12345   │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ PASSO 8: Configurar Nginx (Reverse Proxy)

```bash
# Instalar Nginx
sudo apt install -y nginx

# Parar Nginx por enquanto
sudo systemctl stop nginx

# Criar arquivo de configuração
sudo nano /etc/nginx/sites-available/microservice
```

Copie e cole isso (CTRL+Shift+V para colar no PuTTY):

```nginx
upstream microservice_backend {
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name 212.85.13.64 srv819060.hstgr.cloud;

    client_max_body_size 50M;

    location / {
        proxy_pass http://microservice_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }

    location /health {
        proxy_pass http://microservice_backend;
        access_log off;
    }
}
```

Salve com: `CTRL+O`, `Enter`, `CTRL+X`

Depois ative:
```bash
sudo ln -s /etc/nginx/sites-available/microservice /etc/nginx/sites-enabled/

# Teste configuração
sudo nginx -t

# Inicie Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

---

## ✅ PASSO 9: Testar o Acesso Externo

Em outro terminal (ou seu PC):

```bash
# Testar via IP
curl http://212.85.13.64/health

# Testar via DNS
curl http://srv819060.hstgr.cloud/health
```

Se vir `{"status":"ok"}` = ✅ Funciona!

---

## ✅ PASSO 10: Configurar SSL (HTTPS)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Gerar certificado (substitua seu email)
sudo certbot certonly --standalone -d srv819060.hstgr.cloud -d 212.85.13.64 --email seu@email.com -n --agree-tos

# Atualizar Nginx com SSL
sudo nano /etc/nginx/sites-available/microservice
```

Substitua o arquivo anterior por:

```nginx
upstream microservice_backend {
    server 127.0.0.1:5001;
}

# Redirecionar HTTP para HTTPS
server {
    listen 80;
    server_name 212.85.13.64 srv819060.hstgr.cloud;
    return 301 https://$server_name$request_uri;
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name 212.85.13.64 srv819060.hstgr.cloud;

    ssl_certificate /etc/letsencrypt/live/srv819060.hstgr.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srv819060.hstgr.cloud/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 50M;

    location / {
        proxy_pass http://microservice_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }

    location /health {
        proxy_pass http://microservice_backend;
        access_log off;
    }
}
```

Salve com: `CTRL+O`, `Enter`, `CTRL+X`

Depois teste e reinicie:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## ✅ PASSO 11: Configurar .env na VPS

```bash
cd ~/microservice
nano .env.production
```

Cole (ajuste se necessário):
```env
DEBUG=False
ENVIRONMENT=production
FLASK_PORT=5001
FLASK_HOST=0.0.0.0
ALLOW_CORS=True
CORS_ORIGINS=*
LOG_LEVEL=INFO
OUTPUT_IMAGE_QUALITY=90
PADDING_X=30
PADDING_Y=30
LINE_HEIGHT_MULTIPLIER=1.2
PRODUCT_BLOCK_WIDTH_PERCENT=0.45
FONT_DESCRIPTION_SIZE=28
FONT_REF_SIZE_PROMO=22
FONT_PRICE_SIZE=30
FONT_ESGOTADO_SIZE=40
REQUEST_TIMEOUT=30
TASK_TIMEOUT=300
MAX_RETRIES=3
MAX_PRODUCTS_PER_REQUEST=10
USE_REDIS=False
```

Salve com: `CTRL+O`, `Enter`, `CTRL+X`

Reinicie o PM2:
```bash
source venv/bin/activate
pm2 restart microservice
pm2 save
```

---

## ✅ PASSO 12: Verificar Status e Logs

```bash
# Ver status do serviço
pm2 status

# Ver logs em tempo real
pm2 logs microservice

# Ver últimas 100 linhas de log
pm2 logs microservice -n 100

# Parar/Iniciar/Reiniciar
pm2 stop microservice
pm2 start microservice
pm2 restart microservice
```

---

## 🎯 RESUMO DO QUE FOI FEITO

✅ Python + dependências instalados
✅ Microservice rodando em http://localhost:5001 (local VPS)
✅ PM2 gerenciando o processo
✅ Nginx como reverse proxy em http://212.85.13.64 (externo)
✅ SSL/HTTPS configurado
✅ Auto-restart após reboot via PM2

---

## 📝 TESTAR ENDPOINTS

```bash
# Health check
curl https://212.85.13.64/health

# Processar imagem (exemplo básico)
curl -X POST https://212.85.13.64/process-image \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/produto.jpg",
    "product_data": {
      "referencia": "ABC123",
      "preco": "99.90",
      "descricao": "Produto Teste"
    }
  }'
```

---

## 🆘 TROUBLESHOOTING

### Microservice não inicia
```bash
cd ~/microservice
source venv/bin/activate
python3 wsgi.py  # Ver erro detalhado
```

### Nginx erro
```bash
sudo nginx -t  # Ver erro de configuração
sudo journalctl -u nginx -n 50  # Ver logs
```

### Porta 5001 em uso
```bash
sudo lsof -i :5001
sudo kill -9 PID
```

### Verificar permissões
```bash
ls -la ~/microservice
```

---

## 📞 PRÓXIMOS PASSOS

1. ✅ Testar endpoints da API
2. ✅ Configurar Supabase Edge Function com URL do microservice
3. ✅ Atualizar frontend React para apontar para a VPS
4. ✅ Testar fluxo completo: Frontend → Microservice → Supabase

