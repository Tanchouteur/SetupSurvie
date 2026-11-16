[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Package,
    [Parameter(Mandatory=$true)][string]$Sha256,
    [Parameter(Mandatory=$true)][string]$WorkDir
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'windows-common.ps1')
Initialize-SurvieTools
$settings = Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$portable = Join-Path $settings.data_dir 'tools\Python312\python.exe'
$python = if (Test-Path -LiteralPath $portable) { @{ Path = $portable; Prefix = @() } } else { Find-SurviePython }
if (-not $python) { throw 'Python manque. Utilisez la préparation du PC.' }
$launcher = Join-Path $settings.app_dir 'scripts\pilot_update.py'
$arguments = @($python.Prefix) + @('-X', 'utf8', $launcher, 'rollback', $Package, '--sha256', $Sha256, '--work-dir', $WorkDir)
& $python.Path @arguments
if ($LASTEXITCODE -ne 0) { throw 'Retour interrompu. Conservez les sauvegardes et consultez le message précédent.' }
