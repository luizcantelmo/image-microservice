# 🚀 COMO INICIAR O MICROSERVICE

## ⚡ Forma Mais Rápida (Windows)

### Opção 1: Duplo clique (Mais simples)
```
📁 image-microservice/
├─ start.bat  ← Duplo clique aqui!
└─ start.ps1  ← Ou clique com botão direito > Run with PowerShell
```

Uma janela vai abrir, o microservice vai iniciar automaticamente!

### Opção 2: PowerShell
```powershell
cd d:\Repositorio\image-microservice
.\start.ps1
```

### Opção 3: Command Prompt (CMD)
```cmd
cd d:\Repositorio\image-microservice
start.bat
```

### Opção 4: Manual (Linha de comando)
```powershell
cd d:\Repositorio\image-microservice
.\venv\Scripts\Activate.ps1
python run.py
```

---

## ✅ Verificar se Está Funcionando

Após iniciar, você deve ver:

```
🚀 Iniciando Flask...
   Host: 127.0.0.1
   Port: 5001
   Debug: True

 * Running on http://127.0.0.1:5001
 * Debug mode: on
 * Press CTRL+C to quit
```

Então abra no navegador:
```
http://127.0.0.1:5001/health
```

Você deve ver:
```json
{
  "status": "ok",
  "timestamp": "2025-11-22T..."
}
```

---

## 🐛 Se Algo Der Errado

### Erro: "ModuleNotFoundError: No module named 'app'"
**Solução:** Use `run.py` ou `start.bat` (que já resolve isso)

### Erro: "Port 5001 is already in use"
**Solução:** 
- Mude a porta no `.env`: `FLASK_PORT=5002`
- Ou finalize o processo anterior

### Erro: "ModuleNotFoundError: No module named 'flask'"
**Solução:** Instale as dependências
```powershell
pip install -r requirements.txt
```

---

## 📋 Arquivos para Iniciar

| Arquivo | Como Usar | Dificuldade |
|---------|-----------|------------|
| `start.bat` | Duplo clique | ⭐ Mais fácil |
| `start.ps1` | Duplo clique ou PowerShell | ⭐ Fácil |
| `run.py` | `python run.py` | ⭐⭐ Normal |
| `app/main.py` | `python -m app.main` | ⭐⭐⭐ Complicado |

---

## 🌍 Depois de Iniciar

### Testar via Terminal
```powershell
cd photo-monitor\supabase\functions\process-product-image
.\test-local.ps1
```

### Testar via Interface
```powershell
cd photo-monitor
npm run dev
# Depois: Configurações > TESTES > Testar!
```

---

## 📝 Notas

- **Porta padrão:** 5001 (configurável via `FLASK_PORT`)
- **Host padrão:** 127.0.0.1 (localhost)
- **Modo debug:** Ativado (recarrega automático)
- **CORS:** Ativado (permite requisições de localhost:5173)

---

**Versão:** 1.0  
**Criado:** 22 de Novembro de 2025
