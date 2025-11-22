# 📚 Índice Completo - Microserviço de Processamento de Imagens

## 🎯 Documentação

| Arquivo | Descrição | Uso |
|---------|-----------|-----|
| **QUICKSTART.md** | ⚡ Iniciar em 5 minutos | **COMECE AQUI** |
| **README.md** | 📖 Documentação completa e exemplos | Referência principal |
| **RESUMO_PROJETO.md** | 📊 Visão geral técnica | Entender arquitetura |
| **DEPLOY_HOSTINGER.md** | 🚀 Deploy em VPS Linux | Deploy em produção |

## 📂 Estrutura de Código

### Aplicação Principal

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `app/main.py` | 450+ | 🔴 **Aplicação Flask + Rotas API** |
| `app/config.py` | 150+ | ⚙️ Configurações centralizadas |
| `app/utils/image_processor.py` | 500+ | 🎨 **Processamento Pillow** |
| `app/utils/task_manager.py` | 140+ | 📋 Gerenciador de tarefas (Redis/Memória) |
| `app/utils/validators.py` | 80+ | ✅ Validação de entrada |
| `app/utils/logger.py` | 50+ | 📝 Logging centralizado |

### Configuração e Setup

| Arquivo | Descrição |
|---------|-----------|
| `requirements.txt` | Dependências Python |
| `.env.example` | Template de variáveis de ambiente |
| `setup.sh` | Setup automático (Linux/Mac) |
| `setup.bat` | Setup automático (Windows) |

### Deploy e Produção

| Arquivo | Descrição |
|---------|-----------|
| `wsgi.py` | Entry point para Gunicorn |
| `Dockerfile` | Containerização Docker |
| `docker-compose.yml` | Orquestração com Docker Compose |
| `nginx-config.conf` | Configuração Nginx (proxy reverso) |
| `image-processing.service` | Unit file Systemd (Linux service) |

### Integração e Exemplos

| Arquivo | Descrição |
|---------|-----------|
| `payload_example.json` | Exemplo de requisição JSON |
| `dev_test.py` | Script de testes automáticos |
| `supabase-edge-function.ts` | Exemplo de integração com Supabase |

### Controle de Versão

| Arquivo | Descrição |
|---------|-----------|
| `.gitignore` | Exclusões git |

## 🚀 Fluxo de Uso

### 1. Primeira Execução

```
1. Clonar/copiar projeto
   ↓
2. Executar setup.sh (Linux/Mac) ou setup.bat (Windows)
   ↓
3. Adicionar fonte .ttf na pasta fonts/
   ↓
4. Executar: python -m app.main
```

### 2. Fazer Requisição

```
POST /api/v1/process-image
{
  "products": [...],
  "original_image_url": "...",
  "watermark_url": "..." (opcional)
}

Response:
{
  "status": "processing",
  "task_id": "uuid",
  "status_url": "/api/v1/status/uuid",
  "final_image_url": "/processed_images/uuid.jpg"
}
```

### 3. Polling de Status

```
GET /api/v1/status/{task_id}

Respostas:
- "PENDING" → Aguardando processamento
- "PROCESSING" → Processando
- "COMPLETED" → Pronto para download
- "FAILED" → Erro no processamento
```

### 4. Download

```
GET /processed_images/{task_id}.jpg

Auto-cleanup:
- Imagem servida
- Arquivo removido do disco
- Status deletado
```

## 📋 Endpoints da API

### Health & Debug

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| GET | `/health` | ✅ | Health check (sempre disponível) |
| GET | `/config` | 🔐 | Config (apenas debug=true) |
| GET | `/api/v1/tasks` | 🔐 | Listar tarefas (apenas debug=true) |
| POST | `/api/v1/cleanup` | 🔐 | Limpeza manual (apenas debug=true) |

### Processamento

| Método | Rota | Status | Descrição |
|--------|------|--------|-----------|
| POST | `/api/v1/process-image` | ✅ | Enviar para processar |
| GET | `/api/v1/status/{task_id}` | ✅ | Consultar status |
| GET | `/processed_images/{task_id}.jpg` | ✅ | Download e auto-cleanup |

## 🔧 Configurações (config.py)

### Variáveis de Ambiente

```env
# Executar
DEBUG=False
ENVIRONMENT=development|staging|production
FLASK_PORT=5001
FLASK_HOST=0.0.0.0

# Redis (produção)
USE_REDIS=False
REDIS_HOST=localhost
REDIS_PORT=6379

# Fontes
FONT_DESCRIPTION_SIZE=28
FONT_PRICE_SIZE=30
FONT_ESGOTADO_SIZE=40

# Layout
PADDING_X=30
PRODUCT_BLOCK_WIDTH_PERCENT=0.45

# Cores
COLOR_PROMO_BACKGROUND=(255, 0, 0, 200)
COLOR_NORMAL_BACKGROUND=(0, 0, 0, 150)

# Limites
MAX_PRODUCTS_PER_REQUEST=10
REQUEST_TIMEOUT=30
TASK_TIMEOUT=300
```

## 🎨 Customização

### Adicionar Novo Endpoint

Edite `app/main.py`:

```python
@app.route('/api/v1/novo-endpoint', methods=['POST'])
@error_handler
def novo_endpoint():
    """Sua documentação"""
    # Sua lógica
    return jsonify({...}), 200
```

### Personalizar Renderização

Edite `app/utils/image_processor.py`:

```python
def _draw_custom_element(self, draw, ...):
    # Implementar novo elemento visual
    pass
```

### Adicionar Nova Validação

Edite `app/utils/validators.py`:

```python
def validate_novo_campo(data):
    # Sua validação
    return is_valid, error_message
```

## 📦 Dependências

```
Flask==3.0.0              # Web framework
Pillow==10.1.0           # Processamento de imagem
requests==2.31.0         # Download HTTP
redis==5.0.1             # Cache (opcional)
rq==1.15.1               # Fila de tarefas (opcional)
gunicorn==21.2.0         # WSGI server
```

## 🚀 Deploy Rápido

### Desenvolvimento

```bash
python -m app.main
```

### Produção Local

```bash
gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
```

### Docker

```bash
docker-compose up -d
```

### VPS Linux (Hostinger)

Veja **DEPLOY_HOSTINGER.md** para instruções completas.

## 🧪 Testes

### Teste Automático

```bash
python dev_test.py --full
```

### Teste Manual

```bash
curl http://localhost:5001/health
curl -X POST http://localhost:5001/api/v1/process-image -d @payload_example.json
```

## 📊 Performance

| Operação | Tempo |
|----------|-------|
| Download imagem | 100-500ms |
| Processamento/produto | 200-500ms |
| Salvamento | 100-300ms |
| **Total** | **500ms - 5s** |

**Limite recomendado**: 10 produtos por imagem

## 🛡️ Segurança

- ✅ Validação rigorosa de entrada
- ✅ Tratamento centralizado de erros
- ✅ Logging de todos os eventos
- ✅ CORS configurável
- ⚠️ Implementar autenticação (API keys)
- ⚠️ HTTPS obrigatório em produção
- ⚠️ Rate limiting recomendado

## 📞 Troubleshooting

### "Font not found"
→ Copie `.ttf` para pasta `fonts/`

### "Connection refused"
→ Servidor não está rodando: `python -m app.main`

### "502 Bad Gateway"
→ Verifique logs: `tail -f logs/app.log`

### "Task not found"
→ Tarefa expirada (TTL 24h) ou ID inválido

## 📚 Referências Externas

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pillow (PIL) Documentation](https://python-pillow.org/)
- [Redis Documentation](https://redis.io/)
- [RQ Documentation](https://python-rq.org/)
- [Gunicorn Documentation](https://gunicorn.org/)

## ✅ Checklist de Produção

- [ ] Debug desabilitado (`DEBUG=False`)
- [ ] Variáveis de ambiente configuradas
- [ ] Fonte TrueType adicionada
- [ ] Redis configurado (opcional)
- [ ] Nginx como proxy reverso
- [ ] HTTPS com Let's Encrypt
- [ ] Systemd service configurado
- [ ] Backups automáticos
- [ ] Monitoramento de logs
- [ ] Rate limiting implementado

## 📝 Histórico de Versões

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0.0 | 2024 | Versão inicial - MVP completo |

## 📄 Licença

MIT

---

**Última atualização**: 2024-01-15  
**Status**: ✅ Pronto para Produção

Para dúvidas, consulte a documentação completa em **README.md** ou **QUICKSTART.md**
