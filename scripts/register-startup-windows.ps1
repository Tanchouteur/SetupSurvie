[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$WorkDir,[switch]$Disable,[switch]$RefreshOnly)
$ErrorActionPreference='Stop'
$config=Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$stable=Join-Path (Split-Path $config.app_dir) 'maintenance'
$runtime=Get-Content -LiteralPath (Join-Path $stable 'startup-settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$name=$runtime.task_name
$existing=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
$description='SetupSurvie managed document services startup without AI'
if ($existing -and $existing.Description -ne $description) { throw 'Une autre tache occupe ce nom ; aucun remplacement.' }
if ($RefreshOnly -and (-not $existing -or $existing.State -eq 'Disabled')) { exit 0 }
if ($Disable) {
    if ($existing) { Disable-ScheduledTask -TaskName $name | Out-Null }
    $download=Get-ScheduledTask -TaskName ($name+'-Transfert') -ErrorAction SilentlyContinue
    if ($download -and $download.Description -eq 'SetupSurvie managed pinned download after login') { Disable-ScheduledTask -TaskName $download.TaskName | Out-Null }

    exit 0
}
# Disable only the vendor login link for the exact Ollama installation in use.
$startupFolder=[Environment]::GetFolderPath('Startup')
$ollamaLink=Join-Path $startupFolder 'Ollama.lnk'
if ($runtime.ollama -and (Test-Path -LiteralPath $ollamaLink)) {
    $shell=New-Object -ComObject WScript.Shell
    $vendor=$shell.CreateShortcut($ollamaLink)
    if ((Split-Path $vendor.TargetPath) -ieq (Split-Path $runtime.ollama)) {
        $saved=Join-Path $stable ('Ollama-startup-before-'+[guid]::NewGuid().ToString('N')+'.lnk')
        Move-Item -LiteralPath $ollamaLink -Destination $saved
    }
}
$user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$login=New-ScheduledTaskTrigger -AtLogOn -User $user
$timer=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(5)) -RepetitionInterval (New-TimeSpan -Minutes 5)
$pythonw=Join-Path (Split-Path $runtime.python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { throw 'Python sans console introuvable.' }
$launcher=Join-Path $stable 'windows_background.py'
$action=New-ScheduledTaskAction -Execute $pythonw -Argument ('"'+$launcher+'" -WorkDir "'+$WorkDir+'" -Startup') -WorkingDirectory $stable
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $name -Action $action -Trigger @($login,$timer) -Principal $principal -Settings $settings -Description $description -Force | Out-Null
# Migrate only our existing login links; a task upgrade must not leave a legacy
# PowerShell startup entry flashing at the next login.
foreach ($link in @(Get-ChildItem -LiteralPath $startupFolder -Filter 'SetupSurvie*.lnk' -ErrorAction SilentlyContinue)) {
    $shell=New-Object -ComObject WScript.Shell
    $shortcut=$shell.CreateShortcut($link.FullName)
    if ($shortcut.Arguments.Contains('-WorkDir "'+$WorkDir+'"') -and ($shortcut.Arguments.Contains('startup-windows.ps1') -or $shortcut.Arguments.Contains('windows_background.py'))) {
        $shortcut.TargetPath=$pythonw
        $shortcut.Arguments='"'+$launcher+'" -WorkDir "'+$WorkDir+'" -Startup'
        $shortcut.WindowStyle=7
        $shortcut.Save()
    }
}
Write-Output ('Demarrage automatique enregistre : '+$name)

$downloadName=$name+'-Transfert'
$downloadDescription='SetupSurvie managed pinned download after login'
$download=Get-ScheduledTask -TaskName $downloadName -ErrorAction SilentlyContinue
if ($download -and $download.Description -ne $downloadDescription) { throw 'Une autre tache occupe le nom de reprise ; aucun remplacement.' }
if ($RefreshOnly -and -not $download) { exit 0 }
$downloadDisabled=$RefreshOnly -and $download.State -eq 'Disabled'
$downloadAction=New-ScheduledTaskAction -Execute $pythonw -Argument ('"'+(Join-Path $stable 'windows_resume.py')+'" run --work-dir "'+$WorkDir+'"') -WorkingDirectory $stable
$downloadSettings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $downloadName -Action $downloadAction -Trigger @($login,$timer) -Principal $principal -Settings $downloadSettings -Description $downloadDescription -Force | Out-Null
if ($downloadDisabled) { Disable-ScheduledTask -TaskName $downloadName | Out-Null }
