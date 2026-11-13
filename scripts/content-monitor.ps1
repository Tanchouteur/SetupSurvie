param([string]$WorkDir = (Join-Path (Split-Path $PSScriptRoot) '.local'), [switch]$Continu, [int]$Intervalle = 5)
$ErrorActionPreference = 'Stop'
$config=Get-Content -LiteralPath (Join-Path $WorkDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$root=$config.data_dir
do {
 try {
  $transfer = Get-Content -LiteralPath "$root\diagnostics\bibliotheque-transfer.json" -Raw | ConvertFrom-Json
  $plan = Get-Content -LiteralPath $transfer.plan -Raw | ConvertFrom-Json
  $receipt = Get-Content -LiteralPath "$root\catalog\downloaded-content.json" -Raw | ConvertFrom-Json
  $progressPath = "$root\catalog\content-progress.json"
  $progress = Get-Content -LiteralPath $progressPath -Raw | ConvertFrom-Json
  $worker = Get-Process -Id $transfer.pid -ErrorAction SilentlyContinue
  if ($worker -and $worker.ProcessName -notin @('python','pythonw')) { $worker = $null }
  $paths = @{}; foreach ($item in $receipt.items) { $paths[$item.path] = $true }
  $done = @($plan.items | Where-Object { $paths.ContainsKey($_.path) })
  $total = ($plan.items | Measure-Object bytes -Sum).Sum
  $verified = ($done | Measure-Object bytes -Sum).Sum
  $allVerified = ($receipt.items | Measure-Object bytes -Sum).Sum
  $partials = @(Get-ChildItem -LiteralPath "$root\library" -Recurse -File -Filter '*.part')
  $partialBytes=0
  foreach ($partial in $partials) {
   try {
    $stream=[IO.File]::Open($partial.FullName,[IO.FileMode]::Open,[IO.FileAccess]::Read,([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    try { $partialBytes+=$stream.Length } finally { $stream.Dispose() }
   } catch [IO.FileNotFoundException] { } catch { $partialBytes+=$partial.Length }
  }
  $current = @(Get-Content -LiteralPath $transfer.log -Tail 1 -ErrorAction SilentlyContinue)[-1]
  $errors = @(Get-Content -LiteralPath $transfer.errors -Tail 80 -ErrorAction SilentlyContinue | Where-Object { $_ -match 'ERREUR|En attente|Error:|Exception:' } | Select-Object -Last 4)
  $phase = 'Arrete'
  if ($worker) {
   if ($worker.StartTime -and (Get-Item -LiteralPath $progressPath).LastWriteTime -lt $worker.StartTime) { $phase = 'Verification des archives deja presentes' }
   elseif ($progress.status -eq 'downloading') { $phase = 'Telechargement'; $current = if ($progress.title) { $progress.title } else { $progress.id } }
   elseif ($progress.status -eq 'waiting_retry') { $phase = 'Attente avant nouvelle tentative automatique'; $current = $progress.message }
   else { $phase = 'Processus actif : verification ou passage au fichier suivant' }
  }
  if ($done.Count -eq @($plan.items).Count -and -not $worker) { $phase = 'Tous les elements du plan sont verifies' }
  if ($Continu) { Clear-Host }
  Write-Host ('SUIVI BIBLIOTHEQUE SETUPSURVIE - '+(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')) -ForegroundColor Cyan
  Write-Host ('Etat : '+$phase)
  Write-Host ('En cours : '+$current)
  Write-Host ('Plan : {0:N2} / {1:N2} Go verifies ({2:N1} %) - {3}/{4} ajouts' -f ($verified/1e9),($total/1e9),(100*$verified/$total),$done.Count,@($plan.items).Count)
  Write-Host ('Total local verifie : {0:N2} Go ; {1} contenus' -f ($allVerified/1e9),@($receipt.items).Count)
  $mapManifest=Join-Path $root 'library\maps\manifest.json'
  $mapCount=0
  if (Test-Path -LiteralPath $mapManifest) {
   $mapData=Get-Content -LiteralPath $mapManifest -Raw -Encoding UTF8 | ConvertFrom-Json
   foreach ($map in @($mapData.maps)) {
    if ($map.path -notmatch '^[a-z0-9-]+\.pmtiles$') { continue }
    $mapFile=Join-Path $root ('library\maps\'+$map.path)
    if ((Test-Path -LiteralPath $mapFile) -and (Get-Item -LiteralPath $mapFile).Length -eq $map.bytes) { $mapCount++ }
   }
  }
  Write-Host ('Cartes hors ligne : {0} fond(s) present(s), en plus du plan documentaire.' -f $mapCount)
  if (-not $mapCount) { Write-Host 'Cartes absentes : lancer la preparation des cartes ; les 100 % du plan ne les incluent pas.' -ForegroundColor Yellow }
  Write-Host ('Fichiers partiels : {0:N2} Go (pas encore verifies)' -f ($partialBytes/1e9))
  if ($worker) { Write-Host ('Processus : '+$worker.Id+' ('+$worker.ProcessName+')') }
  if ($progress.active) {
   foreach ($entry in @($progress.active)) { Write-Host ('Transfert : {0} - {1:N2} / {2:N2} Go' -f $entry.title,($entry.bytes/1e9),($entry.total/1e9)) }
  } elseif ($progress.status -eq 'downloading') { Write-Host ('Fichier courant : {0:N2} / {1:N2} Go' -f ($progress.bytes/1e9),($progress.total/1e9)) }
  if ($errors.Count) { Write-Host 'Dernieres erreurs du transfert :' -ForegroundColor Yellow; $errors | ForEach-Object { Write-Host $_ } }
  Write-Host ('Journal : '+$transfer.log)
  Write-Host 'La verification peut durer plusieurs minutes sur le HDD, sans hausse du volume.'
  if ($Continu) { Write-Host 'Actualisation toutes les 5 secondes. Fermer cette fenetre ne coupe pas le telechargement.' }
 } catch { Write-Host ('Lecture en cours de mise a jour : '+$_.Exception.Message) -ForegroundColor Yellow }
 if ($Continu) { Start-Sleep -Seconds ([math]::Max(2,$Intervalle)) }
} while ($Continu)
