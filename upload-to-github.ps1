#!/usr/bin/env powershell
# Script para fazer upload do microservice para GitHub

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           🚀 UPLOAD MICROSERVICE PARA GITHUB               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Verificar se está no diretório correto
$currentDir = Get-Location
if (-not (Test-Path "$currentDir\wsgi.py")) {
    Write-Host "❌ Erro: Você não está na pasta do microservice!" -ForegroundColor Red
    Write-Host "   Execute este script de: d:\Repositorio\image-microservice" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Diretório correto: $currentDir`n" -ForegroundColor Green

# 2. Verificar se Git está instalado
try {
    $gitVersion = git --version
    Write-Host "✅ Git encontrado: $gitVersion`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Git não está instalado!" -ForegroundColor Red
    Write-Host "   Instale de: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# 3. Perguntar informações do GitHub
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "INFORMAÇÕES DO GITHUB" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

$githubUser = Read-Host "Seu usuário GitHub"
$repoName = Read-Host "Nome do repositório (ex: image-microservice)" -DefaultValue "image-microservice"
$githubToken = Read-Host "Seu token GitHub (PAT)" -AsSecureString

# Converter token seguro para string
$token = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUni($githubToken)
)

$repoUrl = "https://${githubUser}:${token}@github.com/${githubUser}/${repoName}.git"
$repoDisplay = "https://github.com/${githubUser}/${repoName}.git"

Write-Host "`n✅ Será criado: $repoDisplay`n" -ForegroundColor Green

# 4. Configurar Git
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "CONFIGURANDO GIT" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

$userName = Read-Host "Seu nome (para git config)" -DefaultValue "Developer"
$userEmail = Read-Host "Seu email (para git config)" -DefaultValue "dev@example.com"

git config --global user.name "$userName"
git config --global user.email "$userEmail"

Write-Host "✅ Git configurado`n" -ForegroundColor Green

# 5. Inicializar repositório local
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "INICIALIZANDO REPOSITÓRIO LOCAL" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

if (Test-Path ".git") {
    Write-Host "⚠️  Repositório Git já existe" -ForegroundColor Yellow
    $reinit = Read-Host "Deseja reinicializar? (s/n)" -DefaultValue "n"
    if ($reinit -eq "s") {
        Remove-Item -Recurse -Force ".git"
        git init
    }
} else {
    git init
    Write-Host "✅ Repositório inicializado`n" -ForegroundColor Green
}

# 6. Adicionar arquivos
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "ADICIONANDO ARQUIVOS" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

git add .
git status

Write-Host "`n✅ Arquivos adicionados`n" -ForegroundColor Green

# 7. Fazer commit
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "FAZENDO COMMIT" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

git commit -m "Microservice ready for production deployment on Hostinger VPS"
Write-Host "`n✅ Commit realizado`n" -ForegroundColor Green

# 8. Adicionar remote
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "CONFIGURANDO REMOTE" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Verificar se remote já existe
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "⚠️  Remote 'origin' já existe" -ForegroundColor Yellow
    git remote remove origin
}

git remote add origin $repoUrl
Write-Host "✅ Remote adicionado`n" -ForegroundColor Green

# 9. Fazer push
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "FAZENDO PUSH PARA GITHUB" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

git branch -M main
git push -u origin main

Write-Host "`n════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✅ SUCESSO! PROJETO NO GITHUB" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Green

Write-Host "📍 URL do repositório:" -ForegroundColor Cyan
Write-Host "   $repoDisplay`n" -ForegroundColor Green

Write-Host "📋 Próximo passo:" -ForegroundColor Cyan
Write-Host "   1. Clonar no VPS: git clone $repoDisplay" -ForegroundColor Yellow
Write-Host "   2. Ou fazer upload via SFTP`n" -ForegroundColor Yellow

Write-Host "════════════════════════════════════════════════════════════════`n" -ForegroundColor Green
