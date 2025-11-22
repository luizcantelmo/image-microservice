# Script para corrigir e fazer push para GitHub
# Este script cria o repositório no GitHub e faz o push

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        CORRIGIR E FAZER PUSH PARA GITHUB                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host ""
Write-Host "⚠️  INFORMAÇÕES NECESSÁRIAS:" -ForegroundColor Yellow
Write-Host ""

# Pedir PAT Token
Write-Host "Você precisa de um Token de Acesso Pessoal (PAT) do GitHub." -ForegroundColor Cyan
Write-Host "Acesse: https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host ""

$PAT = Read-Host "Cole seu GitHub PAT Token (será ocultado)" -AsSecureString
$PATPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($PAT))

Write-Host ""
$Username = Read-Host "Seu usuário GitHub (ex: luizcantelmo)"
Write-Host ""
$RepoName = Read-Host "Nome do repositório (ex: image-microservice) [padrão: image-microservice]"
if ([string]::IsNullOrWhiteSpace($RepoName)) {
    $RepoName = "image-microservice"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# Criar repositório no GitHub via API
Write-Host "📦 Criando repositório no GitHub..." -ForegroundColor Cyan

$RepoData = @{
    name        = $RepoName
    description = "Image Processing Microservice for Hostinger VPS - Flask + Gunicorn"
    private     = $false
    auto_init   = $false
} | ConvertTo-Json

try {
    $headers = @{
        "Authorization" = "token $PATPlain"
        "Accept"        = "application/vnd.github+json"
    }

    $response = Invoke-RestMethod `
        -Uri "https://api.github.com/user/repos" `
        -Method POST `
        -Headers $headers `
        -Body $RepoData `
        -ContentType "application/json" `
        -ErrorAction Stop

    Write-Host "✅ Repositório criado com sucesso!" -ForegroundColor Green
    Write-Host "   URL: $($response.html_url)" -ForegroundColor Green
}
catch {
    $errorMsg = $_.Exception.Message
    if ($errorMsg -like "*422*" -or $errorMsg -like "*exists*") {
        Write-Host "⚠️  Repositório já existe no GitHub. Continuando..." -ForegroundColor Yellow
    }
    else {
        Write-Host "❌ Erro ao criar repositório: $errorMsg" -ForegroundColor Red
        Write-Host "💡 Dica: Verifique se o PAT Token é válido." -ForegroundColor Yellow
        Read-Host "Pressione Enter para sair"
        exit 1
    }
}

Write-Host ""
Write-Host "🔄 Configurando remote do Git..." -ForegroundColor Cyan

# Remover remote existente e adicionar novo
try {
    $repoUrl = "https://${Username}:${PATPlain}@github.com/${Username}/${RepoName}.git"
    
    # Remover remote antigo
    git remote remove origin 2>$null | Out-Null
    
    # Adicionar novo remote
    git remote add origin $repoUrl
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Remote configurada!" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Erro ao configurar remote" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Erro: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📤 Fazendo push para GitHub..." -ForegroundColor Cyan

try {
    $output = git push -u origin main 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Push realizado com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "🎉 SUCESSO!" -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "Seu repositório está em:" -ForegroundColor Cyan
        Write-Host "https://github.com/${Username}/${RepoName}" -ForegroundColor Green
        Write-Host ""
        Write-Host "Próximo passo: Faça clone no VPS Hostinger" -ForegroundColor Yellow
        Write-Host "git clone https://github.com/${Username}/${RepoName}.git" -ForegroundColor Yellow
        Write-Host ""
    }
    else {
        Write-Host "❌ Erro no push:" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Erro: $_" -ForegroundColor Red
    exit 1
}

# Limpar dados sensíveis
$PATPlain = ""
$repoUrl = ""
