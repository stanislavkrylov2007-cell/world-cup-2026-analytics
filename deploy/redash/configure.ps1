$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (Test-Path -LiteralPath '.env') { exit 0 }
function New-Secret { $b = New-Object byte[] 32; $rng = [Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($b); $rng.Dispose(); return ([BitConverter]::ToString($b)).Replace('-','').ToLowerInvariant() }
$metadataSecret = New-Secret
$content = @(
    'POSTGRES_USER=redash', 'POSTGRES_DB=redash', "POSTGRES_PASSWORD=$metadataSecret",
    "REDASH_DATABASE_URL=postgresql://redash:$metadataSecret@metadata:5432/redash",
    'REDASH_REDIS_URL=redis://redis:6379/0', "REDASH_SECRET_KEY=$(New-Secret)",
    "REDASH_COOKIE_SECRET=$(New-Secret)", 'REDASH_HOST=http://localhost:5000',
    'REDASH_ENFORCE_CSRF=true', 'REDASH_LOG_LEVEL=INFO',
    "ANALYTICS_ADMIN_PASSWORD=$(New-Secret)", "ANALYTICS_READER_PASSWORD=$(New-Secret)"
)
[IO.File]::WriteAllLines((Join-Path $PSScriptRoot '.env'), $content, (New-Object Text.UTF8Encoding($false)))
