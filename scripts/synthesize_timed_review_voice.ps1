param([Parameter(Mandatory=$true)][string]$InputPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
Add-Type -ReferencedAssemblies System.Speech -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Speech.Synthesis;
using System.Speech.AudioFormat;
public class ReviewWord {
    public int start;
    public int length;
    public double seconds;
    public string text;
}
public static class TimedReviewSpeech {
    public static List<ReviewWord> Speak(string text, string output) {
        var words = new List<ReviewWord>();
        using (var voice = new SpeechSynthesizer()) {
            voice.SelectVoice("Microsoft Heami Desktop");
            voice.Rate = -1;
            voice.SpeakProgress += (sender, e) => words.Add(new ReviewWord {
                start=e.CharacterPosition, length=e.CharacterCount,
                seconds=e.AudioPosition.TotalSeconds, text=e.Text
            });
            voice.SetOutputToWaveFile(output, new SpeechAudioFormatInfo(16000, AudioBitsPerSample.Sixteen, AudioChannel.Mono));
            voice.Speak(text);
        }
        return words;
    }
}
'@
$manifest = Get-Content -LiteralPath $InputPath -Raw -Encoding UTF8 | ConvertFrom-Json
$base = Split-Path -Parent (Resolve-Path -LiteralPath $InputPath).Path
foreach ($line in $manifest) {
    if ($line.id -notmatch '^scene-[0-9]{3}$') { throw 'Invalid scene ID' }
    $output = Join-Path $base ($line.id + '.wav')
    $timing = Join-Path $base ($line.id + '.words.json')
    if ((Test-Path -LiteralPath $output) -or (Test-Path -LiteralPath $timing)) { throw 'Preserve existing evidence' }
    $words = [TimedReviewSpeech]::Speak([string]$line.narration, $output)
    if ($words.Count -eq 0) { throw 'Voice did not supply word timings' }
    $json = ConvertTo-Json -InputObject @($words) -Depth 5
    [System.IO.File]::WriteAllText($timing,$json,(New-Object System.Text.UTF8Encoding($false)))
}
