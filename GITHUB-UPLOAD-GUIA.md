# 📤 SUBIR PARA GITHUB - PASSO A PASSO

## ⚠️ PRÉ-REQUISITOS

1. **Conta no GitHub** (crie em https://github.com/signup se não tiver)
2. **Git instalado** no Windows
3. **Token de acesso pessoal (PAT)** gerado no GitHub

---

## 🔑 GERAR TOKEN NO GITHUB

1. Vá em: https://github.com/settings/tokens
2. Clique: **Generate new token** → **Generate new token (classic)**
3. Configure:
   - **Token name:** Hostinger Deploy
   - **Expiration:** 90 days (ou mais)
   - **Scopes:** Marque ✅ `repo` (all options)
4. Clique: **Generate token**
5. **COPIE o token** (você só vê uma vez!)

---

## 🚀 EXECUTAR UPLOAD

### Opção 1: Script Automático (Recomendado)

```powershell
P
.\upload-to-github.ps1
```

**O script vai pedir:**
- Seu usuário GitHub
- Nome do repositório
- Token GitHub (PAT)
- Seu nome (para git config)
- Seu email (para git config)

**Depois faz tudo automaticamente!**

---

### Opção 2: Manual (Passo a Passo)

```powershell
cd d:\Repositorio\image-microservice

# Configurar Git
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# Inicializar repositório
git init

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Microservice ready for production deployment on Hostinger VPS"

# Adicionar remote (substitua SEU_USUARIO e image-microservice)
git remote add origin https://github.com/SEU_USUARIO/image-microservice.git

# Renomear branch para main
git branch -M main

# Fazer push (vai pedir token)
git push -u origin main
```

---

## ✅ VERIFICAR SE FUNCIONOU

Vá em: `https://github.com/SEU_USUARIO/image-microservice`

Você deve ver todos os arquivos do microservice lá!

---

## 📋 PRÓXIMO PASSO

Depois do upload, você pode:

**Opção A:** Clonar no VPS
```bash
git clone https://github.com/luizcantelmo/image-microservice.git
cd image-microservice
```

**Opção B:** Fazer upload via SFTP (se preferir)

---

## 🆘 ERROS COMUNS

### "Git not found"
- Instale Git: https://git-scm.com/download/win

### "fatal: destination path already exists"
- Delete `.git` se existir: `rm -r .git`

### "fatal: Authentication failed"
- Token errado ou expirado
- Regenere em: https://github.com/settings/tokens

### "remote origin already exists"
- Remova: `git remote remove origin`
- E adicione novamente

---

## 📝 RESUMO

1. Gere token no GitHub
2. Execute: `.\upload-to-github.ps1`
3. Responda as perguntas
4. Verifique em: github.com/seu_usuario/image-microservice
5. Pronto para clonar no VPS!
