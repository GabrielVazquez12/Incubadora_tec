param(
    [string]$SourceProfile = 'incubadora-dev',
    [switch]$Watch
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sessionPath = Join-Path $projectRoot 'backend/.aws-documentos-session.json'
$roleArn = 'arn:aws:iam::940827433988:role/incubadora-tec-documentos-local'

function Update-DocumentSession {
    $identityOutput = & aws sts get-caller-identity --profile $SourceProfile --output json --no-cli-pager
    if ($LASTEXITCODE -ne 0) { throw 'La sesión del perfil de desarrollo no está disponible.' }
    $identity = ($identityOutput -join "`n") | ConvertFrom-Json
    if ($identity.Account -ne '940827433988' -or $identity.Arn -eq 'arn:aws:iam::940827433988:root') {
        throw 'Utiliza un perfil IAM autorizado de la cuenta del proyecto, no root.'
    }
    $assumedOutput = & aws sts assume-role --profile $SourceProfile --role-arn $roleArn --role-session-name incubadora-docker --duration-seconds 3600 --output json --no-cli-pager
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo obtener la sesión limitada del backend.' }
    try { $assumed = ($assumedOutput -join "`n") | ConvertFrom-Json }
    catch { throw 'AWS no devolvió una sesión válida.' }
    if ($assumed.AssumedRoleUser.Arn -notlike 'arn:aws:sts::940827433988:assumed-role/incubadora-tec-documentos-local/*') {
        throw 'La sesión no corresponde al rol del backend.'
    }
    $documentSession = [ordered]@{
        Version = 1
        AccessKeyId = $assumed.Credentials.AccessKeyId
        SecretAccessKey = $assumed.Credentials.SecretAccessKey
        SessionToken = $assumed.Credentials.SessionToken
        Expiration = $assumed.Credentials.Expiration
    }
    # Protect the file before writing credentials; only this Windows user and SYSTEM.
    if (-not (Test-Path -LiteralPath $sessionPath)) {
        [IO.File]::WriteAllText($sessionPath, '{}')
    }
    $acl = Get-Acl -LiteralPath $sessionPath
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($rule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($rule) }
    $owner = [Security.Principal.WindowsIdentity]::GetCurrent().User
    foreach ($principal in @($owner, [Security.Principal.SecurityIdentifier]::new('S-1-5-18'))) {
        $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($principal, 'FullControl', 'Allow'))
    }
    Set-Acl -LiteralPath $sessionPath -AclObject $acl
    [IO.File]::WriteAllText($sessionPath, ($documentSession | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
    Write-Host "Sesión limitada actualizada. Expira: $($assumed.Credentials.Expiration)"
}

do {
    Update-DocumentSession
    if ($Watch) { Start-Sleep -Seconds 1800 }
} while ($Watch)
