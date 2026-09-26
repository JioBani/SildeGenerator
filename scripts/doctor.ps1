param([switch]$SkipSmoke)
$ErrorActionPreference = "Stop"
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..")); $runtimeDir=Join-Path $projectRoot ".runtime"; $envFile=Join-Path $runtimeDir "compose.env"
$pass=0; $warn=0; $fail=0
function Pass($m){$script:pass++;Write-Host "PASS $m"} function Warn($m){$script:warn++;Write-Warning $m} function Fail($m){$script:fail++;Write-Host "FAIL $m"}
Set-Location $projectRoot
try { docker compose --env-file $envFile ps --format json | Out-Null; Pass "Compose services" } catch { Fail "Compose services" }
try {
  $expectedMode = ([regex]::Matches((Get-Content -Raw $envFile), '(?m)^RUNNER_MODE=(.+)$') | Select-Object -Last 1).Groups[1].Value.Trim()
  $expectedProvider = ([regex]::Matches((Get-Content -Raw $envFile), '(?m)^IMAGE_PROVIDER=(.+)$') | Select-Object -Last 1).Groups[1].Value.Trim()
  $actualJson = & docker compose --env-file $envFile exec -T runner python -c "import json; from app.config import settings; print(json.dumps({'mode':settings.runner_mode,'imageProvider':settings.image_provider}))"
  if ($LASTEXITCODE -ne 0) { throw "runner configuration unavailable" }
  $actual = $actualJson | ConvertFrom-Json
  $workerJson = & docker compose --env-file $envFile exec -T worker node -e "const c=require('/app/dist/config/app-config.js').config; console.log(JSON.stringify({mode:c.runnerMode,imageProvider:c.imageProvider}))"
  if ($LASTEXITCODE -ne 0) { throw "worker configuration unavailable" }
  $worker = $workerJson | ConvertFrom-Json
  if ($actual.mode -ne $expectedMode -or $actual.imageProvider -ne $expectedProvider) {
    throw "expected $expectedMode/$expectedProvider, running $($actual.mode)/$($actual.imageProvider)"
  }
  if ($worker.mode -ne $expectedMode -or $worker.imageProvider -ne $expectedProvider) {
    throw "expected $expectedMode/$expectedProvider, worker $($worker.mode)/$($worker.imageProvider)"
  }
  if ($expectedMode -eq "live" -and ($actual.mode -eq "mock" -or $actual.imageProvider -eq "mock")) { throw "mock production is forbidden in live mode" }
  Pass "Running runner configuration"
} catch { Fail "Running runner configuration: $($_.Exception.Message)" }
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3000/api/health).StatusCode | Out-Null; Pass "API health" } catch { Fail "API health" }
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/health).StatusCode | Out-Null; Pass "Web same-origin health" } catch { Fail "Web same-origin health" }
$state=Get-Content -Raw (Join-Path $runtimeDir "bootstrap-state.json") | ConvertFrom-Json
if ($state.mode -eq "live") {
  try {
    $containerId = (& docker compose --env-file $envFile --profile live ps -q image-oauth 2>$null).Trim()
    if (-not $containerId) { throw "image-oauth container is not running" }
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker compose --env-file $envFile exec -T runner python -c "import json,urllib.request; data=json.load(urllib.request.urlopen('http://image-oauth:10531/v1/models',timeout=5)); assert isinstance(data.get('data'),list)" *> $null
    $probeExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    if ($probeExitCode -ne 0) { throw "model discovery failed" }
    Pass "Project Codex OAuth bridge"
  } catch { Fail "Project Codex OAuth bridge: $($_.Exception.Message)" }
}
if (-not $SkipSmoke -and $state.mode -eq "mock") {
  try {
    $tokenFile = Join-Path $runtimeDir "access-token.txt"
    if (Test-Path $tokenFile) { $token=(Get-Content -Raw $tokenFile).Trim() }
    else { $token=((& docker compose --env-file $envFile --profile ops run --rm keyctl issue doctor-smoke 2>$null | Select-Object -Last 1).Trim()) }
    if (-not $token) { throw "access token issue failed" }
    $headers=@{Authorization="Bearer $token"}
    $job=Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/api/jobs -Headers $headers -ContentType application/json -Body (@{scenario="작은 질문이 내일을 만듭니다."}|ConvertTo-Json)
    $deadline=(Get-Date).AddMinutes(5); do { Start-Sleep 2; $status=Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/jobs/$($job.id)" -Headers $headers } while($status.status -notin @("completed","failed") -and (Get-Date) -lt $deadline)
    if($status.status -ne "completed"){throw "mock job $($status.status)"}; $video=Join-Path $runtimeDir "doctor-smoke.mp4"; Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/api/jobs/$($job.id)/video" -Headers $headers -OutFile $video
    docker compose --env-file $envFile exec -T runner ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of json "/data/jobs/$($job.id)/output/video.mp4" | Out-Null
    if($LASTEXITCODE -ne 0){throw "ffprobe failed"}; Remove-Item -Force $video; Pass "Mock create/download/ffprobe"
  } catch { Fail "Mock create/download/ffprobe: $($_.Exception.Message)" }
} else { Warn "Mock smoke skipped" }
Write-Host "PASS $pass / WARN $warn / FAIL $fail"; Write-Host "Web: http://localhost:8080"; Write-Host "Mode: $($state.mode)"; Write-Host "Ready for local use: $(if($fail -eq 0){'yes'}else{'no'})"; if($fail){exit 1}
