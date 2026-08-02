#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9]{32}$')]
    [string]$GuardId,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9]{64}$')]
    [string]$GuardSha256,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

function Get-RawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function ConvertFrom-StableJson {
    param([Parameter(Mandatory = $true)][string]$Json)
    $Parameters = @{}
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        $Parameters.DateKind = 'String'
    }
    return $Json | ConvertFrom-Json @Parameters
}

function Get-WorkspaceSnapshot {
    param([Parameter(Mandatory = $true)][string]$Root)
    $ExcludedRoots = @(
        [IO.Path]::GetFullPath((Join-Path $Root '.git')),
        [IO.Path]::GetFullPath((Join-Path $Root '.story-locks')),
        [IO.Path]::GetFullPath((Join-Path $Root '_site'))
    )
    return @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Where-Object {
        $Full = [IO.Path]::GetFullPath($_.FullName)
        -not (@($ExcludedRoots | Where-Object {
            $Full.StartsWith($_ + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
            $Full -ceq $_
        }).Count)
    } | Sort-Object FullName | ForEach-Object {
        [ordered]@{
            path = [IO.Path]::GetRelativePath($Root, $_.FullName).Replace('\', '/')
            sha256 = Get-RawSha256 $_.FullName
        }
    })
}
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$LockDirectory = Join-Path $ProjectRoot '.story-locks'
$LockPath = Join-Path $LockDirectory 'repository.lock'
$GuardPath = Join-Path $LockDirectory "$GuardId.json"
if (-not (Test-Path -LiteralPath $GuardPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $LockPath -PathType Leaf)) {
    throw "Guard '$GuardId' is not the active repository mutation guard."
}
$LockFields = @((Get-Content -LiteralPath $LockPath -Raw).Replace("`r`n", "`n").Split("`n") |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($LockFields.Count -ne 2 -or $LockFields[0] -cne $GuardId -or
    $LockFields[1] -cne $GuardSha256 -or
    (Get-RawSha256 $GuardPath) -cne $GuardSha256) {
    throw "Guard '$GuardId' digest/lock binding is invalid; abort refused."
}
$Guard = ConvertFrom-StableJson (Get-Content -LiteralPath $GuardPath -Raw)
$ExpectedProperties = @(
    'schemaVersion', 'guardId', 'story', 'actor', 'mode', 'createdAt',
    'allowedPaths', 'inputs', 'workspace'
)
$ActualProperties = @($Guard.PSObject.Properties.Name)
if (@($ExpectedProperties | Where-Object { $_ -cnotin $ActualProperties }).Count -gt 0 -or
    @($ActualProperties | Where-Object { $_ -cnotin $ExpectedProperties }).Count -gt 0 -or
    $Guard.schemaVersion -ne 1 -or $Guard.guardId -cne $GuardId) {
    throw 'Handoff guard identity/schema is invalid; abort refused.'
}
$Before = @{}; foreach ($Item in @($Guard.workspace)) {
    $Before[[string]$Item.path] = [string]$Item.sha256
}
$After = @{}; foreach ($Item in @(Get-WorkspaceSnapshot $ProjectRoot)) {
    $After[[string]$Item.path] = [string]$Item.sha256
}
$Changed = @(@($Before.Keys) + @($After.Keys) | Sort-Object -Unique | Where-Object {
    -not $Before.ContainsKey($_) -or -not $After.ContainsKey($_) -or
    $Before[$_] -cne $After[$_]
})
if ($Changed.Count -gt 0) {
    throw "Abort refused because workspace changes remain: $($Changed -join ', '). Restore the captured state; the guard stays active."
}
Remove-Item -LiteralPath $GuardPath -Force
Remove-Item -LiteralPath $LockPath -Force
"Aborted unchanged handoff guard $GuardId."
