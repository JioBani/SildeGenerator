$tokenFile = Join-Path ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))) ".runtime\access-token.txt"
if (-not (Test-Path $tokenFile)) { throw "bootstrap을 먼저 실행하세요." }
Get-Content -Raw $tokenFile
