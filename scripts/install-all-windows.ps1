# One entry point; keep both existing steps independently usable.
[CmdletBinding()]
param([string]$BaseDir, [string]$Kit, [string]$LanHost, [switch]$Resume,
    [switch]$NoBrowser, [switch]$NoStartup, [switch]$Check, [string]$CacheDir, [string]$CollectionSort)
$ErrorActionPreference = 'Stop'

function Invoke-SurvieInstallerScript([string]$Script, [array]$Arguments) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $Script) @Arguments | Out-Host
    return $LASTEXITCODE
}

function Get-SurvieResumeKit([string]$Directory) {
    $journal = Get-Content -LiteralPath (Join-Path $Directory '.installation.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    return $journal.options.kit
}

function Select-SurvieInstallKit {
    if ($Kit) { return $Kit }
    if ($Resume) { return (Get-SurvieResumeKit $BaseDir) }
    $application = Split-Path $PSScriptRoot
    if ((Split-Path $application -Leaf) -eq 'app') {
        $root = Split-Path $application
        if ((Test-Path -LiteralPath (Join-Path $root 'manifest.json') -PathType Leaf) -or
                (Test-Path -LiteralPath (Join-Path $root 'kit-building.json') -PathType Leaf)) { return $root }
    }
    if (-not $Check) {
        $chosen = Read-Host 'Dossier du kit local, ou Entrée pour télécharger avec Internet'
        if ($chosen) { return $chosen.Trim('"') }
    }
}

function Invoke-SurvieWindowsInstall {
    if ($Resume -and -not $BaseDir) {
        $suggested = if (Test-Path 'D:\') { 'D:\SetupSurvie' } else { Join-Path $env:USERPROFILE 'SetupSurvie' }
        $BaseDir = Read-Host ("Dossier de l'installation à reprendre [Entrée : " + $suggested + ']')
        if (-not $BaseDir) { $BaseDir = $suggested }
    }
    $selectedKit = Select-SurvieInstallKit
    Write-Host 'SetupSurvie : 1/2 - vérification et préparation du PC'
    $preparation = @()
    if ($Check) { $preparation += '-Check' }
    if ($selectedKit) { $preparation += @('-Kit', $selectedKit) }
    if ($CacheDir) { $preparation += @('-CacheDir', $CacheDir) }
    $code = Invoke-SurvieInstallerScript 'prepare-windows.ps1' $preparation
    if ($code -eq 3010) {
        Write-Host 'Redémarrez Windows puis relancez Installer-SetupSurvie.cmd avec les mêmes options.'
        return 3010
    }
    if ($code -ne 0 -or $Check) { return $code }
    Write-Host 'SetupSurvie : 2/2 - installation de la bibliothèque et du serveur'
    $installation = @('-SourceChosen')
    if ($BaseDir) { $installation += @('-BaseDir', $BaseDir) }
    if ($selectedKit) { $installation += @('-Kit', $selectedKit) }
    if ($CollectionSort) { $installation += @('-CollectionSort', $CollectionSort) }
    if ($LanHost) { $installation += @('-LanHost', $LanHost) }
    if ($Resume) { $installation += '-Resume' }
    if ($NoBrowser) { $installation += '-NoBrowser' }
    if ($NoStartup) { $installation += '-NoStartup' }
    return (Invoke-SurvieInstallerScript 'install-windows.ps1' $installation)
}

if ($MyInvocation.InvocationName -ne '.') {
    try { exit (Invoke-SurvieWindowsInstall) }
    catch { Write-Host ('Installation arrêtée : ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
}
