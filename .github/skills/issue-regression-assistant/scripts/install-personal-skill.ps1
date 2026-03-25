$ErrorActionPreference = 'Stop'

$sourceDir = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $HOME '.copilot\skills\issue-regression-assistant'

if (Test-Path $targetDir) {
    Remove-Item -Path $targetDir -Recurse -Force
}

New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
Copy-Item -Path (Join-Path $sourceDir '*') -Destination $targetDir -Recurse -Force

Write-Host "Installed skill to $targetDir"