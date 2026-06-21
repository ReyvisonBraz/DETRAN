# setup-env.ps1 — Le .env.secrets, valida e distribui para os servicos
# Uso: powershell -ExecutionPolicy Bypass -File scripts/setup-env.ps1
# Nao commite os arquivos .env gerados (estao no .gitignore)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SecretsFile = Join-Path $Root ".env.secrets"

if (-not (Test-Path $SecretsFile)) {
    Write-Host "ERRO: .env.secrets nao encontrado em $Root" -ForegroundColor Red
    Write-Host "Copie o template:  copy .env.secrets.example .env.secrets" -ForegroundColor Yellow
    Write-Host "Depois preencha os valores e rode este script novamente." -ForegroundColor Yellow
    exit 1
}

# Parse .env.secrets (ignora comentarios e linhas vazias)
$envVars = @{}
Get-Content $SecretsFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#")) {
        $idx = $line.IndexOf("=")
        if ($idx -gt 0) {
            $key = $line.Substring(0, $idx).Trim()
            $val = $line.Substring($idx + 1).Trim()
            if ($val.StartsWith('"') -and $val.EndsWith('"')) {
                $val = $val.Substring(1, $val.Length - 2)
            }
            $envVars[$key] = $val
        }
    }
}

# ── Validacao ──────────────────────────────────────────────────────────────────
$required = @(
    @{ Name="FIREBASE_PROJECT_ID"; Label="Firebase Project ID"; Service="backend" },
    @{ Name="FIREBASE_CLIENT_EMAIL"; Label="Firebase Client Email"; Service="backend" },
    @{ Name="FIREBASE_PRIVATE_KEY"; Label="Firebase Private Key"; Service="backend" },
    @{ Name="FIREBASE_STORAGE_BUCKET"; Label="Firebase Storage Bucket"; Service="backend" },
    @{ Name="NEXT_PUBLIC_FIREBASE_API_KEY"; Label="Firebase API Key (web)"; Service="frontend" },
    @{ Name="NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN"; Label="Firebase Auth Domain"; Service="frontend" },
    @{ Name="NEXT_PUBLIC_FIREBASE_PROJECT_ID"; Label="Firebase Project ID (web)"; Service="frontend" },
    @{ Name="NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET"; Label="Firebase Storage Bucket (web)"; Service="frontend" },
    @{ Name="NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID"; Label="Firebase Sender ID"; Service="frontend" },
    @{ Name="NEXT_PUBLIC_FIREBASE_APP_ID"; Label="Firebase App ID"; Service="frontend" }
)

$optional = @(
    @{ Name="TWOCAPTCHA_API_KEY"; Label="2Captcha API Key"; Hint="Sem esta key, consultas RENACH vao falhar" }
)

$missing = @()
foreach ($r in $required) {
    $val = $envVars[$r.Name]
    if ([string]::IsNullOrWhiteSpace($val)) {
        $missing += $r
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  VALIDACAO FALHOU - Campos obrigatorios vazios:" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    foreach ($m in $missing) {
        Write-Host "  [ ] $($m.Label) ($($m.Service): $($m.Name))" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Preencha os campos acima no arquivo .env.secrets e rode novamente." -ForegroundColor Cyan
    Write-Host "Arquivo: $SecretsFile" -ForegroundColor Cyan
    exit 1
}

# Avisos para campos opcionais
foreach ($o in $optional) {
    $val = $envVars[$o.Name]
    if ([string]::IsNullOrWhiteSpace($val)) {
        $warnings += "$($o.Label) nao preenchido. $($o.Hint)."
    }
}

# Validacoes especificas de formato
$warnings = @()

if ($envVars["FIREBASE_PRIVATE_KEY"] -notmatch "BEGIN PRIVATE KEY") {
    $warnings += "FIREBASE_PRIVATE_KEY parece invalida (nao contem 'BEGIN PRIVATE KEY'). Copie a chave inteira do JSON."
}

if ($envVars["FIREBASE_CLIENT_EMAIL"] -notmatch "@.*\.iam\.gserviceaccount\.com$") {
    $warnings += "FIREBASE_CLIENT_EMAIL parece invalido (deve ser formato xxx@projeto.iam.gserviceaccount.com)."
}

if ($envVars["FIREBASE_STORAGE_BUCKET"] -notmatch "firebasestorage\.app$" -and $envVars["FIREBASE_STORAGE_BUCKET"] -notmatch "appspot\.com$") {
    $warnings += "FIREBASE_STORAGE_BUCKET parece invalido (deve ser projeto.firebasestorage.app ou projeto.appspot.com)."
}

if ($envVars["NEXT_PUBLIC_API_URL"] -notmatch "^https?://") {
    $warnings += "NEXT_PUBLIC_API_URL parece invalido (deve comecar com http:// ou https://). Tem valor padrao 'http://localhost:8000'."
}

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  AVISOS - Valores podem estar incorretos:" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    foreach ($w in $warnings) {
        Write-Host "  [!] $w" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Os arquivos .env serao gerados, mas podem nao funcionar corretamente." -ForegroundColor Yellow
    Write-Host ""
}

function Env-Line($key, $val) {
    if ($val -match "\n") {
        return "$key=`"$val`""
    }
    return "$key=$val"
}

# ── 1. Backend .env ────────────────────────────────────────────────────────────
$backendEnv = @(
    (Env-Line "TWOCAPTCHA_API_KEY" $envVars["TWOCAPTCHA_API_KEY"]),
    (Env-Line "CORS_ORIGINS" $envVars["CORS_ORIGINS"]),
    (Env-Line "MAX_WORKERS" $envVars["MAX_WORKERS"]),
    (Env-Line "FIREBASE_PROJECT_ID" $envVars["FIREBASE_PROJECT_ID"]),
    (Env-Line "FIREBASE_CLIENT_EMAIL" $envVars["FIREBASE_CLIENT_EMAIL"]),
    (Env-Line "FIREBASE_PRIVATE_KEY_ID" $envVars["FIREBASE_PRIVATE_KEY_ID"]),
    (Env-Line "FIREBASE_PRIVATE_KEY" $envVars["FIREBASE_PRIVATE_KEY"]),
    (Env-Line "FIREBASE_STORAGE_BUCKET" $envVars["FIREBASE_STORAGE_BUCKET"]),
    ""
) -join "`n"

$backendPath = Join-Path $Root "backend\.env"
Set-Content -LiteralPath $backendPath -Value $backendEnv -Encoding UTF8
Write-Host "[OK] backend/.env" -ForegroundColor Green

# ── 2. Scraper .env ───────────────────────────────────────────────────────────
$scraperEnv = "TWOCAPTCHA_API_KEY=$($envVars['TWOCAPTCHA_API_KEY'])`n"
$scraperPath = Join-Path $Root "detran-pa-consultas\.env"
Set-Content -LiteralPath $scraperPath -Value $scraperEnv -Encoding UTF8
Write-Host "[OK] detran-pa-consultas/.env" -ForegroundColor Green

# ── 3. Frontend .env.local ────────────────────────────────────────────────────
$frontendEnv = @(
    "NEXT_PUBLIC_API_URL=$($envVars['NEXT_PUBLIC_API_URL'])",
    "",
    "# Firebase",
    (Env-Line "NEXT_PUBLIC_FIREBASE_API_KEY" $envVars["NEXT_PUBLIC_FIREBASE_API_KEY"]),
    (Env-Line "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN" $envVars["NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN"]),
    (Env-Line "NEXT_PUBLIC_FIREBASE_PROJECT_ID" $envVars["NEXT_PUBLIC_FIREBASE_PROJECT_ID"]),
    (Env-Line "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET" $envVars["NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET"]),
    (Env-Line "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID" $envVars["NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID"]),
    (Env-Line "NEXT_PUBLIC_FIREBASE_APP_ID" $envVars["NEXT_PUBLIC_FIREBASE_APP_ID"]),
    ""
) -join "`n"

$frontendPath = Join-Path $Root "frontend\.env.local"
Set-Content -LiteralPath $frontendPath -Value $frontendEnv -Encoding UTF8
Write-Host "[OK] frontend/.env.local" -ForegroundColor Green

# ── Resumo ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup concluido com sucesso!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Arquivos gerados:" -ForegroundColor White
Write-Host "  backend/.env              (7 variaveis)" -ForegroundColor Gray
Write-Host "  detran-pa-consultas/.env   (1 variavel)" -ForegroundColor Gray
Write-Host "  frontend/.env.local       (8 variaveis)" -ForegroundColor Gray
Write-Host ""
Write-Host "Nenhum valor sensivel foi enviado para fora da maquina." -ForegroundColor Green
Write-Host "Configure o Render/Vercel com as mesmas variaveis de ambiente." -ForegroundColor Gray