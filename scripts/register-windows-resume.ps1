[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$WorkDir,
      [Parameter(Mandatory=$true)][string]$Python,
      [Parameter(Mandatory=$true)][string]$UserId,
      [switch]$Probe,
      [switch]$ApplyWindowsSettings)
$ErrorActionPreference='Stop'
$WorkDir=(Resolve-Path -LiteralPath $WorkDir).Path
$Python=(Resolve-Path -LiteralPath $Python).Path
$config=Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$base=Split-Path $config.app_dir
$stable=Join-Path $base 'maintenance\windows_resume.py'
if (-not (Test-Path -LiteralPath $stable)) { throw 'Activer windows_resume.py avant de creer la tâche.' }
$backup=Join-Path $base 'maintenance\windows-recovery-backup'
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$sha=[Security.Cryptography.SHA256]::Create()
try { $id=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($WorkDir.ToLowerInvariant())))).Replace('-','').Substring(0,8) } finally { $sha.Dispose() }
$name='SetupSurvie-Bibliotheque-'+$id
if ($Probe) { $name+='-Test' }
$existing=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($existing -and $existing.Description -ne 'SetupSurvie managed pinned library recovery') { throw 'Une tâche homonyme existe et ne nous appartient pas.' }
$mode=if ($Probe) {'probe'} else {'run'}
$resumeArguments=$mode+' --work-dir "'+$WorkDir+'"'
# A limited S4U identity stores no password and does not grant administrator rights.
# The probe verifies actual public HTTPS access on this PC before activation.
$principal=New-ScheduledTaskPrincipal -UserId $UserId -LogonType S4U -RunLevel Limited
$action=New-ScheduledTaskAction -Execute $Python -Argument ('"'+$stable+'" '+$resumeArguments) -WorkingDirectory (Split-Path $stable)
$boot=New-ScheduledTaskTrigger -AtStartup
$boot.Delay='PT45S'
$periodic=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(5)) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2)
Register-ScheduledTask -TaskName $name -Action $action -Trigger @($boot,$periodic) -Settings $settings -Principal $principal -Description 'SetupSurvie managed pinned library recovery' -Force | Out-Null
if ($Probe) {
    Start-ScheduledTask -TaskName $name
} elseif ($ApplyWindowsSettings) {
    $test=Get-ScheduledTask -TaskName ($name+'-Test') -ErrorAction Stop
    if ($test.Description -ne 'SetupSurvie managed pinned library recovery' -or ($test | Get-ScheduledTaskInfo).LastTaskResult -ne 0) { throw 'Le test de reprise doit reussir avant activation.' }
    $probePath=Join-Path $config.data_dir 'diagnostics\windows-resume-probe.json'
    $proof=Get-Content -LiteralPath $probePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $proof.ok -or -not $proof.https) { throw 'Test HTTPS de la tache manquant.' }
    $userProfile=(Get-ItemProperty -LiteralPath ('HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\'+$UserId)).ProfileImagePath
    $startupFolder=Join-Path $userProfile 'AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'
    $shell=New-Object -ComObject WScript.Shell
    $link=Join-Path $startupFolder 'SetupSurvie.lnk'
    $wrapper=Join-Path $base 'maintenance\start-without-inference.ps1'
    if (-not (Test-Path -LiteralPath $wrapper)) { throw 'Lanceur sans IA absent.' }
    if (Test-Path -LiteralPath $link) {
        $old=$shell.CreateShortcut($link)
        $owned=$old.Arguments.Contains((Join-Path $WorkDir 'start-local.ps1')) -or ($old.Arguments.Contains($WorkDir) -and ($old.Arguments.Contains('start-pilot.ps1') -or $old.Arguments.Contains('start-without-inference.ps1')))
        if (-not $owned) { throw 'Raccourci de demarrage inconnu ; aucun remplacement.' }
        $saved=Join-Path $backup 'SetupSurvie-startup-before.lnk'
        if (-not (Test-Path -LiteralPath $saved)) { Copy-Item -LiteralPath $link -Destination $saved }
    }
    $consolePython=Join-Path (Split-Path $Python) 'python.exe'
    if (-not (Test-Path -LiteralPath $consolePython)) { throw 'Python de demarrage absent.' }
    $shortcut=$shell.CreateShortcut($link)
    $shortcut.TargetPath=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $shortcut.Arguments='-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$wrapper+'" -WorkDir "'+$WorkDir+'" -Python "'+$consolePython+'"'
    $shortcut.WorkingDirectory=$base
    $shortcut.WindowStyle=7
    $shortcut.Description='SetupSurvie : bibliotheque au demarrage, IA sur demande'
    $shortcut.Save()
    $ollamaLink=Join-Path $startupFolder 'Ollama.lnk'
    if (Test-Path -LiteralPath $ollamaLink) {
        $old=$shell.CreateShortcut($ollamaLink)
        $expectedApp=Join-Path $config.data_dir 'tools\Ollama\ollama app.exe'
        if ($old.TargetPath -ieq $expectedApp) {
            $saved=Join-Path $backup ('Ollama-startup-'+[guid]::NewGuid().ToString('N')+'.lnk')
            Move-Item -LiteralPath $ollamaLink -Destination $saved
        } else { throw 'Raccourci Ollama inconnu ; conserver et examiner manuellement.' }
    }
    $expected=[IO.Path]::GetFullPath((Join-Path $config.data_dir 'tools\Ollama\ollama.exe'))
    $rules=@(Get-NetFirewallRule -Direction Inbound -Action Allow | Where-Object DisplayName -eq 'ollama' | Where-Object { ([string]$_.Profile) -match 'Public|Any' } | Where-Object {
        $filter=$_ | Get-NetFirewallApplicationFilter
        $filter.Program -and [IO.Path]::GetFullPath($filter.Program) -ieq $expected
    })
    $saved=Join-Path $backup 'ollama-firewall-before.xml'
    if (-not (Test-Path -LiteralPath $saved)) { $rules | Export-Clixml -LiteralPath $saved }
    foreach ($rule in $rules) { Disable-NetFirewallRule -Name $rule.Name | Out-Null }
    # Official active-hours policy: protect 18:00-12:00, keeping Windows Update enabled.
    $key='HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate'
    $saved=Join-Path $backup 'windows-update-before.json'
    if (-not (Test-Path -LiteralPath $saved)) {
        $old=Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
        @{SetActiveHours=$old.SetActiveHours;ActiveHoursStart=$old.ActiveHoursStart;ActiveHoursEnd=$old.ActiveHoursEnd} | ConvertTo-Json | Set-Content -LiteralPath $saved -Encoding UTF8
    }
    New-Item -Path $key -Force | Out-Null
    New-ItemProperty -LiteralPath $key -Name SetActiveHours -Value 1 -PropertyType DWord -Force | Out-Null
    New-ItemProperty -LiteralPath $key -Name ActiveHoursStart -Value 18 -PropertyType DWord -Force | Out-Null
    New-ItemProperty -LiteralPath $key -Name ActiveHoursEnd -Value 12 -PropertyType DWord -Force | Out-Null
    $edition=(Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').EditionID
    if ($edition -like 'Core*') { Write-Warning 'Windows familial : confirmer manuellement 18:00-12:00 dans Windows Update > Options avancees > Heures activite. La strategie seule ne prouve pas son application.' }

    Export-ScheduledTask -TaskName ($name+'-Test') | Set-Content -LiteralPath (Join-Path $backup 'task-probe-before-removal.xml') -Encoding UTF8
    Unregister-ScheduledTask -TaskName ($name+'-Test') -Confirm:$false

}
@{task=$name;probe=[bool]$Probe;windows_settings=[bool]$ApplyWindowsSettings;registered=(Get-Date -Format o)} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backup $(if ($Probe) {'task-probe.json'} else {'task-installed.json'})) -Encoding UTF8
Write-Output $name
