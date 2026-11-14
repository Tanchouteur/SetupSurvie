# Windows PowerShell 5.1+, no Python or WinGet required.
[CmdletBinding()]
param([switch]$Check, [string]$CacheDir = (Join-Path $env:LOCALAPPDATA 'SetupSurvie\installateurs'))
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

function Invoke-SurviePreparation {
    Initialize-SurvieTools
    $facts = Get-SurvieWindowsFacts
    if (-not $facts.X64 -or $facts.Build -lt 26100) { throw 'Ce parcours nécessite Windows 11 24H2 ou plus récent, x64. Aucun changement effectué.' }
    if (-not $facts.Virtualization) { throw 'Activez la virtualisation dans le BIOS/UEFI puis relancez. Aucun changement effectué.' }
    $catalog = Get-Content -LiteralPath (Join-Path (Split-Path $PSScriptRoot) 'deploy\windows-installers.json') -Raw | ConvertFrom-Json
    $statePath = Join-Path $CacheDir 'preparation.json'
    if (Test-Path -LiteralPath $statePath) {
        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        if ($state.restart -and $state.boot -eq $facts.Boot) {
            Write-Host 'Redémarrez Windows, puis relancez 1-Preparer-le-PC.cmd.'
            return 3010
        }
    }
    if (-not (Test-SurvieWSL)) {
        if ($Check) { throw 'WSL 2 récent manque ou doit être actualisé. Relancez sans -Check pour le préparer.' }
        $null = New-Item -ItemType Directory -Force -Path $CacheDir
        Invoke-SurvieWSLInstall
        @{ restart = $true; boot = $facts.Boot } | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
        Write-Host 'Redémarrez Windows, puis relancez ce même lanceur. Ubuntu n''est pas nécessaire.'
        return 3010
    }
    foreach ($item in $catalog.installers) {
        $available = switch ($item.id) {
            'python' { [bool](Find-SurviePython) }
            'docker' {
                $desktop=Find-SurvieDockerDesktop; $engine=Get-SurvieDockerType
                if ($desktop -and -not $engine) {
                    $directory=[IO.Path]::GetFullPath((Split-Path $desktop)).TrimEnd('\')
                    $registered=@(Get-SurvieDockerInstallLocations | Where-Object { [IO.Path]::GetFullPath($_).TrimEnd('\') -ieq $directory })
                    if (-not $registered.Count) { throw 'Fichiers Docker presents mais installation Windows non enregistree. Reparer avec l installateur officiel et le meme emplacement de donnees avant de continuer.' }
                }
                [bool]$desktop -or [bool]$engine
            }
            'ollama' { [bool](Find-SurvieOllama) }
            'git' { [bool](Find-SurvieGit) }
            default { throw 'Composant inconnu dans le catalogue.' }
        }
        if ($available) { Write-Host ($item.id + ' déjà présent ; installation conservée.'); continue }
        if ($Check) { throw ($item.id + ' manque. Relancez sans -Check pour l''installer.') }
        $code = Install-SurvieDependency $item $CacheDir
        if ($code -eq 3010) {
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
    if (-not $gpu) {
        throw 'Pilote NVIDIA à vérifier. Installez le pilote adapté à votre carte depuis https://www.nvidia.com/Download/index.aspx puis relancez. Aucun pilote choisi automatiquement.'
    }
    & $gpu.Source --query-gpu=name,memory.total --format=csv,noheader | ForEach-Object { Write-Host $_ }
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
