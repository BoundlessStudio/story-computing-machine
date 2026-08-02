#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$TransactionLibrary = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/PipelineTransactions.ps1'
$CandidateScript = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Complete-StoryCandidate.ps1'
$LifecycleScript = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Set-StoryLifecycle.ps1'
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) (
    'story-transaction-tests-' + [guid]::NewGuid().ToString('N')
)
$script:Passed = 0
$script:Failed = 0

. $TransactionLibrary

function Write-Utf8Fixture {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )

    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }
    $Normalized = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    [IO.File]::WriteAllText($Path, $Normalized, [Text.UTF8Encoding]::new($false))
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if (-not $Condition) { throw $Message }
}

function Assert-BytesEqual {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Context
    )

    $Actual = [IO.File]::ReadAllBytes($Path)
    Assert-True `
        ([Convert]::ToBase64String($Expected) -ceq [Convert]::ToBase64String($Actual)) `
        "$Context was not restored byte-for-byte."
}

function Invoke-ExternalScript {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $Output = & $Pwsh -NoLogo -NoProfile -File $Path @Arguments 2>&1 | Out-String
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = $Output.Trim()
    }
}

function Invoke-Test {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Body
    )

    try {
        & $Body
        $script:Passed++
        Write-Host "PASS: $Name"
    }
    catch {
        $script:Failed++
        Write-Host "FAIL: $Name"
        Write-Host $_.Exception.Message
    }
}

function New-MinimalStoryFixture {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [ValidateSet('candidate', 'final-review')][string]$State,
        [bool]$Publish = $false
    )

    $Root = Join-Path $TestRoot $Name
    $Slug = 'fixture-story'
    $Directory = Join-Path $Root "stories/$Slug"
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $Root 'universe') -Force | Out-Null

    $Status = if ($State -eq 'candidate') { 'candidate' } else { 'in-progress' }
    $Disposition = if ($State -eq 'candidate') { 'accepted' } else { 'pending' }
    $Metadata = [ordered]@{
        schemaVersion = 1
        slug = $Slug
        title = 'Fixture Story'
        created = '2026-08-02'
        stage = $State
        status = $Status
        canon = $false
        userDisposition = $Disposition
        publish = $Publish
        promotionDate = $null
    }
    Write-Utf8Fixture (Join-Path $Directory 'story.json') (($Metadata | ConvertTo-Json -Depth 5) + "`n")
    Write-Utf8Fixture (Join-Path $Directory 'release.json') "{}`n"
    Write-Utf8Fixture (Join-Path $Directory 'promotion.json') @"
{
  "schemaVersion": 1,
  "state": "not-prepared",
  "storySlug": "$Slug",
  "promotionDate": null,
  "preparedAt": null,
  "authorization": null,
  "stewardship": null,
  "authority": null,
  "bundle": null,
  "deltaInventory": null,
  "deltaDispositions": [],
  "universeChanges": [],
  "retcon": null,
  "completion": null
}
"@
    $PublishText = if ($Publish) { 'yes' } else { 'no' }
    Write-Utf8Fixture (Join-Path $Directory 'README.md') @"
# Fixture Story — production record

- Slug: ``$Slug``
- Created: 2026-08-02
- Current stage: $State
- Status: $Status
- Canon: no
- User disposition: $Disposition
- Publish: $PublishText
- Promotion date: —
"@
    Write-Utf8Fixture (Join-Path $Root 'stories/INDEX.md') @"
# Story index

| Slug | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ``$Slug`` | *Fixture Story* | $Status | no | $Disposition | $PublishText | — | Synthetic fixture. |
"@
    Write-Utf8Fixture (Join-Path $Root 'stories/NAMES.md') @"
# Character name registry

| Canonical name | Forms used | Story | State | Reuse | Notes |
| --- | --- | --- | --- | --- | --- |
"@
    Write-Utf8Fixture (Join-Path $Root 'universe/README.md') "# Fixture authority`n"

    return [pscustomobject]@{
        Root = $Root
        Slug = $Slug
        Directory = $Directory
        TrackedPaths = @(
            (Join-Path $Directory 'story.json'),
            (Join-Path $Directory 'release.json'),
            (Join-Path $Directory 'promotion.json'),
            (Join-Path $Directory 'README.md'),
            (Join-Path $Root 'stories/INDEX.md'),
            (Join-Path $Root 'stories/NAMES.md')
        )
    }
}

function Get-ByteSnapshots {
    param([Parameter(Mandatory = $true)][string[]]$Path)

    return @($Path | ForEach-Object {
        [pscustomobject]@{ Path = $_; Bytes = [IO.File]::ReadAllBytes($_) }
    })
}

New-Item -ItemType Directory -Path $TestRoot -Force | Out-Null
try {
    Invoke-Test 'compare-and-swap rejects stale transaction inputs' {
        $Directory = Join-Path $TestRoot 'cas'
        $Path = Join-Path $Directory 'record.md'
        Write-Utf8Fixture $Path "original`n"
        $Snapshot = @(New-PipelineSnapshot -Path @($Path))
        Write-Utf8Fixture $Path "concurrent edit`n"

        $Message = $null
        try {
            Assert-PipelineSnapshotCurrent -Snapshot $Snapshot -Context 'synthetic CAS'
        }
        catch { $Message = $_.Exception.Message }
        Assert-True ($Message -match 'compare-and-swap failed') 'A stale snapshot was accepted.'
        Assert-True ((Get-Content -LiteralPath $Path -Raw) -ceq "concurrent edit`n") 'CAS failure modified the concurrent bytes.'

        Restore-PipelineSnapshot -Snapshot $Snapshot
        Assert-BytesEqual $Snapshot[0].Bytes $Path 'Explicit snapshot restore'
    }

    Invoke-Test 'repository mutation lock excludes a concurrent transaction' {
        $Root = Join-Path $TestRoot 'lock'
        New-Item -ItemType Directory -Path $Root -Force | Out-Null
        $Lock = Enter-PipelineMutationLock -ProjectRoot $Root -Operation 'first'
        try {
            $Message = $null
            try { $null = Enter-PipelineMutationLock -ProjectRoot $Root -Operation 'second' }
            catch { $Message = $_.Exception.Message }
            Assert-True ($Message -match 'Another pipeline mutation is active') 'Concurrent mutation lock was accepted.'
        }
        finally { Exit-PipelineMutationLock -Lock $Lock }
        Assert-True (-not (Test-Path -LiteralPath $Lock.Path -PathType Leaf)) 'Released mutation lock file remains.'
    }

    Invoke-Test 'candidate completion refuses a missing authority snapshot without writes' {
        $Fixture = New-MinimalStoryFixture -Name 'candidate-preflight' -State final-review
        $Before = Get-ByteSnapshots $Fixture.TrackedPaths
        $Result = Invoke-ExternalScript $CandidateScript @(
            '-Story', $Fixture.Slug, '-ProjectRoot', $Fixture.Root
        )
        Assert-True ($Result.ExitCode -ne 0) 'Candidate completion accepted a missing authority snapshot.'
        Assert-True ($Result.Output -match 'authority\.json|Authority manifest') `
            "Candidate failure did not identify the authority gate: $($Result.Output)"
        foreach ($Entry in $Before) {
            Assert-BytesEqual $Entry.Bytes $Entry.Path "Candidate preflight $($Entry.Path)"
        }
        Assert-True (
            -not (Test-Path -LiteralPath (Join-Path $Fixture.Root '.story-locks/repository.lock') -PathType Leaf)
        ) 'Candidate preflight left the repository lock active.'
    }

    Invoke-Test 'lifecycle postcondition failure rolls all coordinated files back' {
        $Fixture = New-MinimalStoryFixture -Name 'lifecycle-rollback' -State candidate -Publish $true
        $Before = Get-ByteSnapshots $Fixture.TrackedPaths
        $Result = Invoke-ExternalScript $LifecycleScript @(
            '-Story', $Fixture.Slug, '-Action', 'Unpublish', '-ProjectRoot', $Fixture.Root
        )
        Assert-True ($Result.ExitCode -ne 0) 'Invalid synthetic repository unexpectedly passed the lifecycle postcondition.'
        Assert-True (
            $Result.Output -match 'lifecycle postcondition failed'
        ) "Lifecycle failure did not reach the post-write validator. Output:`n$($Result.Output)"
        foreach ($Entry in $Before) {
            Assert-BytesEqual $Entry.Bytes $Entry.Path "Lifecycle rollback $($Entry.Path)"
        }
        $Metadata = Get-Content -LiteralPath (Join-Path $Fixture.Directory 'story.json') -Raw | ConvertFrom-Json
        Assert-True ($Metadata.publish -eq $true) 'Lifecycle rollback left the story unpublished.'
        Assert-True (
            -not (Test-Path -LiteralPath (Join-Path $Fixture.Root '.story-locks/repository.lock') -PathType Leaf)
        ) 'Lifecycle rollback left the repository lock active.'
        $TemporaryFiles = @(Get-ChildItem -LiteralPath $Fixture.Root -Recurse -File -Filter '*.tmp.*')
        Assert-True ($TemporaryFiles.Count -eq 0) 'Lifecycle rollback left atomic-write temporary files.'
    }
}
finally {
    $ResolvedTestRoot = [IO.Path]::GetFullPath($TestRoot)
    $ResolvedTempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($ResolvedTestRoot.StartsWith($ResolvedTempRoot, [StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $ResolvedTestRoot -PathType Container)) {
        Remove-Item -LiteralPath $ResolvedTestRoot -Recurse -Force
    }
}

Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
