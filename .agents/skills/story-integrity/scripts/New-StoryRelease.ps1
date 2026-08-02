#Requires -Version 7.0

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [string]$ProjectRoot,

    [switch]$PromotionFinalize
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ReviewContracts.ps1')
. (Join-Path $PSScriptRoot 'PromotionContracts.ps1')

function Get-RawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-JsonAtomically {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $TemporaryPath = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        $Json = ($Value | ConvertTo-Json -Depth 8).Replace("`r`n", "`n").Replace("`r", "`n")
        Set-Content -LiteralPath $TemporaryPath -Value ($Json + "`n") -Encoding utf8NoBOM -NoNewline
        [System.IO.File]::Move($TemporaryPath, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryPath -PathType Leaf) {
            Remove-Item -LiteralPath $TemporaryPath -Force
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
    throw "Story directory not found: $StoryDirectory"
}

$PromptPath = Join-Path $StoryDirectory '00-prompt.md'
$CanonBriefPath = Join-Path $StoryDirectory '01-canon-brief.md'
$PlanPath = Join-Path $StoryDirectory '02-story-plan.md'
$DraftPath = Join-Path $StoryDirectory '03-draft.md'
$ReviewPath = Join-Path $StoryDirectory '04-review.md'
$StoryPath = Join-Path $StoryDirectory '05-story.md'
$DeltaPath = Join-Path $StoryDirectory '06-canon-delta.md'
$MetadataPath = Join-Path $StoryDirectory 'story.json'
$AuthorityPath = Join-Path $StoryDirectory 'authority.json'
$HandoffPath = Join-Path $StoryDirectory 'handoffs.json'
$PromotionPath = Join-Path $StoryDirectory 'promotion.json'
$ReleasePath = Join-Path $StoryDirectory 'release.json'
foreach ($RequiredPath in @(
    $PromptPath, $CanonBriefPath, $PlanPath, $DraftPath, $ReviewPath,
    $StoryPath, $DeltaPath, $MetadataPath, $AuthorityPath, $HandoffPath
)) {
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) {
        throw "Required release artifact not found: $RequiredPath"
    }
}

try {
    $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
}
catch {
    throw "Invalid story.json: $($_.Exception.Message)"
}
if ($Metadata.schemaVersion -ne 1 -or $Metadata.slug -cne $Story) {
    throw "story.json must use schemaVersion 1 and exact slug '$Story'."
}
if ($Metadata.status -cnotin @('candidate', 'final')) {
    throw "A release certificate may be issued only for candidate or final status; found '$($Metadata.status)'."
}
if ($Metadata.stage -cne $Metadata.status) {
    throw "Story stage '$($Metadata.stage)' must match release status '$($Metadata.status)'."
}

$HandoffChecker = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-StoryHandoffs.ps1'
if (-not (Test-Path -LiteralPath $HandoffChecker -PathType Leaf)) {
    throw "Handoff checker not found: $HandoffChecker"
}
try {
    $HandoffReceipt = & $HandoffChecker -Story $Story -RequireReleaseChain `
        -OutputFormat Json -ProjectRoot $ProjectRoot | ConvertFrom-Json
}
catch {
    throw "Release handoff chain failed validation: $($_.Exception.Message)"
}
if ($HandoffReceipt.passed -ne $true -or $HandoffReceipt.story -cne $Story -or
    $HandoffReceipt.ledgerSha256 -cnotmatch '^[a-f0-9]{64}$' -or
    $HandoffReceipt.ledgerSha256 -cne (Get-RawSha256 $HandoffPath)) {
    throw 'Release handoff checker did not return a valid passing receipt.'
}

if ($Metadata.status -in @('candidate', 'final')) {
    $AuthorityVerifier = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1'
    if (-not (Test-Path -LiteralPath $AuthorityVerifier -PathType Leaf)) {
        throw "Authority manifest verifier not found: $AuthorityVerifier"
    }
    try {
        $AuthorityReceipt = & $AuthorityVerifier -Story $Story -Verify `
            -OutputFormat Json -ProjectRoot $ProjectRoot | ConvertFrom-Json
    }
    catch {
        throw "Candidate authority manifest failed validation: $($_.Exception.Message)"
    }
    if ($AuthorityReceipt.passed -ne $true -or $AuthorityReceipt.story -cne $Story -or
        $AuthorityReceipt.manifestSha256 -cnotmatch '^[a-f0-9]{64}$' -or
        $AuthorityReceipt.manifestSha256 -cne (Get-RawSha256 $AuthorityPath)) {
        throw 'Authority verifier did not return a valid passing receipt.'
    }
}

$StoryContent = Get-Content -LiteralPath $StoryPath -Raw
$DeltaContent = Get-Content -LiteralPath $DeltaPath -Raw
foreach ($Artifact in @(
    [pscustomobject]@{ Name = '05-story.md'; Path = $StoryPath; Content = $StoryContent },
    [pscustomobject]@{ Name = '06-canon-delta.md'; Path = $DeltaPath; Content = $DeltaContent }
)) {
    if ([string]::IsNullOrWhiteSpace($Artifact.Content) -or
        $Artifact.Content -match '{{[^{}]+}}' -or
        $Artifact.Content -match '(?i)complete (?:working|reader-facing|polished) prose goes here') {
        throw "$($Artifact.Name) still contains a placeholder or is empty."
    }
    if (13 -in [IO.File]::ReadAllBytes($Artifact.Path)) {
        throw "$($Artifact.Name) contains CR or CRLF bytes. Normalize release artifacts to LF before certification."
    }
}

$CurrentDraftHash = Get-RawSha256 $DraftPath
$CurrentStoryHash = Get-RawSha256 $StoryPath
$CurrentDeltaHash = Get-RawSha256 $DeltaPath
$CurrentCanonBriefHash = Get-RawSha256 $CanonBriefPath
$CurrentPlanHash = Get-RawSha256 $PlanPath
$CurrentAuthorityHash = Get-RawSha256 $AuthorityPath
$ReviewAuthorityHash = $CurrentAuthorityHash
$PromotionPreparationHash = $null
if ($PromotionFinalize) {
    if ($Metadata.status -cne 'final' -or $Metadata.stage -cne 'final' -or
        $Metadata.canon -ne $true -or $Metadata.userDisposition -cne 'accepted' -or
        [string]::IsNullOrWhiteSpace([string]$Metadata.promotionDate)) {
        throw '-PromotionFinalize requires the already-written final canon lifecycle projection.'
    }
    if (-not (Test-Path -LiteralPath $PromotionPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $ReleasePath -PathType Leaf)) {
        throw '-PromotionFinalize requires ready promotion.json and the candidate release.json.'
    }
    try {
        $Promotion = Get-Content -LiteralPath $PromotionPath -Raw | ConvertFrom-Json
        $CandidateRelease = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json
    }
    catch {
        throw "Promotion finalization input is invalid JSON: $($_.Exception.Message)"
    }
    if ($Promotion.state -cne 'ready' -or $Promotion.storySlug -cne $Story -or
        $Promotion.authorization.storySlug -cne $Story -or
        $Promotion.authorization.approved -ne $true -or
        $Promotion.authorization.scope -cne 'canon-promotion') {
        throw '-PromotionFinalize requires a ready manifest with explicit matching canon-promotion authority.'
    }
    $PromotionPreparationHash = Assert-PromotionPreparationSha256 $Promotion
    $CandidateReleaseHash = Get-RawSha256 $ReleasePath
    if ($Promotion.bundle.release.path -cne "stories/$Story/release.json" -or
        $Promotion.bundle.release.sha256 -cne $CandidateReleaseHash -or
        $Promotion.bundle.story.sha256 -cne $CurrentStoryHash -or
        $Promotion.bundle.canonDelta.sha256 -cne $CurrentDeltaHash -or
        $Promotion.authority.path -cne "stories/$Story/authority.json" -or
        $Promotion.authority.sha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw '-PromotionFinalize manifest does not bind the exact candidate release bundle and reviewed authority.'
    }
    if ($CandidateRelease.schemaVersion -ne 2 -or $CandidateRelease.certified -ne $true -or
        $CandidateRelease.storySlug -cne $Story -or
        $CandidateRelease.provenance.authorityManifestSha256 -cne $Promotion.authority.sha256 -or
        $CandidateRelease.provenance.reviewAuthorityManifestSha256 -cne $Promotion.authority.sha256 -or
        $null -ne $CandidateRelease.provenance.promotionPreparationSha256) {
        throw '-PromotionFinalize candidate release is not a current unbridged schema-version-2 certificate.'
    }
    $ReviewAuthorityHash = [string]$Promotion.authority.sha256
}

$NameChecker = Join-Path $ProjectRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
if (-not (Test-Path -LiteralPath $NameChecker -PathType Leaf)) {
    throw "Name checker not found: $NameChecker"
}
$NameCheckJson = & $NameChecker -Story $Story -Phase Final -OutputFormat Json -ProjectRoot $ProjectRoot
try {
    $NameCheck = $NameCheckJson | ConvertFrom-Json
}
catch {
    throw "Name checker did not return valid JSON: $($_.Exception.Message)"
}
if ($NameCheck.schemaVersion -ne 1 -or
    $NameCheck.passed -ne $true -or $NameCheck.story -cne $Story -or
    $NameCheck.phase -cne 'Final' -or
    $NameCheck.storySha256 -cne $CurrentStoryHash -or
    $NameCheck.canonDeltaSha256 -cne $CurrentDeltaHash -or
    $NameCheck.receiptId -cnotmatch '^[a-f0-9]{64}$' -or
    $NameCheck.scopedRegistrySha256 -cnotmatch '^[a-f0-9]{64}$' -or
    $NameCheck.activeRegistrySha256 -cnotmatch '^[a-f0-9]{64}$' -or
    $NameCheck.checkerVersion -cne 'story-names/2' -or
    $null -eq $NameCheck.warnings) {
    throw 'Final scoped name check did not return a valid passing receipt.'
}
$NamePlanHash = $NameCheck.planSha256
if ($null -ne $NamePlanHash -and
    ($NamePlanHash -cnotmatch '^[a-f0-9]{64}$' -or
        $NamePlanHash -cne $CurrentPlanHash)) {
    throw 'Final scoped name check returned a stale or invalid plan binding.'
}
$NameArtifactHash = if ($null -eq $NamePlanHash) {
    Get-ReviewTextSha256 "$CurrentStoryHash`n$CurrentDeltaHash"
}
else {
    Get-ReviewTextSha256 "$CurrentStoryHash`n$CurrentDeltaHash`n$CurrentPlanHash"
}
$NameWarningsHash = Get-ReviewTextSha256 (
    ConvertTo-Json -InputObject @($NameCheck.warnings) -Compress
)
$ExpectedNameReceiptId = Get-ReviewTextSha256 (
    "$($NameCheck.checkerVersion)`n$Story`nfinal`n$NameArtifactHash`n" +
    "$($NameCheck.scopedRegistrySha256)`n$($NameCheck.activeRegistrySha256)`n$NameWarningsHash"
)
if ($NameCheck.receiptId -cne $ExpectedNameReceiptId) {
    throw 'Final scoped name check receiptId checksum is inconsistent with its returned fields.'
}
try {
    $ReviewContract = Get-StoryReviewContract `
        -Content (Get-Content -LiteralPath $ReviewPath -Raw) `
        -StorySlug $Story `
        -DraftSha256 $CurrentDraftHash `
        -FinalSha256 $CurrentStoryHash `
        -CanonDeltaSha256 $CurrentDeltaHash `
        -CanonBriefSha256 $CurrentCanonBriefHash `
        -PlanSha256 $CurrentPlanHash `
        -AuthorityManifestSha256 $ReviewAuthorityHash `
        -ScopedRegistrySha256 $NameCheck.scopedRegistrySha256 `
        -RequireReleaseReady
    $HandoffLedger = ConvertFrom-ReviewStableJson (
        Get-Content -LiteralPath $HandoffPath -Raw
    )
    Assert-ReviewLedgerBindings -ReviewContract $ReviewContract `
        -Ledger $HandoffLedger -StorySlug $Story `
        -RequireLatestReviewAtChainHead
}
catch {
    throw "Review release binding failed validation: $($_.Exception.Message)"
}
$ReviewReceipt = $ReviewContract.ReleaseReview
$NameCheckedAtUtc = ([DateTimeOffset]$NameCheck.checkedAt).ToUniversalTime().ToString('o')

$CertifiedAt = [DateTimeOffset]::UtcNow.ToString('o')
$Release = [ordered]@{
    schemaVersion = 2
    certified = $true
    storySlug = $Story
    certifiedAt = $CertifiedAt
    artifacts = [ordered]@{
        story = [ordered]@{
            path = '05-story.md'
            sha256 = $CurrentStoryHash
        }
        canonDelta = [ordered]@{
            path = '06-canon-delta.md'
            sha256 = $CurrentDeltaHash
        }
    }
    review = [ordered]@{
        artifact = $ReviewReceipt.artifact
        pass = $ReviewReceipt.pass
        verdict = $ReviewReceipt.verdict
        reviewer = $ReviewReceipt.reviewer
        unresolvedCritical = $ReviewReceipt.unresolvedCritical
        unresolvedMajor = $ReviewReceipt.unresolvedMajor
        passSha256 = $ReviewReceipt.passSha256
        historySha256 = $ReviewReceipt.historySha256
        draftPass = $ReviewReceipt.draftPass
        draftPassSha256 = $ReviewReceipt.draftPassSha256
        reviewedAt = $ReviewReceipt.reviewedAt
    }
    nameCheck = [ordered]@{
        story = $Story
        phase = 'Final'
        passed = $true
        checkedAt = $NameCheckedAtUtc
        receiptId = $NameCheck.receiptId
        storySha256 = $NameCheck.storySha256
        canonDeltaSha256 = $NameCheck.canonDeltaSha256
        scopedRegistrySha256 = $NameCheck.scopedRegistrySha256
        activeRegistrySha256 = $NameCheck.activeRegistrySha256
        checkerVersion = $NameCheck.checkerVersion
        warnings = @($NameCheck.warnings)
    }
    provenance = [ordered]@{
        promptSha256 = Get-RawSha256 $PromptPath
        canonBriefSha256 = $CurrentCanonBriefHash
        planSha256 = $CurrentPlanHash
        draftSha256 = $CurrentDraftHash
        authorityManifestSha256 = $CurrentAuthorityHash
        reviewAuthorityManifestSha256 = $ReviewAuthorityHash
        promotionPreparationSha256 = $PromotionPreparationHash
        handoffLedgerSha256 = Get-RawSha256 $HandoffPath
    }
}

if ($PSCmdlet.ShouldProcess($ReleasePath, 'Issue content-bound story release certificate')) {
    Write-JsonAtomically -Value $Release -Path $ReleasePath
}
Write-Output "Release certificate issued: $ReleasePath"
