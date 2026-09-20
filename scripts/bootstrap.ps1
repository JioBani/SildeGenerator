param([switch]$Check, [switch]$Reconfigure, [switch]$Mock)
$ErrorActionPreference = "Stop"
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$runtimeDir = Join-Path $projectRoot ".runtime"
$composeEnv = Join-Path $runtimeDir "compose.env"
$stateFile = Join-Path $runtimeDir "bootstrap-state.json"
$marker = Join-Path $runtimeDir "setup-complete"

function Assert-Prerequisites {
  docker version --format '{{.Server.Version}}' | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Docker daemon에 연결할 수 없습니다." }
  docker compose version | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Docker Compose v2가 필요합니다." }
  if (-not [Environment]::Is64BitOperatingSystem) { throw "64-bit 운영체제가 필요합니다." }
  $ram = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
  if ($ram -lt 6GB) { Write-Warning "RAM이 6GB 미만입니다. 8GB 이상을 권장합니다." }
  foreach ($port in 8080,8090,3000) { if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { Write-Warning "포트 $port 가 사용 중입니다. 설정 웹에서 대체 포트를 지정하세요." } }
  Write-Host "PASS Docker/Compose/architecture/runtime path checks"
}
function Compose([string[]]$arguments) { & docker compose --env-file $composeEnv @arguments; if ($LASTEXITCODE -ne 0) { throw "docker compose 실패: $($arguments -join ' ')" } }
function Initialize-Runtime {
  New-Item -ItemType Directory -Force $runtimeDir, (Join-Path $runtimeDir "codex") | Out-Null
  if (-not (Test-Path $composeEnv)) {
    $passwordBytes = New-Object byte[] 32
    $passwordGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $passwordGenerator.GetBytes($passwordBytes) } finally { $passwordGenerator.Dispose() }
    $password = [Convert]::ToBase64String($passwordBytes).TrimEnd('=').Replace('+','_').Replace('/','-')
    [IO.File]::WriteAllText($composeEnv, "POSTGRES_PASSWORD=$password`nSETUP_PORT=8090`n", [Text.UTF8Encoding]::new($false))
  }
  $runnerFile = Join-Path $runtimeDir "runner.env"
  if (-not (Test-Path $runnerFile)) { [IO.File]::WriteAllText($runnerFile, "# Configured by the loopback setup portal.`n", [Text.UTF8Encoding]::new($false)) }
}
function Merge-User-Config {
  $userFile = Join-Path $runtimeDir "compose.user.env"
  if (-not (Test-Path $userFile)) { return }
  $base = Get-Content $composeEnv | Where-Object { $_ -and $_ -notmatch '^(RUNNER_MODE|IMAGE_PROVIDER|VOICE_PROVIDER|WEB_PORT|IMAGE_TASK_CONCURRENCY|VOICE_TASK_CONCURRENCY|VIDEO_FPS|JOB_RETENTION_HOURS|ELEVENLABS_CONFIGURED|MICROSOFT_EDGE_|ELEVENLABS_VOICE_|ELEVENLABS_MODEL_ID)=' }
  $next = @($base) + @(Get-Content $userFile)
  $temp = "$composeEnv.tmp"
  [IO.File]::WriteAllLines($temp, $next, [Text.UTF8Encoding]::new($false)); Move-Item -Force -LiteralPath $temp -Destination $composeEnv
}

Set-Location $projectRoot
Assert-Prerequisites
if ($Check) { docker compose config --quiet; exit $LASTEXITCODE }
Initialize-Runtime
if ($Reconfigure) {
  $backupDir = Join-Path $runtimeDir ("backups/" + [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ"))
  New-Item -ItemType Directory -Force $backupDir | Out-Null
  foreach ($fileName in "compose.env","compose.user.env","runner.env","bootstrap-state.json") {
    $sourceFile = Join-Path $runtimeDir $fileName
    if (Test-Path $sourceFile) { Copy-Item -LiteralPath $sourceFile -Destination (Join-Path $backupDir $fileName) }
  }
  Remove-Item -Force -ErrorAction SilentlyContinue $marker
}
if ($Mock -and -not (Test-Path $marker)) {
  $payload = @{ mode="mock"; voiceProvider="mock"; webPort=8080; imageConcurrency=8; voiceConcurrency=2; fps=24; retentionHours=720; edgeVoice="ko-KR-InJoonNeural"; edgeRate="-30%"; edgePitch="+0Hz"; edgeVolume="+0%" } | ConvertTo-Json
  Compose @("--profile","setup","up","-d","--build","setup","setup-proxy")
  $ready = $false; 1..10 | ForEach-Object { if (-not $ready) { try { Invoke-RestMethod -Uri "http://127.0.0.1:8090/api/setup/status" | Out-Null; $ready=$true } catch { Start-Sleep -Seconds 1 } } }
  if (-not $ready) { throw "설정 웹이 준비되지 않았습니다." }
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8090/api/setup/save" -ContentType "application/json" -Body $payload | Out-Null
}
if (-not (Test-Path $marker)) {
  Compose @("--profile","setup","up","-d","--build","setup","setup-proxy")
  Write-Host "설정 웹: http://127.0.0.1:8090"
  while (-not (Test-Path $marker)) { Write-Host "설정 완료를 기다리는 중..."; Start-Sleep -Seconds 5 }
}
Compose @("--profile","setup","stop","setup-proxy","setup")
Merge-User-Config
$state = Get-Content -Raw $stateFile | ConvertFrom-Json
$sourceRevision = $env:SOURCE_REVISION
if (-not $sourceRevision) {
  $sourceRevision = (& git rev-parse HEAD 2>$null).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $sourceRevision) { $sourceRevision = "working-tree" }
}
$env:SOURCE_REVISION = $sourceRevision
if ($state.mode -eq "live") {
  if (-not (Get-Command codex -ErrorAction SilentlyContinue)) { throw "Live 모드에는 Codex CLI가 필요합니다. https://developers.openai.com/codex/cli 를 확인하세요." }
  $slidegenCodexHome = (Resolve-Path (Join-Path $runtimeDir "codex")).Path
  $previousCodexHome = $env:CODEX_HOME; $env:CODEX_HOME = $slidegenCodexHome
  try {
    codex login status | Out-Null
    if ($LASTEXITCODE -ne 0) { codex login -c 'cli_auth_credentials_store="file"'; if ($LASTEXITCODE -ne 0) { throw "Codex 로그인이 완료되지 않았습니다." } }
  } finally { if ($null -eq $previousCodexHome) { Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue } else { $env:CODEX_HOME=$previousCodexHome } }
  $state.codexLogin = "confirmed"; $state | ConvertTo-Json | Set-Content -Encoding UTF8 $stateFile
  Compose @("--profile","live","build")
  $projectName = ((Get-Content $composeEnv | Select-String '^COMPOSE_PROJECT_NAME=' | Select-Object -Last 1).Line -replace '^COMPOSE_PROJECT_NAME=','')
  if (-not $projectName) { $projectName = "slidegenerator" }
  $runnerImage = "${projectName}-runner:$sourceRevision"
  $env:RUNNER_IMAGE_DIGEST = (& docker image inspect --format '{{.Id}}' $runnerImage).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $env:RUNNER_IMAGE_DIGEST) { throw "runner image digest lookup failed" }
  Compose @("--profile","live","up","-d")
} else {
  Compose @("build")
  $projectName = ((Get-Content $composeEnv | Select-String '^COMPOSE_PROJECT_NAME=' | Select-Object -Last 1).Line -replace '^COMPOSE_PROJECT_NAME=','')
  if (-not $projectName) { $projectName = "slidegenerator" }
  $runnerImage = "${projectName}-runner:$sourceRevision"
  $env:RUNNER_IMAGE_DIGEST = (& docker image inspect --format '{{.Id}}' $runnerImage).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $env:RUNNER_IMAGE_DIGEST) { throw "runner image digest lookup failed" }
  Compose @("up","-d")
}
$tokenFile = Join-Path $runtimeDir "access-token.txt"
if (-not (Test-Path $tokenFile)) {
  $tokenOutput = & docker compose --env-file $composeEnv --profile ops run --rm keyctl issue local-admin 2>$null
  $token = ($tokenOutput | Select-String -Pattern '^sg_[A-Za-z0-9_-]+$' | Select-Object -Last 1).Line
  if (-not $token) { throw "접근 토큰 발급에 실패했습니다." }
  [IO.File]::WriteAllText($tokenFile, "$token`n", [Text.UTF8Encoding]::new($false))
}
& (Join-Path $PSScriptRoot "doctor.ps1")
Write-Host "Web: http://localhost:8080"
Write-Host "Access token: .runtime/access-token.txt (scripts/show-token.ps1로 확인)"
