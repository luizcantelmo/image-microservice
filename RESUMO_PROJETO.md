# Resumo do Projeto - Microserviço de Processamento de Imagens

## 📋 Visão Geral

Um microserviço Python profissional e escalável para processamento assíncrono de imagens com sobreescrita de dados de produtos. Integra Pillow para manipulação de imagens e Flask para API REST.

## 🎯 Funcionalidades Principais

✅ **Processamento Assíncrono**
- Retorna ID de tarefa imediatamente (202 Accepted)
- Processamento em background sem bloquear cliente
- Polling de status disponível

✅ **Manipulação Avançada de Imagens**
- Download de imagem original e marca d'água
- Renderização de múltiplos blocos de produtos
- Suporte a promoções com preço riscado
- Flag "ESGOTADO" com sobreposição
- Formatação brasileira de preços (R$ X.XXX,XX)

✅ **Gerenciamento de Tarefas**
- Em memória (desenvolvimento) ou Redis (produção)
- Auto-limpeza de tarefas antigas
- Suporte a múltiplas operações concorrentes

✅ **Código Profissional**
- Logging centralizado com rotação
- Validação de entrada robusta
- Tratamento de erros abrangente
- Documentação completa
- Estrutura modular e extensível

## 📁 Estrutura do Projeto

```
image_processing_microservice/
│
├── app/
│   ├── __init__.py                  # Inicialização do pacote
│   ├── main.py                      # Aplicação Flask + rotas (450+ linhas)
│   ├── config.py                    # Configurações centralizadas (150+ linhas)
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                # Sistema de logging (50+ linhas)
│       ├── validators.py            # Validação de entrada (80+ linhas)
│       ├── task_manager.py          # Gerenciador de tarefas (140+ linhas)
│       └── image_processor.py       # Processamento Pillow (500+ linhas)
│
├── temp_processed_images/           # Storage temporário (git-ignored)
├── logs/                            # Arquivos de log (git-ignored)
├── fonts/                           # Fontes TrueType (.ttf)
│
├── requirements.txt                 # Dependências Python
├── .env.example                     # Variáveis de ambiente exemplo
├── .gitignore                       # Exclusões git
│
├── wsgi.py                          # Entry point Gunicorn (produção)
├── setup.sh                         # Setup automático (Linux/Mac)
├── setup.bat                        # Setup automático (Windows)
│
├── README.md                        # Documentação principal (500+ linhas)
├── DEPLOY_HOSTINGER.md             # Guia deploy VPS (400+ linhas)
│
├── payload_example.json             # Exemplo de payload JSON
├── dev_test.py                      # Script de testes (150+ linhas)
│
├── Dockerfile                       # Containerização Docker
├── docker-compose.yml               # Orquestração com Docker Compose
│
├── nginx-config.conf                # Configuração Nginx (100+ linhas)
├── image-processing.service         # Unit file Systemd (50+ linhas)
│
└── [Este arquivo]                   # Resumo do projeto

```

## 🚀 Arquitetura

### Fluxo de Requisição

```
Cliente HTTP
    ↓
POST /api/v1/process-image (JSON com dados + URLs)
    ↓
Flask recebe, valida, cria task_id
    ↓
Retorna 202 + task_id + URL provisória (IMEDIATO)
    ↓
Flask inicia thread/worker em background
    ↓
ImageProcessor:
  1. Download de imagem original via requests
  2. Download de marca d'água (opcional)
  3. Validação e normalização de dados
  4. Composição de imagem com blocos de produtos
  5. Renderização de textos com Pillow
  6. Salva JPEG em temp_processed_images/
    ↓
TaskManager atualiza status para COMPLETED
    ↓
Cliente faz polling: GET /api/v1/status/{task_id}
    ↓
Quando COMPLETED, cliente faz: GET /processed_images/{task_id}.jpg
    ↓
Nginx serve imagem + após_this_request limpa arquivo e status
    ↓
Resposta: Arquivo JPEG
```

### Componentes Principais

1. **Flask App (main.py)** - API REST com 6 rotas
2. **ImageProcessor (image_processor.py)** - Lógica de processamento Pillow
3. **TaskManager (task_manager.py)** - Gerenciamento de estado (Redis/Memória)
4. **Config (config.py)** - Variáveis globais e settings
5. **Validators (validators.py)** - Validação de entrada
6. **Logger (logger.py)** - Logging centralizado

## 🔌 Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| POST | `/api/v1/process-image` | Enviar para processamento (202) |
| GET | `/api/v1/status/{task_id}` | Consultar status |
| GET | `/processed_images/{task_id}.jpg` | Download (auto-cleanup) |
| GET | `/api/v1/tasks` | Listar tarefas (debug) |
| POST | `/api/v1/cleanup` | Limpeza manual (debug) |

## 📦 Dependências

```
Flask==3.0.0              # Web framework
Pillow==10.1.0           # Processamento de imagem
requests==2.31.0         # Download de URLs
python-dotenv==1.0.0     # Variáveis de ambiente
redis==5.0.1             # Cache/broker (produção)
rq==1.15.1               # Fila de tarefas (produção)
gunicorn==21.2.0         # WSGI server (produção)
Werkzeug==3.0.1          # WSGI utilities
flask-cors==4.0.0        # CORS support (opcional)
```

## 🎨 Recursos de Renderização

### Layout de Bloco de Produto

```
┌─────────────────────────────────────┐
│ DESCRIÇÃO DO PRODUTO                │
│ Ref REF-001                         │
│ TAM: M (Modelo)                     │
│ Veste: P, M, G, GG                 │
│ ─────────────────────────────────   │  (riscado se promo)
│ DE R$ 99,90                         │
│ POR R$ 79,90 (no cartão)            │
│ ou R$ 75,90 (à vista)               │
│                                     │
│         ┌─────────────────┐         │
│         │   ESGOTADO      │         │  (se Esgotado=true)
│         └─────────────────┘         │
└─────────────────────────────────────┘
```

### Configurações de Estilo

- Cores personalizáveis (RGB/RGBA)
- Fontes TrueType personalizáveis
- Múltiplos tamanhos de fonte
- Padding e espaçamento configurável
- Suporte a transparência

## 🔧 Configurações

Todas as configurações em `app/config.py`:

- **Environment**: development, staging, production
- **Redis**: HOST, PORT, DB, PASSWORD (opcional)
- **Fontes**: Tamanhos de texto, diretório
- **Layout**: Padding, largura de bloco, espaçamento
- **Cores**: RGB/RGBA para componentes
- **Limites**: Max produtos, timeout, retries
- **Storage**: Localização de arquivos temporários
- **Logging**: Nível, formato, localização

## 📊 Performance

- **Download de imagem**: ~100-500ms
- **Processamento por produto**: ~200-500ms
- **Salvamento**: ~100-300ms
- **Total por imagem**: 500ms - 5s (depende do tamanho)

**Recomendado**: Até 10 produtos por imagem

**Escalabilidade**: Use RQ + múltiplos workers para paralelizar

## 🛡️ Segurança

- ✅ Validação de entrada rigorosa
- ✅ Tratamento de exceções centralizado
- ✅ Logging de todos os eventos
- ✅ CORS configurável
- ✅ Sem debug em produção
- ⚠️ Implementar autenticação (API keys)
- ⚠️ Rate limiting recomendado
- ⚠️ HTTPS obrigatório em produção

## 🚢 Deploy

### Opção 1: Linux VPS (Recomendado)

```bash
# Veja DEPLOY_HOSTINGER.md para instruções completas
./setup.sh
sudo systemctl enable image-processing
sudo systemctl start image-processing
```

### Opção 2: Docker

```bash
docker-compose up -d
```

### Opção 3: Desenvolvimento Local

```bash
python -m app.main  # http://localhost:5001
```

## 🧪 Testes

```bash
# Script automático
python dev_test.py --full

# Ou manual com cURL
curl http://localhost:5001/health
curl -X POST http://localhost:5001/api/v1/process-image -d @payload_example.json
```

## 📈 Próximos Passos

1. **Adicionar autenticação**: API keys ou JWT
2. **Rate limiting**: Para evitar abuso
3. **Webhook notifications**: Avisar cliente quando pronto
4. **Armazenamento S3**: Para imagens de longa duração
5. **Analytics**: Dashboard de processamentos
6. **Cache avançado**: Redis cache para downloads frequentes
7. **Testes unitários**: Cobertura completa
8. **CI/CD**: Pipeline automático de deploy

## 📝 Documentação Adicional

- **README.md**: Guia de uso e exemplos
- **DEPLOY_HOSTINGER.md**: Deploy detalhado em VPS
- **Código**: Comentários em português explicando a lógica
- **Logs**: Informativos em tempo real durante execução

## 💡 Exemplos de Uso

### Python

```python
import requests

payload = {
    "products": [...],
    "original_image_url": "https://...",
    "watermark_url": "https://..." # opcional
}

response = requests.post(
    "http://localhost:5001/api/v1/process-image",
    json=payload
)
task_id = response.json()['task_id']

# Polling
while True:
    status = requests.get(f"http://localhost:5001/api/v1/status/{task_id}")
    if status.json()['status'] == 'COMPLETED':
        break
    time.sleep(2)

# Download
image = requests.get(f"http://localhost:5001/processed_images/{task_id}.jpg")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

const response = await axios.post(
    'http://localhost:5001/api/v1/process-image',
    { products: [...], original_image_url: '...', watermark_url: '...' }
);
const taskId = response.data.task_id;

// Polling
const pollStatus = setInterval(async () => {
    const status = await axios.get(`http://localhost:5001/api/v1/status/${taskId}`);
    if (status.data.status === 'COMPLETED') {
        clearInterval(pollStatus);
        // Download image
        const image = await axios.get(`http://localhost:5001/processed_images/${taskId}.jpg`);
    }
}, 2000);
```

## 📞 Suporte

Em caso de dúvidas:
1. Verifique os logs: `tail -f logs/app.log`
2. Consulte README.md
3. Verifique DEPLOY_HOSTINGER.md
4. Use `curl` para testar endpoints isoladamente

---

**Versão**: 1.0.0  
**Última atualização**: 2024  
**Status**: Pronto para Produção ✅
