param(
    [Parameter(Mandatory)][ValidateSet('Foundation', 'BuildPush', 'Migrate', 'Service')][string]$Stage,
    [string]$Profile = 'incubadora-deploy',
    [string]$Region = 'us-east-1',
    [string]$FoundationStack = 'incubadora-foundation',
    [string]$ApplicationStack = 'incubadora-application',
    [string]$ImageTag,
    [switch]$Execute
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

function Invoke-AwsJson {
    param([string[]]$Arguments)
    $result = & aws @Arguments --profile $Profile --region $Region --output json --no-cli-pager
    if ($LASTEXITCODE -ne 0) { throw "AWS failed: $($Arguments[0]) $($Arguments[1])" }
    if ($result) { return ($result -join "`n" | ConvertFrom-Json) }
}

function Get-Outputs([string]$StackName) {
    $stack = (Invoke-AwsJson @('cloudformation', 'describe-stacks', '--stack-name', $StackName)).Stacks[0]
    $values = @{}
    foreach ($item in $stack.Outputs) { $values[$item.OutputKey] = $item.OutputValue }
    return $values
}

function Publish-Template([string]$StackName, [string]$Template, [array]$Parameters) {
    $existing = (Invoke-AwsJson @('cloudformation', 'list-stacks')).StackSummaries |
        Where-Object { $_.StackName -eq $StackName -and $_.StackStatus -ne 'DELETE_COMPLETE' } |
        Select-Object -First 1
    $changeType = if ($existing -and $existing.StackStatus -ne 'REVIEW_IN_PROGRESS') { 'UPDATE' } else { 'CREATE' }
    $changeName = 'review-' + (Get-Date -Format 'yyyyMMddHHmmss')
    $arguments = @('cloudformation', 'create-change-set', '--stack-name', $StackName,
        '--template-body', "file://$Template", '--change-set-name', $changeName,
        '--change-set-type', $changeType, '--capabilities', 'CAPABILITY_IAM')
    $parameterPath = Join-Path ([IO.Path]::GetTempPath()) ('incubadora-parameters-' + [guid]::NewGuid().ToString() + '.json')
    try {
        if ($Parameters.Count) {
            [IO.File]::WriteAllText($parameterPath, (ConvertTo-Json -InputObject @($Parameters)), [Text.UTF8Encoding]::new($false))
            $arguments += @('--parameters', "file://$parameterPath")
        }
        $change = Invoke-AwsJson $arguments
    } finally {
        if (Test-Path -LiteralPath $parameterPath) { Remove-Item -LiteralPath $parameterPath }
    }
    & aws cloudformation wait change-set-create-complete --change-set-name $change.Id --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) {
        $failed = Invoke-AwsJson @('cloudformation', 'describe-change-set', '--change-set-name', $change.Id)
        throw "Change set failed: $($failed.StatusReason)"
    }
    $events = Invoke-AwsJson @('cloudformation', 'describe-events', '--change-set-name', $change.Id)
    $validationErrors = @($events.OperationEvents | Where-Object { $_.EventType -eq 'VALIDATION_ERROR' })
    if ($validationErrors.Count) {
        $validationErrors | Select-Object LogicalResourceId, ValidationStatusReason, ValidationFailureMode | Format-Table
        throw 'Review validation findings before deployment.'
    }
    $details = Invoke-AwsJson @('cloudformation', 'describe-change-set', '--change-set-name', $change.Id)
    $details.Changes.ResourceChange | Select-Object Action, LogicalResourceId, ResourceType, Replacement | Format-Table
    Write-Host "Change set: $($change.Id)"
    if (-not $Execute) { return }
    if (@($details.Changes.ResourceChange | Where-Object { $_.Action -eq 'Remove' -or $_.Replacement -eq 'True' }).Count) {
        throw 'Deletion or replacement requires separate review; this script will not execute it.'
    }
    Invoke-AwsJson @('cloudformation', 'execute-change-set', '--change-set-name', $change.Id) | Out-Null
    $waiter = if ($changeType -eq 'CREATE') { 'stack-create-complete' } else { 'stack-update-complete' }
    & aws cloudformation wait $waiter --stack-name $StackName --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) {
        Invoke-AwsJson @('cloudformation', 'describe-events', '--stack-name', $StackName, '--filters', 'FailedEvents=true') | ConvertTo-Json -Depth 10
        throw 'Stack did not complete; inspect the reported events.'
    }
}

$identity = Invoke-AwsJson @('sts', 'get-caller-identity')
if ($identity.Account -ne '940827433988') { throw 'Unexpected AWS account.' }

if ($Stage -eq 'Foundation') {
    Publish-Template $FoundationStack 'infra/aws/rds-foundation.yml' @()
    return
}
if (-not $ImageTag) { throw 'Supply an immutable -ImageTag, such as release-20260929-1.' }
$foundation = Get-Outputs $FoundationStack

if ($Stage -eq 'Migrate' -and $Execute) {
    # Initialize ECS's account-level role before CloudFormation creates the first cluster.
    $linkedRoles = Invoke-AwsJson @('iam', 'list-roles', '--path-prefix', '/aws-service-role/ecs.amazonaws.com/')
    if (-not @($linkedRoles.Roles | Where-Object RoleName -eq 'AWSServiceRoleForECS').Count) {
        Invoke-AwsJson @('iam', 'create-service-linked-role', '--aws-service-name', 'ecs.amazonaws.com') | Out-Null
        & aws iam wait role-exists --role-name AWSServiceRoleForECS --profile $Profile --region $Region
        if ($LASTEXITCODE -ne 0) { throw 'ECS service-linked role is not available.' }
        Start-Sleep -Seconds 15
    }
}

if ($Stage -eq 'BuildPush') {
    if (-not $Execute) { throw 'BuildPush requires -Execute because it publishes an image.' }
    $image = "$($foundation.RepositoryUri):$ImageTag"
    & docker build --platform linux/amd64 -f Dockerfile.production -t $image .
    if ($LASTEXITCODE -ne 0) { throw 'Image build failed.' }
    $registry = $foundation.RepositoryUri.Split('/')[0]
    $ecrPassword = & aws ecr get-login-password --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw 'ECR authentication failed.' }
    try { $ecrPassword | & docker login --username AWS --password-stdin $registry }
    finally { $ecrPassword = $null }
    if ($LASTEXITCODE -ne 0) { throw 'Docker registry login failed.' }
    & docker push $image
    if ($LASTEXITCODE -ne 0) { throw 'Image push failed.' }
    return
}

# Never turn off an existing service when preparing its next migration.
$enabled = 'false'
$existingApp = (Invoke-AwsJson @('cloudformation', 'list-stacks')).StackSummaries |
    Where-Object { $_.StackName -eq $ApplicationStack -and $_.StackStatus -notin @('DELETE_COMPLETE', 'REVIEW_IN_PROGRESS') } |
    Select-Object -First 1
if ($existingApp) {
    $currentApp = (Invoke-AwsJson @('cloudformation', 'describe-stacks', '--stack-name', $ApplicationStack)).Stacks[0]
    $enabled = ($currentApp.Parameters | Where-Object ParameterKey -eq 'EnableService').ParameterValue
    if ($Stage -eq 'Migrate' -and $enabled -eq 'true') {
        throw 'Existing live service: stage a separate migration revision before updating its image.'
    }
}
if ($Stage -eq 'Service') { $enabled = 'true' }
$parameters = @(
    @{ParameterKey='FoundationStack'; ParameterValue=$FoundationStack},
    @{ParameterKey='ImageTag'; ParameterValue=$ImageTag},
    @{ParameterKey='EnableService'; ParameterValue=$enabled}
)
Publish-Template $ApplicationStack 'infra/aws/application.yml' $parameters
if (-not $Execute) { return }
$application = Get-Outputs $ApplicationStack
if ($Stage -eq 'Migrate') {
    $subnets = $foundation.PublicSubnets
    $group = $foundation.AppSecurityGroup
    $network = "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$group],assignPublicIp=ENABLED}"
    $run = Invoke-AwsJson @('ecs', 'run-task', '--cluster', $application.Cluster,
        '--task-definition', $application.MigrationTask, '--launch-type', 'FARGATE', '--network-configuration', $network)
    if ($run.failures.Count -or -not $run.tasks.Count) { throw 'Migration task could not start.' }
    $taskArn = $run.tasks[0].taskArn
    & aws ecs wait tasks-stopped --cluster $application.Cluster --tasks $taskArn --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw "Migration still running or waiter failed: $taskArn" }
    $task = (Invoke-AwsJson @('ecs', 'describe-tasks', '--cluster', $application.Cluster, '--tasks', $taskArn)).tasks[0]
    if ($null -eq $task.containers[0].exitCode -or $task.containers[0].exitCode -ne 0) {
        throw "Migration failed. Inspect log group $($application.LogGroup)."
    }
    Write-Host 'Migration completed successfully. Ready for the Service stage.'
} else {
    $serviceArn = (Invoke-AwsJson @('cloudformation', 'describe-stack-resource', '--stack-name', $ApplicationStack,
        '--logical-resource-id', 'Service')).StackResourceDetail.PhysicalResourceId
    & aws ecs wait services-stable --cluster $application.Cluster --services $serviceArn --profile $Profile --region $Region
    if ($LASTEXITCODE -ne 0) { throw 'The web service has not stabilized.' }
    $service = (Invoke-AwsJson @('ecs', 'describe-services', '--cluster', $application.Cluster, '--services', $serviceArn)).services[0]
    if ($service.status -ne 'ACTIVE' -or $service.runningCount -lt 1) {
        throw 'CloudFormation completed, but no web task is running.'
    }
    $endpoint = $application.Endpoint
    if ($endpoint -notmatch '^https://') { $endpoint = 'https://' + $endpoint }
    $health = Invoke-RestMethod ($endpoint.TrimEnd('/') + '/health') -TimeoutSec 30
    if ($health.status -ne 'ok') { throw 'The public HTTPS health check failed.' }
    Write-Host "Portal endpoint: $($application.Endpoint)"
}
