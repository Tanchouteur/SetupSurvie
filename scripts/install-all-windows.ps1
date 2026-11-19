# One entry point; keep both existing steps independently usable.
[CmdletBinding()]
param([string]$BaseDir, [string]$Kit, [string]$LanHost, [switch]$Resume,
    [switch]$NoBrowser, [switch]$NoStartup, [switch]$Check, [string]$CacheDir, [string]$CollectionSort)
$ErrorActionPreference = 'Stop'

function Invoke-SurvieInstallerScript([string]$Script, [array]$Arguments) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $Script) @Arguments | Out-Host
    return $LASTEXITCODE
}

function Invoke-SurvieWindowsInstall {
    Write-Host 'SetupSurvie : 1/2 - vérification et préparation du PC'
    $preparation = @()
    if ($Check) { $preparation += '-Check' }
    if ($CacheDir) { $preparation += @('-CacheDir', $CacheDir) }
    $code = Invoke-SurvieInstallerScript 'prepare-windows.ps1' $preparation
    if ($code -eq 3010) {
        Write-Host 'Redémarrez Windows puis relancez Installer-SetupSurvie.cmd avec les mêmes options.'
        return 3010
    }
    if ($code -ne 0 -or $Check) { return $code }
    Write-Host 'SetupSurvie : 2/2 - installation de la bibliothèque et du serveur'
    $installation = @()
    if ($BaseDir) { $installation += @('-BaseDir', $BaseDir) }
    if ($Kit) { $installation += @('-Kit', $Kit) }
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
