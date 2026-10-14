param([int]$Port=8091,[switch]$SkipBuild,[switch]$InnovaTec,[switch]$OnlyInnovaTec,[switch]$Incubadora,[switch]$Encuestas,[switch]$Difusion,[switch]$OnlyDifusion,[switch]$Gobierno,[switch]$OnlyGobierno,[switch]$Lighthouse,[switch]$OnlyLighthouse)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$runId=[guid]::NewGuid().ToString('N')
$network="incubadora-design-$runId"
$db="incubadora-design-db-$runId"
$web="incubadora-design-web-$runId"
$image='incubadora-tec-audit:phase-a'
$artifacts=Join-Path $repoRoot ".local/design-test-$runId"
$credentialFile=Join-Path $artifacts 'coordinator.json'
$governanceFile=Join-Path $artifacts 'governance.json'
$previousGovernance=$env:TEST_DESIGN_GOVERNANCE
New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
$previousUrl=$env:TEST_PORTAL_URL
$previousAdmin=$env:TEST_DESIGN_ADMIN
$previousArtifacts=$env:TEST_DESIGN_ARTIFACTS
$networkCreated=$false;$dbCreated=$false;$webCreated=$false
try {
  if(-not $SkipBuild) {
    docker build --platform linux/amd64 -f Dockerfile.production -t $image .
    if($LASTEXITCODE -ne 0){throw 'No se pudo construir la imagen de pruebas.'}
  }
  docker network create $network | Out-Null
  if($LASTEXITCODE -ne 0){throw 'No se pudo crear la red aislada.'}
  $networkCreated=$true
  docker run -d --name $db --network $network -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=test_enlaces postgres:15 | Out-Null
  if($LASTEXITCODE -ne 0){throw 'No se pudo iniciar PostgreSQL aislado.'}
  $dbCreated=$true
  $ready=$false
  for($attempt=0;$attempt -lt 30;$attempt++) {
    docker exec $db pg_isready -U postgres | Out-Null
    if($LASTEXITCODE -eq 0){$ready=$true;break}
    Start-Sleep -Seconds 1
  }
  if(-not $ready){throw 'PostgreSQL no está listo.'}
  $databaseUrl="postgresql://postgres@${db}:5432/test_enlaces"
  docker run --rm --network $network -e "DATABASE_URL=$databaseUrl" -e JWT_SECRET=isolated-design-test-only -e DOCUMENT_STORAGE=local $image python -m alembic upgrade head
  if($LASTEXITCODE -ne 0){throw 'Falló la migración de la base temporal.'}
  docker run -d --name $web --network $network -p "127.0.0.1:${Port}:8000" -e "DATABASE_URL=$databaseUrl" -e JWT_SECRET=isolated-design-test-only -e DOCUMENT_STORAGE=local $image | Out-Null
  if($LASTEXITCODE -ne 0){throw 'No se pudo iniciar el portal de pruebas; comprueba el puerto.'}
  $webCreated=$true
  $base="http://127.0.0.1:$Port"
  $ready=$false
  for($attempt=0;$attempt -lt 30;$attempt++) {
    try {if((Invoke-WebRequest "$base/health").StatusCode -eq 200){$ready=$true;break}}catch{}
    Start-Sleep -Seconds 1
  }
  if(-not $ready){throw 'El portal temporal no responde.'}
  $account=@{nombre='Coordinación temporal de verificación';correo="qa-design-$runId@example.com";password=[guid]::NewGuid().ToString();rol='estudiante'}
  $user=Invoke-RestMethod "$base/api/auth/registro" -Method Post -ContentType application/json -Body ($account|ConvertTo-Json)
  # This role change affects only the random synthetic account inside this run's database.
  docker exec $web python -c "import sys; from uuid import UUID; from app.database import SessionLocal; from app.models import Usuario,RolUsuario; db=SessionLocal(); u=db.get(Usuario,UUID(sys.argv[1])); assert u is not None; u.rol=RolUsuario.admin; db.commit(); db.close()" $user.id
  if($LASTEXITCODE -ne 0){throw 'No se pudo preparar la cuenta temporal de coordinación.'}
  $account | ConvertTo-Json | Set-Content -LiteralPath $credentialFile
  $env:TEST_PORTAL_URL=$base;$env:TEST_DESIGN_ADMIN=$credentialFile;$env:TEST_DESIGN_ARTIFACTS=$artifacts
  if(-not $OnlyInnovaTec -and -not $OnlyDifusion -and -not $OnlyGobierno -and -not $OnlyLighthouse) {
    node frontend/scripts/design-browser.cjs
    if($LASTEXITCODE -ne 0){throw 'Falló la prueba de diseño en Chrome.'}
    npm run test:browser --prefix frontend
    if($LASTEXITCODE -ne 0){throw 'Falló la regresión de formularios en Chrome.'}
  }
  if($InnovaTec -or $OnlyInnovaTec -or $Incubadora) {
    node frontend/scripts/innovatec-browser.cjs
    if($LASTEXITCODE -ne 0){throw 'Falló el flujo InnovaTec en Chrome.'}
  }
  if($Incubadora) {
    node frontend/scripts/incubadora-browser.cjs
    if($LASTEXITCODE -ne 0){throw 'Falló el flujo Incubadora en Chrome.'}
  }
  if($Encuestas) {
    node frontend/scripts/encuestas-browser.cjs
    if($LASTEXITCODE -ne 0){throw 'Falló el flujo Encuestas en Chrome.'}
  }
  if($Difusion -or $OnlyDifusion) {
    node frontend/scripts/difusion-browser.cjs
    if($LASTEXITCODE -ne 0){throw 'Falló el flujo Difusión en Chrome.'}
  }
  if($Gobierno -or $OnlyGobierno) {
    $fixtures=@{}
    foreach($kind in @('advisor','owner')) {
      $person=@{nombre="Cuenta sintética $kind";correo="qa-$kind-$runId@example.com";password=[guid]::NewGuid().ToString();rol='estudiante'}
      $created=Invoke-RestMethod "$base/api/auth/registro" -Method Post -ContentType application/json -Body ($person|ConvertTo-Json)
      $fixtures[$kind]=@{id=$created.id;correo=$person.correo;password=$person.password}
    }
    $fixtures.project=[guid]::NewGuid().ToString();$fixtures.foreign=[guid]::NewGuid().ToString()
    docker exec $web python -c "import sys; from uuid import UUID; from datetime import date; from app.database import SessionLocal; from app.models import Proyecto,ExpedienteIncubadora; db=SessionLocal(); pid,fid,owner=[UUID(v) for v in sys.argv[1:]]; db.add_all([Proyecto(id=pid,nombre='Expediente sintético asignado',usuario_id=owner),Proyecto(id=fid,nombre='Expediente sintético ajeno',usuario_id=owner)]); db.flush(); db.add(ExpedienteIncubadora(proyecto_id=pid,estado='activo',ultimo_movimiento=date.today(),version=1,historial=[])); db.commit(); db.close()" $fixtures.project $fixtures.foreign $fixtures.owner.id
    if($LASTEXITCODE -ne 0){throw 'No se pudieron preparar expedientes sintéticos.'}
    $fixtures|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $governanceFile
    $env:TEST_DESIGN_GOVERNANCE=$governanceFile
    node frontend/scripts/governance-browser.cjs
    if($LASTEXITCODE -ne 0){throw 'Falló el flujo de perfiles/auditoría en Chrome.'}
  }
  if($Lighthouse -or $OnlyLighthouse) {
    node frontend/scripts/performance-browser.cjs
    if($LASTEXITCODE -ne 0){throw 'Falló la regresión de carga diferida y enlaces de noticias.'}
    foreach($preset in @('mobile','desktop')) {
      $report=Join-Path $artifacts "lighthouse-$preset"
      $lighthouseArgs=@('--only-categories=performance,accessibility,best-practices,seo','--output=json','--output=html',"--output-path=$report",'--chrome-flags=--headless=new --disable-gpu --no-first-run','--quiet')
      if($preset -eq 'desktop'){$lighthouseArgs+='--preset=desktop'}
      npm exec --yes --package=lighthouse@13.5.0 -- lighthouse $base @lighthouseArgs
      if($LASTEXITCODE -ne 0){throw 'Falló la medición Lighthouse.'}
      $result=Get-Content "$report.report.json" -Raw|ConvertFrom-Json
      if($result.runtimeError){throw $result.runtimeError.message}
      foreach($category in $result.categories.PSObject.Properties){Write-Host "Lighthouse $preset $($category.Name): $([math]::Round(100*$category.Value.score))"}
    }
  }
  Write-Host "Verificación aprobada. Capturas: $artifacts"
} finally {
  $env:TEST_DESIGN_GOVERNANCE=$previousGovernance
  if(Test-Path -LiteralPath $governanceFile){Remove-Item -LiteralPath $governanceFile}
  $env:TEST_PORTAL_URL=$previousUrl;$env:TEST_DESIGN_ADMIN=$previousAdmin;$env:TEST_DESIGN_ARTIFACTS=$previousArtifacts
  if(Test-Path -LiteralPath $credentialFile){Remove-Item -LiteralPath $credentialFile}
  # Resource names are generated above, never taken from production or user input.
  foreach($item in @(@{name=$web;created=$webCreated},@{name=$db;created=$dbCreated})) {
    if($item.created) {docker rm -f $item.name | Out-Null; if($LASTEXITCODE -ne 0){Write-Warning "No se pudo retirar el contenedor temporal $($item.name)."}}
  }
  if($networkCreated) {docker network rm $network | Out-Null; if($LASTEXITCODE -ne 0){Write-Warning "No se pudo retirar la red temporal $network."}}
}
