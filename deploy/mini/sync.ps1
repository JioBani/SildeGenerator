param(
  [string]$HostName = "mini"
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$token = [Guid]::NewGuid().ToString("N")
$archive = Join-Path ([System.IO.Path]::GetTempPath()) "slidegen-source-$token.tar.gz"
$remoteArchive = "/tmp/slidegen-source-$token.tar.gz"

try {
  & tar.exe -C $root -czf $archive `
    --exclude=node_modules --exclude=dist --exclude=.git --exclude=.env `
    --exclude=.codex-runtime --exclude=.runtime --exclude=private --exclude=data --exclude=__pycache__ `
    docker-compose.yml README.md AGENTS.md .env.example .github server video-generator web infra deploy setup scripts harnesses
  if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE" }

  & scp.exe $archive "${HostName}:$remoteArchive"
  if ($LASTEXITCODE -ne 0) { throw "scp failed with exit code $LASTEXITCODE" }

  & ssh.exe $HostName "mkdir -p ~/slidegen && tar -xzf $remoteArchive -C ~/slidegen && rm -f $remoteArchive"
  if ($LASTEXITCODE -ne 0) { throw "remote extraction failed with exit code $LASTEXITCODE" }

  Write-Output "synced source to ${HostName}:~/slidegen"
  Write-Output "server/.env, .runtime, and .codex-runtime/auth.json were intentionally not copied"
}
finally {
  if ([System.IO.File]::Exists($archive)) {
    [System.IO.File]::Delete($archive)
  }
}
