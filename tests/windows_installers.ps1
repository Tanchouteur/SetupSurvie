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
function Get-SurvieWindowsFacts { return @{ Build = 26100; X64 = $true; Virtualization = $true; Boot = 'fixture' } }
function Test-SurvieWSL { return $true }
function Find-SurviePython { return @{ Path = 'fixture'; Prefix = @() } }
function Find-SurvieDockerDesktop { return 'fixture' }
function Find-SurvieOllama { return 'fixture' }
function Get-Command { param($Name, $ErrorAction) return @{ Source = 'mock-nvidia' } }
function mock-nvidia { $global:LASTEXITCODE = 0; return 'Mock GPU, 8192 MiB' }
function Install-SurvieDependency { throw 'Unexpected installation' }
function Invoke-SurvieWSLInstall { throw 'Unexpected WSL modification' }
Assert ((Invoke-SurviePreparation) -eq 0) 'Ready PC must not reinstall or modify dependencies'
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
Write-Host 'Windows installer checks passed; no real dependency installed.'
