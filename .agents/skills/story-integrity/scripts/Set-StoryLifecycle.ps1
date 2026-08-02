#Requires -Version 7.0

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [Parameter(Mandatory = $true)]
    [ValidateSet('Accept', 'Reject', 'Publish', 'Unpublish', 'Reopen')]
    [string]$Action,

    [switch]$AuthorizePublishedReopen,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PipelineTransactions.ps1')

function Invoke-LifecycleIntegrity {
    param(
        [Parameter(Mandatory = $true)][string]$Script,
        [Parameter(Mandatory = $true)][string]$StorySlug,
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Context
    )

    $Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
    $Output = & $Pwsh -NoLogo -NoProfile -File $Script `
        -Story $StorySlug -OutputFormat Json -ProjectRoot $Root 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "$Context failed:`n$($Output.Trim())"
    }
    $Receipt = $Output.Trim() | ConvertFrom-Json
    if ($Receipt.passed -ne $true -or $Receipt.story -cne $StorySlug) {
        throw "$Context returned an invalid receipt."
    }
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
$PromotionPath = Join-Path $StoryDirectory 'promotion.json'
$ReadmePath = Join-Path $StoryDirectory 'README.md'
$IndexPath = Join-Path $ProjectRoot 'stories/INDEX.md'
$NamesPath = Join-Path $ProjectRoot 'stories/NAMES.md'
$IntegrityScript = Join-Path $PSScriptRoot 'Test-StoryIntegrity.ps1'
$TemplateReleasePath = Join-Path $ProjectRoot 'stories/_template/release.json'

$Paths = @(
    $StoryJsonPath, $ReleasePath, $PromotionPath, $ReadmePath,
    $IndexPath, $NamesPath
)
$Lock = Enter-PipelineMutationLock -ProjectRoot $ProjectRoot -Operation "lifecycle-$Action-$Story"
$Snapshot = $null
$MutationStarted = $false
try {
    $Snapshot = New-PipelineSnapshot -Path $Paths
    $Metadata = ConvertFrom-PipelineJson (Get-Content -LiteralPath $StoryJsonPath -Raw)
    if ($Metadata.schemaVersion -ne 1 -or $Metadata.slug -cne $Story) {
        throw 'story.json identity or schema is invalid.'
    }
    $Promotion = ConvertFrom-PipelineJson (Get-Content -LiteralPath $PromotionPath -Raw)
    if ($Promotion.schemaVersion -ne 1 -or $Promotion.storySlug -cne $Story) {
        throw 'promotion.json identity or schema is invalid.'
    }

    $ReadmeValues = @{}
    $Checklist = @{}
    $Notes = $null
    $RegistryState = $null
    $ResetRelease = $false
    switch ($Action) {
        'Accept' {
            if ($Metadata.status -cne 'candidate' -or
                $Metadata.userDisposition -cne 'pending') {
                throw 'Accept requires a candidate with pending user disposition.'
            }
            Invoke-LifecycleIntegrity $IntegrityScript $Story $ProjectRoot 'acceptance preflight'
            $Metadata.userDisposition = 'accepted'
            $ReadmeValues['User disposition'] = 'accepted'
            $Notes = 'Accepted release-certified candidate; canon promotion remains separate.'
        }
        'Reject' {
            if ($Metadata.status -notin @('in-progress', 'candidate') -or
                $Metadata.canon -ne $false) {
                throw 'Reject applies only to a non-canon in-progress or candidate story.'
            }
            if ($Promotion.state -cne 'not-prepared') {
                throw 'Reject cannot discard a prepared promotion manifest; close that transaction first.'
            }
            $Metadata.stage = 'abandoned'
            $Metadata.status = 'abandoned'
            $Metadata.canon = $false
            $Metadata.userDisposition = 'rejected'
            $Metadata.publish = $false
            $Metadata.promotionDate = $null
            foreach ($Pair in @{
                'Current stage' = 'abandoned'; Status = 'abandoned'; Canon = 'no'
                'User disposition' = 'rejected'; Publish = 'no'; 'Promotion date' = '—'
            }.GetEnumerator()) { $ReadmeValues[$Pair.Key] = $Pair.Value }
            $Checklist['Release certificate issued'] = $false
            $Checklist['Canon promotion explicitly approved (optional)'] = $false
            $Notes = 'User rejected; retained as non-canon production history.'
            $RegistryState = 'abandoned'
            $ResetRelease = $true
        }
        'Publish' {
            if ($Metadata.status -notin @('candidate', 'final') -or
                $Metadata.publish -ne $false) {
                throw 'Publish requires an unpublished candidate or final story.'
            }
            Invoke-LifecycleIntegrity $IntegrityScript $Story $ProjectRoot 'publication preflight'
            $Metadata.publish = $true
            $ReadmeValues['Publish'] = 'yes'
            $Notes = 'Publication enabled after a current integrity check.'
        }
        'Unpublish' {
            if ($Metadata.status -notin @('candidate', 'final') -or
                $Metadata.publish -ne $true) {
                throw 'Unpublish requires a published candidate or final story.'
            }
            $Metadata.publish = $false
            $ReadmeValues['Publish'] = 'no'
            $Notes = 'Publication disabled; lifecycle and canon state unchanged.'
        }
        'Reopen' {
            if ($Metadata.status -cne 'candidate' -or $Metadata.canon -ne $false) {
                throw 'Reopen applies only to a non-canon candidate; canon finals require an explicit retcon workflow.'
            }
            if ($Metadata.publish -eq $true -and -not $AuthorizePublishedReopen) {
                throw 'A published candidate requires explicit -AuthorizePublishedReopen authority.'
            }
            if ($Promotion.state -cne 'not-prepared') {
                throw 'Reopen cannot discard a prepared promotion manifest; abort and preserve that transaction first.'
            }
            $Metadata.stage = 'final-review'
            $Metadata.status = 'in-progress'
            $Metadata.canon = $false
            $Metadata.userDisposition = 'pending'
            $Metadata.publish = $false
            $Metadata.promotionDate = $null
            foreach ($Pair in @{
                'Current stage' = 'final-review'; Status = 'in-progress'; Canon = 'no'
                'User disposition' = 'pending'; Publish = 'no'; 'Promotion date' = '—'
            }.GetEnumerator()) { $ReadmeValues[$Pair.Key] = $Pair.Value }
            foreach ($Label in @(
                'Critical and major findings resolved', 'Final story review passed',
                'Final name check passed', 'Release certificate issued'
            )) { $Checklist[$Label] = $false }
            $Checklist['Canon promotion explicitly approved (optional)'] = $false
            $Notes = 'Candidate reopened at final review; prior review and handoff history preserved.'
            $RegistryState = 'in-progress'
            $ResetRelease = $true
        }
    }

    $UpdatedReadme = Set-ProductionReadmeValues `
        -Content (Get-Content -LiteralPath $ReadmePath -Raw) `
        -Values $ReadmeValues -Checklist $Checklist
    $UpdatedIndex = Set-StoryIndexProjection `
        -Content (Get-Content -LiteralPath $IndexPath -Raw) `
        -Story $Story -Title ([string]$Metadata.title) `
        -Status ([string]$Metadata.status) -Canon ([bool]$Metadata.canon) `
        -Disposition ([string]$Metadata.userDisposition) `
        -Publish ([bool]$Metadata.publish) `
        -PromotionDate ([string]$Metadata.promotionDate) -Notes $Notes
    $UpdatedRegistry = if ($null -ne $RegistryState) {
        Set-RegistryStoryState `
            -Content (Get-Content -LiteralPath $NamesPath -Raw) `
            -Story $Story -State $RegistryState
    }
    else { $null }
    $MetadataText = ($Metadata | ConvertTo-Json -Depth 12) + "`n"
    $ReleaseText = $null
    if ($ResetRelease) {
        $ReleaseText = (Get-Content -LiteralPath $TemplateReleasePath -Raw).
            Replace('{{slug}}', $Story)
        $null = $ReleaseText | ConvertFrom-Json
    }

    Assert-PipelineSnapshotCurrent -Snapshot $Snapshot -Context 'lifecycle preflight'
    if (-not $PSCmdlet.ShouldProcess($StoryDirectory, "$Action story lifecycle")) {
        return
    }
    $MutationStarted = $true
    Write-PipelineTextAtomically -Path $StoryJsonPath -Text $MetadataText
    Write-PipelineTextAtomically -Path $ReadmePath -Text $UpdatedReadme
    Write-PipelineTextAtomically -Path $IndexPath -Text $UpdatedIndex
    if ($null -ne $UpdatedRegistry) {
        Write-PipelineTextAtomically -Path $NamesPath -Text $UpdatedRegistry.Content
    }
    if ($ResetRelease) {
        Write-PipelineTextAtomically -Path $ReleasePath -Text $ReleaseText
    }

    Invoke-LifecycleIntegrity $IntegrityScript $Story $ProjectRoot 'lifecycle postcondition'
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
    action = $Action
    status = [string]$Metadata.status
    userDisposition = [string]$Metadata.userDisposition
    publish = [bool]$Metadata.publish
} | ConvertTo-Json -Depth 4
