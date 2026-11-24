[CmdletBinding()]
param([string]$Source,[Parameter(Mandatory=$true)][string]$Destination,[string]$TaskName)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
. (Join-Path $PSScriptRoot 'windows-common.ps1')

function Local-Path([string]$Path) {
    $Path=$Path -replace '^\\\\\?\\',''
    if ($Path -notmatch '^[A-Za-z]:[\\/]') { return }
    try { [IO.Path]::GetFullPath($Path) } catch { }
}

$diskCache=@{}
function Disk-Info([string]$Path) {
    $local=Local-Path $Path
    if (-not $local) { return @{known=$false} }
    $letter=$local.Substring(0,1)
    if (-not $diskCache.ContainsKey($letter)) {
        $volume=Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue
        $partition=Get-Partition -DriveLetter $letter -ErrorAction SilentlyContinue
        $diskCache[$letter]=if ($volume -and $partition) {
            @{known=$true;disk=$partition.DiskNumber;filesystem=[string]$volume.FileSystemType}
        } else { @{known=$false} }
    }
    return $diskCache[$letter]
}

function Located-Path([string]$Path) {
    return @{path=$Path;physical_disk=(Disk-Info $Path)}
}

function Existing-Vhds([string]$Root) {
    foreach ($relative in @('docker_data.vhdx','disk\docker_data.vhdx','data\docker_data.vhdx','DockerDesktopWSL\disk\docker_data.vhdx')) {
        $path=Join-Path $Root $relative
        if (Test-Path -LiteralPath $path -PathType Leaf) { $path }
    }
}

$docker=$null
foreach ($name in @('settings-store.json','settings.json')) {
    $path=Join-Path $env:APPDATA ('Docker\'+$name)
    if (-not (Test-Path -LiteralPath $path)) { continue }
    try {
        $settings=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($key in @('customWslDistroDir','diskImageLocation','dataFolder','wslDataRoot')) {
            $property=$settings.PSObject.Properties[$key]
            if ($property -and $property.Value -is [string]) {
                $location=Local-Path $property.Value
                if (-not $location) { continue }
                $docker=@{recorded_path=$location;physical_disk=(Disk-Info $location);exists=(Test-Path -LiteralPath $location);active_location_verified=$false}
                break
            }
        }
    } catch { }
    if ($docker) { break }
}
$startup=$false
if ($TaskName) {
    $task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    $startup=$task -and $task.State -ne 'Disabled' -and $task.Description -eq 'SetupSurvie managed document services startup without AI'
}
$backend=@(Get-Process -Name 'com.docker.backend' -ErrorAction SilentlyContinue | ForEach-Object {
    try { Local-Path $_.Path } catch { }
} | Select-Object -Unique)
$registered=@(Get-SurvieDockerInstallLocations | ForEach-Object { Local-Path $_ } | Select-Object -Unique)
$dataDisks=@()
$managedRoots=@()
$systemDisks=@()
$swapDisks=@()
$distributions=Get-ChildItem -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction SilentlyContinue
foreach ($distribution in $distributions) {
    $wsl=Get-ItemProperty -LiteralPath $distribution.PSPath -ErrorAction SilentlyContinue
    if (-not $wsl) { continue }
    $name=$wsl.PSObject.Properties['DistributionName']
    $root=$wsl.PSObject.Properties['BasePath']
    if (-not $name -or -not $root -or $name.Value -notin @('docker-desktop','docker-desktop-data')) { continue }
    $base=Local-Path $root.Value
    if (-not $base) { continue }
    $property=$wsl.PSObject.Properties['VhdFileName']
    $vhd=if ($property -and $property.Value) { $property.Value } else { 'ext4.vhdx' }
    if ([IO.Path]::GetFileName($vhd) -ne $vhd) { continue }
    $path=Join-Path $base $vhd
    if ($name.Value -eq 'docker-desktop-data') {
        if (Test-Path -LiteralPath $path -PathType Leaf) { $dataDisks+=$path }
    } else {
        if (Test-Path -LiteralPath $path -PathType Leaf) { $systemDisks+=$path }
        if ((Split-Path $base -Leaf) -eq 'main') {
            $parent=Split-Path $base
            $managedRoots+=$parent
            $swapDisks+=Join-Path $parent 'wsl-swap.vhdx'
        }
    }
}
if ($docker) {
    if ($docker.recorded_path -match '\.vhdx$' -and (Test-Path -LiteralPath $docker.recorded_path -PathType Leaf)) {
        $dataDisks+=$docker.recorded_path
    } else {
        $managedRoots+=$docker.recorded_path
    }
}
if (-not $managedRoots.Count -and -not $dataDisks.Count) {
    $managedRoots+=Join-Path $env:LOCALAPPDATA 'Docker\wsl'
}
$dataDisks+=@($managedRoots | Select-Object -Unique | ForEach-Object { Existing-Vhds $_ })
$dataDisks=@($dataDisks | Select-Object -Unique)
$dockerDisks=@(($dataDisks+$systemDisks+$swapDisks) | Select-Object -Unique)
@{
    source=(Disk-Info $Source);destination=(Disk-Info $Destination);docker=$docker
    docker_evidence=@{
        backend=@($backend | ForEach-Object { Located-Path $_ })
        registration=@($registered | ForEach-Object { Located-Path $_ })
        data_images=@($dataDisks | ForEach-Object { Located-Path $_ })
        wsl_system=@($systemDisks | ForEach-Object { Located-Path $_ })
    }
    docker_disks=$dockerDisks;startup_enabled=[bool]$startup
} | ConvertTo-Json -Depth 6 -Compress
