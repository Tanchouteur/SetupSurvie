# All Git mutations, downloads and service actions are mocked; fixtures only.
$ErrorActionPreference = 'Stop'
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
$root = Split-Path $PSScriptRoot
$fixture = [IO.Path]::GetFullPath((Join-Path $env:TEMP ('survie-update-' + [guid]::NewGuid())))
$work = Join-Path $fixture 'reglages ailleurs'
$app = Join-Path $fixture 'application'
$source = Join-Path $fixture 'maintenance\source'
$null = New-Item -ItemType Directory -Path $work, (Join-Path $app 'deploy'), (Join-Path $app 'scripts'), (Join-Path $source 'deploy'), (Join-Path $source '.git') -Force
@{ app_dir = $app; data_dir = (Join-Path $fixture 'donnees'); target = 'windows' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $work 'settings.json')
'{"version":"0.1.20"}' | Set-Content -LiteralPath (Join-Path $app 'deploy\release.json')
'{"version":"0.1.21"}' | Set-Content -LiteralPath (Join-Path $source 'deploy\release.json')
'fixture' | Set-Content -LiteralPath (Join-Path $app 'scripts\windows_update.py')
try {
    . (Join-Path $root 'scripts\update-windows.ps1') -WorkDir $work -Check
    $settings = Get-SurvieUpdateSettings
    Assert ($settings.Work -eq $work) 'Private folder must be taken from the installation, without a fixed drive'
    Assert ($settings.Application -eq $app) ("Application must come from settings: expected [$app], actual [$($settings.Application)]")
    $transcriptPath = Join-Path $fixture 'update.log'
    $failure = '[Console]::Error.WriteLine("Video inventory still active."); exit 7'
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($failure))
    Start-Transcript -Path $transcriptPath | Out-Null
    try {
        $message = ''
        try { Invoke-SurvieUpdateCommand 'powershell.exe' @('-NoProfile', '-EncodedCommand', $encoded) }
        catch { $message = $_.Exception.Message }
    } finally { Stop-Transcript | Out-Null }
    Assert ($message -match 'code 7.*Video inventory still active') 'Native failure must include its exit code and stderr'
    Assert ((Get-Content -LiteralPath $transcriptPath -Raw) -match 'Video inventory still active') 'Native stderr must be in the update log'
    function Initialize-SurvieTools { }
    function Find-SurviePython { return @{ Path = 'python-fixture'; Prefix = @('-3') } }
    function Find-SurvieGit { return 'git-fixture' }
    $script:calls = @(); $script:dirty = $false; $script:ahead = '0'; $script:badHash = $false
    function Get-SurvieGitOutput($Git, $Arguments) {
        switch ($Arguments[2]) {
            'remote' { return 'https://github.com/Tanchouteur/SetupSurvie.git' }
            'status' { if ($script:dirty) { return ' M file' }; return '' }
            'branch' { return 'main' }
            'rev-list' { return $script:ahead }
            default { throw 'Unexpected Git query' }
        }
    }
    function Invoke-SurvieUpdateCommand($File, $Arguments) {
        $script:calls += @{ File = $File; Arguments = @($Arguments) }
        if ($Arguments -contains 'build') {
            $package = $Arguments[-1]
            Set-Content -LiteralPath $package -Value 'fixture package'
            $hash = if ($script:badHash) { '0' * 64 } else { (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash }
            Set-Content -LiteralPath ($package + '.sha256') -Value ($hash + '  fixture.zip')
        }
    }
    Invoke-SurvieGitUpdate $settings
    Assert ($script:calls.Count -eq 2) 'Check must only fetch and fast-forward Git'
    Assert (@($script:calls | Where-Object File -eq 'python-fixture').Count -eq 0) 'Check must not build or apply'
    $Check = $false; $script:calls = @()
    Invoke-SurvieGitUpdate $settings
    Assert ($script:calls.Count -eq 5) 'Normal update must fetch, fast-forward, build, apply and refresh launcher'
    $apply = @($script:calls | Where-Object { $_.Arguments -contains 'apply' })
    Assert ($apply.Count -eq 1) 'Apply must run once'
    Assert ($apply[0].Arguments[0] -eq '-3') 'Python launcher prefix must be retained'
    Assert ($apply[0].Arguments -contains $work) 'Private path with spaces must remain one argument'
    $script:calls = @(); $script:badHash = $true
    $failed = $false
    try { Invoke-SurvieGitUpdate $settings } catch { $failed = $_.Exception.Message -match 'Empreinte' }
    Assert $failed 'Bad hash must stop before apply'
    Assert (@($script:calls | Where-Object { $_.Arguments -contains 'apply' }).Count -eq 0) 'Bad package must not be installed'
    $script:calls = @(); $script:badHash = $false; $script:dirty = $true
    $failed = $false
    try { Invoke-SurvieGitUpdate $settings } catch { $failed = $_.Exception.Message -match 'Modifications locales' }
    Assert $failed 'Dirty source must be preserved'
    Assert ($script:calls.Count -eq 0) 'Dirty checkout must not be fetched or modified'
    $script:dirty = $false; $script:ahead = '1'; $script:calls = @()
    $failed = $false
    try { Invoke-SurvieGitUpdate $settings } catch { $failed = $_.Exception.Message -match 'commits locaux' }
    Assert $failed 'Unpublished commits must not be installed'
    Assert ($script:calls.Count -eq 1) 'Unpublished commits must not be merged or built'
    $script:ahead = '0'; $script:calls = @()
    '{"phase":"switched","previous":"C:\\fixture-previous"}' | Set-Content -LiteralPath (Join-Path $work 'update.json')
    $Recover = $true
    Invoke-SurvieGitUpdate $settings
    Assert ($script:calls.Count -eq 1) 'Recovery must not fetch, build or update Git'
    Assert ($script:calls[0].Arguments -contains 'recover') 'Recovery must use the installed recovery mechanism'
    Assert ($script:calls[0].Arguments -contains 'C:\fixture-previous\scripts\pilot_update.py') 'Recovery must remain possible with a missing application script'
    Write-Host 'Windows Git updater checks passed; no real Git fetch, installation or service action.'
} finally {
    $absolute = [IO.Path]::GetFullPath($fixture)
    if (-not $absolute.StartsWith(([IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected fixture path' }
    Remove-Item -LiteralPath $absolute -Recurse -Force
}
