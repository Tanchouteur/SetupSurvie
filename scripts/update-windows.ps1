[CmdletBinding()]
param([string]$WorkDir, [switch]$Check, [switch]$Recover)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'windows-common.ps1')

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
    & $File @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) { throw ('Étape interrompue (code ' + $LASTEXITCODE + '). Les sauvegardes sont conservées ; consultez le journal.') }
}

function Get-SurvieGitOutput([string]$Git, [array]$Arguments) {
    $value = @(& $Git @Arguments)
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de vérifier le dépôt Git de maintenance.' }
    return ($value -join "`n")
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
    Write-Host 'Récupération des changements depuis GitHub...'
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
    if ([version]$available.version -le [version]$installed.version) { Write-Host 'SetupSurvie est déjà à jour. Aucun service redémarré.'; return }
    if ($Check) { Write-Host 'Nouvelle version disponible. Relancez sans -Check pour appliquer la mise à jour.'; return }
    $packages = Join-Path $maintenance 'paquets'
    $null = New-Item -ItemType Directory -Path $packages -Force
    $package = Join-Path $packages ('SetupSurvie-' + $available.version + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.zip')
    Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', (Join-Path $source 'scripts\pilot_update.py'), 'build', $package))
    $digest = ((Get-Content -LiteralPath ($package + '.sha256') -Raw).Trim() -split '\s+')[0]
    if ($digest -notmatch '^[0-9a-fA-F]{64}$' -or (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash -ne $digest) { throw 'Empreinte incorrecte : application conservée.' }
    Write-Host 'Sauvegarde puis mise à jour. Le site sera brièvement indisponible ; les transferts indépendants continuent.'
    Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', (Join-Path $Settings.Application 'scripts\pilot_update.py'), 'apply', $package, '--sha256', $digest, '--work-dir', $Settings.Work))
    $refresh = Join-Path $Settings.Application 'scripts\windows_update.py'
    if (Test-Path -LiteralPath $refresh) { Invoke-SurvieUpdateCommand $python.Path @($prefix + @('-X', 'utf8', $refresh, '--work-dir', $Settings.Work)) }
    Write-Host 'Mise à jour terminée. Actualisez http://localhost:8080.'
}

if ($MyInvocation.InvocationName -ne '.') {
    $mutex = New-Object Threading.Mutex($false, 'Local\SetupSurvie-MiseAJour')
    $acquired = $false; $transcript = $false
    try {
        try { $acquired = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) { throw 'Une mise à jour est déjà lancée dans une autre fenêtre.' }
        $settings = Get-SurvieUpdateSettings
        $maintenance = Join-Path $settings.Base 'maintenance'
        $logs = Join-Path $maintenance 'logs'
        $null = New-Item -ItemType Directory -Path $logs -Force
        Start-Transcript -Path (Join-Path $logs ('maj-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')) | Out-Null
        $transcript = $true
        Set-Location -LiteralPath $maintenance
        Invoke-SurvieGitUpdate $settings
        exit 0
    } catch { Write-Host ('Mise à jour arrêtée : ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
    finally { if ($transcript) { Stop-Transcript | Out-Null }; if ($acquired) { $mutex.ReleaseMutex() }; $mutex.Dispose() }
}
