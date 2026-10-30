[CmdletBinding()]
param(
    [string]$DataDir,
    [switch]$Lan,
    [switch]$Offline
)
$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot 'survie.ps1'
$arguments = @('install', '--target', 'windows')
if ($DataDir) { $arguments += @('--data-dir', $DataDir) }
if ($Lan) { $arguments += '--lan' }
if ($Offline) { $arguments += '--offline' }
& $launcher @arguments
exit $LASTEXITCODE
