# PowerShell 5.1 or 7. No system settings are changed by this wrapper.
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'setup.py'
$python = $null
foreach ($candidate in @('py', 'python', 'python3')) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue
    if (-not $command) { continue }
    $prefix = @()
    if ($candidate -eq 'py') { $prefix = @('-3') }
    try {
        & $command.Source @prefix -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $python = $command.Source; break }
    } catch { continue }
}
if (-not $python) {
    throw 'Python 3.11+ est requis. Installer Python 3, Docker Desktop et Ollama, puis rouvrir PowerShell. Voir docs/14-installation.md.'
}
& $python @prefix -X utf8 $scriptPath @args
exit $LASTEXITCODE
