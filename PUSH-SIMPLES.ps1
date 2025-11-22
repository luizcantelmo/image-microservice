# Script simples para fazer push no GitHub
# Use este se já criou o repositório no GitHub manualmente

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                 PUSH SIMPLES PARA GITHUB                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host ""
Write-Host "📋 PRÉ-REQUISITOS:" -ForegroundColor Yellow
Write-Host "1. Você criou um repositório no GitHub (vazio, sem README)" -ForegroundColor Yellow
Write-Host "2. Você tem um token PAT válido com permissão 'repo'" -ForegroundColor Yellow
Write-Host ""

$Username = Read-Host "Seu usuário GitHub (ex: luizcantelmo)"
$RepoName = Read-Host "Nome do repositório (ex: image-microservice)"

Write-Host ""
Write-Host "🔐 Gerando URL de autenticação..." -ForegroundColor Cyan

# Pedir PAT Token
$PAT = Read-Host "Cole seu GitHub PAT Token" -AsSecureString
$PATPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($PAT))

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green

# Montar URL com autenticação
$repoUrl = "https://${Username}:${PATPlain}@github.com/${Username}/${RepoName}.git"

Write-Host "🔄 Removendo remote anterior..." -ForegroundColor Cyan
git remote remove origin 2>$null | Out-Null

Write-Host "🔗 Adicionando novo remote..." -ForegroundColor Cyan
git remote add origin $repoUrl
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao adicionar remote" -ForegroundColor Red
    exit 1
}

Write-Host "📤 Fazendo push..." -ForegroundColor Cyan
git push -u origin main 2>&1
$pushExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green

if ($pushExitCode -eq 0) {
    Write-Host "✅ SUCESSO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Seu repositório está em:" -ForegroundColor Cyan
    Write-Host "https://github.com/${Username}/${RepoName}" -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Host "❌ ERRO NO PUSH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possíveis problemas:" -ForegroundColor Yellow
    Write-Host "1. Token inválido ou expirado" -ForegroundColor Yellow
    Write-Host "2. Repositório não existe no GitHub" -ForegroundColor Yellow
    Write-Host "3. Sem permissão no repositório" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Solução: Crie um novo repositório em https://github.com/new" -ForegroundColor Yellow
}

# Limpar dados sensíveis
$PATPlain = ""
$repoUrl = ""

Read-Host "Pressione Enter para sair"
