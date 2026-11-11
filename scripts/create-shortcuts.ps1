[CmdletBinding()]
param([string]$WorkDir = (Join-Path (Split-Path $PSScriptRoot) '.local'), [switch]$Startup)
$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot 'start-pilot.ps1'
$WorkDir = (Resolve-Path -LiteralPath $WorkDir).Path
$shell = New-Object -ComObject WScript.Shell
function Add-PilotShortcut([string]$Folder, [bool]$OpenBrowser) {
    $shortcut = $shell.CreateShortcut((Join-Path $Folder 'SetupSurvie.lnk'))
    $shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $launcher + '" -WorkDir "' + $WorkDir + '"'
    if ($OpenBrowser) { $shortcut.Arguments += ' -OpenBrowser' }
    $shortcut.WorkingDirectory = Split-Path $PSScriptRoot
    $shortcut.Description = 'Démarrer la bibliothèque et les assistants locaux SetupSurvie'
    $shortcut.Save()
}
Add-PilotShortcut ([Environment]::GetFolderPath('Desktop')) $true
if ($Startup) { Add-PilotShortcut ([Environment]::GetFolderPath('Startup')) $false }
Write-Host 'Raccourcis créés pour cet utilisateur. Aucune tâche administrateur ajoutée.'
