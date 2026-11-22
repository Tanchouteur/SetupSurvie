$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
. (Join-Path $PSScriptRoot 'windows-common.ps1')

try {
    $kit = Split-Path (Split-Path $PSScriptRoot)
    if (-not (Test-Path -LiteralPath (Join-Path $kit 'manifest.json') -PathType Leaf)) {
        throw 'Ouvrez ce lanceur depuis le dossier app d’un kit SetupSurvie complet.'
    }
    Update-SurviePath
    $python = Find-SurviePython
    if (-not $python) {
        throw 'Ce PC a besoin de Python pour dupliquer le kit. L’installateur local se trouve sur le SSD, dans installateurs-windows.'
    }
    $prefix = $python.Prefix
    & $python.Path @prefix -X utf8 (Join-Path $PSScriptRoot 'kit_duplicate_gui.py') $kit
    if ($LASTEXITCODE -ne 0) { throw 'La fenêtre de copie ne s’est pas ouverte. Vérifiez que Python inclut Tcl/Tk.' }
} catch {
    [void][Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Dupliquer le kit SetupSurvie', 'OK', 'Error')
    exit 1
}
