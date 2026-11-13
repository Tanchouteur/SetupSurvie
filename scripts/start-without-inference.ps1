[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$WorkDir,
      [Parameter(Mandatory=$true)][string]$Python)
$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$stable=Join-Path (Split-Path $config.app_dir) 'maintenance\windows_resume.py'
& $Python -X utf8 $stable prepare-login --work-dir $WorkDir
if ($LASTEXITCODE -ne 0) { throw 'La pause de démarrage IA ne peut pas être enregistrée ; démarrage interrompu.' }
$local=Join-Path $WorkDir 'start-local.ps1'
if (Test-Path -LiteralPath $local) {
    & $local
} else {
    & (Join-Path $config.app_dir 'scripts\start-pilot.ps1') -WorkDir $WorkDir
}
exit $LASTEXITCODE
