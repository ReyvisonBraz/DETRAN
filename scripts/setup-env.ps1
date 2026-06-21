# setup-env.ps1 — Le .env.secrets e distribui para os servicos
# Uso: pwsh scripts/setup-env.ps1
# Nao commite os arquivos .env gerados (estao no .gitignore)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SecretsFile = Join-Path $Root ".env.secrets"

if (-not (Test-Path $SecretsFile)) {
    Write-Host "ERRO: .env.secrets nao encontrado em $Root" -ForegroundColor Red
    Write-Host "Crie o arquivo com base no .env.secrets.example e preencha os valores." -ForegroundColor Yellow
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
            # Remove aspas duplas se presentes
            if ($val.StartsWith('"') -and $val.EndsWith('"')) {
                $val = $val.Substring(1, $val.Length - 2)
            }
            $envVars[$key] = $val
        }
    }
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
Write-Host "[OK] backend/.env gerado ($backendPath)" -ForegroundColor Green

# ── 2. Scraper .env ───────────────────────────────────────────────────────────
$scraperEnv = "TWOCAPTCHA_API_KEY=$($envVars['TWOCAPTCHA_API_KEY'])`n"
$scraperPath = Join-Path $Root "detran-pa-consultas\.env"
Set-Content -LiteralPath $scraperPath -Value $scraperEnv -Encoding UTF8
Write-Host "[OK] detran-pa-consultas/.env gerado ($scraperPath)" -ForegroundColor Green

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
Write-Host "[OK] frontend/.env.local gerado ($frontendPath)" -ForegroundColor Green

Write-Host ""
Write-Host "Concluido! Arquivos .env gerados a partir de .env.secrets" -ForegroundColor Cyan
Write-Host "Nunca commite .env.secrets ou arquivos .env - estao no .gitignore" -ForegroundColor Yellow