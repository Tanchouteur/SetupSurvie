[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$WorkDir,[switch]$OpenBrowser,[switch]$Startup)
$ErrorActionPreference='Stop'
$mutex=$null; $owned=$false
try {
    $runtime=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'startup-settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($runtime.kind -ne 'SetupSurvie managed Windows startup' -or $runtime.work_dir -ne $WorkDir) { throw 'Configuration de demarrage incoherente.' }
    $mutex=New-Object Threading.Mutex($false,('Local\'+$runtime.task_name))
    try { $owned=$mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $owned=$true }
    if (-not $owned) { exit 0 }
    $env:PATH=(@($runtime.paths)+@($env:PATH)) -join ';'
    . (Join-Path $PSScriptRoot 'windows-common.ps1')
    Initialize-SurvieTools
    $config=Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $log=Join-Path $config.data_dir 'diagnostics\demarrage-automatique.log'
    New-Item -ItemType Directory -Path (Split-Path $log) -Force | Out-Null
    Start-Transcript -Path $log -Append | Out-Null
    $application=$config.app_dir
    $paused=Join-Path $WorkDir 'startup-paused.json'
    if (Test-Path -LiteralPath $paused) {
        if ($OpenBrowser) { Remove-Item -LiteralPath $paused } else { exit 0 }
    }
    # A completed update is required before restarting any services.
    $journal=Join-Path $WorkDir 'update.json'
    if (Test-Path -LiteralPath $journal) {
        $update=Get-Content -LiteralPath $journal -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($update.phase -notin @('complete','rolled_back')) { throw 'Mise a jour incomplete : recuperation explicite necessaire.' }
    }
    # The download uses a separate unlimited task, never a child of this
    # ten-minute web startup task (which must not terminate a long transfer).
    $downloadTask=Get-ScheduledTask -TaskName ($runtime.task_name+'-Transfert') -ErrorAction SilentlyContinue
    if ($downloadTask -and $downloadTask.Description -eq 'SetupSurvie managed pinned download after login' -and $downloadTask.State -ne 'Running') {
        Start-ScheduledTask -TaskName $downloadTask.TaskName
    }
    $release=Get-Content -LiteralPath (Join-Path $application 'deploy\release.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $ready=$false
    try { $health=Invoke-RestMethod -Uri 'http://127.0.0.1:8080/api/health' -TimeoutSec 3; $ready=$health.ok -and $health.version -eq $release.version } catch { }
    if (-not $ready) {
        # No dependency on Docker install-settings.json, which may disappear.
        Start-SurvieDocker
        & $runtime.python -X utf8 (Join-Path $application 'scripts\setup.py') --work-dir $WorkDir up
        if ($LASTEXITCODE -ne 0) { throw 'Services indisponibles ; nouvel essai automatique dans cinq minutes.' }
    }
    if ($OpenBrowser) { Start-Process 'http://localhost:8080' }
} catch {
    try { $_ | Out-String | Add-Content -LiteralPath $log -Encoding UTF8 } catch { }
    Write-Error $_
    exit 1
} finally {
    try { Stop-Transcript | Out-Null } catch { }
    if ($owned -and $mutex) { $mutex.ReleaseMutex() }
    if ($mutex) { $mutex.Dispose() }
}
