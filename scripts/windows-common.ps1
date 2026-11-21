# Shared functions; dot-sourcing never installs or starts anything.
Set-StrictMode -Version 2

function Get-SurviePrivateIPv4 {
    return @(Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetProfile.NetworkCategory -eq 'Private' } | ForEach-Object { $_.IPv4Address.IPAddress } | Select-Object -Unique)
}

function Select-SurvieLanHost([string]$Requested) {
    $addresses=@(Get-SurviePrivateIPv4)
    if ($Requested -and $Requested -ieq 'LOCAL') { return '' }
    if (-not $Requested) {
        if ($addresses.Count -eq 1) {
            $Requested=Read-Host ('Reseau prive : '+$addresses[0]+' ; Entree pour partager, ou LOCAL pour limiter au PC')
            if (-not $Requested) { return $addresses[0] }
        } else {
            foreach ($address in $addresses) { Write-Host ('Reseau prive : '+$address) }
            $Requested=Read-Host 'Indiquez une adresse privee ci-dessus, ou LOCAL pour limiter au PC'
        }
    }
    if ($Requested -ieq 'LOCAL') { return '' }
    if (-not $Requested -or $addresses -notcontains $Requested) { throw 'Choisissez une IPv4 du reseau Windows prive. Passez le reseau domestique en prive puis relancez, ou choisissez LOCAL.' }
    return $Requested
}

function Test-SurvieLanEndpoint([string]$Address,[string]$Version) {
    $value=Invoke-RestMethod -Uri ('http://'+$Address+':8080/api/health') -TimeoutSec 15 -ErrorAction Stop
    if (-not $value.ok -or $value.version -ne $Version) { throw 'La version installee ne repond pas sur son adresse reseau.' }
}

function Disable-SurviePublicOllamaRules([string]$Program,[string]$BackupDir) {
    if (-not (Test-Path -LiteralPath $Program -PathType Leaf) -or [IO.Path]::GetFileName($Program) -ine 'ollama.exe') { throw 'Executable Ollama exact requis pour revoir ses regles.' }
    $expected=[IO.Path]::GetFullPath($Program)
    $rules=@(Get-NetFirewallRule -Direction Inbound -Action Allow | Where-Object DisplayName -eq 'ollama' | Where-Object { ([string]$_.Profile) -match 'Public|Any' } | Where-Object {
        $filter=$_ | Get-NetFirewallApplicationFilter
        $filter.Program -and [IO.Path]::GetFullPath($filter.Program) -ieq $expected
    })
    if ($rules.Count) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        $backup=Join-Path $BackupDir ('ollama-firewall-'+[guid]::NewGuid().ToString('N')+'.xml')
        $rules | Export-Clixml -LiteralPath $backup
        foreach ($rule in $rules) { Disable-NetFirewallRule -Name $rule.Name | Out-Null }
    }
}

function Update-SurviePath {
    # Keep portable tools supplied by the caller as well as newly installed tools.
    $paths = @($env:PATH, [Environment]::GetEnvironmentVariable('Path', 'Machine'), [Environment]::GetEnvironmentVariable('Path', 'User')) -join ';'
    $env:PATH = (($paths -split ';' | Where-Object { $_ } | Select-Object -Unique) -join ';')
}

function Find-SurviePython {
    foreach ($candidate in @('py', 'python', 'python3')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        $prefix = @()
        if ($candidate -eq 'py') { $prefix = @('-3') }
        try {
            & $command.Source @prefix -c 'import sys,struct; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,15) and struct.calcsize(chr(80))==8 else 1)' 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return @{ Path = $command.Source; Prefix = $prefix } }
        } catch { }
    }
    return $null
}

function Find-SurvieGit {
    $command = Get-Command git -ErrorAction SilentlyContinue
    $candidates = @()
    if ($command) { $candidates += $command.Source }
    $candidates += @((Join-Path $env:ProgramFiles 'Git\cmd\git.exe'), (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd\git.exe'))
    if (Get-Command Get-AppxPackage -ErrorAction SilentlyContinue) {
        foreach ($package in @(Get-AppxPackage -Name '*CodexPrimaryRuntime*' -ErrorAction SilentlyContinue | Sort-Object Version -Descending)) {
            $candidates += Join-Path $package.InstallLocation 'dependencies\native\git\cmd\git.exe'
        }
    }
    foreach ($path in $candidates) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        try {
            & $path --version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return $path }
        } catch { }
    }
    return $null
}

function Get-SurvieDockerInstallLocations {
    foreach ($hive in @('HKCU:','HKLM:')) {
        foreach ($key in @('SOFTWARE\Docker Inc.\Docker Desktop','SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Docker Desktop','SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Docker Desktop')) {
            $value=Get-ItemProperty -LiteralPath ($hive+'\'+$key) -ErrorAction SilentlyContinue
            if (-not $value) { continue }
            foreach ($name in @('InstallLocation','InstallPath')) {
                $property=$value.PSObject.Properties[$name]
                if ($property -and $property.Value) { [string]$property.Value }
            }
        }
    }
}

function Find-SurvieDockerDesktop {
    $candidates = @((Get-SurvieDockerInstallLocations | ForEach-Object { Join-Path $_ 'Docker Desktop.exe' })) + @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe')
    )
    $cli = Get-Command docker -ErrorAction SilentlyContinue
    if ($cli) {
        $directory = Split-Path (Split-Path (Split-Path $cli.Source))
        $candidates += Join-Path $directory 'Docker Desktop.exe'
    }
    # A running Desktop can live on a data disk without being registered in PATH.
    foreach ($process in @(Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue)) {
        try { if ($process.Path) { $candidates += $process.Path } } catch { }
    }
    foreach ($path in $candidates) { if (Test-Path -LiteralPath $path -PathType Leaf) { return $path } }
    return $null
}

function Initialize-SurvieTools {
    Update-SurviePath
    $desktop = Find-SurvieDockerDesktop
    if ($desktop) {
        $bin = Join-Path (Split-Path $desktop) 'resources\bin'
        if (Test-Path -LiteralPath (Join-Path $bin 'docker.exe')) { $env:PATH = $bin + ';' + $env:PATH }
    }
    $ollama = Find-SurvieOllama
    if ($ollama) { $env:PATH = (Split-Path $ollama) + ';' + $env:PATH }
}

function Find-SurvieOllama {
    $command = Get-Command ollama -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $path = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (Test-Path -LiteralPath $path) { return $path }
    return $null
}

function Get-SurvieDockerType {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $command) { return '' }
    try {
        $value = & $command.Source info --format '{{.OSType}}' 2>$null
        if ($LASTEXITCODE -eq 0) { return "$value".Trim() }
    } catch { }
    return ''
}

function Start-SurvieDocker {
    param([switch]$Automatic,[string]$WorkDir)
    $kind = Get-SurvieDockerType
    if ($kind -eq 'linux') { return }
    if ($kind) { throw 'Docker utilise les conteneurs Windows. Choisissez les conteneurs Linux dans Docker Desktop.' }
    $desktop = Find-SurvieDockerDesktop
    if (-not $desktop) { throw 'Docker Desktop manque. Relancez 1-Preparer-le-PC.cmd.' }
    $directory=[IO.Path]::GetFullPath((Split-Path $desktop)).TrimEnd('\')
    $registered=@(Get-SurvieDockerInstallLocations | Where-Object { [IO.Path]::GetFullPath($_).TrimEnd('\') -ieq $directory })
    if (-not $registered.Count) { throw 'Docker Desktop est present mais son installation Windows est absente ou incoherente. Reparez Docker avec son installateur officiel ; aucun lancement automatique effectue.' }
    $running=@(Get-Process -Name 'Docker Desktop','com.docker.backend' -ErrorAction SilentlyContinue | Where-Object { try { $_.Path -and [IO.Path]::GetFullPath($_.Path).StartsWith($directory+'\',[StringComparison]::OrdinalIgnoreCase) } catch { $false } })
    if (-not $running.Count) {
        if ($Automatic -and -not $WorkDir) { throw 'Dossier prive requis pour limiter les tentatives automatiques Docker.' }
        if ($WorkDir) {
            $attempt=Join-Path $WorkDir 'docker-start-attempt.json'
            $boot=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o')
            if ($Automatic -and (Test-Path -LiteralPath $attempt)) {
                $last=Get-Content -LiteralPath $attempt -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($last.boot -eq $boot) { throw 'Docker a deja ete lance automatiquement depuis ce demarrage Windows. Verifier le journal puis utiliser Ouvrir SetupSurvie pour une reprise explicite.' }
            }
            @{boot=$boot;desktop=$desktop;attempted=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $attempt -Encoding UTF8
        }
        Start-Process -FilePath $desktop -WindowStyle Hidden | Out-Null
    }
    Write-Host 'Docker Desktop démarre. Validez son accueil et sa licence si nécessaire.'
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        Start-Sleep -Seconds 2
        $kind = Get-SurvieDockerType
        if ($kind -eq 'linux') { return }
        if ($kind) { throw 'Choisissez les conteneurs Linux dans Docker Desktop.' }
    }
    throw 'Docker ne répond pas encore. Terminez sa configuration puis relancez ce lanceur.'
}

function Assert-SurvieInstallerHash($Path, $Expected) {
    if ($Expected -notmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Expected) {
        throw 'Installateur incomplet ou modifié. Aucun programme exécuté ; retirez ce fichier du cache puis réessayez.'
    }
}

function Get-SurvieInstaller($Item, $CacheDir, [switch]$Offline) {
    $path = Join-Path $CacheDir $Item.file
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        if ($Offline) { throw ('Installateur manquant dans le kit : ' + $Item.file) }
        $null = New-Item -ItemType Directory -Force -Path $CacheDir
        Write-Host ('Téléchargement : ' + $Item.id + ' ' + $Item.version)
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri $Item.url -OutFile ($path + '.part')
        Assert-SurvieInstallerHash ($path + '.part') $Item.sha256
        Move-Item -LiteralPath ($path + '.part') -Destination $path -Force
    }
    Assert-SurvieInstallerHash $path $Item.sha256
    return $path
}

function Install-SurvieDependency($Item, $CacheDir, [switch]$Offline) {
    $path = Get-SurvieInstaller $Item $CacheDir -Offline:$Offline
    Write-Host ('Ouverture de l''installateur ' + $Item.id + '. Suivez ses écrans et sa licence.')
    $options = @{ FilePath = $path; Wait = $true; PassThru = $true }
    if (@($Item.arguments).Count) { $options.ArgumentList = @($Item.arguments) }
    $process = Start-Process @options
    if ($process.ExitCode -eq 3010 -or $process.ExitCode -eq 1641) { return 3010 }
    if ($process.ExitCode -ne 0) { throw ('Installation interrompue : ' + $Item.id + ' (code ' + $process.ExitCode + '). Relancez après correction.') }
    Update-SurviePath
    return 0
}
