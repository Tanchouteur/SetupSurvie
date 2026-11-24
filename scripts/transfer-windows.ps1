[CmdletBinding()]
param([string]$WorkDir, [switch]$Browser)
$ErrorActionPreference='Stop'
try {
    . (Join-Path $PSScriptRoot 'windows-common.ps1')
    Initialize-SurvieTools
    if (-not $WorkDir) {
        $saved=Join-Path $PSScriptRoot 'update-settings.json'
        if (Test-Path -LiteralPath $saved) { $WorkDir=(Get-Content -LiteralPath $saved -Raw -Encoding UTF8 | ConvertFrom-Json).work_dir }
    }
    if (-not $WorkDir) { throw 'Utilisez le raccourci Transférer SetupSurvie ou sélectionnez le dossier privé.' }
    $config=Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $python=Find-SurviePython
    $portable=Join-Path $config.data_dir 'tools\Python312\python.exe'
    if (Test-Path -LiteralPath $portable) { $python=@{Path=$portable;Prefix=@()} }
    if (-not $python) { throw 'Python manque. La copie de secours doit fournir un runtime ou un installateur hors ligne.' }
    $wizardArgs=@('-X','utf8',(Join-Path $config.app_dir 'scripts\transfer_wizard.py'),'--work-dir',$WorkDir,'--base',(Split-Path $config.app_dir))
    if ($Browser) { $wizardArgs+='--browser' }
    & $python.Path @($python.Prefix) @wizardArgs
    if ($LASTEXITCODE -ne 0) { throw 'Assistant de transfert interrompu. Python avec Tk est nécessaire.' }
} catch {
    $shell=New-Object -ComObject WScript.Shell
    $null=$shell.Popup($_.Exception.Message,0,'Transférer SetupSurvie',16)
    exit 1
}
