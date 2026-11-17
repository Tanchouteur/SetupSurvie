[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Source,[Parameter(Mandatory=$true)][string]$Destination,[string]$TaskName)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
function Disk-Info([string]$Path) {
    $root=[IO.Path]::GetPathRoot([IO.Path]::GetFullPath($Path))
    if ($root -notmatch '^([A-Za-z]):\\$') { return @{known=$false} }
    $letter=$Matches[1]
    $volume=Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue
    $partition=Get-Partition -DriveLetter $letter -ErrorAction SilentlyContinue
    if (-not $volume -or -not $partition) { return @{known=$false} }
    return @{known=([bool]$volume -and [bool]$partition);disk=$partition.DiskNumber;filesystem=$volume.FileSystemType.ToString()}
}
$docker=$null
foreach ($name in @('settings-store.json','settings.json')) {
    $path=Join-Path $env:APPDATA ('Docker\'+$name)
    if (-not (Test-Path -LiteralPath $path)) { continue }
    try {
        $settings=Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($key in @('diskImageLocation','dataFolder','wslDataRoot')) {
            $property=$settings.PSObject.Properties[$key]
            if ($property -and $property.Value -is [string] -and $property.Value) {
                $docker=@{recorded_path=$property.Value;exists=(Test-Path -LiteralPath $property.Value);active_location_verified=$false}
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
$dockerDisks=@()
$distributions=Get-ChildItem -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction SilentlyContinue
foreach ($distribution in $distributions) {
    $wsl=Get-ItemProperty -LiteralPath $distribution.PSPath
    if ($wsl.DistributionName -notin @('docker-desktop','docker-desktop-data') -or -not $wsl.BasePath) { continue }
    $base=$wsl.BasePath -replace '^\\\\\?\\',''
    $vhd=$wsl.VhdFileName
    if (-not $vhd) { $vhd='ext4.vhdx' }
    if ([IO.Path]::GetFileName($vhd) -ne $vhd) { continue }
    $dockerDisks+=Join-Path $base $vhd
    if ($wsl.DistributionName -eq 'docker-desktop' -and (Split-Path $base -Leaf) -eq 'main') {
        $parent=Split-Path $base
        $dockerDisks+=Join-Path $parent 'disk\docker_data.vhdx'
        $dockerDisks+=Join-Path $parent 'wsl-swap.vhdx'
    }
}
@{source=(Disk-Info $Source);destination=(Disk-Info $Destination);docker=$docker;docker_disks=$dockerDisks;startup_enabled=[bool]$startup} | ConvertTo-Json -Depth 5 -Compress
