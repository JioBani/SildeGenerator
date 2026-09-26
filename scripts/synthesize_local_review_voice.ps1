param([Parameter(Mandatory=$true)][string]$InputPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$manifest = Get-Content -LiteralPath $InputPath -Raw -Encoding UTF8 | ConvertFrom-Json
$base = Split-Path -Parent (Resolve-Path -LiteralPath $InputPath).Path
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $speech.SelectVoice('Microsoft Heami Desktop')
    $speech.Rate = -1
    foreach ($line in $manifest) {
        if ($line.id -notmatch '^scene-[0-9]{3}$') { throw 'Invalid scene ID' }
        $output = Join-Path $base ($line.id + '.wav')
        if (Test-Path -LiteralPath $output) { throw 'Preserve existing audio' }
        $speech.SetOutputToWaveFile($output)
        $speech.Speak([string]$line.narration)
        $speech.SetOutputToNull()
    }
} finally { $speech.Dispose() }
