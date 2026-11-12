[CmdletBinding()]
param([string]$WorkDir = (Join-Path (Split-Path $PSScriptRoot) '.local'), [switch]$Startup, [switch]$DisableStartup,
    [string]$DesktopDir, [string]$StartupDir)
$ErrorActionPreference = 'Stop'
if ($Startup -and $DisableStartup) { throw 'Choisir Startup ou DisableStartup, pas les deux.' }
$launcher = Join-Path $PSScriptRoot 'start-pilot.ps1'
$stopper = Join-Path $PSScriptRoot 'stop-pilot.ps1'
$icon = Join-Path (Split-Path $PSScriptRoot) 'portal\branding\favicon.ico'
$WorkDir = (Resolve-Path -LiteralPath $WorkDir).Path
$shell = New-Object -ComObject WScript.Shell
$updater = Join-Path $PSScriptRoot 'update-windows.ps1'
$settingsPath = Join-Path $WorkDir 'settings.json'
if (Test-Path -LiteralPath $settingsPath) {
    $settings = Get-Content -LiteralPath $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($settings.app_dir) {
        $stable = Join-Path (Split-Path $settings.app_dir) 'maintenance\update-windows.ps1'
        if (Test-Path -LiteralPath $stable) { $updater = $stable }
    }
}
$hasher = [Security.Cryptography.SHA256]::Create()
try { $installationId = ([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($WorkDir.ToLowerInvariant())))).Replace('-', '').Substring(0, 8) }
finally { $hasher.Dispose() }
function Test-PilotShortcutOwner([string]$Path) {
    $existing = $shell.CreateShortcut($Path)
    return $existing.Arguments.Contains('-WorkDir "' + $WorkDir + '"')
}
function Add-PilotShortcut([string]$Folder, [string]$Name, [string]$Script, [bool]$OpenBrowser, [string]$Description) {
    $path = Join-Path $Folder $Name
    if ((Test-Path -LiteralPath $path) -and -not (Test-PilotShortcutOwner $path)) {
        $nameWithId = [IO.Path]::GetFileNameWithoutExtension($Name) + ' (' + $installationId + ').lnk'
        $path = Join-Path $Folder $nameWithId
        if ((Test-Path -LiteralPath $path) -and -not (Test-PilotShortcutOwner $path)) { throw ('Raccourci déjà occupé : ' + $path + '. Aucun raccourci existant remplacé.') }
    }
    $shortcut = $shell.CreateShortcut($path)
    $shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $Script + '" -WorkDir "' + $WorkDir + '"'
    if ($OpenBrowser) { $shortcut.Arguments += ' -OpenBrowser' }
    $shortcut.WorkingDirectory = Split-Path $Script
    $shortcut.Description = $Description
    $shortcut.WindowStyle = 7
    if (Test-Path -LiteralPath $icon) { $shortcut.IconLocation = $icon + ',0' }
    $shortcut.Save()
}
# Explicit destinations also allow real COM checks outside Windows' live Startup.
$desktop = if ($DesktopDir) { (Resolve-Path -LiteralPath $DesktopDir).Path } else { [Environment]::GetFolderPath('Desktop', 'Create') }
$startupFolder = if ($StartupDir) { (Resolve-Path -LiteralPath $StartupDir).Path } else { [Environment]::GetFolderPath('Startup', 'Create') }
Add-PilotShortcut $desktop 'Ouvrir SetupSurvie.lnk' $launcher $true 'Démarrer SetupSurvie et ouvrir la bibliothèque'
Add-PilotShortcut $desktop 'Arrêter SetupSurvie.lnk' $stopper $false 'Arrêter les services SetupSurvie en conservant les données'
Add-PilotShortcut $desktop 'Mettre à jour SetupSurvie.lnk' $updater $false 'Récupérer la dernière version avec Git, sauvegarder et mettre à jour'
if ($Startup) { Add-PilotShortcut $startupFolder 'SetupSurvie.lnk' $launcher $false "Démarrer SetupSurvie à l'ouverture de session" }
if ($DisableStartup) {
    foreach ($name in @('SetupSurvie.lnk', ('SetupSurvie (' + $installationId + ').lnk'))) {
        $path = Join-Path $startupFolder $name
        if (Test-Path -LiteralPath $path) {
            $existing = $shell.CreateShortcut($path)
            if ((Test-PilotShortcutOwner $path) -and $existing.Arguments.Contains('start-pilot.ps1')) { Remove-Item -LiteralPath $path }
        }
    }
}
# Replace only our former desktop launcher; keep unrelated shortcuts untouched.
$legacy = Join-Path $desktop 'SetupSurvie.lnk'
if (Test-Path -LiteralPath $legacy) {
    $existing = $shell.CreateShortcut($legacy)
    if ($existing.Arguments.Contains('-WorkDir "' + $WorkDir + '"') -and $existing.Arguments.Contains('start-pilot.ps1')) { Remove-Item -LiteralPath $legacy }
}
Write-Host 'Raccourcis créés pour cet utilisateur. Aucune tâche administrateur ajoutée.'
