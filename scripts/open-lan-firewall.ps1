# Explicit, optional step. Run as administrator, only on a trusted Private network.
# Ollama's API port is deliberately NOT opened.
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Ouvrir PowerShell en administrateur pour ajouter la règle LAN.'
}
$engineRule = 'SetupSurvie-Engine-Physical'
$physicalAliases = @(Get-NetAdapter -Physical | Select-Object -ExpandProperty Name)
if ($physicalAliases.Count -and -not (Get-NetFirewallRule -Name $engineRule -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name $engineRule -DisplayName 'SetupSurvie - proteger les commandes du moteur sur les interfaces physiques' -Direction Inbound -Action Block -Protocol TCP -LocalPort 11435,11436 -InterfaceAlias $physicalAliases -Profile Any | Out-Null
}
$mdnsName = 'SetupSurvie-mDNS-Private'
if (-not (Get-NetFirewallRule -Name $mdnsName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name $mdnsName -DisplayName 'SetupSurvie - nom local automatique' -Direction Inbound -Action Allow -Protocol UDP -LocalPort 5353 -Profile Private -RemoteAddress LocalSubnet | Out-Null
}
$name = 'SetupSurvie-Web-Private'
$rule = Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue
if ($rule) { Set-NetFirewallRule -Name $name -Profile Private -RemoteAddress LocalSubnet; $rule | Get-NetFirewallPortFilter | Set-NetFirewallPortFilter -Protocol TCP -LocalPort 3000,8080,8081,8443,8444,8445; Write-Host 'Règle privée mise à jour.'; exit 0 }
New-NetFirewallRule -Name $name -DisplayName 'SetupSurvie - lecteurs et assistant sur le LAN prive' `
    -Direction Inbound -Action Allow -Protocol TCP -LocalPort 3000,8080,8081,8443,8444,8445 `
    -Profile Private -RemoteAddress LocalSubnet | Out-Null
Write-Host 'Ports Web ouverts sur le réseau privé local. Le port Ollama 11435 reste non ouvert par cette règle.'
