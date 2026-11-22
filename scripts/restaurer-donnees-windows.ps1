param([switch]$Ouvrir)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'windows-common.ps1')

function Invoke-SurvieOfflineRestorePreparation([string]$Kit) {
    $script = Join-Path $PSScriptRoot 'prepare-windows.ps1'
    # Use the existing preparation executable, including its restart journal
    # and mutex. Passing -Kit prevents downloads on the target.
    $details = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -Kit $Kit 2>&1 | Out-String
    return @{ Code = $LASTEXITCODE; Details = $details.Trim() }
}

function Initialize-SurvieRestoreRuntime([string]$Kit, [switch]$Installed, [scriptblock]$Confirm) {
    Initialize-SurvieTools
    $python = Find-SurviePython -RequireTk
    if ($Installed) {
        if (-not $python) { throw 'Python avec Tcl/Tk est nécessaire pour ouvrir cette installation.' }
    } else {
        if (-not (Get-SurvieDockerType) -and -not (Find-SurvieDockerDesktop)) {
            if (-not (& $Confirm 'Préparer Windows depuis les installateurs du SSD ? Windows pourra demander une autorisation ou un redémarrage.')) { return }
            $result = Invoke-SurvieOfflineRestorePreparation $Kit
            if ($result.Code -eq 3010) { throw 'Redémarrez Windows, laissez le SSD branché, puis rouvrez Restaurer mes données SetupSurvie.' }
            if ($result.Code -ne 0) {
                throw ("Préparation de Windows interrompue.`n`n" + $result.Details)
            }
            Initialize-SurvieTools
            $python = Find-SurviePython -RequireTk
        }
        if (-not $python) {
            if (-not (& $Confirm 'Installer Python avec Tcl/Tk pour votre compte depuis le SSD ?')) { return }
            $python = Install-SurvieKitPython $Kit
        }
    }
    Start-SurvieDocker
    return $python
}

if ($MyInvocation.InvocationName -eq '.') { return }
Add-Type -AssemblyName System.Windows.Forms

try {
    $kit = Split-Path (Split-Path $PSScriptRoot)
    if (-not $Ouvrir -and -not (Test-Path -LiteralPath (Join-Path $kit 'manifest.json') -PathType Leaf)) {
        throw "Ouvrez ce lanceur depuis le dossier app d’un kit SetupSurvie complet."
    }
    $python = Initialize-SurvieRestoreRuntime $kit -Installed:$Ouvrir -Confirm {
        param($Message)
        [Windows.Forms.MessageBox]::Show($Message, 'Restaurer mes données SetupSurvie', 'YesNo', 'Question') -eq 'Yes'
    }
    if (-not $python) { exit 0 }
    $prefix = $python.Prefix
    $arguments = @($kit)
    if ($Ouvrir) { $arguments = @('--open', $kit) }
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $python.Path @prefix -X utf8 (Join-Path $PSScriptRoot 'pilot_restore_gui.py') @arguments
    if ($LASTEXITCODE -ne 0) { throw "La fenêtre de restauration ne s’est pas ouverte. Vérifiez que Python inclut Tcl/Tk." }
} catch {
    [void][Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Restaurer mes données SetupSurvie', 'OK', 'Error')
    exit 1
}
