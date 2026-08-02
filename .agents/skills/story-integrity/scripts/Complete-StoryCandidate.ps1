#Requires -Version 7.0

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [switch]$Publish,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PipelineTransactions.ps1')

function Invoke-PipelineContractScript {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Context
    )

    $Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
    $Output = & $Pwsh -NoLogo -NoProfile -File $Path @Arguments 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "$Context failed:`n$($Output.Trim())"
    }
    return $Output.Trim()
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
    throw "Story directory not found: $StoryDirectory"
}

$StoryJsonPath = Join-Path $StoryDirectory 'story.json'
$ReleasePath = Join-Path $StoryDirectory 'release.json'
$ReadmePath = Join-Path $StoryDirectory 'README.md'
$IndexPath = Join-Path $ProjectRoot 'stories/INDEX.md'
$NamesPath = Join-Path $ProjectRoot 'stories/NAMES.md'
$AuthorityScript = Join-Path $PSScriptRoot 'New-AuthorityManifest.ps1'
$HandoffScript = Join-Path $PSScriptRoot 'Test-StoryHandoffs.ps1'
$ReleaseScript = Join-Path $PSScriptRoot 'New-StoryRelease.ps1'
$IntegrityScript = Join-Path $PSScriptRoot 'Test-StoryIntegrity.ps1'

$SnapshotPaths = @($StoryJsonPath, $ReleasePath, $ReadmePath, $IndexPath, $NamesPath)
$Lock = Enter-PipelineMutationLock -ProjectRoot $ProjectRoot -Operation "candidate-$Story"
$Snapshot = $null
$MutationStarted = $false
try {
    $Snapshot = New-PipelineSnapshot -Path $SnapshotPaths
    $Metadata = ConvertFrom-PipelineJson (Get-Content -LiteralPath $StoryJsonPath -Raw)
    $ExactMetadataFields = @(
        'schemaVersion', 'slug', 'title', 'created', 'stage', 'status',
        'canon', 'userDisposition', 'publish', 'promotionDate'
    )
    $ActualFields = @($Metadata.PSObject.Properties.Name)
    if (@($ExactMetadataFields | Where-Object { $_ -cnotin $ActualFields }).Count -gt 0 -or
        @($ActualFields | Where-Object { $_ -cnotin $ExactMetadataFields }).Count -gt 0) {
        throw 'story.json does not use the exact schema-version-1 field set.'
    }
    if ($Metadata.schemaVersion -ne 1 -or $Metadata.slug -cne $Story -or
        $Metadata.stage -cne 'final-review' -or
        $Metadata.status -cne 'in-progress' -or $Metadata.canon -ne $false -or
        $Metadata.userDisposition -cne 'pending' -or $Metadata.publish -ne $false -or
        $null -ne $Metadata.promotionDate) {
        throw 'Candidate completion requires in-progress/final-review, non-canon, pending, unpublished metadata.'
    }

    $PromotionPath = Join-Path $StoryDirectory 'promotion.json'
    $Promotion = ConvertFrom-PipelineJson (Get-Content -LiteralPath $PromotionPath -Raw)
    if ($Promotion.schemaVersion -ne 1 -or $Promotion.storySlug -cne $Story -or
        $Promotion.state -cne 'not-prepared') {
        throw 'Candidate completion requires promotion.json in not-prepared state.'
    }

    $null = Invoke-PipelineContractScript -Path $AuthorityScript -Context 'authority snapshot verification' -Arguments @(
        '-Story', $Story, '-Verify', '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    $null = Invoke-PipelineContractScript -Path $HandoffScript -Context 'specialist handoff-chain verification' -Arguments @(
        '-Story', $Story, '-RequireReleaseChain', '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    Assert-PipelineSnapshotCurrent -Snapshot $Snapshot -Context 'candidate preflight'

    $Metadata.stage = 'candidate'
    $Metadata.status = 'candidate'
    $Metadata.publish = [bool]$Publish
    $MetadataJson = ($Metadata | ConvertTo-Json -Depth 12) + "`n"

    $ReadmeValues = @{
        'Current stage' = 'candidate'
        'Status' = 'candidate'
        'Canon' = 'no'
        'User disposition' = 'pending'
        'Publish' = $(if ($Publish) { 'yes' } else { 'no' })
        'Promotion date' = '—'
    }
    $Checklist = @{}
    foreach ($Label in @(
        'Prompt contract captured', 'Authority snapshot recorded',
        'Canon brief completed', 'Story plan completed', 'Plan name check passed',
        'Complete draft written', 'Draft review passed',
        'Critical and major findings resolved', 'Final story written',
        'Canon delta recorded', 'Final story review passed',
        'Final name check passed', 'Name registry updated',
        'Release certificate issued', 'Story index updated',
        'Specialist handoff ledger validated',
        'Promotion manifest closed or not prepared'
    )) { $Checklist[$Label] = $true }
    $Checklist['Canon promotion explicitly approved (optional)'] = $false
    $Readme = Set-ProductionReadmeValues `
        -Content (Get-Content -LiteralPath $ReadmePath -Raw) `
        -Values $ReadmeValues -Checklist $Checklist

    $Index = Set-StoryIndexProjection `
        -Content (Get-Content -LiteralPath $IndexPath -Raw) `
        -Story $Story -Title ([string]$Metadata.title) -Status candidate `
        -Canon $false -Disposition pending -Publish ([bool]$Publish) `
        -PromotionDate $null -Notes 'Release-certified candidate.'
    $RegistryResult = Set-RegistryStoryState `
        -Content (Get-Content -LiteralPath $NamesPath -Raw) `
        -Story $Story -State candidate

    if (-not $PSCmdlet.ShouldProcess($StoryDirectory, 'Complete candidate transaction')) {
        return
    }

    $MutationStarted = $true
    Write-PipelineTextAtomically -Path $StoryJsonPath -Text $MetadataJson
    Write-PipelineTextAtomically -Path $ReadmePath -Text $Readme
    Write-PipelineTextAtomically -Path $IndexPath -Text $Index
    Write-PipelineTextAtomically -Path $NamesPath -Text $RegistryResult.Content

    $null = Invoke-PipelineContractScript -Path $ReleaseScript -Context 'release issuance' -Arguments @(
        '-Story', $Story, '-ProjectRoot', $ProjectRoot
    )
    $IntegrityJson = Invoke-PipelineContractScript -Path $IntegrityScript -Context 'candidate integrity verification' -Arguments @(
        '-Story', $Story, '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    $Integrity = $IntegrityJson | ConvertFrom-Json
    if ($Integrity.passed -ne $true -or $Integrity.story -cne $Story) {
        throw 'Candidate integrity receipt was not a passing story-scoped receipt.'
    }
}
catch {
    if ($MutationStarted -and $null -ne $Snapshot) {
        Restore-PipelineSnapshot -Snapshot $Snapshot
    }
    throw
}
finally {
    Exit-PipelineMutationLock -Lock $Lock
}

[ordered]@{
    schemaVersion = 1
    story = $Story
    status = 'candidate'
    publish = [bool]$Publish
    releaseSha256 = Get-PipelineRawSha256 $ReleasePath
} | ConvertTo-Json -Depth 4
