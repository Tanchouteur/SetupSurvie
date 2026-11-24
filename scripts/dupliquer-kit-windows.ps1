param([switch]$Verifier)
$ErrorActionPreference = 'Stop'
$title = if ($Verifier) { 'Vérifier le kit SetupSurvie' } else { 'Dupliquer le kit SetupSurvie' }
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
            'Ce lanceur utilise Python pour ouvrir sa fenêtre. Installer Python pour votre compte depuis le SSD ?',
            $title, 'YesNo', 'Question')
        if ($answer -ne 'Yes') { exit 0 }
        $python = Install-SurvieKitPython $kit
    }
    $prefix = $python.Prefix
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $arguments = @($kit)
    if ($Verifier) { $arguments += '--verify' }
    & $python.Path @prefix -X utf8 (Join-Path $PSScriptRoot 'kit_duplicate_gui.py') @arguments
    if ($LASTEXITCODE -ne 0) { throw "La fenêtre SetupSurvie ne s’est pas ouverte. Vérifiez que Python inclut Tcl/Tk." }
} catch {
    [void][Windows.Forms.MessageBox]::Show($_.Exception.Message, $title, 'OK', 'Error')
    exit 1
}
