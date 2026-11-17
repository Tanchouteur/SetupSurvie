[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$WorkDir)
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath (Join-Path $WorkDir 'transfer-guard.json')) {
    throw 'Transfert en cours : reprendre ou revenir a la source depuis Transferer SetupSurvie.'
}
$runtime=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'startup-settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$env:PATH=(@($runtime.paths)+@($env:PATH)) -join ';'
$config=Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
& $runtime.python -X utf8 (Join-Path $PSScriptRoot 'windows_resume.py') pause-site --work-dir $WorkDir
if ($LASTEXITCODE -ne 0) { throw 'La surveillance automatique ne peut pas etre mise en pause.' }
& (Join-Path $config.app_dir 'scripts\stop-pilot.ps1') -WorkDir $WorkDir
exit $LASTEXITCODE
