# Windows PowerShell 5.1+, no Python or WinGet required.
[CmdletBinding()]
param([switch]$Check, [string]$CacheDir = (Join-Path $env:LOCALAPPDATA 'SetupSurvie\installateurs'),
    [string]$Kit, [switch]$DownloadOnly)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'windows-common.ps1')

function Get-SurvieWindowsFacts {
    $os = Get-CimInstance Win32_OperatingSystem
    $system = Get-CimInstance Win32_ComputerSystem
    $processors = @(Get-CimInstance Win32_Processor)
    $virtualization = $system.HypervisorPresent -or (@($processors | Where-Object { $_.VirtualizationFirmwareEnabled }).Count -gt 0)
    return @{ Build = [int]$os.BuildNumber; X64 = ($env:PROCESSOR_ARCHITECTURE -eq 'AMD64'); Virtualization = $virtualization; Boot = $os.LastBootUpTime.ToUniversalTime().ToString('o') }
}

function Get-SurvieWSLVersion {
    try {
        $text = (& wsl.exe --version 2>$null | Out-String) -replace "`0", ''
        if ($LASTEXITCODE -ne 0) { return $null }
        $match = [regex]::Match($text, '\d+\.\d+\.\d+')
        if ($match.Success) { return [version]$match.Value }
    } catch { }
    return $null
}

function Test-SurvieWSL {
    $version = Get-SurvieWSLVersion
    return $version -and $version -ge [version]'2.1.5'
}

function Invoke-SurvieWSLInstall {
    Write-Host 'Windows va demander les droits administrateur pour préparer WSL 2. Aucun redémarrage forcé.'
    $arguments = @('--install', '--no-distribution', '--no-launch')
    if (Get-SurvieWSLVersion) { $arguments = @('--update') }
    $process = Start-Process -FilePath 'wsl.exe' -ArgumentList $arguments -Verb RunAs -Wait -PassThru
    if ($process.ExitCode -notin @(0, 3010, 1641)) { throw 'WSL n''a pas pu être préparé. Vérifiez Windows Update et la virtualisation, puis relancez.' }
}


function Get-SurvieKitInstallerFolder([string]$Root) {
    $path = (Resolve-Path -LiteralPath $Root).ProviderPath
    if (Test-Path -LiteralPath (Join-Path $path 'kit-building.json')) { throw 'Kit encore en préparation.' }
    $manifest = Get-Content -LiteralPath (Join-Path $path 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.schema -ne 1 -or $manifest.kind -ne 'SetupSurvie public pilot kit' -or $manifest.files -isnot [array]) {
        throw 'Choisissez un kit public SetupSurvie complet.'
    }
    return (Join-Path $path 'installateurs-windows')
}

function Test-SurvieVirtualMachinePlatform {
    $feature = Get-CimInstance Win32_OptionalFeature -Filter "Name='VirtualMachinePlatform'"
    return ($feature -and $feature.InstallState -eq 1)
}

function Install-SurvieOfflineWSL([string]$Msi, [string]$Source) {
    if (-not (Test-SurvieVirtualMachinePlatform)) {
        $arguments = '/Online /Enable-Feature /FeatureName:VirtualMachinePlatform /All /NoRestart /LimitAccess'
        if (Test-Path -LiteralPath $Source -PathType Container) { $arguments += ' /Source:"' + $Source + '"' }
        $process = Start-Process -FilePath "$env:SystemRoot\System32\dism.exe" -ArgumentList $arguments -Verb RunAs -Wait -PassThru
        if ($process.ExitCode -in @(3010, 1641)) { return 3010 }
        if ($process.ExitCode -ne 0) { throw 'La plateforme de virtualisation manque dans Windows. Fournissez les fichiers sources correspondant à ce Windows dans installateurs-windows\sxs.' }
    }
    if ($Msi) {
        $arguments = '/i "' + $Msi + '" /passive /norestart'
        $process = Start-Process -FilePath "$env:SystemRoot\System32\msiexec.exe" -ArgumentList $arguments -Verb RunAs -Wait -PassThru
        if ($process.ExitCode -notin @(0, 3010, 1641)) { throw ('Installation locale de WSL interrompue (code ' + $process.ExitCode + ').') }
        return 3010
    }
    return 0
}

function Test-SurvieDependencyPresent([string]$Id) {
    switch ($Id) {
        'python' { return [bool](Find-SurviePython) }
        'docker' {
            $desktop=Find-SurvieDockerDesktop; $engine=Get-SurvieDockerType
            if ($desktop -and -not $engine) {
                $directory=[IO.Path]::GetFullPath((Split-Path $desktop)).TrimEnd('\')
                $registered=@(Get-SurvieDockerInstallLocations | Where-Object { [IO.Path]::GetFullPath($_).TrimEnd('\') -ieq $directory })
                if (-not $registered.Count) { throw 'Fichiers Docker presents mais installation Windows non enregistree. Reparer avec l installateur officiel et le meme emplacement de donnees avant de continuer.' }
            }
            return ([bool]$desktop -or [bool]$engine)
        }
        'ollama' { return [bool](Find-SurvieOllama) }
        'git' { return [bool](Find-SurvieGit) }
        default { throw 'Composant inconnu dans le catalogue.' }
    }
}

function Invoke-SurviePreparation {
    $catalogPath = Join-Path (Split-Path $PSScriptRoot) 'deploy\windows-installers.json'
    $catalog = Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $offline = [bool]$Kit
    if ($DownloadOnly -and (-not $offline -or $Check)) { throw 'Indiquez un kit avec -Kit pour préparer ses installateurs.' }
    $installerDir = if ($offline) { Get-SurvieKitInstallerFolder $Kit } else { $CacheDir }
    if ($DownloadOnly) {
        foreach ($item in @($catalog.wsl) + @($catalog.installers)) {
            $null = Get-SurvieInstaller $item $installerDir
        }
        Write-Host 'Installateurs Windows vérifiés sur le kit.'
        return 0
    }
    Initialize-SurvieTools
    $facts = Get-SurvieWindowsFacts
    if (-not $facts.X64 -or $facts.Build -lt 26100) { throw 'Ce parcours nécessite Windows 11 24H2 ou plus récent, x64. Aucun changement effectué.' }
    if (-not $facts.Virtualization) { throw 'Activez la virtualisation dans le BIOS/UEFI puis relancez. Aucun changement effectué.' }
    $statePath = Join-Path $CacheDir 'preparation.json'
    if (Test-Path -LiteralPath $statePath) {
        $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($state.restart -and $state.boot -eq $facts.Boot) {
            Write-Host 'Redémarrez Windows, puis relancez le même lanceur.'
            return 3010
        }
    }
    $wslMissing = -not (Test-SurvieWSL)
    $platformMissing = $offline -and -not (Test-SurvieVirtualMachinePlatform)
    if ($Check -and ($wslMissing -or $platformMissing)) { throw 'WSL 2 ou sa plateforme de virtualisation manque. Relancez sans -Check pour le préparer.' }
    if ($offline -and -not $Check) {
        # Before modifying Windows, reject a missing or damaged local installer.
        foreach ($item in $catalog.installers) {
            if (-not (Test-SurvieDependencyPresent $item.id)) {
                $null = Get-SurvieInstaller $item $installerDir -Offline
            }
        }
    }
    if ($wslMissing -or $platformMissing) {
        $restart = 3010
        if ($offline) {
            $msi = if ($wslMissing) { Get-SurvieInstaller $catalog.wsl $installerDir -Offline }
            $restart = Install-SurvieOfflineWSL $msi (Join-Path $installerDir 'sxs')
        } else {
            Invoke-SurvieWSLInstall
        }
        if ($restart -eq 3010) {
            $null = New-Item -ItemType Directory -Force -Path $CacheDir
            @{ restart = $true; boot = $facts.Boot } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
            Write-Host 'Redémarrez Windows, puis relancez ce même lanceur. Ubuntu n''est pas nécessaire.'
            return 3010
        }
    }
    foreach ($item in $catalog.installers) {
        $available = Test-SurvieDependencyPresent $item.id
        if ($available) { Write-Host ($item.id + ' déjà présent ; installation conservée.'); continue }
        if ($Check) { throw ($item.id + ' manque. Relancez sans -Check pour l''installer.') }
        $code = Install-SurvieDependency $item $installerDir -Offline:$offline
        if ($code -eq 3010) {
            $null = New-Item -ItemType Directory -Force -Path $CacheDir
            @{ restart = $true; boot = $facts.Boot } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
            Write-Host 'Redémarrez Windows puis relancez ce même lanceur.'
            return 3010
        }
        # An installer may complete successfully without installing the chosen component.
        $found = switch ($item.id) {
            'python' { [bool](Find-SurviePython) }
            'docker' { [bool](Find-SurvieDockerDesktop) -or [bool](Get-SurvieDockerType) }
            'ollama' { [bool](Find-SurvieOllama) }
            'git' { [bool](Find-SurvieGit) }
        }
        if (-not $found) { throw ($item.id + ' reste introuvable. Fermez cette fenêtre et relancez le lanceur après avoir terminé son installation.') }
    }
    $gpu = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($offline -and -not $gpu) {
        Write-Host 'Pilote NVIDIA indisponible. Le moteur local pourra utiliser le processeur.'
        return 0
    }
    if (-not $gpu) {
        throw 'Pilote NVIDIA à vérifier. Installez le pilote adapté à votre carte depuis https://www.nvidia.com/Download/index.aspx puis relancez. Aucun pilote choisi automatiquement.'
    }
    & $gpu.Source --query-gpu=name,memory.total --format=csv,noheader | ForEach-Object { Write-Host $_ }
    if ($offline -and $LASTEXITCODE -ne 0) {
        Write-Host 'Le pilote NVIDIA ne répond pas. Le moteur local pourra utiliser le processeur.'
        return 0
    }
    if ($LASTEXITCODE -ne 0) { throw 'Le pilote NVIDIA ne répond pas. Corrigez-le puis relancez.' }
    Write-Host 'Prérequis présents. Docker et le GPU seront encore à valider en usage réel.'
    Write-Host 'Le lanceur Installer-SetupSurvie.cmd poursuit automatiquement ; sinon, lancez 2-Installer-SetupSurvie.cmd.'
    return 0
}

if ($MyInvocation.InvocationName -ne '.') {
    $mutex = New-Object Threading.Mutex($false, 'Local\SetupSurvie-Preparation')
    $acquired = $false
    try {
        try { $acquired = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) { throw 'Une préparation du PC est déjà en cours.' }
        exit (Invoke-SurviePreparation)
    }
    catch { Write-Host ('Préparation arrêtée : ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
    finally { if ($acquired) { $mutex.ReleaseMutex() }; $mutex.Dispose() }
}
