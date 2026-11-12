[CmdletBinding()]
param([string]$WorkDir = (Join-Path (Split-Path $PSScriptRoot) '.local'), [switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
try {
    . (Join-Path $PSScriptRoot 'windows-common.ps1')
    Initialize-SurvieTools
    $WorkDir = (Resolve-Path -LiteralPath $WorkDir).Path
    Start-Transcript -Path (Join-Path $WorkDir 'demarrage.log') -Append | Out-Null
    Start-SurvieDocker
    & (Join-Path $PSScriptRoot 'survie.ps1') --work-dir $WorkDir up
    if ($LASTEXITCODE -ne 0) { throw 'Le démarrage a échoué. Consulter le message ci-dessus.' }
    if ($OpenBrowser) { Start-Process 'http://localhost:8080' }
} catch {
    $message = "SetupSurvie n'a pas pu démarrer. " + $_.Exception.Message + "`nConsultez demarrage.log dans le dossier privé."
    Write-Host $message -ForegroundColor Red
    try { $popup = New-Object -ComObject WScript.Shell; $null = $popup.Popup($message, 0, 'SetupSurvie — démarrage', 16) } catch { }
    exit 1
} finally {
    try { Stop-Transcript | Out-Null } catch { }
}
