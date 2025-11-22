# Microserviço de Processamento de Imagens

Microserviço em Python para processamento assíncrono de imagens com sobreescrita de dados de produtos.

## Arquitetura

```
Client (Supabase Edge Function)
  ↓
  POST /api/v1/process-image → Retorna task_id + URL temporária (202 Accepted)
  ↓
  Polling: GET /api/v1/status/{task_id} → Verifica status
  ↓
  GET /processed_images/{task_id}.jpg → Download da imagem
  ↓
  Imagem é servida e removida do storage temporário
```

### Fluxo de Processamento

1. **Requisição Assíncrona**: Cliente faz POST com dados dos produtos e URL da imagem
2. **Retorno Imediato**: Microserviço retorna ID de tarefa e URL provisória
3. **Processamento em Background**: Thread/Worker processa a imagem
4. **Polling de Status**: Cliente consulta status periodicamente
5. **Download**: Quando pronto, cliente faz download
6. **Limpeza**: Arquivo é removido após download

## Requisitos

- Python 3.8+
- Flask 3.0.0
- Pillow 10.1.0
- requests 2.31.0
- redis 5.0.1 (opcional, para produção)
- rq 1.15.1 (opcional, para produção)

## Instalação

### 1. Clone ou copie o projeto

```bash
cd image_processing_microservice
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Obtenha uma fonte TrueType

Baixe uma fonte em formato `.ttf` (ex: Arial, Roboto, etc.) e coloque na pasta `fonts/`:

```bash
mkdir fonts
# Copie seu arquivo arial.ttf (ou outro) para a pasta fonts/
```

### 5. Configure variáveis de ambiente (opcional)

Crie um arquivo `.env`:

```env
DEBUG=False
ENVIRONMENT=development
FLASK_PORT=5001
FLASK_HOST=0.0.0.0

# Redis (opcional, para produção)
USE_REDIS=False
REDIS_HOST=localhost
REDIS_PORT=6379

# Limites
MAX_PRODUCTS_PER_REQUEST=10
REQUEST_TIMEOUT=30
TASK_TIMEOUT=300
```

## Execução

### Desenvolvimento Local

```bash
python -m app.main
```

O servidor estará disponível em `http://localhost:5001`

### Produção (com Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:5001 app.main:app
```

Ou com Nginx como proxy reverso (veja seção de Deploy).

## Endpoints da API

### 1. Health Check

```
GET /health
```

**Response (200 OK):**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00.000000",
    "version": "1.0.0",
    "environment": "development"
}
```

### 2. Processar Imagem

```
POST /api/v1/process-image
Content-Type: application/json
```

**Body:**
```json
{
    "products": [
        {
            "Referencia": "REF-001",
            "DescricaoFinal": "Camiseta Premium Algodão",
            "Preco": 99.90,
            "PrecoPromocional": 79.90,
            "PrecoPromocionalAVista": 75.90,
            "TamanhosDisponiveis": "P, M, G, GG",
            "NumeracaoUtilizada": "M",
            "Esgotado": false
        },
        {
            "Referencia": "REF-002",
            "DescricaoFinal": "Calça Jeans Slim",
            "Preco": 149.90,
            "PrecoPromocional": 0,
            "PrecoPromocionalAVista": 0,
            "TamanhosDisponiveis": "P, M, G",
            "NumeracaoUtilizada": "32",
            "Esgotado": true
        }
    ],
    "original_image_url": "https://example.com/image.jpg",
    "watermark_url": "https://example.com/logo.png"
}
```

**Response (202 Accepted):**
```json
{
    "status": "processing",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status_url": "/api/v1/status/550e8400-e29b-41d4-a716-446655440000",
    "final_image_url": "/processed_images/550e8400-e29b-41d4-a716-446655440000.jpg"
}
```

### 3. Consultar Status

```
GET /api/v1/status/{task_id}
```

**Response (200 OK) - Processando:**
```json
{
    "status": "PROCESSING",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00.000000"
}
```

**Response (200 OK) - Concluído:**
```json
{
    "status": "COMPLETED",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:15.000000",
    "final_image_url": "/processed_images/550e8400-e29b-41d4-a716-446655440000.jpg"
}
```

**Response (200 OK) - Erro:**
```json
{
    "status": "FAILED",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:20.000000",
    "error_message": "Erro ao baixar imagem..."
}
```

### 4. Download da Imagem

```
GET /processed_images/{task_id}.jpg
```

**Response:** Imagem JPEG + Auto-delete + Status cleanup

## Exemplos de Uso

### cURL

```bash
# 1. Enviar requisição de processamento
curl -X POST http://localhost:5001/api/v1/process-image \
  -H "Content-Type: application/json" \
  -d @payload.json

# Response:
# {
#   "status": "processing",
#   "task_id": "550e8400-e29b-41d4-a716-446655440000",
#   ...
# }

# 2. Consultar status (repetir até COMPLETED)
curl http://localhost:5001/api/v1/status/550e8400-e29b-41d4-a716-446655440000

# 3. Download da imagem (quando COMPLETED)
curl -o output.jpg http://localhost:5001/processed_images/550e8400-e29b-41d4-a716-446655440000.jpg
```

### Python

```python
import requests
import time
import json

# Dados dos produtos
payload = {
    "products": [
        {
            "Referencia": "REF-001",
            "DescricaoFinal": "Camiseta Premium",
            "Preco": 99.90,
            "PrecoPromocional": 79.90,
            "PrecoPromocionalAVista": 75.90,
            "TamanhosDisponiveis": "P, M, G, GG",
            "NumeracaoUtilizada": "M",
            "Esgotado": False
        }
    ],
    "original_image_url": "https://example.com/image.jpg",
    "watermark_url": "https://example.com/logo.png"
}

BASE_URL = "http://localhost:5001"

# 1. Enviar requisição
response = requests.post(f"{BASE_URL}/api/v1/process-image", json=payload)
data = response.json()
task_id = data['task_id']
print(f"Task ID: {task_id}")

# 2. Polling de status
while True:
    status_response = requests.get(f"{BASE_URL}/api/v1/status/{task_id}")
    status_data = status_response.json()
    print(f"Status: {status_data['status']}")
    
    if status_data['status'] == 'COMPLETED':
        break
    elif status_data['status'] == 'FAILED':
        print(f"Erro: {status_data['error_message']}")
        break
    
    time.sleep(2)  # Aguardar 2 segundos antes de consultar novamente

# 3. Download da imagem
if status_data['status'] == 'COMPLETED':
    image_response = requests.get(f"{BASE_URL}{data['final_image_url']}")
    with open('output.jpg', 'wb') as f:
        f.write(image_response.content)
    print("Imagem salva como output.jpg")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');
const fs = require('fs');

const payload = {
    products: [
        {
            Referencia: "REF-001",
            DescricaoFinal: "Camiseta Premium",
            Preco: 99.90,
            PrecoPromocional: 79.90,
            PrecoPromocionalAVista: 75.90,
            TamanhosDisponiveis: "P, M, G, GG",
            NumeracaoUtilizada: "M",
            Esgotado: false
        }
    ],
    original_image_url: "https://example.com/image.jpg",
    watermark_url: "https://example.com/logo.png"
};

const BASE_URL = "http://localhost:5001";

async function processImage() {
    try {
        // 1. Enviar requisição
        const response = await axios.post(`${BASE_URL}/api/v1/process-image`, payload);
        const { task_id, final_image_url } = response.data;
        console.log(`Task ID: ${task_id}`);
        
        // 2. Polling de status
        let status = 'PROCESSING';
        while (status === 'PROCESSING') {
            const statusResponse = await axios.get(`${BASE_URL}/api/v1/status/${task_id}`);
            status = statusResponse.data.status;
            console.log(`Status: ${status}`);
            
            if (status === 'FAILED') {
                console.error(`Erro: ${statusResponse.data.error_message}`);
                return;
            }
            
            if (status !== 'COMPLETED') {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        
        // 3. Download da imagem
        const imageResponse = await axios.get(`${BASE_URL}${final_image_url}`, {
            responseType: 'arraybuffer'
        });
        fs.writeFileSync('output.jpg', imageResponse.data);
        console.log('Imagem salva como output.jpg');
    } catch (error) {
        console.error('Erro:', error.message);
    }
}

processImage();
```

## Estrutura do Projeto

```
image_processing_microservice/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configurações centralizadas
│   ├── main.py                # Aplicação Flask + rotas
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Sistema de logging
│       ├── validators.py      # Validação de entrada
│       ├── task_manager.py    # Gerenciador de tarefas (Redis/Memória)
│       └── image_processor.py # Lógica de processamento (Pillow)
├── fonts/                     # Diretório para fontes .ttf
├── logs/                      # Diretório para logs
├── temp_processed_images/     # Armazenamento temporário
├── requirements.txt           # Dependências Python
├── .env.example              # Exemplo de variáveis de ambiente
├── .gitignore                # Arquivo git ignore
└── README.md                 # Este arquivo
```

## Configuração Avançada

### 1. Usar Redis para Gerenciamento de Tarefas

Para produção, configure Redis:

```env
USE_REDIS=True
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=sua_senha
```

### 2. Usar RQ para Fila de Tarefas

Modifique `app/main.py` para usar RQ em vez de threads:

```python
from rq import Queue
import redis

redis_conn = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    password=config.REDIS_PASSWORD
)
q = Queue(connection=redis_conn)

# No endpoint process_image_request:
job = q.enqueue(image_processor.process_image, task_id, products, original_image_url, watermark_url)
```

Rode um worker:
```bash
rq worker
```

### 3. Nginx Proxy Reverso

```nginx
server {
    listen 80;
    server_name seu.dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_request_buffering off;
    }
}
```

### 4. Systemd Service (Linux)

Crie `/etc/systemd/system/image-processing.service`:

```ini
[Unit]
Description=Image Processing Microservice
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/microservice
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5001 app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Ativar:
```bash
sudo systemctl enable image-processing
sudo systemctl start image-processing
```

## Deploy na Hostinger VPS

### 1. Preparação do Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e dependências
sudo apt install python3 python3-venv python3-pip nginx -y

# Criar diretório da aplicação
sudo mkdir -p /opt/image-processing
cd /opt/image-processing
```

### 2. Setup da Aplicação

```bash
# Clone o repositório ou copie os arquivos
git clone seu-repo .

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Baixar fontes
mkdir fonts
# Copie suas fontes .ttf para fonts/
```

### 3. Configurar Nginx

```bash
# Criar arquivo de configuração
sudo nano /etc/nginx/sites-available/image-processing

# Adicionar configuração (veja seção anterior)

# Ativar
sudo ln -s /etc/nginx/sites-available/image-processing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Configurar SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d seu.dominio.com
```

### 5. Configurar Redis (Produção)

```bash
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 6. Começar a Aplicação

```bash
# Com systemd (veja seção anterior)
sudo systemctl start image-processing

# Ou manualmente
gunicorn -w 4 -b 0.0.0.0:5001 app.main:app
```

## Monitoramento

### Logs

```bash
# Ver logs em tempo real
tail -f logs/app.log

# Filtrar por nível
grep ERROR logs/app.log
grep WARNING logs/app.log
```

### Endpoints de Debug (DEBUG=True)

```bash
# Status de todas as tarefas
curl http://localhost:5001/api/v1/tasks

# Limpeza manual
curl -X POST http://localhost:5001/api/v1/cleanup?max_age_hours=24

# Configuração
curl http://localhost:5001/config
```

## Troubleshooting

### Problema: "Font not found"

**Solução**: Copie um arquivo `.ttf` para a pasta `fonts/` ou especifique o caminho completo em `config.py`.

### Problema: "Connection to Redis failed"

**Solução**: 
- Instale Redis: `sudo apt install redis-server`
- Inicie Redis: `sudo systemctl start redis-server`
- Ou desative Redis em `.env`: `USE_REDIS=False`

### Problema: "Imagem não aparece na resposta"

**Solução**:
- Verifique se a URL original é acessível
- Verifique se a fonte está carregada
- Consulte os logs: `tail -f logs/app.log`

### Problema: "Memory leak / Arquivos não limpam"

**Solução**:
- Ativar limpeza automática em `config.py`
- Usar endpoint manual: `POST /api/v1/cleanup`
- Adicionar cron job: `0 * * * * curl -X POST http://localhost:5001/api/v1/cleanup`

## Performance

- **Processamento de imagem**: ~500ms a 5s (depende do tamanho)
- **Limite recomendado**: 10 produtos por imagem
- **Escalabilidade**: Use RQ + múltiplos workers para processar múltiplas imagens em paralelo

## Segurança

- [ ] Configurar CORS para domínios específicos (não usar `*` em produção)
- [ ] Usar HTTPS/SSL em produção
- [ ] Validar todas as URLs de entrada
- [ ] Implementar rate limiting
- [ ] Usar autenticação/API keys
- [ ] Manter dependencies atualizadas

## Licença

MIT

## Contato

Para dúvidas ou contribuições, abra uma issue ou entre em contato.
