## LabMind AI - Full Backend Bootstrap Script

Set-Location "d:\New folder\ai-backend"

$ErrorActionPreference = "Continue"
$results = @()

function Log($msg) {
    Write-Host "[BOOTSTRAP] $msg" -ForegroundColor Cyan
}

function Pass($msg) {
    $script:results += "[PASS] $msg"
    Write-Host "[PASS] $msg" -ForegroundColor Green
}

function Fail($msg) {
    $script:results += "[FAIL] $msg"
    Write-Host "[FAIL] $msg" -ForegroundColor Red
}

# -- Step 1: Docker compose up --
Log "Step 1: docker compose up -d"
docker compose up -d 2>&1 | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -eq 0) {
    Pass "docker compose up -d"
}
else {
    Fail "docker compose up -d (exit $LASTEXITCODE)"
}

Start-Sleep -Seconds 5

# -- Step 2: Verify containers --
Log "Step 2: Checking containers"
$containers = docker ps --format "{{.Names}} {{.Status}}" 2>&1
Write-Host $containers

if ($containers -match "labmind_postgres.*Up") {
    Pass "PostgreSQL container running"
}
else {
    Fail "PostgreSQL container NOT running"
}

if ($containers -match "labmind_redis.*Up") {
    Pass "Redis container running"
}
else {
    Fail "Redis container NOT running"
}

# -- Step 3: Database connectivity --
Log "Step 3: Testing PostgreSQL connectivity"
$dbCheck = docker exec labmind_postgres pg_isready -U labmind -d labmind_db 2>&1
Write-Host $dbCheck

if ($dbCheck -match "accepting") {
    Pass "PostgreSQL accepting connections"
}
else {
    Fail "PostgreSQL connectivity check failed"
}

# -- Step 4: Activate venv and run alembic --
Log "Step 4: Activating venv and running alembic upgrade head"
& ".\.venv\Scripts\Activate.ps1"
alembic upgrade head 2>&1 | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -eq 0) {
    Pass "alembic upgrade head"
}
else {
    Fail "alembic upgrade head (exit $LASTEXITCODE)"
}

# -- Step 5: Start backend in background --
Log "Step 5: Starting uvicorn in background"
$uvicornJob = Start-Job -ScriptBlock {
    Set-Location "d:\New folder\ai-backend"
    & ".\.venv\Scripts\Activate.ps1"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1
}
$jobId = $uvicornJob.Id
Write-Host "Uvicorn job started with ID: $jobId"
Start-Sleep -Seconds 8

# -- Step 6: Health check --
Log "Step 6: Checking /health"
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 10
    Write-Host ($health | ConvertTo-Json)
    $hStatus = $health.status
    Pass "/health returned status: $hStatus"
}
catch {
    $errMsg = $_.Exception.Message
    Fail "/health failed: $errMsg"
}

# -- Step 7: Docs check --
Log "Step 7: Checking /docs"
try {
    $docs = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 10 -UseBasicParsing
    $docsCode = $docs.StatusCode
    if ($docsCode -eq 200) {
        Pass "/docs returned 200 OK"
    }
    else {
        Fail "/docs returned $docsCode"
    }
}
catch {
    $errMsg = $_.Exception.Message
    Fail "/docs failed: $errMsg"
}

# -- Step 8: Register --
Log "Step 8: POST /api/auth/register"
$regBody = @{
    email     = "testuser@labmind.ai"
    password  = "TestPass123!"
    full_name = "Test User"
} | ConvertTo-Json

try {
    $reg = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/register" -Method POST -Body $regBody -ContentType "application/json" -TimeoutSec 10
    Write-Host ($reg | ConvertTo-Json)
    Pass "POST /api/auth/register - user created"
}
catch {
    $respStream = $_.Exception.Response
    $statusVal = 0
    if ($null -ne $respStream) {
        $statusVal = [int]$respStream.StatusCode
    }
    if ($statusVal -eq 409) {
        Pass "POST /api/auth/register - user already exists (409, expected on re-run)"
    }
    else {
        $errMsg = $_.Exception.Message
        Fail "POST /api/auth/register failed: $errMsg"
    }
}

# -- Step 9: Login --
Log "Step 9: POST /api/auth/token"
$loginBody = @{
    email    = "testuser@labmind.ai"
    password = "TestPass123!"
} | ConvertTo-Json

try {
    $token = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/token" -Method POST -Body $loginBody -ContentType "application/json" -TimeoutSec 10
    Write-Host ($token | ConvertTo-Json)
    Pass "POST /api/auth/token - JWT received"
}
catch {
    $errMsg = $_.Exception.Message
    Fail "POST /api/auth/token failed: $errMsg"
}

# -- Final Report --
Write-Host ""
Write-Host "=======================================" -ForegroundColor Yellow
Write-Host "  BOOTSTRAP FINAL REPORT" -ForegroundColor Yellow
Write-Host "=======================================" -ForegroundColor Yellow
foreach ($r in $results) {
    Write-Host $r
}
Write-Host "=======================================" -ForegroundColor Yellow

Write-Host ""
Write-Host "Uvicorn is running in background job ID: $jobId" -ForegroundColor Cyan
$stopCmd = "Stop-Job " + $jobId
$removeCmd = "Remove-Job " + $jobId
Write-Host "To stop it later: $stopCmd then $removeCmd" -ForegroundColor Cyan
