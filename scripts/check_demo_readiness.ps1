# Read-only live-service preflight. No token, job creation, login or paid call.
param(
    [string]$BaseUrl = 'http://127.0.0.1:8080',
    [ValidateSet('slide', 'motion', 'hybrid', 'all')][string]$Scope = 'all'
)
$ErrorActionPreference = 'Stop'
$base = $BaseUrl.TrimEnd('/')
$findings = [System.Collections.Generic.List[string]]::new()
try {
    $health = Invoke-RestMethod -Uri "$base/api/health" -TimeoutSec 8
    if ($health.ok -ne $true) { $findings.Add('api_health_failed') }
    $harnesses = Invoke-RestMethod -Uri "$base/api/jobs/options/harnesses" -TimeoutSec 8
    $production = Invoke-RestMethod -Uri "$base/api/jobs/options/production" -TimeoutSec 8
} catch {
    $report = [pscustomobject]@{
        status = 'SERVICE_UNREACHABLE'
        baseUrl = $base
        findings = @('public_health_or_options_unavailable')
        scope = 'Read-only reachability and compatibility preflight; not a production E2E or release approval'
    }
    $report | ConvertTo-Json -Depth 6
    exit 1
}
$classic = $harnesses | Where-Object { $_.id -eq 'classic-slide' } | Select-Object -First 1
$motion = $harnesses | Where-Object { $_.id -eq 'astra-motion' } | Select-Object -First 1
$hybrid = $harnesses | Where-Object { $_.id -eq 'hybrid-story' } | Select-Object -First 1
if ($Scope -in @('slide', 'all') -and (-not $classic -or -not $classic.compatible -or -not $classic.public)) { $findings.Add('classic_slide_unavailable') }
if ($Scope -in @('motion', 'all') -and (-not $motion -or -not $motion.compatible -or -not $motion.public)) { $findings.Add('astra_motion_unavailable') }
if ($Scope -in @('motion', 'all') -and $production.motionProductionAvailable -eq $false) { $findings.Add('motion_scene_direction_unavailable') }
if ($Scope -in @('hybrid', 'all') -and (-not $hybrid -or -not $hybrid.compatible)) { $findings.Add('hybrid_runner_incompatible') }
$report = [pscustomobject]@{
    status = if ($findings.Count) { 'PREFLIGHT_BLOCKED' } else { 'PREFLIGHT_ONLY_E2E_REQUIRED' }
    baseUrl = $base
    scopeRequested = $Scope
    health = $health.ok
    harnesses = @(
        [pscustomobject]@{ id='classic-slide'; version=$classic.version; compatible=$classic.compatible; public=$classic.public },
        [pscustomobject]@{ id='astra-motion'; version=$motion.version; compatible=$motion.compatible; public=$motion.public },
        [pscustomobject]@{ id='hybrid-story'; version=$hybrid.version; compatible=$hybrid.compatible; public=$hybrid.public; error=$hybrid.error }
    )
    providerModes = [pscustomobject]@{ image=$production.imageProvider; motionImage=$production.motionImageProvider; voice=$production.voiceProvider; motionProductionAvailable=$production.motionProductionAvailable }
    findings = @($findings.ToArray())
    unverified = @('authenticated_job_e2e', 'actual_image_generation', 'ten_and_thirty_minute_reliability', 'human_design_and_story_review')
    scope = 'Read-only reachability and compatibility preflight; not a production E2E or release approval'
}
$report | ConvertTo-Json -Depth 6
if ($findings.Count) { exit 2 }
