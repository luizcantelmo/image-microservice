# Quick Start - Microserviço de Processamento de Imagens

## ⚡ Iniciar em 5 Minutos

### 1. Preparação (Primeira Vez)

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Adicionar Fonte TrueType

Baixe uma fonte (ex: Arial, Roboto) em formato `.ttf` e copie para `fonts/`:

```bash
# Opção: usar fonte padrão do sistema
cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf fonts/arial.ttf
```

### 3. Iniciar Servidor

**Desenvolvimento (com debug):**
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
python -m app.main
```

**Produção (com Gunicorn):**
```bash
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
```

Server está pronto em: `http://localhost:5001`

### 4. Testar Imediatamente

```bash
# Terminal 1: Servidor já rodando

# Terminal 2: Executar testes
python dev_test.py --full

# Ou com cURL:
curl http://localhost:5001/health
```

## 📤 Fazer sua Primeira Requisição

### Opção A: cURL (Linux/Mac/Windows)

```bash
curl -X POST http://localhost:5001/api/v1/process-image \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {
        "Referencia": "TEST-001",
        "DescricaoFinal": "Camiseta Premium",
        "Preco": 99.90,
        "PrecoPromocional": 79.90,
        "PrecoPromocionalAVista": 75.90,
        "TamanhosDisponiveis": "P, M, G, GG",
        "NumeracaoUtilizada": "M",
        "Esgotado": false
      }
    ],
    "original_image_url": "https://via.placeholder.com/1200x800",
    "watermark_url": null
  }'
```

**Resposta esperada:**
```json
{
  "status": "processing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status_url": "/api/v1/status/550e8400-e29b-41d4-a716-446655440000",
  "final_image_url": "/processed_images/550e8400-e29b-41d4-a716-446655440000.jpg"
}
```

### Opção B: Python

```python
import requests
import time

# Enviar requisição
payload = {
    "products": [
        {
            "Referencia": "TEST-001",
            "DescricaoFinal": "Camiseta Premium",
            "Preco": 99.90,
            "PrecoPromocional": 79.90,
            "PrecoPromocionalAVista": 75.90,
            "TamanhosDisponiveis": "P, M, G, GG",
            "NumeracaoUtilizada": "M",
            "Esgotado": False
        }
    ],
    "original_image_url": "https://via.placeholder.com/1200x800",
    "watermark_url": None
}

response = requests.post("http://localhost:5001/api/v1/process-image", json=payload)
data = response.json()
task_id = data['task_id']
print(f"Task ID: {task_id}")

# Polling
while True:
    status = requests.get(f"http://localhost:5001/api/v1/status/{task_id}")
    status_data = status.json()
    print(f"Status: {status_data['status']}")
    
    if status_data['status'] == 'COMPLETED':
        # Download imagem
        image = requests.get(f"http://localhost:5001{data['final_image_url']}")
        with open('output.jpg', 'wb') as f:
            f.write(image.content)
        print("Imagem salva como output.jpg")
        break
    elif status_data['status'] == 'FAILED':
        print(f"Erro: {status_data['error_message']}")
        break
    
    time.sleep(2)
```

### Opção C: Arquivo JSON

Edite `payload_example.json` e envie:

```bash
curl -X POST http://localhost:5001/api/v1/process-image \
  -H "Content-Type: application/json" \
  -d @payload_example.json
```

## 🔍 Verificar Status

Copie o `task_id` da resposta anterior:

```bash
# cURL
curl http://localhost:5001/api/v1/status/SEU_TASK_ID_AQUI

# Browser
http://localhost:5001/api/v1/status/SEU_TASK_ID_AQUI
```

## 📥 Baixar Imagem

Quando status for `COMPLETED`:

```bash
# cURL
curl -o output.jpg http://localhost:5001/processed_images/SEU_TASK_ID_AQUI.jpg

# Browser (acesse a URL)
http://localhost:5001/processed_images/SEU_TASK_ID_AQUI.jpg
```

## 📊 Estrutura de Dados

### Produto (JSON)

```json
{
  "Referencia": "REF-001",           // String: Código único do produto
  "DescricaoFinal": "Camiseta",      // String: Nome/descrição
  "Preco": 99.90,                    // Float: Preço original
  "PrecoPromocional": 79.90,         // Float: Preço promo (0 = sem promo)
  "PrecoPromocionalAVista": 75.90,   // Float: Preço à vista
  "TamanhosDisponiveis": "P, M, G",  // String: Tamanhos disponíveis
  "NumeracaoUtilizada": "M",         // String: Tamanho a exibir no bloco
  "Esgotado": false                  // Bool: Mostrar flag "ESGOTADO"
}
```

### Requisição Completa

```json
{
  "products": [ /* array de produtos */ ],
  "original_image_url": "https://...",  // URL para download
  "watermark_url": "https://..."        // Opcional
}
```

## 🎨 Customizar Estilos

Edite `.env` (ou copie `.env.example` para `.env`):

```env
# Tamanhos de fonte
FONT_DESCRIPTION_SIZE=28
FONT_PRICE_SIZE=30
FONT_ESGOTADO_SIZE=40

# Cores (RGB)
# Formato: (R, G, B, Alpha)
COLOR_PROMO_BACKGROUND=(255, 0, 0, 200)    # Vermelho

# Layout
PADDING_X=30
PADDING_Y=30
PRODUCT_BLOCK_WIDTH_PERCENT=0.45            # 45% da imagem

# Marca d'água
WATERMARK_WIDTH_PERCENT=0.2                 # 20% da largura
WATERMARK_MARGIN_BOTTOM=20
```

Reinicie o servidor para aplicar mudanças.

## 🐛 Resolver Problemas

| Problema | Solução |
|----------|---------|
| "Font not found" | Copie um `.ttf` para `fonts/` |
| "Connection refused" | Servidor não está rodando: `python -m app.main` |
| "502 Bad Gateway" | Verifique logs: `tail -f logs/app.log` |
| "Imagem preta/branca" | Verifique URLs da imagem original |
| "Caracteres estranhos" | Verifique encoding da fonte |

## 📚 Documentação Completa

- **README.md** - Guia detalhado + exemplos
- **DEPLOY_HOSTINGER.md** - Deploy em VPS Linux
- **RESUMO_PROJETO.md** - Visão geral técnica
- **payload_example.json** - Exemplo de requisição

## 🔧 Comandos Úteis

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Parar servidor (Ctrl+C no terminal)

# Instalar nova dependência
pip install package_name

# Ver logs
tail -f logs/app.log

# Limpar arquivos temporários
rm -rf temp_processed_images/*

# Testar saúde
curl http://localhost:5001/health
```

## 🚀 Ir Para Produção

1. **Configurar variáveis**: Edite `.env`
2. **Usar Redis**: `USE_REDIS=True` em `.env`
3. **Deploy**: Veja `DEPLOY_HOSTINGER.md`
4. **HTTPS**: Configure com Let's Encrypt
5. **Proxy**: Use Nginx como reverse proxy
6. **Service**: Use systemd service

## 📞 Resumo Rápido

| Ação | Comando |
|------|---------|
| Setup inicial | `./setup.sh` ou `setup.bat` |
| Iniciar desenvolvimento | `python -m app.main` |
| Testar API | `python dev_test.py --full` |
| Ver logs | `tail -f logs/app.log` |
| Deploy produção | Veja `DEPLOY_HOSTINGER.md` |
| Documentação | Abra `README.md` |

---

**Pronto para começar!** 🎉

Qualquer dúvida, revise a documentação completa em `README.md`
