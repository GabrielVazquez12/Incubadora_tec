param(
    [string]$Profile = 'incubadora-deploy',
    [string]$Region = 'us-east-1',
    [string]$FoundationStack = 'incubadora-foundation',
    [string]$ApplicationStack = 'incubadora-application'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
function Invoke-VerificationAws([string[]]$Arguments) {
    $output = & aws @Arguments --profile $Profile --region $Region --output json --no-cli-pager
    if ($LASTEXITCODE -ne 0) { throw "AWS verification command failed: $($Arguments[0]) $($Arguments[1])" }
    if ($output) { return ($output -join "`n" | ConvertFrom-Json) }
}
function Read-StackOutputs([string]$Name) {
    $stack = (Invoke-VerificationAws @('cloudformation', 'describe-stacks', '--stack-name', $Name)).Stacks[0]
    $result = @{}
    foreach ($item in $stack.Outputs) { $result[$item.OutputKey] = $item.OutputValue }
    return $result
}
$foundation = Read-StackOutputs $FoundationStack
$application = Read-StackOutputs $ApplicationStack
$serviceId = (Invoke-VerificationAws @('cloudformation', 'describe-stack-resource', '--stack-name', $ApplicationStack,
    '--logical-resource-id', 'Service')).StackResourceDetail.PhysicalResourceId
$service = (Invoke-VerificationAws @('ecs', 'describe-express-gateway-service', '--service-arn', $serviceId)).service
$taskDefinition = $service.activeConfigurations[0].taskDefinitionArn
if (-not $taskDefinition) { throw 'No active service task definition is available.' }
$endpoint = ($service.activeConfigurations[0].ingressPaths | Where-Object accessType -eq 'PUBLIC' | Select-Object -First 1).endpoint
if (-not $endpoint) { throw 'No public endpoint is available for the active service.' }
if ($endpoint -notmatch '^https://') { $endpoint = 'https://' + $endpoint }
$python = @'
import json, os, secrets
from urllib.request import Request, urlopen
import verify_deployment
verify_deployment.main()
from app.database import SessionLocal
from app.models import Usuario

base = os.environ['PORTAL_URL'].rstrip('/')
def request(path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(base + path, headers=headers,
                  data=json.dumps(data).encode() if data is not None else None)
    with urlopen(req, timeout=30) as response:
        return json.load(response)
assert request('/health')['status'] == 'ok'
assert request('/api/health')['status'] == 'ok'
email = 'deployment-test-' + secrets.token_hex(12) + '@example.com'
password = secrets.token_urlsafe(24)
try:
    request('/api/auth/registro', {'nombre': 'Deployment test', 'correo': email,
                                 'password': password, 'rol': 'estudiante'})
    token = request('/api/auth/login', {'correo': email, 'password': password})['access_token']
    assert 'data' in request('/api/portal/state', token=token)
    print('HTTPS registration, login and authenticated portal: OK', flush=True)
finally:
    with SessionLocal() as db:
        account = db.query(Usuario).filter(Usuario.correo == email).first()
        if account is not None:
            db.delete(account)
            db.commit()
    print('Temporary verification account removed', flush=True)
'@
$overrides = @{containerOverrides=@(@{name='Main';command=@('python','-c',$python);environment=@(@{name='PORTAL_URL';value=$endpoint})})}
$overridePath = Join-Path ([IO.Path]::GetTempPath()) ('incubadora-verification-' + [guid]::NewGuid().ToString() + '.json')
try {
    [IO.File]::WriteAllText($overridePath, ($overrides | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
    $network = "awsvpcConfiguration={subnets=[$($foundation.PublicSubnets)],securityGroups=[$($foundation.AppSecurityGroup)],assignPublicIp=ENABLED}"
    $run = Invoke-VerificationAws @('ecs', 'run-task', '--cluster', $application.Cluster,
        '--task-definition', $taskDefinition, '--launch-type', 'FARGATE',
        '--network-configuration', $network, '--overrides', "file://$overridePath")
} finally {
    if (Test-Path -LiteralPath $overridePath) { Remove-Item -LiteralPath $overridePath }
}
if ($run.failures.Count -or -not $run.tasks.Count) { throw 'Verification task could not start.' }
$taskArn = $run.tasks[0].taskArn
Write-Host "Verification task: $taskArn"
& aws ecs wait tasks-stopped --cluster $application.Cluster --tasks $taskArn --profile $Profile --region $Region
if ($LASTEXITCODE -ne 0) { throw "Verification waiter failed; check task $taskArn" }
$task = (Invoke-VerificationAws @('ecs', 'describe-tasks', '--cluster', $application.Cluster, '--tasks', $taskArn)).tasks[0]
$taskId = $taskArn.Split('/')[-1]
Invoke-VerificationAws @('logs', 'get-log-events', '--log-group-name', $application.LogGroup,
    '--log-stream-name', "app/Main/$taskId") | ForEach-Object { $_.events.message | Write-Output }
if ($null -eq $task.containers[0].exitCode -or $task.containers[0].exitCode -ne 0) {
    throw "Cloud verification failed; inspect task $taskArn"
}
Write-Host "Cloud verification passed: $endpoint"
