[CmdletBinding()]
param([string]$WorkDir = (Join-Path (Split-Path $PSScriptRoot) '.local'), [switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) { throw 'Docker Desktop est requis. Voir docs/22-pilote-marc.md.' }
& $docker.Source info --format '{{.OSType}}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
    if (-not (Test-Path -LiteralPath $desktop)) { throw 'Docker Desktop est introuvable.' }
    Start-Process -FilePath $desktop
    $ready = $false
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Seconds 2
        & $docker.Source info --format '{{.OSType}}' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    }
    if (-not $ready) { throw 'Docker tarde à démarrer. Ouvrez Docker Desktop puis réessayez.' }
}
& (Join-Path $PSScriptRoot 'survie.ps1') --work-dir $WorkDir up
if ($LASTEXITCODE -ne 0) { throw 'Le démarrage a échoué. Consulter le message ci-dessus.' }
if ($OpenBrowser) { Start-Process 'http://localhost:8080' }
