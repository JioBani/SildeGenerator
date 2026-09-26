#Requires -Version 7.0
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$root = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $root) { throw 'Preserve prior narration output' }
$brief = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\experiments\night-lights-transfer-v1\scene-brief.json') -Raw -Encoding utf8 | ConvertFrom-Json
New-Item -ItemType Directory -Path $root | Out-Null
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$rows = @()
try {
    $speaker.SelectVoice('Microsoft Heami Desktop')
    $speaker.Rate = 0
    foreach ($scene in $brief.scenes) {
        $parts = @($scene.narration -split '(?<=[.!?])\s+' | Where-Object { $_.Trim() })
        $cueRows = @()
        $partFiles = @()
        $cursor = 0.0
        for ($i=0; $i -lt $parts.Count; $i++) {
            $partFile = Join-Path $root ($scene.id + '-part-' + $i + '.wav')
            $speaker.SetOutputToWaveFile($partFile)
            $speaker.Speak($parts[$i])
            $speaker.SetOutputToNull()
            $partDuration = [double](& ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $partFile)
            if ($LASTEXITCODE -ne 0 -or $partDuration -le 0) { throw "Invalid narration part: $($scene.id):$i" }
            $cueRows += [pscustomobject]@{ text=$parts[$i]; start=$cursor; end=$cursor+$partDuration }
            $cursor += $partDuration
            $partFiles += $partFile
        }
        $file = Join-Path $root ($scene.id + '.wav')
        $list = Join-Path $root ($scene.id + '-concat.txt')
        $partFiles | ForEach-Object { "file '$($_.Replace('\','/'))'" } | Set-Content -LiteralPath $list -Encoding utf8
        & ffmpeg -v error -y -f concat -safe 0 -i $list -c:a pcm_s16le $file
        if ($LASTEXITCODE -ne 0) { throw "Could not join narration parts: $($scene.id)" }
        $duration = [double](& ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $file)
        if ($LASTEXITCODE -ne 0 -or $duration -le 0) { throw "Invalid local voice output: $($scene.id)" }
        if ([Math]::Abs($duration - $cursor) -gt 0.08) { throw "Narration cue duration mismatch: $($scene.id)" }
        $rows += [pscustomobject]@{ id=$scene.id; narration=$scene.narration; file=[IO.Path]::GetFileName($file); duration=$duration; subtitle_cues=$cueRows }
    }
} finally { $speaker.Dispose() }
$report = [pscustomobject]@{provider='Windows System.Speech offline';voice='Microsoft Heami Desktop';paid_api_calls=0;scenes=$rows;status='TECHNICAL_NARRATION_UNREVIEWED'}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root 'manifest.json') -Encoding utf8
$report | ConvertTo-Json -Depth 5
