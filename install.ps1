# Install the AI-engineer agent pack on Windows (run from the unzipped ai-engineer-agents folder).
#   .\install.ps1              -> Claude Code  (%USERPROFILE%\.claude\agents, \skills)
#   .\install.ps1 -OpenCode    -> OpenCode     (%USERPROFILE%\.config\opencode\agents, \skills)
# Existing files with the same name are backed up to *.bak-<timestamp> before being replaced.
param([switch]$OpenCode)
$ErrorActionPreference = 'Stop'
$src = if ($OpenCode) { Join-Path $PSScriptRoot 'opencode' } else { Join-Path $PSScriptRoot 'claude' }
$dst = if ($OpenCode) { Join-Path $env:USERPROFILE '.config\opencode' } else { Join-Path $env:USERPROFILE '.claude' }
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
foreach ($kind in 'agents', 'skills') {
    $from = Join-Path $src $kind
    if (-not (Test-Path $from)) { continue }
    $to = Join-Path $dst $kind
    New-Item -ItemType Directory -Force -Path $to | Out-Null
    Get-ChildItem -LiteralPath $from | ForEach-Object {
        $target = Join-Path $to $_.Name
        if (Test-Path -LiteralPath $target) { Move-Item -LiteralPath $target -Destination "$target.bak-$ts" }
        Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse
        Write-Host "installed $kind\$($_.Name)"
    }
}
if ($OpenCode) { Write-Host "Now merge opencode\opencode-mcp.jsonc into $dst\opencode.jsonc (the mcp block)." }
Write-Host 'Done. Restart Claude Code / OpenCode (or reload) to pick up new agents.'
