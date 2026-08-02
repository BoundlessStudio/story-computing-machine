#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$ReviewContractsPath = Join-Path $RepositoryRoot '.agents/skills/story-integrity/scripts/ReviewContracts.ps1'
$ReleaseIssuerPath = Join-Path $RepositoryRoot '.agents/skills/story-integrity/scripts/New-StoryRelease.ps1'
$IntegrityValidatorPath = Join-Path $RepositoryRoot '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1'
. $ReviewContractsPath

$script:Passed = 0
$script:Failed = 0

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Assert-Equal {
    param(
        [AllowNull()][object]$Actual,
        [AllowNull()][object]$Expected,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if ($Actual -cne $Expected) {
        throw "$Message Expected '$Expected', found '$Actual'."
    }
}

function Assert-Throws {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [Parameter(Mandatory = $true)][string]$Pattern
    )
    try {
        & $Action
    }
    catch {
        if ($_.Exception.Message -notmatch $Pattern) {
            throw "Expected error /$Pattern/, found: $($_.Exception.Message)"
        }
        return
    }
    throw "Expected action to fail with /$Pattern/."
}

function Invoke-Case {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Body
    )
    try {
        & $Body
        $script:Passed++
        Write-Output "PASS: $Name"
    }
    catch {
        $script:Failed++
        Write-Output "FAIL: $Name"
        Write-Output "  $($_.Exception.Message)"
    }
}

function Set-Utf8LfFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )
    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }
    $Lf = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    Set-Content -LiteralPath $Path -Value $Lf -Encoding utf8NoBOM -NoNewline
}

function Initialize-SyntheticIntegritySchemas {
    param([Parameter(Mandatory = $true)][string]$FixtureRoot)

    foreach ($RelativePath in @(
        'schemas/pipeline-contract.json',
        '.agents/skills/canon-maintenance/schemas/promotion.schema.json'
    )) {
        Set-Utf8LfFile (Join-Path $FixtureRoot $RelativePath) (
            Get-Content -LiteralPath (Join-Path $RepositoryRoot $RelativePath) -Raw
        )
    }
    $PipelineArtifactValidator = `
        '.agents/skills/story-integrity/scripts/Test-PipelineArtifacts.ps1'
    Set-Utf8LfFile (Join-Path $FixtureRoot $PipelineArtifactValidator) (
        Get-Content -LiteralPath (
            Join-Path $RepositoryRoot $PipelineArtifactValidator
        ) -Raw
    )
}

function New-SyntheticPass {
    param(
        [Parameter(Mandatory = $true)][string]$Story,
        [Parameter(Mandatory = $true)][int]$Pass,
        [Parameter(Mandatory = $true)][ValidateSet('03-draft.md', '05-story.md')][string]$Artifact,
        [Parameter(Mandatory = $true)][string]$ArtifactSha256,
        [Parameter(Mandatory = $true)][string]$CanonDeltaSha256,
        [Parameter(Mandatory = $true)][ValidateSet('PASS', 'REVISE', 'BLOCK')][string]$Verdict,
        [Parameter(Mandatory = $true)][string]$ReviewedAt,
        [ValidateSet('REVIEW_DRAFT', 'REVIEW_FINAL')][string]$Mode,
        [ValidateSet('READY', 'USER_RULING_REQUIRED', 'HANDOFF_ERROR')][string]$Status = 'READY',
        [string]$CanonBriefSha256 = ('1' * 64),
        [string]$PlanSha256 = ('2' * 64),
        [string]$ScopedRegistrySha256 = ('a' * 64),
        [string]$AuthorityManifestSha256 = ('3' * 64),
        [string]$HandoffLedgerSha256 = ('4' * 64),
        [string]$HandoffLedgerChainHead = ('5' * 64),
        [string]$AuthorityManifest,
        [string]$HandoffLedger,
        [string]$Reviewer = 'continuity_critic',
        [string]$ReviewBasis = 'synthetic authority snapshot',
        [ValidateSet('NONE', 'REPAIRABLE', 'USER_RULING_REQUIRED')][string]$BlockType = 'NONE',
        [string]$ResolutionOwner = 'coordinator',
        [string]$ResolutionQuestion = 'none',
        [string]$ErrorCode = 'none',
        [int]$Critical = 0,
        [int]$Major = 0,
        [int]$Minor = 0,
        [bool]$CertificationEligible = $true
    )

    if ([string]::IsNullOrWhiteSpace($Mode)) {
        $Mode = if ($Artifact -ceq '03-draft.md') { 'REVIEW_DRAFT' } else { 'REVIEW_FINAL' }
    }
    if ([string]::IsNullOrWhiteSpace($AuthorityManifest)) {
        $AuthorityManifest = "stories/$Story/authority.json"
    }
    if ([string]::IsNullOrWhiteSpace($HandoffLedger)) {
        $HandoffLedger = "stories/$Story/handoffs.json"
    }
    $FindingLines = [Collections.Generic.List[string]]::new()
    foreach ($FindingSpec in @(
        [pscustomobject]@{ Severity = 'Critical'; Count = $Critical },
        [pscustomobject]@{ Severity = 'Major'; Count = $Major },
        [pscustomobject]@{ Severity = 'Minor'; Count = $Minor }
    )) {
        for ($FindingIndex = 1; $FindingIndex -le $FindingSpec.Count; $FindingIndex++) {
            $FindingId = "synthetic-$($FindingSpec.Severity.ToLowerInvariant())-$FindingIndex"
            $FindingLines.Add(
                "- findingId: $FindingId; lane: Craft; severity: $($FindingSpec.Severity); " +
                'location: synthetic fixture; evidence: synthetic evidence; ' +
                'whyItMatters: it exercises review integrity; ' +
                'smallestEffectiveFix: repair the synthetic fixture'
            )
        }
    }
    $Findings = if ($FindingLines.Count -eq 0) {
        'none'
    }
    else { @($FindingLines) -join "`n" }
    $Payload = (@(
        'REVIEW_PASS_PAYLOAD'
        "story: $Story"
        "mode: $Mode"
        "status: $Status"
        "pass: $Pass"
        "reviewedArtifact: $Artifact"
        "artifactSha256: $ArtifactSha256"
        "canonDeltaSha256: $CanonDeltaSha256"
        "canonBriefSha256: $CanonBriefSha256"
        "planSha256: $PlanSha256"
        "scopedRegistrySha256: $ScopedRegistrySha256"
        "authorityManifest: $AuthorityManifest"
        "authorityManifestSha256: $AuthorityManifestSha256"
        "handoffLedger: $HandoffLedger"
        "handoffLedgerSha256: $HandoffLedgerSha256"
        "handoffLedgerChainHead: $HandoffLedgerChainHead"
        "reviewer: $Reviewer"
        "reviewedAt: $ReviewedAt"
        "reviewBasis: $ReviewBasis"
        "verdict: $Verdict"
        "blockType: $BlockType"
        "resolutionOwner: $ResolutionOwner"
        "resolutionQuestion: $ResolutionQuestion"
        "errorCode: $ErrorCode"
        "unresolvedCounts: { critical: $Critical, major: $Major, minor: $Minor }"
        'priorFindingDispositions: none'
        "findings: $Findings"
        ('certificationEligible: ' + $(if ($CertificationEligible) { 'true' } else { 'false' }))
        'changeReport: read-only; no files changed'
        'END_REVIEW_PASS_PAYLOAD'
    ) -join "`n") + "`n"

    return [pscustomobject][ordered]@{
        Pass = $Pass
        Mode = $Mode
        Status = $Status
        Artifact = $Artifact
        ArtifactSha256 = $ArtifactSha256
        CanonDeltaSha256 = $CanonDeltaSha256
        Verdict = $Verdict
        Reviewer = $Reviewer
        ReviewedAt = $ReviewedAt
        Critical = $Critical
        Major = $Major
        CanonBriefSha256 = $CanonBriefSha256
        PlanSha256 = $PlanSha256
        ScopedRegistrySha256 = $ScopedRegistrySha256
        AuthorityManifestSha256 = $AuthorityManifestSha256
        HandoffLedgerSha256 = $HandoffLedgerSha256
        HandoffLedgerChainHead = $HandoffLedgerChainHead
        Payload = $Payload
    }
}

function Copy-SyntheticJsonObject {
    param([Parameter(Mandatory = $true)][object]$Value)
    return ConvertFrom-ReviewStableJson ($Value | ConvertTo-Json -Depth 16)
}

function Get-SyntheticEntrySha256 {
    param([Parameter(Mandatory = $true)][object]$Entry)

    $Payload = [ordered]@{}
    foreach ($Property in $Entry.PSObject.Properties) {
        if ($Property.Name -cne 'entrySha256') {
            $Payload[$Property.Name] = $Property.Value
        }
    }
    $Json = ($Payload | ConvertTo-Json -Depth 10 -Compress).
        Replace("`r`n", "`n").Replace("`r", "`n")
    return Get-ReviewTextSha256 $Json
}

function Add-SyntheticLedgerEntry {
    param(
        [Parameter(Mandatory = $true)][object]$Ledger,
        [Parameter(Mandatory = $true)][string]$Actor,
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][string]$Report,
        [Parameter(Mandatory = $true)][object[]]$Inputs,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Outputs,
        [string]$Status = 'READY',
        [string]$Persister
    )

    if ([string]::IsNullOrWhiteSpace($Persister)) {
        $Persister = if ($Actor -in @('continuity_critic', 'canon_librarian')) {
            'coordinator'
        }
        else { $Actor }
    }
    $Sequence = @($Ledger.entries).Count + 1
    $Entry = [pscustomobject][ordered]@{
        sequence = $Sequence
        story = [string]$Ledger.storySlug
        actor = $Actor
        mode = $Mode
        status = $Status
        recordedAt = "2026-08-02T$('{0:D2}' -f (12 + $Sequence)):00:00.0000000+00:00"
        guardId = ('{0:x32}' -f $Sequence)
        persister = $Persister
        report = $Report
        reportSha256 = Get-ReviewTextSha256 $Report
        inputs = @($Inputs)
        outputs = @($Outputs)
        previousEntrySha256 = $Ledger.chainHead
        entrySha256 = $null
    }
    $Entry.entrySha256 = Get-SyntheticEntrySha256 $Entry
    $Ledger.entries = @(@($Ledger.entries) + $Entry)
    $Ledger.chainHead = $Entry.entrySha256
}

function New-SyntheticInput {
    param([string]$Path, [string]$Sha256)
    return [pscustomobject][ordered]@{ path = $Path; sha256 = $Sha256 }
}

function New-SyntheticOutput {
    param(
        [string]$Path,
        [string]$AfterSha256,
        [AllowNull()][object]$BeforeSha256 = $null
    )
    return [pscustomobject][ordered]@{
        path = $Path
        beforeSha256 = $BeforeSha256
        afterSha256 = $AfterSha256
    }
}

function New-ReviewDocument {
    param([Parameter(Mandatory = $true)][object[]]$Passes)

    $Latest = $Passes[-1]
    $Lines = [System.Collections.Generic.List[string]]::new()
    foreach ($Line in @(
        '# Continuity and story review', '', '## Current certification', '',
        "- Reviewed artifact: $($Latest.Artifact)",
        "- Artifact SHA-256: $($Latest.ArtifactSha256)",
        "- Canon delta SHA-256: $($Latest.CanonDeltaSha256)",
        "- Review pass: $($Latest.Pass)",
        "- Verdict: $($Latest.Verdict)",
        "- Reviewer: $($Latest.Reviewer)",
        "- Unresolved Critical findings: $($Latest.Critical)",
        "- Unresolved Major findings: $($Latest.Major)",
        "- Updated: $($Latest.ReviewedAt)", '', '## Review passes', ''
    )) { $Lines.Add($Line) }
    foreach ($PassRecord in $Passes) {
        $Lines.Add("### Pass $($PassRecord.Pass) — synthetic review")
        $Lines.Add('')
        foreach ($Line in @($PassRecord.Payload -split "`n")) { $Lines.Add($Line) }
        $Lines.Add('')
    }
    return ($Lines -join "`n") + "`n"
}

function New-BaseReviewFixture {
    $Story = 'synthetic-review'
    $Prompt = @(
        '# Prompt contract', '', '## Verbatim writing prompt', '',
        '> Synthetic prompt.', '', '## Story controls', '',
        '- Working title: Synthetic Review', '- Target length: 130 words',
        '- POV: third person', '- Tense: present',
        '- Tone and genre: neutral fixture',
        '- Audience/content rating: general',
        '- Required elements: deterministic review evidence',
        '- Prohibited elements: none', '', '## Assumptions', '',
        '- The fixture remains story-local.', '', '## Completion tests', '',
        '- The review and release bindings validate.', ''
    ) -join "`n"
    $Plan = @(
        '# Story plan', '', '## Story controls', '',
        '- Use the captured synthetic controls.', '', '## Character engine', '',
        'None.', '', '## Causal arc', '',
        '- Evidence is produced, reviewed, and certified.', '',
        '## Scene plan', '',
        '| # | Purpose | Conflict | Turn | Canon used | Word budget |',
        '| --- | --- | --- | --- | --- | --- |',
        '| 1 | Produce evidence | Validation is strict | The receipt binds | None | 130 |',
        '', '## Setup and payoff', '', 'None.', '', '## Name check', '',
        'None.', '', '## Failure modes to watch', '',
        '- Stale hashes must fail closed.', ''
    ) -join "`n"
    $Draft = "# Draft`n`nSynthetic draft bytes.`n"
    $FinalWords = (1..130 | ForEach-Object { "syntheticword$_" }) -join ' '
    $Final = "---`ntitle: Synthetic Review`nslug: synthetic-review`ncreated: 2026-08-02`n---`n`n# Synthetic Review`n`n$FinalWords`n"
    $Delta = @(
        '# Proposed canon delta', '', '## New characters or character facts', '',
        'None.', '', '## New locations', '', 'None.', '',
        '## New factions or cultural facts', '', 'None.', '',
        '## New rules, capabilities, or costs', '', 'None.', '',
        '## Timeline events', '', 'None.', '',
        '## New glossary terms or aliases', '', 'None.', '',
        '## Final character-facing name inventory', '', 'None.', '',
        '## Name registry updates', '', 'None.', '',
        '## Possible conflicts or retcons', '', 'None.', '',
        '## Recommended promotions', '', 'None.', ''
    ) -join "`n"
    $DraftHash = Get-ReviewTextSha256 $Draft
    $FinalHash = Get-ReviewTextSha256 $Final
    $DeltaHash = Get-ReviewTextSha256 $Delta
    $PromptHash = Get-ReviewTextSha256 $Prompt
    $PlanHash = Get-ReviewTextSha256 $Plan
    $ScopedRegistryHash = 'a' * 64
    $NamesHash = 'b' * 64
    $InitialReview = Get-Content -LiteralPath (
        Join-Path $RepositoryRoot 'stories/_template/04-review.md'
    ) -Raw
    $InitialReviewHash = Get-ReviewTextSha256 $InitialReview
    $MetadataObject = [ordered]@{
        schemaVersion = 1; slug = $Story; title = 'Synthetic Review'
        created = '2026-08-02'; stage = 'candidate'; status = 'candidate'
        canon = $false; userDisposition = 'accepted'; publish = $false
        promotionDate = $null
    }
    $MetadataJson = (($MetadataObject | ConvertTo-Json).
        Replace("`r`n", "`n").Replace("`r", "`n")) + "`n"
    $MetadataHash = Get-ReviewTextSha256 $MetadataJson
    $Authority = [ordered]@{
        schemaVersion = 1
        storySlug = $Story
        generatedAt = '2026-08-02T16:00:00.0000000+00:00'
        universeFiles = @()
        canonStories = @()
        manifestSha256 = $null
    }
    $AuthorityPayload = [ordered]@{
        schemaVersion = 1
        storySlug = $Story
        generatedAt = $Authority.generatedAt
        universeFiles = @()
        canonStories = @()
    }
    $Authority.manifestSha256 = Get-ReviewTextSha256 (
        $AuthorityPayload | ConvertTo-Json -Depth 12 -Compress
    )
    $AuthorityJson = (($Authority | ConvertTo-Json -Depth 12).
        Replace("`r`n", "`n").Replace("`r", "`n")) + "`n"
    $AuthorityHash = Get-ReviewTextSha256 $AuthorityJson
    $CanonBrief = @(
        '# Canon brief', '', '> Research status: READY',
        '> Resolution owner: coordinator',
        "> Prompt SHA-256: $PromptHash",
        "> Authority manifest SHA-256: $AuthorityHash", '',
        '## Hard constraints', '', 'None.', '',
        '## Useful established context', '', 'None.', '',
        '## Conflicts or ambiguity', '', 'None.', '',
        '## Unknowns', '', 'None.', '',
        '## Safe invention space', '', 'None.', '',
        '## Name constraints', '', 'None.', '',
        '## Required checks after drafting', '', 'None.', '',
        '## Sources', '', 'None.', ''
    ) -join "`n"
    $CanonBriefHash = Get-ReviewTextSha256 $CanonBrief

    $Ledger = [pscustomobject][ordered]@{
        schemaVersion = 2
        storySlug = $Story
        chainHead = $null
        entries = @()
    }
    $PrefixHash = Get-ReviewLedgerSnapshotSha256 -StorySlug $Story `
        -Entries @($Ledger.entries) -ChainHead $Ledger.chainHead
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor canon_librarian -Mode RESEARCH_CANON `
        -Report "story: $Story`nmode: RESEARCH_CANON`nstatus: READY`nsynthetic canon research handoff`n" `
        -Inputs @(
            (New-SyntheticInput "stories/$Story/00-prompt.md" $PromptHash),
            (New-SyntheticInput "stories/$Story/story.json" $MetadataHash),
            (New-SyntheticInput "stories/$Story/authority.json" $AuthorityHash),
            (New-SyntheticInput "stories/$Story/handoffs.json" $PrefixHash)
        ) `
        -Outputs @((New-SyntheticOutput "stories/$Story/01-canon-brief.md" $CanonBriefHash))
    $PrefixHash = Get-ReviewLedgerSnapshotSha256 -StorySlug $Story `
        -Entries @($Ledger.entries) -ChainHead $Ledger.chainHead
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor story_architect -Mode CREATE_PLAN `
        -Report "story: $Story`nmode: CREATE_PLAN`nstatus: READY`nsynthetic plan handoff`n" `
        -Inputs @(
            (New-SyntheticInput "stories/$Story/00-prompt.md" $PromptHash),
            (New-SyntheticInput "stories/$Story/story.json" $MetadataHash),
            (New-SyntheticInput "stories/$Story/01-canon-brief.md" $CanonBriefHash),
            (New-SyntheticInput "stories/$Story/authority.json" $AuthorityHash),
            (New-SyntheticInput "stories/$Story/handoffs.json" $PrefixHash),
            (New-SyntheticInput 'stories/NAMES.md' $NamesHash)
        ) `
        -Outputs @((New-SyntheticOutput "stories/$Story/02-story-plan.md" $PlanHash))
    $PrefixHash = Get-ReviewLedgerSnapshotSha256 -StorySlug $Story `
        -Entries @($Ledger.entries) -ChainHead $Ledger.chainHead
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor prose_writer -Mode CREATE_DRAFT `
        -Report "story: $Story`nmode: CREATE_DRAFT`nstatus: READY`nsynthetic draft handoff`n" `
        -Inputs @(
            (New-SyntheticInput "stories/$Story/00-prompt.md" $PromptHash),
            (New-SyntheticInput "stories/$Story/story.json" $MetadataHash),
            (New-SyntheticInput "stories/$Story/01-canon-brief.md" $CanonBriefHash),
            (New-SyntheticInput "stories/$Story/02-story-plan.md" $PlanHash),
            (New-SyntheticInput "stories/$Story/authority.json" $AuthorityHash),
            (New-SyntheticInput "stories/$Story/handoffs.json" $PrefixHash),
            (New-SyntheticInput 'stories/NAMES.md' $NamesHash)
        ) `
        -Outputs @((New-SyntheticOutput "stories/$Story/03-draft.md" $DraftHash))

    $DraftLedgerHash = Get-ReviewLedgerSnapshotSha256 -StorySlug $Story `
        -Entries @($Ledger.entries) -ChainHead $Ledger.chainHead
    $DraftPass = New-SyntheticPass -Story $Story -Pass 1 -Artifact '03-draft.md' `
        -ArtifactSha256 $DraftHash -CanonDeltaSha256 'not-applicable' -Verdict PASS `
        -ReviewedAt '2026-08-02T10:00:00-04:00' `
        -CanonBriefSha256 $CanonBriefHash -PlanSha256 $PlanHash `
        -ScopedRegistrySha256 $ScopedRegistryHash `
        -AuthorityManifestSha256 $AuthorityHash `
        -HandoffLedgerSha256 $DraftLedgerHash `
        -HandoffLedgerChainHead $Ledger.chainHead
    $DraftReview = New-ReviewDocument -Passes @($DraftPass)
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor continuity_critic -Mode REVIEW_DRAFT `
        -Report $DraftPass.Payload `
        -Inputs @(
            (New-SyntheticInput "stories/$Story/00-prompt.md" $PromptHash),
            (New-SyntheticInput "stories/$Story/story.json" $MetadataHash),
            (New-SyntheticInput "stories/$Story/01-canon-brief.md" $CanonBriefHash),
            (New-SyntheticInput "stories/$Story/02-story-plan.md" $PlanHash),
            (New-SyntheticInput "stories/$Story/03-draft.md" $DraftHash),
            (New-SyntheticInput "stories/$Story/04-review.md" $InitialReviewHash),
            (New-SyntheticInput "stories/$Story/authority.json" $AuthorityHash),
            (New-SyntheticInput "stories/$Story/handoffs.json" $DraftLedgerHash),
            (New-SyntheticInput 'stories/NAMES.md' $NamesHash)
        ) `
        -Outputs @((New-SyntheticOutput "stories/$Story/04-review.md" `
            (Get-ReviewTextSha256 $DraftReview) $InitialReviewHash))
    $PrefixHash = Get-ReviewLedgerSnapshotSha256 -StorySlug $Story `
        -Entries @($Ledger.entries) -ChainHead $Ledger.chainHead
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor story_editor -Mode CREATE_FINAL `
        -Report "story: $Story`nmode: CREATE_FINAL`nstatus: READY`nsynthetic final edit handoff`n" `
        -Inputs @(
            (New-SyntheticInput "stories/$Story/00-prompt.md" $PromptHash),
            (New-SyntheticInput "stories/$Story/story.json" $MetadataHash),
            (New-SyntheticInput "stories/$Story/01-canon-brief.md" $CanonBriefHash),
            (New-SyntheticInput "stories/$Story/02-story-plan.md" $PlanHash),
            (New-SyntheticInput "stories/$Story/03-draft.md" $DraftHash),
            (New-SyntheticInput "stories/$Story/04-review.md" (Get-ReviewTextSha256 $DraftReview)),
            (New-SyntheticInput "stories/$Story/authority.json" $AuthorityHash),
            (New-SyntheticInput "stories/$Story/handoffs.json" $PrefixHash),
            (New-SyntheticInput 'stories/NAMES.md' $NamesHash)
        ) `
        -Outputs @(
            (New-SyntheticOutput "stories/$Story/05-story.md" $FinalHash),
            (New-SyntheticOutput "stories/$Story/06-canon-delta.md" $DeltaHash)
        )

    $FinalLedgerHash = Get-ReviewLedgerSnapshotSha256 -StorySlug $Story `
        -Entries @($Ledger.entries) -ChainHead $Ledger.chainHead
    $FinalPass = New-SyntheticPass -Story $Story -Pass 2 -Artifact '05-story.md' `
        -ArtifactSha256 $FinalHash -CanonDeltaSha256 $DeltaHash -Verdict PASS `
        -ReviewedAt '2026-08-02T11:00:00-04:00' `
        -ReviewBasis 'synthetic final authority snapshot' `
        -CanonBriefSha256 $CanonBriefHash -PlanSha256 $PlanHash `
        -ScopedRegistrySha256 $ScopedRegistryHash `
        -AuthorityManifestSha256 $AuthorityHash `
        -HandoffLedgerSha256 $FinalLedgerHash `
        -HandoffLedgerChainHead $Ledger.chainHead
    $Review = New-ReviewDocument -Passes @($DraftPass, $FinalPass)
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor continuity_critic -Mode REVIEW_FINAL `
        -Report $FinalPass.Payload `
        -Inputs @(
            (New-SyntheticInput "stories/$Story/00-prompt.md" $PromptHash),
            (New-SyntheticInput "stories/$Story/story.json" $MetadataHash),
            (New-SyntheticInput "stories/$Story/01-canon-brief.md" $CanonBriefHash),
            (New-SyntheticInput "stories/$Story/02-story-plan.md" $PlanHash),
            (New-SyntheticInput "stories/$Story/03-draft.md" $DraftHash),
            (New-SyntheticInput "stories/$Story/04-review.md" (Get-ReviewTextSha256 $DraftReview)),
            (New-SyntheticInput "stories/$Story/05-story.md" $FinalHash),
            (New-SyntheticInput "stories/$Story/06-canon-delta.md" $DeltaHash),
            (New-SyntheticInput "stories/$Story/authority.json" $AuthorityHash),
            (New-SyntheticInput "stories/$Story/handoffs.json" $FinalLedgerHash),
            (New-SyntheticInput 'stories/NAMES.md' $NamesHash)
        ) `
        -Outputs @((New-SyntheticOutput "stories/$Story/04-review.md" `
            (Get-ReviewTextSha256 $Review) (Get-ReviewTextSha256 $DraftReview)))
    $LedgerJson = (($Ledger | ConvertTo-Json -Depth 12).
        Replace("`r`n", "`n").Replace("`r", "`n")) + "`n"
    return [pscustomobject][ordered]@{
        Story = $Story
        Prompt = $Prompt
        CanonBrief = $CanonBrief
        Plan = $Plan
        Draft = $Draft
        Final = $Final
        Delta = $Delta
        CanonBriefHash = $CanonBriefHash
        PlanHash = $PlanHash
        DraftHash = $DraftHash
        FinalHash = $FinalHash
        DeltaHash = $DeltaHash
        ScopedRegistryHash = $ScopedRegistryHash
        Authority = $AuthorityJson
        AuthorityHash = $AuthorityHash
        Metadata = $MetadataJson
        Ledger = $Ledger
        LedgerJson = $LedgerJson
        LedgerHash = Get-ReviewTextSha256 $LedgerJson
        DraftPass = $DraftPass
        FinalPass = $FinalPass
        Review = $Review
    }
}

$Base = New-BaseReviewFixture
$BasePassBindings = @{
    CanonBriefSha256 = $Base.CanonBriefHash
    PlanSha256 = $Base.PlanHash
    ScopedRegistrySha256 = $Base.ScopedRegistryHash
    AuthorityManifestSha256 = $Base.AuthorityHash
}

function Get-BaseReleaseContract {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [string]$DraftSha256 = $Base.DraftHash,
        [string]$FinalSha256 = $Base.FinalHash,
        [string]$CanonDeltaSha256 = $Base.DeltaHash,
        [string]$CanonBriefSha256 = $Base.CanonBriefHash,
        [string]$PlanSha256 = $Base.PlanHash,
        [string]$AuthorityManifestSha256 = $Base.AuthorityHash,
        [string]$ScopedRegistrySha256 = $Base.ScopedRegistryHash
    )

    return Get-StoryReviewContract -Content $Content -StorySlug $Base.Story `
        -DraftSha256 $DraftSha256 -FinalSha256 $FinalSha256 `
        -CanonDeltaSha256 $CanonDeltaSha256 `
        -CanonBriefSha256 $CanonBriefSha256 -PlanSha256 $PlanSha256 `
        -AuthorityManifestSha256 $AuthorityManifestSha256 `
        -ScopedRegistrySha256 $ScopedRegistrySha256 -RequireReleaseReady
}

Invoke-Case 'valid draft PASS followed by current final PASS produces bound receipt' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    Assert-Equal $Contract.Passes.Count 2 'Completed pass count mismatch.'
    Assert-Equal $Contract.DraftPass.Pass ([int64]1) 'Draft pass mismatch.'
    Assert-Equal $Contract.ReleaseReview.pass ([int64]2) 'Final pass mismatch.'
    Assert-True ($Contract.ReleaseReview.passSha256 -cmatch '^[a-f0-9]{64}$') 'Pass digest is invalid.'
    Assert-True ($Contract.ReleaseReview.historySha256 -cmatch '^[a-f0-9]{64}$') 'History digest is invalid.'
}

Invoke-Case 'strict ledger binding accepts exact critic reports and pre-review snapshots' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    Assert-ReviewLedgerBindings -ReviewContract $Contract `
        -Ledger $Base.Ledger -StorySlug $Base.Story
}

Invoke-Case 'strict ledger binding rejects a tampered critic report' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $Entry = @($Ledger.entries | Where-Object mode -ceq 'REVIEW_DRAFT')[0]
    $Entry.report = ([string]$Entry.report).Replace(
        'reviewBasis: synthetic authority snapshot',
        'reviewBasis: tampered authority snapshot'
    )
    $Entry.reportSha256 = Get-ReviewTextSha256 ([string]$Entry.report)
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'not bound to exactly one accepted critic ledger report'
}

Invoke-Case 'strict ledger binding rejects duplicate handoff-ledger inputs' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $Entry = @($Ledger.entries | Where-Object mode -ceq 'REVIEW_DRAFT')[0]
    $Entry.inputs = @(@($Entry.inputs) + (New-SyntheticInput `
        "stories/$($Base.Story)/handoffs.json" ('f' * 64)))
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'not bound to exactly one accepted critic ledger report'
}

Invoke-Case 'strict ledger binding rejects duplicate review outputs' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $Entry = @($Ledger.entries | Where-Object mode -ceq 'REVIEW_DRAFT')[0]
    $Entry.outputs = @(@($Entry.outputs) + (New-SyntheticOutput `
        "stories/$($Base.Story)/04-review.md" ('f' * 64)))
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'does not record the persisted 04-review.md output'
}

Invoke-Case 'strict ledger binding rejects a missing review output' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $Entry = @($Ledger.entries | Where-Object mode -ceq 'REVIEW_DRAFT')[0]
    $Entry.outputs = @()
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'does not record the persisted 04-review.md output'
}

Invoke-Case 'strict ledger binding rejects a false pre-review snapshot digest' {
    $AlteredReview = $Base.Review.Replace(
        "handoffLedgerSha256: $($Base.DraftPass.HandoffLedgerSha256)",
        ('handoffLedgerSha256: ' + ('f' * 64))
    )
    $Contract = Get-BaseReleaseContract -Content $AlteredReview
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Base.Ledger -StorySlug $Base.Story
    } 'not bound to exactly one accepted critic ledger report|actual prior ledger snapshot'
}

Invoke-Case 'strict ledger binding rejects a false pre-review chain head' {
    $AlteredReview = $Base.Review.Replace(
        "handoffLedgerChainHead: $($Base.DraftPass.HandoffLedgerChainHead)",
        ('handoffLedgerChainHead: ' + ('f' * 64))
    )
    $Contract = Get-BaseReleaseContract -Content $AlteredReview
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Base.Ledger -StorySlug $Base.Story
    } 'not bound to exactly one accepted critic ledger report|actual prior ledger head'
}

Invoke-Case 'strict ledger binding rejects a critic entry with the wrong story' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $Entry = @($Ledger.entries | Where-Object mode -ceq 'REVIEW_DRAFT')[0]
    $Entry.story = 'wrong-story'
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'invalid continuity_critic mode or status|not bound to exactly one accepted critic ledger report'
}

Invoke-Case 'strict ledger binding rejects a critic artifact input that contradicts its payload' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $Entry = @($Ledger.entries | Where-Object mode -ceq 'REVIEW_FINAL')[0]
    $ArtifactInput = @($Entry.inputs | Where-Object {
        $_.path -ceq "stories/$($Base.Story)/05-story.md"
    })[0]
    $ArtifactInput.sha256 = '9' * 64
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'does not bind exact input.*05-story\.md'
}

Invoke-Case 'strict ledger binding requires the exact single-LF report terminator' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $Entry = @($Ledger.entries | Where-Object mode -ceq 'REVIEW_DRAFT')[0]
    $Entry.report = ([string]$Entry.report) + "`n"
    $Entry.reportSha256 = Get-ReviewTextSha256 ([string]$Entry.report)
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'not bound to exactly one accepted critic ledger report'
}

Invoke-Case 'strict ledger binding rejects an accepted critic entry absent from review history' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    $PreExtraJson = (($Ledger | ConvertTo-Json -Depth 12).
        Replace("`r`n", "`n").Replace("`r", "`n")) + "`n"
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor continuity_critic -Mode REVIEW_FINAL `
        -Report $Base.FinalPass.Payload `
        -Inputs @((New-SyntheticInput "stories/$($Base.Story)/handoffs.json" `
            (Get-ReviewTextSha256 $PreExtraJson))) `
        -Outputs @((New-SyntheticOutput "stories/$($Base.Story)/04-review.md" `
            (Get-ReviewTextSha256 $Base.Review)))
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'not one-to-one'
}

Invoke-Case 'strict ledger binding rejects an unresolved critic handoff error' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor continuity_critic -Mode REVIEW_FINAL `
        -Status HANDOFF_ERROR -Report 'synthetic final review handoff error' `
        -Inputs @((New-SyntheticInput "stories/$($Base.Story)/handoffs.json" $Base.LedgerHash)) `
        -Outputs @()
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story
    } 'Unresolved continuity_critic HANDOFF_ERROR'
}

Invoke-Case 'release binding requires the latest review at the ledger chain head' {
    $Contract = Get-BaseReleaseContract -Content $Base.Review
    $Ledger = Copy-SyntheticJsonObject $Base.Ledger
    Add-SyntheticLedgerEntry -Ledger $Ledger -Actor coordinator -Mode LATE_MUTATION `
        -Status READY -Report 'synthetic late ledger mutation' `
        -Inputs @((New-SyntheticInput "stories/$($Base.Story)/handoffs.json" $Base.LedgerHash)) `
        -Outputs @((New-SyntheticOutput "stories/$($Base.Story)/04-review.md" `
            (Get-ReviewTextSha256 $Base.Review)))
    Assert-Throws {
        Assert-ReviewLedgerBindings -ReviewContract $Contract `
            -Ledger $Ledger -StorySlug $Base.Story `
            -RequireLatestReviewAtChainHead
    } 'latest persisted review is not the current handoff ledger chain head'
}

Invoke-Case 'canonical digests are stable across LF and CRLF containers' {
    $Lf = Get-BaseReleaseContract -Content $Base.Review
    $CrlfReview = $Base.Review.Replace("`n", "`r`n")
    $Crlf = Get-BaseReleaseContract -Content $CrlfReview
    Assert-Equal $Crlf.ReleaseReview.passSha256 $Lf.ReleaseReview.passSha256 'Pass digest changed across line endings.'
    Assert-Equal $Crlf.ReleaseReview.historySha256 $Lf.ReleaseReview.historySha256 'History digest changed across line endings.'
}

Invoke-Case 'Current certification must exactly match the latest pass' {
    $Stale = $Base.Review.Replace('- Review pass: 2', '- Review pass: 1')
    Assert-Throws {
        Get-BaseReleaseContract -Content $Stale
    } 'does not exactly match latest review pass'
}

Invoke-Case 'duplicate pass numbers are rejected' {
    $Duplicate = $Base.Review.Replace('### Pass 2 —', '### Pass 1 —')
    Assert-Throws {
        Get-StoryReviewContract -Content $Duplicate -StorySlug $Base.Story
    } 'unique, monotonic, and contiguous'
}

Invoke-Case 'gapped pass numbers are rejected' {
    $Gap = $Base.Review.Replace('### Pass 2 —', '### Pass 3 —')
    Assert-Throws {
        Get-StoryReviewContract -Content $Gap -StorySlug $Base.Story
    } 'expected pass 2, found 3'
}

Invoke-Case 'reordered pass blocks are rejected' {
    $Reordered = New-ReviewDocument -Passes @($Base.FinalPass, $Base.DraftPass)
    Assert-Throws {
        Get-StoryReviewContract -Content $Reordered -StorySlug $Base.Story
    } 'unique, monotonic, and contiguous'
}

Invoke-Case 'malformed payload boundaries are rejected' {
    $Malformed = [regex]::Replace(
        $Base.Review,
        '(?m)^END_REVIEW_PASS_PAYLOAD\r?\n?',
        '',
        1
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $Malformed -StorySlug $Base.Story
    } 'exactly one bounded REVIEW_PASS_PAYLOAD'
}

Invoke-Case 'completed passes reject prose outside the exact payload' {
    $Malformed = $Base.Review.Replace(
        '### Pass 1 — synthetic review',
        "### Pass 1 — synthetic review`n`nCoordinator summary outside payload."
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $Malformed -StorySlug $Base.Story
    } 'contains content outside its exact REVIEW_PASS_PAYLOAD'
}

Invoke-Case 'malformed machine fields are rejected' {
    $Malformed = $Base.Review.Replace(
        'reviewer: continuity_critic',
        'reviewerId: continuity_critic'
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $Malformed -StorySlug $Base.Story
    } "must be 'reviewer'"
}

Invoke-Case 'persisted HANDOFF_ERROR payloads are rejected' {
    $Malformed = $Base.Review.Replace('status: READY', 'status: HANDOFF_ERROR')
    Assert-Throws {
        Get-StoryReviewContract -Content $Malformed -StorySlug $Base.Story
    } 'non-persistable status'
}

Invoke-Case 'review mode must match the reviewed artifact' {
    $Malformed = $Base.Review.Replace('mode: REVIEW_DRAFT', 'mode: REVIEW_FINAL')
    Assert-Throws {
        Get-StoryReviewContract -Content $Malformed -StorySlug $Base.Story
    } 'does not match reviewedArtifact'
}

Invoke-Case 'review enums are case-sensitive' {
    $LowerMode = $Base.Review.Replace(
        'mode: REVIEW_DRAFT',
        'mode: review_draft'
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $LowerMode -StorySlug $Base.Story
    } "invalid mode 'review_draft'"

    $Block = New-SyntheticPass -Story $Base.Story -Pass 1 `
        -Artifact '03-draft.md' -ArtifactSha256 $Base.DraftHash `
        -CanonDeltaSha256 not-applicable -Verdict BLOCK `
        -ReviewedAt '2026-08-02T10:00:00-04:00' -Critical 1 `
        -BlockType REPAIRABLE -ResolutionOwner prose_writer `
        -CertificationEligible $false @BasePassBindings
    $LowerBlockType = (New-ReviewDocument -Passes @($Block)).Replace(
        'blockType: REPAIRABLE',
        'blockType: repairable'
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $LowerBlockType -StorySlug $Base.Story
    } "BLOCK has inconsistent type"
}

Invoke-Case 'unresolved counts must match structured finding severities' {
    $InjectedCritical = $Base.Review.Replace(
        'findings: none',
        ('findings: - findingId: hidden-critical; lane: Canon; ' +
            'severity: Critical; location: synthetic fixture; ' +
            'evidence: contradictory evidence; whyItMatters: it blocks release; ' +
            'smallestEffectiveFix: resolve the contradiction')
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $InjectedCritical -StorySlug $Base.Story
    } 'unresolvedCounts do not match its structured findings'
}

Invoke-Case 'a PASS cannot discard a STILL_OPEN prior finding' {
    $StillOpen = $Base.Review.Replace(
        'priorFindingDispositions: none',
        ('priorFindingDispositions: - findingId: old-major; ' +
            'disposition: STILL_OPEN; evidence: the defect remains')
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $StillOpen -StorySlug $Base.Story
    } 'cannot PASS with a STILL_OPEN prior finding'
}

Invoke-Case 'a later pass must disposition every prior Critical or Major finding' {
    $Revise = New-SyntheticPass -Story $Base.Story -Pass 1 `
        -Artifact '03-draft.md' -ArtifactSha256 $Base.DraftHash `
        -CanonDeltaSha256 not-applicable -Verdict REVISE `
        -ReviewedAt '2026-08-02T10:00:00-04:00' -Major 1 `
        -ResolutionOwner prose_writer -CertificationEligible $false `
        @BasePassBindings
    $Pass = New-SyntheticPass -Story $Base.Story -Pass 2 `
        -Artifact '03-draft.md' -ArtifactSha256 $Base.DraftHash `
        -CanonDeltaSha256 not-applicable -Verdict PASS `
        -ReviewedAt '2026-08-02T11:00:00-04:00' @BasePassBindings
    $Document = New-ReviewDocument -Passes @($Revise, $Pass)
    Assert-Throws {
        Get-StoryReviewContract -Content $Document -StorySlug $Base.Story
    } "must disposition prior Major finding 'synthetic-major-1'"

    $ResolvedPass = Copy-SyntheticJsonObject $Pass
    $ResolvedPass.Payload = ([string]$ResolvedPass.Payload).Replace(
        'priorFindingDispositions: none',
        ('priorFindingDispositions: - findingId: synthetic-major-1; ' +
            'disposition: RESOLVED; evidence: the repair removed the defect')
    )
    $ResolvedDocument = New-ReviewDocument -Passes @($Revise, $ResolvedPass)
    $ResolvedContract = Get-StoryReviewContract -Content $ResolvedDocument `
        -StorySlug $Base.Story
    Assert-Equal $ResolvedContract.Passes.Count 2 `
        'A properly dispositioned repair pass was rejected.'
}

Invoke-Case 'reviewer identity must be the independent critic' {
    $Malformed = $Base.Review.Replace(
        'reviewer: continuity_critic',
        'reviewer: coordinator'
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $Malformed -StorySlug $Base.Story
    } 'reviewer must be continuity_critic'
}

Invoke-Case 'draft repair cannot be assigned to the final-story editor' {
    $Pass = New-SyntheticPass -Story $Base.Story -Pass 1 -Artifact '03-draft.md' `
        -ArtifactSha256 $Base.DraftHash -CanonDeltaSha256 not-applicable `
        -Verdict REVISE -ReviewedAt '2026-08-02T10:00:00-04:00' `
        -Major 1 -ResolutionOwner story_editor -CertificationEligible $false `
        @BasePassBindings
    Assert-Throws {
        Get-StoryReviewContract -Content (New-ReviewDocument -Passes @($Pass)) `
            -StorySlug $Base.Story
    } 'REVISE has inconsistent blockers, ownership, counts, or eligibility'
}

Invoke-Case 'final repair cannot be assigned to the draft prose writer' {
    $Pass = New-SyntheticPass -Story $Base.Story -Pass 1 -Artifact '05-story.md' `
        -ArtifactSha256 $Base.FinalHash -CanonDeltaSha256 $Base.DeltaHash `
        -Verdict REVISE -ReviewedAt '2026-08-02T10:00:00-04:00' `
        -Major 1 -ResolutionOwner prose_writer -CertificationEligible $false `
        @BasePassBindings
    Assert-Throws {
        Get-StoryReviewContract -Content (New-ReviewDocument -Passes @($Pass)) `
            -StorySlug $Base.Story
    } 'REVISE has inconsistent blockers, ownership, counts, or eligibility'
}

Invoke-Case 'duplicate Current certification fields are rejected' {
    $DuplicateCurrent = $Base.Review.Replace(
        '- Reviewer: continuity_critic',
        "- Reviewer: continuity_critic`n- Reviewer: continuity_critic"
    )
    Assert-Throws {
        Get-StoryReviewContract -Content $DuplicateCurrent -StorySlug $Base.Story
    } "duplicates field 'Reviewer'"
}

Invoke-Case 'a release cannot omit the draft PASS' {
    $FinalOnly = New-SyntheticPass -Story $Base.Story -Pass 1 -Artifact '05-story.md' `
        -ArtifactSha256 $Base.FinalHash -CanonDeltaSha256 $Base.DeltaHash -Verdict PASS `
        -ReviewedAt '2026-08-02T11:00:00-04:00' @BasePassBindings
    $Document = New-ReviewDocument -Passes @($FinalOnly)
    Assert-Throws {
        Get-BaseReleaseContract -Content $Document
    } 'hash-current 03-draft.md PASS'
}

Invoke-Case 'a stale draft PASS cannot satisfy the draft gate' {
    Assert-Throws {
        Get-BaseReleaseContract -Content $Base.Review -DraftSha256 ('f' * 64)
    } 'hash-current 03-draft.md PASS'
}

Invoke-Case 'a later draft BLOCK invalidates an earlier draft PASS' {
    $DraftBlock = New-SyntheticPass -Story $Base.Story -Pass 2 `
        -Artifact '03-draft.md' -ArtifactSha256 $Base.DraftHash `
        -CanonDeltaSha256 not-applicable -Verdict BLOCK `
        -ReviewedAt '2026-08-02T10:30:00-04:00' -Critical 1 `
        -BlockType REPAIRABLE -ResolutionOwner prose_writer `
        -CertificationEligible $false @BasePassBindings
    $FinalPass = New-SyntheticPass -Story $Base.Story -Pass 3 `
        -Artifact '05-story.md' -ArtifactSha256 $Base.FinalHash `
        -CanonDeltaSha256 $Base.DeltaHash -Verdict PASS `
        -ReviewedAt '2026-08-02T11:00:00-04:00' @BasePassBindings
    $Document = New-ReviewDocument -Passes @(
        $Base.DraftPass, $DraftBlock, $FinalPass
    )
    Assert-Throws {
        Get-BaseReleaseContract -Content $Document
    } 'latest draft review before final review.*hash-current 03-draft.md PASS'
}

foreach ($BindingCase in @(
    [pscustomobject]@{ Name = 'canon brief'; Parameter = 'CanonBriefSha256' },
    [pscustomobject]@{ Name = 'story plan'; Parameter = 'PlanSha256' },
    [pscustomobject]@{ Name = 'authority manifest'; Parameter = 'AuthorityManifestSha256' },
    [pscustomobject]@{ Name = 'scoped name registry'; Parameter = 'ScopedRegistrySha256' }
)) {
    Invoke-Case "a stale $($BindingCase.Name) cannot satisfy the final review gate" {
        $Arguments = @{ Content = $Base.Review }
        $Arguments[$BindingCase.Parameter] = 'f' * 64
        Assert-Throws {
            Get-BaseReleaseContract @Arguments
        } 'Latest review pass must be a certification-eligible PASS'
    }.GetNewClosure()
}

foreach ($BlockingVerdict in @('REVISE', 'BLOCK')) {
    Invoke-Case "later $BlockingVerdict invalidates an earlier final PASS" {
        if ($BlockingVerdict -eq 'REVISE') {
            $Later = New-SyntheticPass -Story $Base.Story -Pass 3 -Artifact '05-story.md' `
                -ArtifactSha256 $Base.FinalHash -CanonDeltaSha256 $Base.DeltaHash -Verdict REVISE `
                -ReviewedAt '2026-08-02T12:00:00-04:00' -Major 1 `
                -ResolutionOwner story_editor -CertificationEligible $false @BasePassBindings
        }
        else {
            $Later = New-SyntheticPass -Story $Base.Story -Pass 3 -Artifact '05-story.md' `
                -ArtifactSha256 $Base.FinalHash -CanonDeltaSha256 $Base.DeltaHash -Verdict BLOCK `
                -ReviewedAt '2026-08-02T12:00:00-04:00' -Critical 1 -BlockType REPAIRABLE `
                -ResolutionOwner story_editor -CertificationEligible $false @BasePassBindings
        }
        $Document = New-ReviewDocument -Passes @($Base.DraftPass, $Base.FinalPass, $Later)
        Assert-Throws {
            Get-BaseReleaseContract -Content $Document
        } 'Latest review pass must be a certification-eligible PASS'
    }
}

Invoke-Case 'editing a certified payload invalidates pass and history digests' {
    $Before = Get-BaseReleaseContract -Content $Base.Review
    $EditedReview = $Base.Review.Replace(
        'reviewBasis: synthetic final authority snapshot',
        'reviewBasis: synthetic final authority snapshot plus edited evidence'
    )
    $After = Get-BaseReleaseContract -Content $EditedReview
    Assert-True ($After.ReleaseReview.passSha256 -cne $Before.ReleaseReview.passSha256) 'Certified pass digest did not change.'
    Assert-True ($After.ReleaseReview.historySha256 -cne $Before.ReleaseReview.historySha256) 'History digest did not change.'
    Assert-Equal $After.ReleaseReview.draftPassSha256 $Before.ReleaseReview.draftPassSha256 'Unchanged draft pass digest changed.'
    Assert-Throws {
        Assert-ReviewReleaseBinding -ReleaseReview $Before.ReleaseReview -ReviewContract $After
    } 'review.passSha256 does not match'
}

Invoke-Case 'integrity validator accepts the untouched pending review contract' {
    $FixtureRoot = Join-Path ([IO.Path]::GetTempPath()) ("review-pending-" + [guid]::NewGuid().ToString('N'))
    $Slug = 'synthetic-pending'
    $Title = 'Synthetic Pending'
    $StoryDirectory = Join-Path $FixtureRoot "stories/$Slug"
    try {
        New-Item -ItemType Directory -Path $StoryDirectory -Force | Out-Null
        Initialize-SyntheticIntegritySchemas $FixtureRoot
        $Index = @(
            '# Story index', '',
            '| Story | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |',
            "| ``$Slug`` | *$Title* | in-progress | no | pending | no | — | Synthetic. |", ''
        ) -join "`n"
        Set-Utf8LfFile (Join-Path $FixtureRoot 'stories/INDEX.md') $Index
        $PendingPrompt = @(
            '# Prompt contract', '', '## Verbatim writing prompt', '',
            '> Synthetic pending prompt.', '', '## Story controls', '',
            '- Working title: Synthetic Pending', '- Target length: 130 words',
            '- POV: third person', '- Tense: present',
            '- Tone and genre: neutral fixture',
            '- Audience/content rating: general',
            '- Required elements: deterministic fixture',
            '- Prohibited elements: none', '', '## Assumptions', '',
            '- Work has not advanced beyond prompt capture.', '',
            '## Completion tests', '', '- Later stages remain pending.', ''
        ) -join "`n"
        Set-Utf8LfFile (Join-Path $StoryDirectory '00-prompt.md') $PendingPrompt
        Set-Utf8LfFile (Join-Path $StoryDirectory '01-canon-brief.md') "# Canon brief`n`nPending.`n"
        Set-Utf8LfFile (Join-Path $StoryDirectory '02-story-plan.md') "# Story plan`n`nPending.`n"
        Set-Utf8LfFile (Join-Path $StoryDirectory '03-draft.md') "# Draft`n`nPending.`n"
        Set-Utf8LfFile (Join-Path $StoryDirectory '04-review.md') (
            Get-Content -LiteralPath (Join-Path $RepositoryRoot 'stories/_template/04-review.md') -Raw
        )
        Set-Utf8LfFile (Join-Path $StoryDirectory '05-story.md') @"
---
title: "$Title"
slug: "$Slug"
created: 2026-08-02
---

# $Title

Pending.
"@
        Set-Utf8LfFile (Join-Path $StoryDirectory '06-canon-delta.md') "# Canon delta`n`nPending.`n"
        $Checklist = @(
            'Prompt contract captured', 'Canon brief completed', 'Story plan completed',
            'Plan name check passed', 'Complete draft written', 'Draft review passed',
            'Critical and major findings resolved', 'Final story written',
            'Canon delta recorded', 'Final story review passed', 'Final name check passed',
            'Name registry updated', 'Release certificate issued', 'Story index updated',
            'Canon promotion explicitly approved (optional)'
        ) | ForEach-Object { "- [ ] $_" }
        $Readme = @(
            "# $Title — production record", '', "- Slug: ``$Slug``",
            '- Created: 2026-08-02', '- Current stage: prompt', '- Status: in-progress',
            '- Canon: no', '- User disposition: pending', '- Publish: no',
            '- Promotion date: —', '', '## Checklist', ''
        ) + $Checklist + @('')
        Set-Utf8LfFile (Join-Path $StoryDirectory 'README.md') ($Readme -join "`n")
        $Metadata = [ordered]@{
            schemaVersion = 1; slug = $Slug; title = $Title; created = '2026-08-02'
            stage = 'prompt'; status = 'in-progress'; canon = $false
            userDisposition = 'pending'; publish = $false; promotionDate = $null
        }
        Set-Utf8LfFile (Join-Path $StoryDirectory 'story.json') (($Metadata | ConvertTo-Json) + "`n")
        $ReleaseTemplate = (Get-Content -LiteralPath (Join-Path $RepositoryRoot 'stories/_template/release.json') -Raw).
            Replace('{{slug}}', $Slug)
        Set-Utf8LfFile (Join-Path $StoryDirectory 'release.json') $ReleaseTemplate
        $AuthorityTemplate = (Get-Content -LiteralPath (Join-Path $RepositoryRoot 'stories/_template/authority.json') -Raw).
            Replace('{{slug}}', $Slug)
        Set-Utf8LfFile (Join-Path $StoryDirectory 'authority.json') $AuthorityTemplate
        $HandoffTemplate = (Get-Content -LiteralPath (Join-Path $RepositoryRoot 'stories/_template/handoffs.json') -Raw).
            Replace('{{slug}}', $Slug)
        Set-Utf8LfFile (Join-Path $StoryDirectory 'handoffs.json') $HandoffTemplate
        $PromotionTemplate = (Get-Content -LiteralPath (Join-Path $RepositoryRoot 'stories/_template/promotion.json') -Raw).
            Replace('{{slug}}', $Slug)
        Set-Utf8LfFile (Join-Path $StoryDirectory 'promotion.json') $PromotionTemplate

        $Output = & pwsh -NoLogo -NoProfile -File $IntegrityValidatorPath `
            -Story $Slug -OutputFormat Json -ProjectRoot $FixtureRoot
        Assert-Equal $LASTEXITCODE 0 "Pending fixture validator failed: $($Output -join ' ')"
        $Receipt = $Output | ConvertFrom-Json
        Assert-True ($Receipt.passed -eq $true) 'Pending fixture did not return a passing receipt.'

        $FixtureContractPath = Join-Path $FixtureRoot 'schemas/pipeline-contract.json'
        $OriginalContract = Get-Content -LiteralPath $FixtureContractPath -Raw
        $MissingLifecycle = $OriginalContract | ConvertFrom-Json
        $MissingLifecycle.PSObject.Properties.Remove('lifecycle')
        Set-Utf8LfFile $FixtureContractPath (($MissingLifecycle | ConvertTo-Json -Depth 12) + "`n")
        $MalformedLifecycleOutput = & pwsh -NoLogo -NoProfile -File $IntegrityValidatorPath `
            -Story $Slug -OutputFormat Json -ProjectRoot $FixtureRoot
        Assert-True ($LASTEXITCODE -ne 0) 'Validator accepted a missing lifecycle contract.'
        $MalformedLifecycleReceipt = $MalformedLifecycleOutput | ConvertFrom-Json
        Assert-True ((@($MalformedLifecycleReceipt.errors) -join ' ') -match
            'lacks story/lifecycle contract structure') `
            'Missing lifecycle contract did not produce a graceful integrity error.'

        Set-Utf8LfFile $FixtureContractPath $OriginalContract
        $MissingRelease = $OriginalContract | ConvertFrom-Json
        $MissingRelease.PSObject.Properties.Remove('release')
        Set-Utf8LfFile $FixtureContractPath (($MissingRelease | ConvertTo-Json -Depth 12) + "`n")
        $MalformedReleaseOutput = & pwsh -NoLogo -NoProfile -File $IntegrityValidatorPath `
            -Story $Slug -OutputFormat Json -ProjectRoot $FixtureRoot
        Assert-True ($LASTEXITCODE -ne 0) 'Validator accepted a missing release contract.'
        $MalformedReleaseReceipt = $MalformedReleaseOutput | ConvertFrom-Json
        Assert-True ((@($MalformedReleaseReceipt.errors) -join ' ') -match
            'lacks a valid release contract') `
            "Missing release contract did not produce a graceful integrity error: $(@($MalformedReleaseReceipt.errors) -join ' | ')"
    }
    finally {
        if (Test-Path -LiteralPath $FixtureRoot -PathType Container) {
            Remove-Item -LiteralPath $FixtureRoot -Recurse -Force
        }
    }
}

Invoke-Case 'release issuer emits v2 review and provenance bindings' {
    $FixtureRoot = Join-Path ([IO.Path]::GetTempPath()) ("review-contract-" + [guid]::NewGuid().ToString('N'))
    $StoryDirectory = Join-Path $FixtureRoot "stories/$($Base.Story)"
    try {
        New-Item -ItemType Directory -Path $StoryDirectory -Force | Out-Null
        Initialize-SyntheticIntegritySchemas $FixtureRoot
        $Index = @(
            '# Story index', '',
            '| Story | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |',
            "| ``$($Base.Story)`` | *Synthetic Review* | candidate | no | accepted | no | — | Synthetic. |", ''
        ) -join "`n"
        Set-Utf8LfFile (Join-Path $FixtureRoot 'stories/INDEX.md') $Index
        Set-Utf8LfFile (Join-Path $StoryDirectory '00-prompt.md') $Base.Prompt
        Set-Utf8LfFile (Join-Path $StoryDirectory '01-canon-brief.md') $Base.CanonBrief
        Set-Utf8LfFile (Join-Path $StoryDirectory '02-story-plan.md') $Base.Plan
        Set-Utf8LfFile (Join-Path $StoryDirectory '03-draft.md') $Base.Draft
        Set-Utf8LfFile (Join-Path $StoryDirectory '04-review.md') $Base.Review
        Set-Utf8LfFile (Join-Path $StoryDirectory '05-story.md') $Base.Final
        Set-Utf8LfFile (Join-Path $StoryDirectory '06-canon-delta.md') $Base.Delta
        Set-Utf8LfFile (Join-Path $StoryDirectory 'authority.json') $Base.Authority
        Set-Utf8LfFile (Join-Path $StoryDirectory 'handoffs.json') $Base.LedgerJson
        $PromotionTemplate = (Get-Content -LiteralPath (Join-Path $RepositoryRoot 'stories/_template/promotion.json') -Raw).
            Replace('{{slug}}', $Base.Story)
        Set-Utf8LfFile (Join-Path $StoryDirectory 'promotion.json') $PromotionTemplate
        Set-Utf8LfFile (Join-Path $StoryDirectory 'story.json') $Base.Metadata
        $Checklist = @(
            'Prompt contract captured', 'Canon brief completed', 'Story plan completed',
            'Plan name check passed', 'Complete draft written', 'Draft review passed',
            'Critical and major findings resolved', 'Final story written',
            'Canon delta recorded', 'Final story review passed', 'Final name check passed',
            'Name registry updated', 'Release certificate issued', 'Story index updated'
        ) | ForEach-Object { "- [x] $_" }
        $Readme = @(
            '# Synthetic Review — production record', '', "- Slug: ``$($Base.Story)``",
            '- Created: 2026-08-02', '- Current stage: candidate', '- Status: candidate',
            '- Canon: no', '- User disposition: accepted', '- Publish: no',
            '- Promotion date: —', '', '## Checklist', ''
        ) + $Checklist + @('- [ ] Canon promotion explicitly approved (optional)', '')
        Set-Utf8LfFile (Join-Path $StoryDirectory 'README.md') ($Readme -join "`n")

        $CheckerPath = Join-Path $FixtureRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
        Set-Utf8LfFile $CheckerPath @'
param($Story, $Phase, $OutputFormat, $ProjectRoot)
$utf8 = [Text.UTF8Encoding]::new($false)
function Get-TextHash([string]$Text) {
    [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($utf8.GetBytes($Text))
    ).ToLowerInvariant()
}
$storyHash = (Get-FileHash -LiteralPath (Join-Path $ProjectRoot "stories/$Story/05-story.md") -Algorithm SHA256).Hash.ToLowerInvariant()
$deltaHash = (Get-FileHash -LiteralPath (Join-Path $ProjectRoot "stories/$Story/06-canon-delta.md") -Algorithm SHA256).Hash.ToLowerInvariant()
$scopedHash = ('a' * 64)
$activeHash = ('c' * 64)
$warnings = @()
$artifactHash = Get-TextHash "$storyHash`n$deltaHash"
$warningsHash = Get-TextHash (ConvertTo-Json -InputObject $warnings -Compress)
$checkerVersion = 'story-names/2'
$receiptId = Get-TextHash (
    "$checkerVersion`n$Story`n$($Phase.ToLowerInvariant())`n$artifactHash`n" +
    "$scopedHash`n$activeHash`n$warningsHash"
)
[ordered]@{
    schemaVersion = 1
    passed = $true
    story = $Story
    phase = $Phase
    checkedAt = '2026-08-02T16:00:00Z'
    receiptId = $receiptId
    storySha256 = $storyHash
    canonDeltaSha256 = $deltaHash
    planSha256 = $null
    scopedRegistrySha256 = $scopedHash
    activeRegistrySha256 = $activeHash
    checkerVersion = $checkerVersion
    warnings = $warnings
} | ConvertTo-Json
'@
        $HandoffCheckerPath = Join-Path $FixtureRoot '.agents/skills/story-integrity/scripts/Test-StoryHandoffs.ps1'
        Set-Utf8LfFile $HandoffCheckerPath @'
param($Story, [switch]$RequireReleaseChain, $OutputFormat, $ProjectRoot)
[ordered]@{
    passed = $true
    story = $Story
    ledgerSha256 = (Get-FileHash -LiteralPath (Join-Path $ProjectRoot "stories/$Story/handoffs.json") -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json
'@
        $AuthorityVerifierPath = Join-Path $FixtureRoot '.agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1'
        Set-Utf8LfFile $AuthorityVerifierPath @'
param($Story, [switch]$Verify, $OutputFormat, $ProjectRoot)
[ordered]@{
    passed = $true
    story = $Story
    manifestSha256 = (Get-FileHash -LiteralPath (Join-Path $ProjectRoot "stories/$Story/authority.json") -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json
'@

        $null = & $ReleaseIssuerPath -Story $Base.Story -ProjectRoot $FixtureRoot
        $ReleasePath = Join-Path $StoryDirectory 'release.json'
        $Release = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json
        Assert-Equal $Release.schemaVersion ([int64]2) 'Issuer did not emit schema v2.'
        Assert-Equal $Release.review.pass ([int64]2) 'Issuer bound the wrong final pass.'
        Assert-Equal $Release.review.draftPass ([int64]1) 'Issuer bound the wrong draft pass.'
        foreach ($Field in @('passSha256', 'historySha256', 'draftPassSha256')) {
            Assert-True ($Release.review.$Field -cmatch '^[a-f0-9]{64}$') "Issuer review.$Field is not a digest."
        }
        foreach ($Field in @(
            'promptSha256', 'canonBriefSha256', 'planSha256', 'draftSha256',
            'authorityManifestSha256', 'handoffLedgerSha256'
        )) {
            Assert-True ($Release.provenance.$Field -cmatch '^[a-f0-9]{64}$') "Issuer provenance.$Field is not a digest."
        }
        $ValidationOutput = & pwsh -NoLogo -NoProfile -File $IntegrityValidatorPath `
            -Story $Base.Story -OutputFormat Json -ProjectRoot $FixtureRoot
        Assert-Equal $LASTEXITCODE 0 "Issued candidate failed integrity: $($ValidationOutput -join ' ')"
        $ValidationReceipt = $ValidationOutput | ConvertFrom-Json
        Assert-True ($ValidationReceipt.passed -eq $true) 'Issued candidate did not return a passing integrity receipt.'

        $CanonBriefPath = Join-Path $StoryDirectory '01-canon-brief.md'
        $OriginalCanonBrief = Get-Content -LiteralPath $CanonBriefPath -Raw
        Set-Utf8LfFile $CanonBriefPath (
            $OriginalCanonBrief.Replace(
                '> Research status: READY',
                '> Research status: MIGRATED'
            )
        )
        $MigratedResearchOutput = & pwsh -NoLogo -NoProfile -File $IntegrityValidatorPath `
            -Story $Base.Story -OutputFormat Json -ProjectRoot $FixtureRoot
        Assert-True ($LASTEXITCODE -ne 0) `
            'Integrity accepted mechanically migrated research for a candidate release.'
        $MigratedResearchReceipt = $MigratedResearchOutput | ConvertFrom-Json
        Assert-True ((@($MigratedResearchReceipt.errors) -join ' ') -match
            'Research status must be READY') `
            "Migrated research did not fail through the pipeline-artifact receipt: $(@($MigratedResearchReceipt.errors) -join ' | ')"
        Set-Utf8LfFile $CanonBriefPath $OriginalCanonBrief

        $OriginalRelease = Get-Content -LiteralPath $ReleasePath -Raw
        $TamperedReceiptRelease = $OriginalRelease | ConvertFrom-Json
        $TamperedReceiptRelease.nameCheck.activeRegistrySha256 = 'e' * 64
        Set-Utf8LfFile $ReleasePath (
            ($TamperedReceiptRelease | ConvertTo-Json -Depth 12) + "`n"
        )
        $TamperedReceiptOutput = & pwsh -NoLogo -NoProfile -File $IntegrityValidatorPath `
            -Story $Base.Story -OutputFormat Json -ProjectRoot $FixtureRoot
        Assert-True ($LASTEXITCODE -ne 0) 'Tampered stored historical name receipt was accepted.'
        Assert-True (($TamperedReceiptOutput -join ' ') -match 'receiptId checksum is inconsistent') `
            'Tampered stored historical name receipt did not fail checksum validation.'
        Set-Utf8LfFile $ReleasePath $OriginalRelease

        $Before = Get-FileHash -LiteralPath $ReleasePath -Algorithm SHA256
        $CheckerSource = Get-Content -LiteralPath $CheckerPath -Raw
        Set-Utf8LfFile $CheckerPath ($CheckerSource.Replace(
            "activeHash = ('c' * 64)",
            "activeHash = ('d' * 64)"
        ))
        $RegistryValidationOutput = & pwsh -NoLogo -NoProfile -File $IntegrityValidatorPath `
            -Story $Base.Story -OutputFormat Json -ProjectRoot $FixtureRoot
        Assert-Equal $LASTEXITCODE 0 "Unrelated active-registry change invalidated release: $($RegistryValidationOutput -join ' ')"

        Set-Utf8LfFile (Join-Path $StoryDirectory 'authority.json') (
            $Base.Authority.TrimEnd() + " `n"
        )
        Assert-Throws {
            & $ReleaseIssuerPath -Story $Base.Story -ProjectRoot $FixtureRoot
        } 'Latest review pass must be a certification-eligible PASS'
        $AfterAuthorityFailure = Get-FileHash -LiteralPath $ReleasePath -Algorithm SHA256
        Assert-Equal $AfterAuthorityFailure.Hash $Before.Hash `
            'Unbridged authority change overwrote the existing release.'
        Set-Utf8LfFile (Join-Path $StoryDirectory 'authority.json') $Base.Authority

        $Later = New-SyntheticPass -Story $Base.Story -Pass 3 -Artifact '05-story.md' `
            -ArtifactSha256 $Base.FinalHash -CanonDeltaSha256 $Base.DeltaHash -Verdict REVISE `
            -ReviewedAt '2026-08-02T12:00:00-04:00' -Major 1 `
            -ResolutionOwner story_editor -CertificationEligible $false @BasePassBindings
        Set-Utf8LfFile (Join-Path $StoryDirectory '04-review.md') (
            New-ReviewDocument -Passes @($Base.DraftPass, $Base.FinalPass, $Later)
        )
        Assert-Throws {
            & $ReleaseIssuerPath -Story $Base.Story -ProjectRoot $FixtureRoot
        } 'Latest review pass must be a certification-eligible PASS'
        $After = Get-FileHash -LiteralPath $ReleasePath -Algorithm SHA256
        Assert-Equal $After.Hash $Before.Hash 'Failed issuance overwrote the existing release.'
    }
    finally {
        if (Test-Path -LiteralPath $FixtureRoot -PathType Container) {
            Remove-Item -LiteralPath $FixtureRoot -Recurse -Force
        }
    }
}

Write-Output "Review contract tests: $($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
