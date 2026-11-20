[CmdletBinding()]
param([string]$WorkDir, [switch]$Check, [switch]$Recover, [switch]$Cleanup, [switch]$ConsoleOnly,
    [Parameter(DontShow)] [string]$ProgressLog, [Parameter(DontShow)] [string]$OperationId)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'windows-common.ps1')

$script:updateVersion = $null
$script:updateLog = $null
# Portal status: data\catalog\maintenance.json, same schema as scripts/maintenance_site.py.
$script:statusFile = $null
$script:statusClock = $null
$script:maintenanceStatus = $null
$script:unavailablePhases = @('apply', 'stop', 'backup', 'switch', 'start', 'check', 'rollback')
$script:finalStates = @{ done = 'completed'; clean = 'completed'; current = 'current'; error = 'failed' }
$script:updateStages = @{
    setup = 'Vérification de l''installation'
    git = 'Récupération de la version disponible'
    build = 'Préparation du paquet'
    package = 'Vérification du paquet et de l''espace disque'
    apply = 'Sauvegarde et installation'
    maintenance = 'Attente de la fin des travaux en cours'
    stop = 'Arrêt des services'
    backup = 'Sauvegarde des données'
    switch = 'Installation de la nouvelle version'
    start = 'Redémarrage des services'
    check = 'Vérification du fonctionnement'
    rollback = 'Restauration de la version précédente'
    prune = 'Nettoyage des anciennes copies de mise à jour'
    launcher = 'Actualisation des raccourcis et du lanceur'
    done = 'Mise à jour terminée'
    clean = 'Nettoyage terminé'
    current = 'SetupSurvie est déjà à jour'
    error = 'Mise à jour arrêtée'
}

function Write-SurvieUpdateProgress([string]$Phase, [string]$Detail, [int]$Current, [int]$Total) {
    $title = $script:updateStages[$Phase]
    if (-not $title) { return }
    if ($Total -gt 0 -and $Phase -eq 'backup') {
        $Detail = '{0:N0} fichiers sur {1:N0} sauvegardés' -f $Current, $Total
    } elseif ($Phase -eq 'prune') {
        $Detail = '{0:N0} anciennes copies traitées sur {1:N0}. Le site est de nouveau disponible.' -f $Current, $Total
    }
    $line = $title
    if ($Detail) { $line += ' — ' + $Detail }
    Write-Host ('[{0:HH:mm:ss}] {1}' -f (Get-Date), $line)
    Update-SurvieMaintenanceStatus $Phase $title $Detail $Current $Total $line
    if ($ProgressLog) {
        $entry = @{ Phase = $Phase; Title = $title; Detail = $Detail; Current = $Current; Total = $Total
            Version = $script:updateVersion; Log = $script:updateLog }
        try {
            $json = $entry | ConvertTo-Json -Compress
            [IO.File]::AppendAllText($ProgressLog, $json + [Environment]::NewLine)
        } catch [IO.IOException] {
            # The progress display is best effort. The transcript remains authoritative.
        } catch [UnauthorizedAccessException] {}
    }
}

function Get-SurvieUnixTime { return [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000 }

function Start-SurvieMaintenanceStatus([string]$DataDir) {
    # Best effort: the portal reads this file through Caddy or the maintenance page.
    try {
        $catalog = Join-Path $DataDir 'catalog'
        if (-not (Test-Path -LiteralPath $catalog -PathType Container)) { return }
        $id = if ($OperationId -match '^[0-9a-f]{32}$') { $OperationId } else { [guid]::NewGuid().ToString('N') }
        $now = Get-SurvieUnixTime
        $script:maintenanceStatus = [ordered]@{
            schema = 1; id = $id; kind = $(if ($Recover) { 'recover' } else { 'update' }); state = 'running'
            phase = 'setup'; title = $script:updateStages.setup; detail = ''; current = $null; total = $null
            unavailable = $false; installed = ''; available = ''; rolled_back = $false
            started = $now; updated = $now; steps = New-Object Collections.ArrayList; lines = New-Object Collections.ArrayList
        }
        $script:statusFile = Join-Path $catalog 'maintenance.json'
        Update-SurvieMaintenanceStatus 'setup' $script:updateStages.setup '' 0 0 $script:updateStages.setup
    } catch { $script:statusFile = $null }
}

function Add-SurvieMaintenanceLine([string]$Text) {
    if (-not $script:maintenanceStatus) { return }
    $clean = (($Text -replace '\s+', ' ').Trim())
    if (-not $clean) { return }
    if ($clean.Length -gt 300) { $clean = $clean.Substring(0, 300) }
    $lines = $script:maintenanceStatus.lines
    $null = $lines.Add(('[{0:HH:mm:ss}] {1}' -f (Get-Date), $clean))
    while ($lines.Count -gt 40) { $lines.RemoveAt(0) }
    Save-SurvieMaintenanceStatus
}

function Update-SurvieMaintenanceStatus([string]$Phase, [string]$Title, [string]$Detail, [int]$Current, [int]$Total, [string]$Line) {
    $value = $script:maintenanceStatus
    if (-not $value) { return }
    $changed = $value.phase -ne $Phase -or $value.steps.Count -eq 0
    if ($changed) {
        $null = $value.steps.Add([ordered]@{ phase = $Phase; title = $Title; at = (Get-SurvieUnixTime) })
        while ($value.steps.Count -gt 30) { $value.steps.RemoveAt(0) }
    }
    if ($Phase -eq 'rollback') { $value.rolled_back = $true }
    if ($Phase -in $script:unavailablePhases) { $value.unavailable = $true }
    elseif ($Phase -in @('prune', 'launcher') -or $script:finalStates.ContainsKey($Phase)) { $value.unavailable = $false }
    $value.phase = $Phase
    $value.title = $Title
    $value.detail = if ($Detail.Length -gt 500) { $Detail.Substring(0, 500) } else { $Detail }
    $value.current = if ($Total -gt 0) { $Current } else { $null }
    $value.total = if ($Total -gt 0) { $Total } else { $null }
    $value.state = if ($script:finalStates.ContainsKey($Phase)) { $script:finalStates[$Phase] } else { 'running' }
    if ($script:updateVersion -match '^([0-9.]+) → ([0-9.]+)$') { $value.installed = $Matches[1]; $value.available = $Matches[2] }
    elseif ($script:updateVersion -match '([0-9]+\.[0-9]+\.[0-9]+)$' -and -not $value.installed) { $value.installed = $Matches[1] }
    if ($changed -or $Detail) {
        $lines = $value.lines
        $null = $lines.Add(('[{0:HH:mm:ss}] {1}' -f (Get-Date), $Line))
        while ($lines.Count -gt 40) { $lines.RemoveAt(0) }
    }
    Save-SurvieMaintenanceStatus -Force:($changed -or $value.state -ne 'running')
}

function Save-SurvieMaintenanceStatus([switch]$Force) {
    if (-not $script:statusFile -or -not $script:maintenanceStatus) { return }
    if (-not $Force -and $script:statusClock -and $script:statusClock.ElapsedMilliseconds -lt 1000) { return }
    $script:maintenanceStatus.updated = Get-SurvieUnixTime
    $temporary = $script:statusFile + '.' + $PID + '.tmp'
    try {
        $json = ConvertTo-Json -InputObject $script:maintenanceStatus -Depth 5 -Compress
        [IO.File]::WriteAllText($temporary, $json, (New-Object Text.UTF8Encoding($false)))
        for ($attempt = 1; $attempt -le 5; $attempt++) {
            try {
                if ([IO.File]::Exists($script:statusFile)) { [IO.File]::Replace($temporary, $script:statusFile, $null) }
                else { [IO.File]::Move($temporary, $script:statusFile) }
                break
            } catch [IO.IOException] { Start-Sleep -Milliseconds (50 * $attempt) }
            catch [UnauthorizedAccessException] { Start-Sleep -Milliseconds (50 * $attempt) }
        }
        $script:statusClock = [Diagnostics.Stopwatch]::StartNew()
    } catch {
        # The status is informative. The transcript and the update journal remain authoritative.
    } finally {
        if ([IO.File]::Exists($temporary)) { try { [IO.File]::Delete($temporary) } catch { } }
    }
}

function Show-SurvieUpdateWindow {
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.Application]::EnableVisualStyles()
    $form = New-Object Windows.Forms.Form -Property @{
        Text = 'Mise à jour de SetupSurvie'
        StartPosition = 'CenterScreen'
        ClientSize = [Drawing.Size]::new(540, 240)
        FormBorderStyle = 'FixedDialog'
        AutoScaleMode = 'Dpi'
        MaximizeBox = $false
        Font = [Drawing.Font]::new('Segoe UI', 10)
    }
    $title = New-Object Windows.Forms.Label -Property @{
        Text = $script:updateStages.setup
        Font = [Drawing.Font]::new('Segoe UI Semibold', 15)
        Location = [Drawing.Point]::new(24, 22)
        Size = [Drawing.Size]::new(492, 35)
    }
    $version = New-Object Windows.Forms.Label -Property @{
        Location = [Drawing.Point]::new(24, 61)
        Size = [Drawing.Size]::new(492, 23)
    }
    $bar = New-Object Windows.Forms.ProgressBar -Property @{
        Location = [Drawing.Point]::new(24, 92)
        Size = [Drawing.Size]::new(492, 14)
        Style = 'Marquee'
        MarqueeAnimationSpeed = 30
        AccessibleName = 'Progression de l''étape'
    }
    $detail = New-Object Windows.Forms.Label -Property @{
        Location = [Drawing.Point]::new(24, 116)
        Size = [Drawing.Size]::new(492, 60)
        AutoEllipsis = $true
    }
    $elapsed = New-Object Windows.Forms.Label -Property @{
        Location = [Drawing.Point]::new(24, 197)
        Size = [Drawing.Size]::new(220, 24)
    }
    $journal = New-Object Windows.Forms.Button -Property @{
        Text = 'Ouvrir le journal'
        Location = [Drawing.Point]::new(275, 190)
        Size = [Drawing.Size]::new(140, 32)
        Enabled = $false
    }
    $close = New-Object Windows.Forms.Button -Property @{
        Text = 'Fermer'
        Location = [Drawing.Point]::new(426, 190)
        Size = [Drawing.Size]::new(90, 32)
        Enabled = $false
    }
    $form.Controls.AddRange(@($title, $version, $bar, $detail, $elapsed, $journal, $close))
    $statusPath = [IO.Path]::GetTempFileName()
    $timer = New-Object Windows.Forms.Timer -Property @{ Interval = 300 }
    $view = @{ ExitCode = $null; Log = $null; Phase = $null }
    $process = $null
    try {
        $worker = New-Object Diagnostics.ProcessStartInfo -Property @{
            FileName = (Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe')
            Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -ConsoleOnly -ProgressLog `"$statusPath`""
            UseShellExecute = $false
            CreateNoWindow = $true
        }
        if ($Cleanup) { $worker.Arguments += ' -Cleanup' }
        if ($WorkDir) {
            $workPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($WorkDir)
            if ($workPath.EndsWith([char]92)) { $workPath += [char]92 }
            $worker.Arguments += ' -WorkDir "' + $workPath + '"'
        }
        $process = [Diagnostics.Process]::Start($worker)
        $watch = [Diagnostics.Stopwatch]::StartNew()
        $journal.Add_Click({ Start-Process -FilePath $view.Log })
        $close.Add_Click({ $form.Close() })
        $form.Add_FormClosing({ param($sender, $eventArgs) $eventArgs.Cancel = $null -eq $view.ExitCode })
        $timer.Add_Tick({
            $elapsed.Text = 'Temps écoulé  ' + $watch.Elapsed.ToString('hh\:mm\:ss')
            try {
                $stream = [IO.File]::Open($statusPath, 'Open', 'Read', 'ReadWrite')
                try {
                    $reader = [IO.StreamReader]::new($stream)
                    try { $lines = $reader.ReadToEnd().Trim().Split("`n") }
                    finally { $reader.Dispose() }
                } finally { $stream.Dispose() }
                if ($lines[-1]) {
                    $status = $lines[-1] | ConvertFrom-Json -ErrorAction Stop
                    $view.Phase = $status.Phase
                    $title.Text = $status.Title
                    $version.Text = $status.Version
                    $detail.Text = $status.Detail
                    if ($status.Log) {
                        $view.Log = $status.Log
                        $journal.Enabled = $true
                    }
                    if ($status.Total -gt 0) {
                        $bar.Style = 'Continuous'
                        $bar.Value = [int][Math]::Floor(100 * $status.Current / $status.Total)
                    } else { $bar.Style = 'Marquee' }
                }
            } catch {
                # A partially written line is read again on the next timer tick.
            }
            if ($process.HasExited) {
                $view.ExitCode = $process.ExitCode
                $timer.Stop()
                $close.Enabled = $true
                $form.AcceptButton = $close
                $close.Focus() | Out-Null
                $bar.Style = 'Continuous'
                if ($view.ExitCode -eq 0) {
                    $bar.Value = 100
                    if ($view.Phase -notin @('done', 'current', 'clean')) {
                        $title.Text = $script:updateStages.done
                        $detail.Text = ''
                    }
                }
                else {
                    $bar.Value = 0
                    $title.Text = $script:updateStages.error
                    if ($view.Phase -ne 'error') { $detail.Text = 'Le programme s''est arrêté. Consultez le journal de mise à jour.' }
                }
            }
        })
        $timer.Start()
        $null = $form.ShowDialog()
        return $view.ExitCode
    } finally {
        $timer.Dispose()
        $form.Dispose()
        if ($process) { $process.Dispose() }
        [IO.File]::Delete($statusPath)
    }
}

function Get-SurvieUpdateSettings {
    $work = $WorkDir
    if (-not $work) {
        $saved = Join-Path $PSScriptRoot 'update-settings.json'
        if (Test-Path -LiteralPath $saved) {
            $metadata = Get-Content -LiteralPath $saved -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($metadata.schema -ne 1) { throw 'Réglages de mise à jour non reconnus.' }
            $work = $metadata.work_dir
        } else {
            $application = Split-Path $PSScriptRoot
            $base = Split-Path $application
            $candidates = @((Join-Path $base 'prive'), (Join-Path $application '.local'), (Join-Path $base 'moteur\.local'))
            $found = @($candidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ 'settings.json') })
            if ($found.Count -ne 1) { throw 'Utilisez le raccourci Mettre à jour SetupSurvie ou indiquez -WorkDir avec le dossier privé.' }
            $work = $found[0]
        }
    }
    $work = (Resolve-Path -LiteralPath $work).Path
    $config = Get-Content -LiteralPath (Join-Path $work 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $config.PSObject.Properties['app_dir'] -or -not $config.app_dir) { throw 'Installation ancienne : séparez le logiciel de ses réglages avant la première mise à jour.' }
    $application = [IO.Path]::GetFullPath($config.app_dir)
    if (Test-Path -LiteralPath (Join-Path $application '.git')) { throw 'La mise à jour ne remplace jamais un dépôt de développement.' }
    return @{ Work = $work; Application = $application; Base = (Split-Path $application); Data = $config.data_dir }
}

function Invoke-SurvieUpdateCommand([string]$File, [array]$Arguments) {
    # Windows PowerShell can wrap redirected stderr as non-terminating errors.
    $ErrorActionPreference = 'Continue'
    $PSNativeCommandUseErrorActionPreference = $false
    $stderr = @()
    & $File @Arguments 2>&1 | ForEach-Object {
        $line = $_.ToString()
        if ($_ -is [Management.Automation.ErrorRecord] -and $line.Trim()) {
            $stderr = @($stderr | Select-Object -Last 2) + $line
        }
        if ($line.StartsWith('SURVIE_UPDATE_PROGRESS ')) {
            $status = $line.Substring('SURVIE_UPDATE_PROGRESS '.Length) | ConvertFrom-Json
            Write-SurvieUpdateProgress $status.phase $status.detail $status.current $status.total
        } else {
            Write-Host $line
            Add-SurvieMaintenanceLine $line
        }
    }
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        $detail = if ($stderr.Count) { ' ' + ($stderr -join ' ') } else { ' Les sauvegardes sont conservées. Consultez le journal.' }
        throw ('Étape interrompue (code ' + $code + ').' + $detail)
    }
}

function Get-SurvieGitOutput([string]$Git, [array]$Arguments) {
    $value = @(& $Git @Arguments)
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de vérifier le dépôt Git de maintenance.' }
    return ($value -join "`n")
}

function Assert-SurvieWorkQueueIdle([version]$Installed) {
    $wait = [Diagnostics.Stopwatch]::StartNew()
    $lastDetail = ''
    while ($true) {
        try {
            $queue = Invoke-RestMethod -Uri 'http://127.0.0.1:8080/api/work-queue' -UseBasicParsing -TimeoutSec 8
        } catch {
            # Releases before the unified queue may have no endpoint for this check.
            if ($Installed -lt [version]'0.63.0') { return }
            throw 'Impossible de vérifier la file d''attente. Vérifiez que SetupSurvie répond, puis relancez la mise à jour.'
        }
        if (-not $queue.preparations_available) {
            throw 'Impossible de vérifier les préparations documentaires. Réessayez quand la File d''attente est disponible.'
        }
        $active = @($queue.jobs | Where-Object { $_.status -in @('running', 'preparing') })
        if (-not $queue.running -and -not $active.Count) { return }
        if (-not $queue.paused) {
            throw 'Un travail est en cours dans SetupSurvie. Mettez la File d''attente en pause ou attendez sa fin, puis relancez la mise à jour.'
        }
        if ($wait.Elapsed.TotalMinutes -ge 5) {
            throw 'Des travaux sont encore en cours après cinq minutes d''attente. Consultez la File d''attente, puis relancez la mise à jour quand ils sont arrêtés.'
        }
        $titles = @($active | ForEach-Object { $_.title } | Where-Object { $_ } | Select-Object -Unique)
        $detail = if ($titles.Count) { $titles -join ' · ' } else { 'SetupSurvie finit les travaux déjà lancés.' }
        if ($detail -ne $lastDetail) {
            Write-SurvieUpdateProgress 'maintenance' $detail
            $lastDetail = $detail
        }
        Start-Sleep -Seconds 3
    }
}

function Invoke-SurvieGitUpdate($Settings) {
    Initialize-SurvieTools
    $portable = Join-Path $Settings.Data 'tools\Python312\python.exe'
    $python = if (Test-Path -LiteralPath $portable) { @{ Path = $portable; Prefix = @() } } else { Find-SurviePython }
    if (-not $python) { throw 'Python x64 3.11 à 3.15 manque. Relancez la préparation du PC.' }
    $prefix = @($python.Prefix)
    $maintenance = Join-Path $Settings.Base 'maintenance'
    $journalPath = Join-Path $Settings.Work 'update.json'
    $journal = if (Test-Path -LiteralPath $journalPath) { Get-Content -LiteralPath $journalPath -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
    if ($Cleanup) {
        if ($Check -or $Recover) { throw 'Choisir le nettoyage seul avec -Cleanup.' }
        $launcher = Join-Path $Settings.Application 'scripts\pilot_update.py'
        Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', '-u', $launcher, 'prune', '--work-dir', $Settings.Work))
        Write-SurvieUpdateProgress 'clean' 'Consultez le journal pour le détail des anciennes copies.'
        return
    }
    if ($Recover) {
        if (-not $journal) { throw 'Aucune mise à jour à récupérer.' }
        $launcher = Join-Path $Settings.Application 'scripts\pilot_update.py'
        if (-not (Test-Path -LiteralPath $launcher)) { $launcher = Join-Path $journal.previous 'scripts\pilot_update.py' }
        Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', $launcher, 'recover', '--work-dir', $Settings.Work))
        return
    }
    if ($journal -and $journal.phase -notin @('complete', 'rolled_back')) { throw 'Une mise à jour est en cours ou interrompue. Après un incident, utilisez -Recover.' }
    $installed = Get-Content -LiteralPath (Join-Path $Settings.Application 'deploy\release.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $git = Find-SurvieGit
    if (-not $git) { throw "Git manque. Relancez Installer-SetupSurvie.cmd -Check puis la préparation du PC pour l'installer." }
    $source = Join-Path $maintenance 'source'
    $script:updateVersion = 'Version installée  ' + $installed.version
    Write-SurvieUpdateProgress 'git' 'Synchronisation avec GitHub…'
    if (-not (Test-Path -LiteralPath (Join-Path $source '.git'))) {
        Invoke-SurvieUpdateCommand $git @('clone', '--branch', 'main', '--single-branch', 'https://github.com/Tanchouteur/SetupSurvie.git', $source)
    }
    if ((Get-SurvieGitOutput $git @('-C', $source, 'remote', 'get-url', 'origin')).TrimEnd('/') -ne 'https://github.com/Tanchouteur/SetupSurvie.git') { throw 'Le dépôt de maintenance ne pointe pas vers le dépôt prévu.' }
    if (Get-SurvieGitOutput $git @('-C', $source, 'status', '--porcelain')) { throw 'Modifications locales dans le dépôt de maintenance : elles sont conservées. Aucune mise à jour appliquée.' }
    if ((Get-SurvieGitOutput $git @('-C', $source, 'branch', '--show-current')) -ne 'main') { throw 'Le dépôt de maintenance doit être sur main.' }
    Invoke-SurvieUpdateCommand $git @('-C', $source, 'fetch', 'origin', 'main')
    $ahead = (Get-SurvieGitOutput $git @('-C', $source, 'rev-list', '--count', 'origin/main..HEAD')).Trim()
    if ($ahead -ne '0') { throw 'Le dépôt de maintenance contient des commits locaux. Ils sont conservés ; aucune mise à jour appliquée.' }
    Invoke-SurvieUpdateCommand $git @('-C', $source, 'merge', '--ff-only', 'origin/main')
    $available = Get-Content -LiteralPath (Join-Path $source 'deploy\release.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host ('Version installée : ' + $installed.version + ' ; disponible : ' + $available.version)
    if ([version]$available.version -le [version]$installed.version) {
        Write-SurvieUpdateProgress 'current' 'Aucun service redémarré.'
        return
    }
    $script:updateVersion = $installed.version + ' → ' + $available.version
    if ($Check) { Write-Host 'Nouvelle version disponible. Relancez sans -Check pour appliquer la mise à jour.'; return }
    Assert-SurvieWorkQueueIdle ([version]$installed.version)
    Write-SurvieUpdateProgress 'build'
    $packages = Join-Path $maintenance 'paquets'
    $null = New-Item -ItemType Directory -Path $packages -Force
    $package = Join-Path $packages ('SetupSurvie-' + $available.version + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.zip')
    Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', (Join-Path $source 'scripts\pilot_update.py'), 'build', $package))
    $digest = ((Get-Content -LiteralPath ($package + '.sha256') -Raw).Trim() -split '\s+')[0]
    if ($digest -notmatch '^[0-9a-fA-F]{64}$' -or (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash -ne $digest) { throw 'Empreinte incorrecte : application conservée.' }
    Assert-SurvieWorkQueueIdle ([version]$installed.version)
    Write-SurvieUpdateProgress 'apply' 'Le site sera indisponible pendant la sauvegarde et le redémarrage.'
    Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', '-u', (Join-Path $Settings.Application 'scripts\pilot_update.py'), 'apply', $package, '--sha256', $digest, '--work-dir', $Settings.Work))
    Write-SurvieUpdateProgress 'launcher'
    $refresh = Join-Path $Settings.Application 'scripts\windows_update.py'
    if (Test-Path -LiteralPath $refresh) { Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', $refresh, '--work-dir', $Settings.Work)) }
    Write-SurvieUpdateProgress 'done' 'Vous pouvez actualiser SetupSurvie dans votre navigateur.'
}

if ($MyInvocation.InvocationName -ne '.') {
    if (-not $ConsoleOnly -and -not $Check -and -not $Recover -and
        $env:SURVIE_NO_PAUSE -ne '1' -and [Environment]::UserInteractive) {
        exit (Show-SurvieUpdateWindow)
    }
    $mutex = New-Object Threading.Mutex($false, 'Local\SetupSurvie-MiseAJour')
    $acquired = $false; $transcript = $false
    $previousEncoding = [Console]::OutputEncoding
    $previousProgress = $env:SURVIE_UPDATE_PROGRESS
    try {
        [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
        try { $acquired = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) { throw 'Une mise à jour est déjà lancée dans une autre fenêtre.' }
        Write-SurvieUpdateProgress 'setup'
        $settings = Get-SurvieUpdateSettings
        if (Test-Path -LiteralPath (Join-Path $settings.Work 'transfer-guard.json')) {
            throw 'Transfert en cours : reprendre ou revenir a la source depuis Transferer SetupSurvie.'
        }
        $maintenance = Join-Path $settings.Base 'maintenance'
        $logs = Join-Path $maintenance 'logs'
        $null = New-Item -ItemType Directory -Path $logs -Force
        $script:updateLog = Join-Path $logs ('maj-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
        Start-Transcript -Path $script:updateLog | Out-Null
        $transcript = $true
        if (-not $Check -and -not $Cleanup -and $settings.Data) { Start-SurvieMaintenanceStatus $settings.Data }
        Set-Location -LiteralPath $maintenance
        $env:SURVIE_UPDATE_PROGRESS = '1'
        Invoke-SurvieGitUpdate $settings
        exit 0
    } catch { Write-SurvieUpdateProgress 'error' $_.Exception.Message; exit 1 }
    finally { $env:SURVIE_UPDATE_PROGRESS = $previousProgress; [Console]::OutputEncoding = $previousEncoding; if ($transcript) { Stop-Transcript | Out-Null }; if ($acquired) { $mutex.ReleaseMutex() }; $mutex.Dispose() }
}
