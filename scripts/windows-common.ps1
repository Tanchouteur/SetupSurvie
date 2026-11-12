# Shared functions; dot-sourcing never installs or starts anything.
Set-StrictMode -Version 2

function Update-SurviePath {
    $env:PATH = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
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

function Find-SurvieDockerDesktop {
    foreach ($path in @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe')
    )) { if (Test-Path -LiteralPath $path) { return $path } }
    return $null
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
    $kind = Get-SurvieDockerType
    if ($kind -eq 'linux') { return }
    if ($kind) { throw 'Docker utilise les conteneurs Windows. Choisissez les conteneurs Linux dans Docker Desktop.' }
    $desktop = Find-SurvieDockerDesktop
    if (-not $desktop) { throw 'Docker Desktop manque. Relancez 1-Preparer-le-PC.cmd.' }
    Start-Process -FilePath $desktop | Out-Null
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

function Install-SurvieDependency($Item, $CacheDir) {
    $null = New-Item -ItemType Directory -Force -Path $CacheDir
    $path = Join-Path $CacheDir $Item.file
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Host ('Téléchargement : ' + $Item.id + ' ' + $Item.version)
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing -Uri $Item.url -OutFile ($path + '.part')
        Assert-SurvieInstallerHash ($path + '.part') $Item.sha256
        Move-Item -LiteralPath ($path + '.part') -Destination $path -Force
    }
    Assert-SurvieInstallerHash $path $Item.sha256
    Write-Host ('Ouverture de l''installateur ' + $Item.id + '. Suivez ses écrans et sa licence.')
    $options = @{ FilePath = $path; Wait = $true; PassThru = $true }
    if (@($Item.arguments).Count) { $options.ArgumentList = @($Item.arguments) }
    $process = Start-Process @options
    if ($process.ExitCode -eq 3010 -or $process.ExitCode -eq 1641) { return 3010 }
    if ($process.ExitCode -ne 0) { throw ('Installation interrompue : ' + $Item.id + ' (code ' + $process.ExitCode + '). Relancez après correction.') }
    Update-SurviePath
    return 0
}
