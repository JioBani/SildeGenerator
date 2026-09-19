param([switch]$SkipSmoke)
$ErrorActionPreference = "Stop"
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..")); $runtimeDir=Join-Path $projectRoot ".runtime"; $envFile=Join-Path $runtimeDir "compose.env"
$pass=0; $warn=0; $fail=0
function Pass($m){$script:pass++;Write-Host "PASS $m"} function Warn($m){$script:warn++;Write-Warning $m} function Fail($m){$script:fail++;Write-Host "FAIL $m"}
Set-Location $projectRoot
try { docker compose --env-file $envFile ps --format json | Out-Null; Pass "Compose services" } catch { Fail "Compose services" }
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3000/api/health).StatusCode | Out-Null; Pass "API health" } catch { Fail "API health" }
try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/api/health).StatusCode | Out-Null; Pass "Web same-origin health" } catch { Fail "Web same-origin health" }
$state=Get-Content -Raw (Join-Path $runtimeDir "bootstrap-state.json") | ConvertFrom-Json
if (-not $SkipSmoke -and $state.mode -eq "mock") {
  try {
    $token=(Get-Content -Raw (Join-Path $runtimeDir "access-token.txt")).Trim(); $headers=@{Authorization="Bearer $token"}
    $job=Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/api/jobs -Headers $headers -ContentType application/json -Body (@{scenario="작은 질문이 내일을 만듭니다."}|ConvertTo-Json)
    $deadline=(Get-Date).AddMinutes(5); do { Start-Sleep 2; $status=Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/jobs/$($job.id)" -Headers $headers } while($status.status -notin @("completed","failed") -and (Get-Date) -lt $deadline)
    if($status.status -ne "completed"){throw "mock job $($status.status)"}; $video=Join-Path $runtimeDir "doctor-smoke.mp4"; Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/api/jobs/$($job.id)/video" -Headers $headers -OutFile $video
    docker compose --env-file $envFile exec -T runner ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of json "/data/jobs/$($job.id)/output/video.mp4" | Out-Null
    if($LASTEXITCODE -ne 0){throw "ffprobe failed"}; Remove-Item -Force $video; Pass "Mock create/download/ffprobe"
  } catch { Fail "Mock create/download/ffprobe: $($_.Exception.Message)" }
} else { Warn "Mock smoke skipped" }
Write-Host "PASS $pass / WARN $warn / FAIL $fail"; Write-Host "Web: http://localhost:8080"; Write-Host "Mode: $($state.mode)"; Write-Host "Ready for local use: $(if($fail -eq 0){'yes'}else{'no'})"; if($fail){exit 1}
