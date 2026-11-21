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
# Network selection and health checks are isolated from this PC's real network.
& {
    . (Join-Path $root 'scripts\windows-common.ps1')
    function Get-SurviePrivateIPv4 { return @('192.168.50.10') }
    function Read-Host { param($Prompt) return '' }
    Assert ((Select-SurvieLanHost '') -eq '192.168.50.10') 'Enter should select the single trusted network, not silently stay local'
    Assert ((Select-SurvieLanHost 'LOCAL') -eq '') 'Local-only must remain an explicit choice'
    $failed=$false
    try { Select-SurvieLanHost '192.168.90.2' } catch { $failed=$true }
    Assert $failed 'An address outside the detected private networks must be refused'
    function Get-SurviePrivateIPv4 { return @() }
    $failed=$false
    try { Select-SurvieLanHost '' } catch { $failed=$true }
    Assert $failed 'No private network must require an explicit choice'
    function Invoke-RestMethod { param($Uri,$TimeoutSec,$ErrorAction) return @{ok=$true;version='0.1.30'} }
    Test-SurvieLanEndpoint '192.168.50.10' '0.1.30'
    $failed=$false
    try { Test-SurvieLanEndpoint '192.168.50.10' '0.1.29' } catch { $failed=$true }
    Assert $failed 'LAN verification must require the installed version'
}
& {
    . (Join-Path $root 'scripts\windows-common.ps1')
    $fixture=Join-Path $env:TEMP ('survie-firewall-'+[guid]::NewGuid())
    New-Item -ItemType Directory -Path $fixture | Out-Null
    $program=Join-Path $fixture 'ollama.exe'; Set-Content -LiteralPath $program -Value 'fixture only'
    $script:disabled=@()
    function Get-NetFirewallRule { param($Direction,$Action)
        return @([pscustomobject]@{Name='ours';DisplayName='ollama';Profile='Public';Program=$program},
                 [pscustomobject]@{Name='another-install';DisplayName='ollama';Profile='Public';Program='C:\Other\ollama.exe'},
                 [pscustomobject]@{Name='private-rule';DisplayName='ollama';Profile='Private';Program=$program})
    }
    function Get-NetFirewallApplicationFilter { param([Parameter(ValueFromPipeline=$true)]$Rule) process { return @{Program=$Rule.Program} } }
    function Disable-NetFirewallRule { param($Name) $script:disabled+=@($Name) }
    try {
        Disable-SurviePublicOllamaRules $program (Join-Path $fixture 'backup')
        Assert ($script:disabled.Count -eq 1 -and $script:disabled[0] -eq 'ours') 'Only the exact installed public Ollama rule may be disabled'
        Assert (@(Get-ChildItem -LiteralPath (Join-Path $fixture 'backup') -Filter '*.xml').Count -eq 1) 'Keep the old rule for recovery'
    } finally {
        if ((Split-Path $fixture) -ne $env:TEMP) { throw 'Unexpected firewall fixture path' }
        Remove-Item -LiteralPath $fixture -Recurse -Force
    }
}
# Real discovery functions, with a tiny portable-layout fixture and no execution.
& {
    . (Join-Path $root 'scripts\windows-common.ps1')
    $portable = Join-Path $env:TEMP ('survie-tools-' + [guid]::NewGuid())
    function Get-SurvieDockerInstallLocations { return @() }
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
& {
    . (Join-Path $root 'scripts\windows-common.ps1')
    $fixture=Join-Path $env:TEMP ('survie-docker-start-'+[guid]::NewGuid())
    New-Item -ItemType Directory -Path $fixture | Out-Null
    try {
        $script:desktopFixture=Join-Path $fixture 'Docker Desktop.exe'
        Set-Content -LiteralPath $script:desktopFixture -Value 'fixture only'
        $script:launches=0; $script:checks=0; $script:registered=$false
        function Find-SurvieDockerDesktop { return $script:desktopFixture }
        function Get-SurvieDockerInstallLocations { if ($script:registered) { return (Split-Path $script:desktopFixture) }; return @() }
        function Get-SurvieDockerType { $script:checks++; if ($script:checks -gt 1) { return 'linux' }; return $null }
        function Get-Process { param($Name,$ErrorAction) return @() }
        function Get-CimInstance { param($ClassName) return @{LastBootUpTime=[datetime]'2026-11-01T10:00:00'} }
        function Start-Process { param($FilePath,$WindowStyle) $script:launches++ }
        function Start-Sleep { param($Seconds) }
        $failed=$false
        try { Start-SurvieDocker -Automatic -WorkDir $fixture } catch { $failed=$true }
        Assert ($failed -and $script:launches -eq 0) 'Missing registration must never open the broken GUI'
        $script:registered=$true;$script:checks=0
        Start-SurvieDocker -Automatic -WorkDir $fixture
        Assert ($script:launches -eq 1) 'Registered Docker can be started once'
        $script:checks=0;$failed=$false
        try { Start-SurvieDocker -Automatic -WorkDir $fixture } catch { $failed=$true }
        Assert ($failed -and $script:launches -eq 1) 'A second automatic attempt in the same boot must not open another GUI'
        $script:checks=0
        Start-SurvieDocker -WorkDir $fixture
        Assert ($script:launches -eq 2) 'Explicit manual recovery remains available'
    } finally {
        if ((Split-Path $fixture) -ne $env:TEMP) { throw 'Unexpected Docker fixture path' }
        Remove-Item -LiteralPath $fixture -Recurse -Force
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
    function Get-SurvieResumeKit($Directory) { return 'E:\kit hors ligne' }
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
    Assert ($script:steps[0].Arguments -contains '-Kit' -and $script:steps[0].Arguments -contains 'E:\kit hors ligne') 'The journal kit must select offline preparation'
    Assert ($script:steps[1].Arguments -contains 'E:\kit hors ligne' -and $script:steps[1].Arguments -contains '-SourceChosen') 'The same kit must reach the application installer'
    Assert ($script:steps[1].Arguments -contains 'D:\test avec espaces') 'Paths with spaces must remain one argument'
    Assert ($script:steps[1].Arguments -contains '-Resume') 'Resume must reach the application installer'
    Assert ($script:steps[1].Arguments -contains '-NoStartup') 'Startup choice must be preserved'
    $script:steps = @(); $script:installationCode = 1
    Assert ((Invoke-SurvieWindowsInstall) -eq 1) 'Application installation errors must reach the caller'
}
# Offline preparation uses only installers on the media and preserves the reboot boundary.
& {
    $fixture = Join-Path $env:TEMP ('survie-offline-' + [guid]::NewGuid())
    $null = New-Item -ItemType Directory -Path $fixture
    try {
        $cache = Join-Path $fixture 'local-status'
        . (Join-Path $root 'scripts\prepare-windows.ps1') -Kit $fixture -CacheDir $cache
        '{"schema":1,"kind":"SetupSurvie public pilot kit","files":[]}' |
            Set-Content -LiteralPath (Join-Path $fixture 'manifest.json')
        $script:boot = 'first'
        $script:platform = $false
        $script:wslReady = $false
        $script:missing = 'docker'
        $script:launched = @()
        $script:downloads = @()
        function Initialize-SurvieTools { }
        function Get-SurvieWindowsFacts { return @{ Build = 26100; X64 = $true; Virtualization = $true; Boot = $script:boot } }
        function Test-SurvieWSL { return $script:wslReady }
        function Test-SurvieVirtualMachinePlatform { return $script:platform }
        function Test-SurvieDependencyPresent($Id) { return ($Id -eq 'docker' -and -not $script:missing) -or $Id -ne 'docker' }
        function Invoke-SurvieWSLInstall { throw 'Internet WSL flow attempted' }
        function Get-SurvieInstaller($Item, $CacheDir, [switch]$Offline) {
            Assert ($CacheDir -eq (Join-Path $fixture 'installateurs-windows')) 'Installers must be found in the kit'
            if ($DownloadOnly) {
                Assert (-not $Offline) 'Only the explicit media preparation may download'
                $script:downloads += $Item.id
            } else {
                Assert $Offline 'Installer lookup must stay offline'
                if ($Item.id -eq $script:missing) { throw 'Docker manquant dans la fixture.' }
            }
            return (Join-Path $CacheDir $Item.file)
        }
        function Start-Process($FilePath, $ArgumentList, $Verb, [switch]$Wait, [switch]$PassThru) {
            $script:launched += @{
                Path = $FilePath; Arguments = $ArgumentList; Verb = $Verb
            }
            return @{ ExitCode = 3010 }
        }
        function Get-Command { param($Name, $ErrorAction) return $null }
        $failed = $false
        try { Invoke-SurviePreparation } catch { $failed = $_.Exception.Message -match 'Docker manquant' }
        Assert ($failed -and $script:launched.Count -eq 0) 'All installers needed must be checked before DISM or MSI'
        $script:missing = ''
        Assert ((Invoke-SurviePreparation) -eq 3010) 'Enabling the Windows feature can require reboot'
        Assert ((Invoke-SurviePreparation) -eq 3010 -and $script:launched.Count -eq 1) 'Same boot must not run DISM again'
        Assert ($script:launched[0].Path -like '*dism.exe' -and $script:launched[0].Arguments -match '/LimitAccess' -and $script:launched[0].Verb -eq 'RunAs') 'DISM must use local sources and UAC'
        $script:boot = 'after-platform'
        $script:platform = $true
        Assert ((Invoke-SurviePreparation) -eq 3010) 'Installing the WSL MSI requires an explicit restart'
        Assert ($script:launched.Count -eq 2 -and $script:launched[1].Path -like '*msiexec.exe' -and $script:launched[1].Arguments -match 'installateurs-windows.*\.msi') 'WSL must come from the local MSI'
        $script:boot = 'after-msi'
        $script:wslReady = $true
        Assert ((Invoke-SurviePreparation) -eq 0) 'A disconnected setup can continue without NVIDIA'
        Assert ($script:launched.Count -eq 2) 'Ready machine must not install prerequisites again'
        $DownloadOnly = $true
        Assert ((Invoke-SurviePreparation) -eq 0 -and $script:downloads.Count -eq 5) 'Preloading prepares WSL and four dependencies'
        Assert ($script:launched.Count -eq 2) 'Preloading must not run any installer'
    } finally {
        Remove-Item -LiteralPath $fixture -Recurse -Force
    }
}

& {
    . (Join-Path $root 'scripts\windows-common.ps1')
    function Invoke-WebRequest { throw 'Network was used' }
    $fixture = Join-Path $env:TEMP ('survie-no-network-' + [guid]::NewGuid())
    $item = @{ file = 'fixture.exe'; id = 'fixture'; sha256 = ('0' * 64) }
    $failed = $false
    try { Get-SurvieInstaller $item $fixture -Offline } catch {
        $failed = $_.Exception.Message -match 'Installateur manquant dans le kit'
    }
    Assert ($failed -and -not (Test-Path -LiteralPath $fixture)) 'Offline missing dependency must not download or alter the kit'
}

# A double-click launched inside kit/app must select the media before preparation.
& {
    $fixture = Join-Path $env:TEMP ('survie-kit-entry-' + [guid]::NewGuid())
    $scripts = Join-Path $fixture 'app\scripts'
    $null = New-Item -ItemType Directory -Path $scripts -Force
    try {
        $entry = Join-Path $scripts 'install-all-windows.ps1'
        Copy-Item -LiteralPath (Join-Path $root 'scripts\install-all-windows.ps1') -Destination $entry
        Set-Content -LiteralPath (Join-Path $fixture 'manifest.json') -Value '{}'
        . $entry
        function Read-Host { throw 'An embedded kit should be detected without asking' }
        $actual = Select-SurvieInstallKit $survieInstallerScripts
        $expected = (Resolve-Path -LiteralPath $fixture).ProviderPath
        Assert ($actual -and (Resolve-Path -LiteralPath $actual).ProviderPath -eq $expected) 'The double-clicked launcher must use its own kit'
    } finally {
        Remove-Item -LiteralPath $fixture -Recurse -Force
    }
}

Write-Host 'Windows installer checks passed; no real dependency installed.'
