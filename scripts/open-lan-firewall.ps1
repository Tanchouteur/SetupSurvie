# Explicit, optional step. Run as administrator, only on a trusted Private network.
# Ollama's API port is deliberately NOT opened.
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Ouvrir PowerShell en administrateur pour ajouter la règle LAN.'
}
$name = 'SetupSurvie-Web-Private'
$rule = Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue
if ($rule) { Write-Host 'La règle existe déjà. Aucun changement.'; exit 0 }
New-NetFirewallRule -Name $name -DisplayName 'SetupSurvie - lecteurs et assistant sur le LAN prive' `
    -Direction Inbound -Action Allow -Protocol TCP -LocalPort 3000,8080,8081 `
    -Profile Private -RemoteAddress LocalSubnet | Out-Null
Write-Host 'Ports Web ouverts sur le réseau privé local. Le port Ollama 11435 reste non ouvert par cette règle.'
