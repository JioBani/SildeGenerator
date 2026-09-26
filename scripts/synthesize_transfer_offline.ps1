#Requires -Version 7.0
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$root = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $root) { throw 'Preserve prior narration output' }
New-Item -ItemType Directory -Path $root | Out-Null
$lines = @(
    'AI가 이미지를 만들 때는 수많은 숫자를 서로 곱하고 더하는 계산을 반복합니다.',
    '하나씩 계산하면 오래 걸리지만,',
    'GPU는 이 계산을 수천 갈래로 나누어 동시에 처리합니다.'
)
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$rows = @()
$cursor = 0.0
try {
    $speaker.SelectVoice('Microsoft Heami Desktop')
    $speaker.Rate = 0
    for ($i=0; $i -lt $lines.Count; $i++) {
        $file = Join-Path $root ('utterance-{0}.wav' -f $i)
        $speaker.SetOutputToWaveFile($file)
        $speaker.Speak($lines[$i])
        $speaker.SetOutputToNull()
        $duration = [double](& ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $file)
        if ($LASTEXITCODE -ne 0 -or $duration -le 0) { throw 'Invalid local voice output' }
        $rows += [pscustomobject]@{ text=$lines[$i]; file=[IO.Path]::GetFileName($file); start=$cursor; end=$cursor+$duration; duration=$duration }
        $cursor += $duration + 0.3
    }
} finally { $speaker.Dispose() }
$report = [pscustomobject]@{provider='Windows System.Speech offline';voice='Microsoft Heami Desktop';paid_calls=0;duration=$cursor;utterances=$rows;status='EXPERIMENTAL_NARRATION_NOT_HUMAN_APPROVED'}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root 'narration.json') -Encoding utf8
$report | ConvertTo-Json -Depth 5
