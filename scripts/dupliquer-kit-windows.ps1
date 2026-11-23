$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
. (Join-Path $PSScriptRoot 'windows-common.ps1')

try {
    $kit = Split-Path (Split-Path $PSScriptRoot)
    if (-not (Test-Path -LiteralPath (Join-Path $kit 'manifest.json') -PathType Leaf)) {
        throw "Ouvrez ce lanceur depuis le dossier app d’un kit SetupSurvie complet."
    }
    Update-SurviePath
    $python = Find-SurviePython -RequireTk
    if (-not $python) {
        $answer = [Windows.Forms.MessageBox]::Show(
            'Python avec Tcl/Tk est nécessaire pour afficher la copie. Installer Python pour votre compte depuis le SSD ?',
            'Dupliquer le kit SetupSurvie', 'YesNo', 'Question')
        if ($answer -ne 'Yes') { exit 0 }
        $python = Install-SurvieKitPython $kit
    }
    $prefix = $python.Prefix
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $python.Path @prefix -X utf8 (Join-Path $PSScriptRoot 'kit_duplicate_gui.py') $kit
    if ($LASTEXITCODE -ne 0) { throw "La fenêtre de copie ne s’est pas ouverte. Vérifiez que Python inclut Tcl/Tk." }
} catch {
    [void][Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Dupliquer le kit SetupSurvie', 'OK', 'Error')
    exit 1
}
