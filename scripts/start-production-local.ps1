$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$localDirectory = Join-Path (Get-Location) '.local'
[void][IO.Directory]::CreateDirectory($localDirectory)
$configPath = Join-Path $localDirectory 'production-test.env'
if (-not (Test-Path -LiteralPath $configPath)) {
    [IO.File]::WriteAllText($configPath, '')
    $acl = Get-Acl -LiteralPath $configPath
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($rule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($rule) }
    $owner = [Security.Principal.WindowsIdentity]::GetCurrent().User
    foreach ($principal in @($owner, [Security.Principal.SecurityIdentifier]::new('S-1-5-18'))) {
        $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($principal, 'FullControl', 'Allow'))
    }
    Set-Acl -LiteralPath $configPath -AclObject $acl
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $bytes = New-Object byte[] 48
        $rng.GetBytes($bytes)
        $dbPassword = [Convert]::ToBase64String($bytes)
        $rng.GetBytes($bytes)
        $jwtSecret = [Convert]::ToBase64String($bytes)
        [IO.File]::WriteAllText($configPath, "LOCAL_DB_PASSWORD=$dbPassword`nLOCAL_JWT_SECRET=$jwtSecret`n", [Text.UTF8Encoding]::new($false))
    } finally { $rng.Dispose() }
}
& docker compose --env-file $configPath -p incubadora-production-local -f compose.production.yml up -d --build
if ($LASTEXITCODE -ne 0) { throw 'The local production environment did not start.' }
Write-Host 'Production image running at http://localhost:8080 with a separate local database.'
