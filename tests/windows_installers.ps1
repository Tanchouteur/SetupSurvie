# Run with Windows PowerShell 5.1 in CI; all machine mutations are mocked.
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
foreach ($path in @((Join-Path $root 'scripts'), $PSScriptRoot)) {
    Get-ChildItem -LiteralPath $path -Filter '*.ps1' | ForEach-Object {
        $tokens = $null; $errors = $null
        $null = [Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$tokens, [ref]$errors)
        if ($errors.Count) { throw ($_.Name + ': ' + (($errors | ForEach-Object { 'line ' + $_.Extent.StartLineNumber + ': ' + $_.Message }) -join '; ')) }
    }
}
. (Join-Path $root 'scripts\prepare-windows.ps1') -Check -CacheDir (Join-Path $env:TEMP ('survie-mock-' + [guid]::NewGuid()))
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
# Real discovery functions, with a tiny portable-layout fixture and no execution.
& {
    . (Join-Path $root 'scripts\windows-common.ps1')
    $portable = Join-Path $env:TEMP ('survie-tools-' + [guid]::NewGuid())
    $null = New-Item -ItemType Directory -Path (Join-Path $portable 'resources\bin') -Force
    $cli = Join-Path $portable 'resources\bin\docker.exe'
    $desktop = Join-Path $portable 'Docker Desktop.exe'
    Set-Content -LiteralPath $cli -Value 'fixture'
    Set-Content -LiteralPath $desktop -Value 'fixture'
    function Get-Command { param($Name, $ErrorAction) if ($Name -eq 'docker') { return @{ Source = $cli } }; return $null }
    function Get-Process { param($Name, $ErrorAction) return @() }
    $savedPath = $env:PATH
    $savedProgramFiles = $env:ProgramFiles
    $savedLocalAppData = $env:LOCALAPPDATA
    try {
        $env:ProgramFiles = $portable
        $env:LOCALAPPDATA = $portable
        Assert ((Find-SurvieDockerDesktop) -eq $desktop) 'Docker Desktop must be found next to a portable CLI'
        $env:PATH = $portable + ';' + $env:PATH
        Update-SurviePath
        Assert (($env:PATH -split ';') -contains $portable) 'Refreshing PATH must preserve caller portable tools'
    } finally {
        $env:PATH = $savedPath
        $env:ProgramFiles = $savedProgramFiles
        $env:LOCALAPPDATA = $savedLocalAppData
        # $portable is an explicitly created child of TEMP, never an arbitrary path.
        if ((Split-Path $portable) -ne $env:TEMP) { throw 'Unexpected fixture path' }
        Remove-Item -LiteralPath $portable -Recurse -Force
    }
}
function Initialize-SurvieTools { }
function Get-SurvieWindowsFacts { return @{ Build = 26100; X64 = $true; Virtualization = $true; Boot = 'fixture' } }
function Test-SurvieWSL { return $true }
function Find-SurviePython { return @{ Path = 'fixture'; Prefix = @() } }
function Find-SurvieDockerDesktop { return 'fixture' }
function Get-SurvieDockerType { return 'linux' }
function Find-SurvieOllama { return 'fixture' }
function Find-SurvieGit { return 'fixture' }
function Get-Command { param($Name, $ErrorAction) return @{ Source = 'mock-nvidia' } }
function mock-nvidia { $global:LASTEXITCODE = 0; return 'Mock GPU, 8192 MiB' }
function Install-SurvieDependency { throw 'Unexpected installation' }
function Invoke-SurvieWSLInstall { throw 'Unexpected WSL modification' }
Assert ((Invoke-SurviePreparation) -eq 0) 'Ready PC must not reinstall or modify dependencies'
function Find-SurvieDockerDesktop { return $null }
Assert ((Invoke-SurviePreparation) -eq 0) 'An accessible Docker engine must not trigger a Desktop reinstall'
function Find-SurvieDockerDesktop { return 'fixture' }
$script:gitPresent = $false
function Find-SurvieGit { if ($script:gitPresent) { return 'fixture' }; return $null }
$failed = $false
try { Invoke-SurviePreparation } catch { $failed = $_.Exception.Message -match 'git manque' }
Assert $failed 'Check must report missing Git without installing it'
$Check = $false
function Install-SurvieDependency($Item, $CacheDir) {
    Assert ($Item.id -eq 'git') 'Only missing Git should be prepared'
    $script:gitPresent = $true
    return 0
}
Assert ((Invoke-SurviePreparation) -eq 0) 'A new Windows installation must prepare missing Git'
$Check = $true
function Find-SurvieGit { return 'fixture' }
function Install-SurvieDependency { throw 'Unexpected installation' }
function Get-SurvieWindowsFacts { return @{ Build = 19045; X64 = $true; Virtualization = $true; Boot = 'fixture' } }
$failed = $false
try { Invoke-SurviePreparation } catch { $failed = $_.Exception.Message -match 'Windows 11' }
Assert $failed 'Unsupported OS must stop before any installation'
function Get-SurvieWindowsFacts { return @{ Build = 26100; X64 = $true; Virtualization = $true; Boot = 'fixture' } }
function Test-SurvieWSL { return $false }
$failed = $false
try { Invoke-SurviePreparation } catch { $failed = $_.Exception.Message -match 'WSL 2' }
Assert $failed 'Check mode must never install WSL'
$Check = $false
$script:wslCalls = 0
function Invoke-SurvieWSLInstall { $script:wslCalls++ }
Assert ((Invoke-SurviePreparation) -eq 3010) 'WSL installation must require an explicit reboot'
Assert ((Invoke-SurviePreparation) -eq 3010) 'Same boot must not repeat WSL installation'
Assert ($script:wslCalls -eq 1) 'WSL must be installed once per boot'
Remove-Item -LiteralPath $CacheDir -Recurse -Force
$file = Join-Path $env:TEMP ('survie-hash-' + [guid]::NewGuid())
try {
    Set-Content -LiteralPath $file -Value 'tiny installer fixture'
    $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
    Assert-SurvieInstallerHash $file $hash
    $failed = $false
    try { Assert-SurvieInstallerHash $file ('0' * 64) } catch { $failed = $true }
    Assert $failed 'A corrupt installer must never be executed'
} finally { Remove-Item -LiteralPath $file -Force }
# The single entry point must never continue after a failed check or reboot request.
& {
    . (Join-Path $root 'scripts\install-all-windows.ps1') -BaseDir 'D:\test avec espaces' -Resume -NoStartup -NoBrowser
    $script:steps = @()
    $script:preparationCode = 3010
    $script:installationCode = 0
    function Invoke-SurvieInstallerScript($Script, $Arguments) {
        $script:steps += @{ Script = $Script; Arguments = $Arguments }
        if ($Script -eq 'prepare-windows.ps1') { return $script:preparationCode }
        return $script:installationCode
    }
    Assert ((Invoke-SurvieWindowsInstall) -eq 3010) 'Reboot code must be preserved'
    Assert ($script:steps.Count -eq 1) 'No application install before reboot'
    $script:steps = @(); $script:preparationCode = 1
    Assert ((Invoke-SurvieWindowsInstall) -eq 1) 'Preparation errors must be preserved'
    Assert ($script:steps.Count -eq 1) 'No application install after preparation failure'
    $script:steps = @(); $script:preparationCode = 0; $Check = $true
    Assert ((Invoke-SurvieWindowsInstall) -eq 0) 'Check must succeed without installation'
    Assert ($script:steps.Count -eq 1) 'Check mode must not start application installation'
    $script:steps = @(); $Check = $false
    Assert ((Invoke-SurvieWindowsInstall) -eq 0) 'Prepared PC must continue automatically'
    Assert ($script:steps.Count -eq 2) 'Both stages must run'
    Assert ($script:steps[1].Arguments -contains 'D:\test avec espaces') 'Paths with spaces must remain one argument'
    Assert ($script:steps[1].Arguments -contains '-Resume') 'Resume must reach the application installer'
    Assert ($script:steps[1].Arguments -contains '-NoStartup') 'Startup choice must be preserved'
    $script:steps = @(); $script:installationCode = 1
    Assert ((Invoke-SurvieWindowsInstall) -eq 1) 'Application installation errors must reach the caller'
}
Write-Host 'Windows installer checks passed; no real dependency installed.'
