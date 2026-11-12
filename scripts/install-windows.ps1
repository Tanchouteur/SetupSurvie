[CmdletBinding()]
param([string]$BaseDir, [string]$Kit, [string]$LanHost, [switch]$Resume, [switch]$NoBrowser, [switch]$NoStartup)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'windows-common.ps1')
try {
    Initialize-SurvieTools
    $python = Find-SurviePython
    if (-not $python) { throw 'Python x64 3.11 à 3.15 manque. Lancez 1-Preparer-le-PC.cmd.' }
    if (-not (Find-SurvieOllama)) { throw 'Ollama manque. Lancez 1-Preparer-le-PC.cmd.' }
    if (-not $BaseDir) {
        $suggested = if (Test-Path 'D:\') { 'D:\SetupSurvie' } else { Join-Path $env:USERPROFILE 'SetupSurvie' }
        $BaseDir = Read-Host ("Dossier d'installation [Entrée : " + $suggested + ']')
        if (-not $BaseDir) { $BaseDir = $suggested }
    }
    $prefix = $python.Prefix
    & $python.Path @prefix -X utf8 (Join-Path $PSScriptRoot 'install_wizard.py') --base-dir $BaseDir --check
    if ($LASTEXITCODE -ne 0) { throw 'Installation non démarrée. Suivez le message ci-dessus pour conserver votre installation existante.' }
    if (-not $Kit -and -not $Resume) {
        $Kit = Read-Host 'Dossier du kit local, ou Entrée pour télécharger avec Internet'
    }
    if (-not $LanHost -and -not $Resume) {
        $connections = @(Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetProfile.NetworkCategory -eq 'Private' })
        foreach ($connection in $connections) { Write-Host ($connection.InterfaceAlias + ' : ' + $connection.IPv4Address.IPAddress) }
        $LanHost = Read-Host 'Pour partager sur votre réseau privé, indiquez une IPv4 ci-dessus ; Entrée limite au PC'
    }
    if ($Resume) {
        $journal = Get-Content -LiteralPath (Join-Path $BaseDir '.installation.json') -Raw | ConvertFrom-Json
        if (-not $Kit -and $journal.options.kit) { $Kit = $journal.options.kit }
        if (-not $LanHost) { $LanHost = $journal.options.lan_host }
        if (-not $PSBoundParameters.ContainsKey('NoStartup')) { $NoStartup = -not $journal.options.startup }
    }
    Start-SurvieDocker
    Write-Host 'Dans Docker Desktop > Settings > Resources > Advanced, vérifiez Disk image location sur le disque choisi.'
    Write-Host 'Les images Docker occupent de la place en plus des données. Le lanceur ne déplace pas le disque Docker.'
    if ((Read-Host 'Emplacement Docker vérifié ? Tapez O pour continuer') -notmatch '^(o|oui)$') { throw 'Vérifiez le disque Docker puis relancez.' }
    $arguments = @('-X', 'utf8', (Join-Path $PSScriptRoot 'install_wizard.py'), '--base-dir', $BaseDir)
    if ($Kit) { $arguments += @('--kit', $Kit) }
    if ($Resume) { $arguments += '--resume' }
    if ($NoStartup) { $arguments += '--no-startup' }
    if ($LanHost) { $arguments += @('--lan-host', $LanHost) }
    & $python.Path @prefix @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Installation interrompue. Corrigez le problème affiché puis relancez avec -Resume pour reprendre.' }
    if ($LanHost) {
        Write-Host 'Windows va demander les droits administrateur pour les règles du réseau privé. Les API du moteur restent bloquées aux lecteurs.'
        $firewall = Join-Path $BaseDir 'application\scripts\open-lan-firewall.ps1'
        try {
            $process = Start-Process -FilePath 'powershell.exe' -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $firewall + '"') -Verb RunAs -Wait -PassThru
            if ($process.ExitCode -ne 0) { throw 'Règles non confirmées.' }
        } catch { Write-Warning 'Application installée ; règles réseau non confirmées. Voir le guide Windows avant utilisation sur téléphone.' }
        Write-Host ('Accès réseau à tester : https://' + $LanHost + ':8443 ; voir le guide pour installer le certificat public sur les téléphones.')
    }
    if (-not $NoBrowser) { Start-Process 'http://localhost:8080' }
    exit 0
} catch { Write-Host ('Installation arrêtée : ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
