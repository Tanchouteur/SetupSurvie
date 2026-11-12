[CmdletBinding()]
param([string]$WorkDir = (Join-Path (Split-Path $PSScriptRoot) '.local'))
$ErrorActionPreference = 'Stop'
try {
    $WorkDir = (Resolve-Path -LiteralPath $WorkDir).Path
    Start-Transcript -Path (Join-Path $WorkDir 'arret.log') -Append | Out-Null
    & (Join-Path $PSScriptRoot 'survie.ps1') --work-dir $WorkDir down
    if ($LASTEXITCODE -ne 0) { throw "L'arrêt n'a pas pu être confirmé." }
    Write-Host 'SetupSurvie arrêté. Les données sont conservées.'
} catch {
    $message = "SetupSurvie n'a pas pu terminer son arrêt. " + $_.Exception.Message + "`nConsultez arret.log dans le dossier privé."
    Write-Host $message -ForegroundColor Red
    try { $popup = New-Object -ComObject WScript.Shell; $null = $popup.Popup($message, 0, 'SetupSurvie — arrêt', 16) } catch { }
    exit 1
} finally {
    try { Stop-Transcript | Out-Null } catch { }
}
