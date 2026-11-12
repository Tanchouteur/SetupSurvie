[CmdletBinding()]
param([string]$WorkDir = (Join-Path (Split-Path $PSScriptRoot) '.local'), [switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
try {
    $WorkDir = (Resolve-Path -LiteralPath $WorkDir).Path
    Start-Transcript -Path (Join-Path $WorkDir 'demarrage.log') -Append | Out-Null
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) { throw 'Docker Desktop est requis. Voir docs/installation/pilote-marc.md.' }
    function Test-PilotDockerReady {
        try {
            & $docker.Source info --format '{{.OSType}}' 2>$null | Out-Null
            return $LASTEXITCODE -eq 0
        } catch { return $false }
    }
    if (-not (Test-PilotDockerReady)) {
        $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (-not (Test-Path -LiteralPath $desktop)) { throw 'Docker Desktop est introuvable.' }
        Start-Process -FilePath $desktop
        $ready = $false
        for ($i = 0; $i -lt 90; $i++) {
            Start-Sleep -Seconds 2
            if (Test-PilotDockerReady) { $ready = $true; break }
        }
        if (-not $ready) { throw 'Docker tarde à démarrer. Ouvrez Docker Desktop puis réessayez.' }
    }
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
