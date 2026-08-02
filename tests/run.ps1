#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$NewStoryScript = Join-Path $RepoRoot '.agents/skills/story-room/scripts/new-story.ps1'
$NameScript = Join-Path $RepoRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
$ReleaseScript = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/New-StoryRelease.ps1'
$IntegrityScript = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1'
$PromotionScript = Join-Path $RepoRoot '.agents/skills/canon-maintenance/scripts/Complete-CanonPromotion.ps1'
$PromotionContracts = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/PromotionContracts.ps1'
. $PromotionContracts
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) (
    'story-integrity-tests-' + [guid]::NewGuid().ToString('N')
)
$script:Passed = 0
$script:Failed = 0

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )
    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
        New-Item -ItemType Directory -Path $Parent | Out-Null
    }
    Set-Content -LiteralPath $Path -Value $Content -Encoding utf8NoBOM -NoNewline
}

function Invoke-ExternalScript {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string[]]$Arguments = @()
    )
    $Output = & $Pwsh -NoLogo -NoProfile -File $Path @Arguments 2>&1 | Out-String
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $Output.Trim() }
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Assert-ExitCode {
    param(
        [Parameter(Mandatory = $true)][object]$Result,
        [Parameter(Mandatory = $true)][int]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )
    if ($Result.ExitCode -ne $Expected) {
        throw "$Context expected exit $Expected, got $($Result.ExitCode). Output:`n$($Result.Output)"
    }
}

function Assert-FileBytesEqual {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Context
    )
    Assert-True (
        [Convert]::ToBase64String($Expected) -ceq
            [Convert]::ToBase64String([IO.File]::ReadAllBytes($Path))
    ) "$Context bytes changed."
}

function Get-TextSha256 {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Bytes)
    ).ToLowerInvariant()
}

function Get-FileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-HandoffEntrySha256 {
    param([Parameter(Mandatory = $true)][object]$Entry)

    $Canonical = [ordered]@{}
    foreach ($Property in $Entry.PSObject.Properties) {
        if ($Property.Name -cne 'entrySha256') {
            $Canonical[$Property.Name] = $Property.Value
        }
    }
    $Json = ($Canonical | ConvertTo-Json -Depth 10 -Compress).
        Replace("`r`n", "`n").Replace("`r", "`n")
    return Get-TextSha256 $Json
}

function Get-HandoffLedgerSnapshotSha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Story,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Entries,
        [Parameter(Mandatory = $true)][AllowNull()][object]$ChainHead
    )

    $Ledger = [ordered]@{
        schemaVersion = 2
        storySlug = $Story
        chainHead = $ChainHead
        entries = @($Entries)
    }
    $Json = ($Ledger | ConvertTo-Json -Depth 16).
        Replace("`r`n", "`n").Replace("`r", "`n") + "`n"
    return Get-TextSha256 $Json
}

function New-HandoffEntry {
    param(
        [Parameter(Mandatory = $true)][int]$Sequence,
        [Parameter(Mandatory = $true)][string]$Story,
        [Parameter(Mandatory = $true)][string]$Actor,
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][string]$Report,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Inputs,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Outputs,
        [Parameter(Mandatory = $true)][AllowNull()][object]$PreviousEntrySha256
    )

    if ($Mode -notin @('REVIEW_DRAFT', 'REVIEW_FINAL')) {
        $InputMap = @{}; foreach ($Input in $Inputs) { $InputMap[[string]$Input.path] = $Input }
        $OutputMap = @{}; foreach ($Output in $Outputs) { $OutputMap[[string]$Output.path] = $Output }
        $Prefix = "stories/$Story"
        $Persister = if ($Actor -ceq 'canon_librarian') { 'coordinator' } else { $Actor }
        $Lines = [Collections.Generic.List[string]]::new()
        foreach ($Line in @(
            'HANDOFF_REPORT', "story: $Story", "mode: $Mode", 'status: READY',
            "resolutionOwner: $Persister", 'errorCode: none', 'resolutionQuestion: none',
            "handoffLedger: $Prefix/handoffs.json",
            "handoffLedgerSha256: $($InputMap["$Prefix/handoffs.json"].sha256)"
        )) { $Lines.Add($Line) }
        switch ($Mode) {
            'RESEARCH_CANON' {
                $Lines.Add("handoffLedgerChainHead: $(if ($null -eq $PreviousEntrySha256) { 'none' } else { $PreviousEntrySha256 })")
                $Lines.Add("sourcePromptSha256: $($InputMap["$Prefix/00-prompt.md"].sha256)")
                $Lines.Add("authorityManifestSha256: $($InputMap["$Prefix/authority.json"].sha256)")
                $Lines.Add('BEGIN_FILE_CONTENT')
                foreach ($Line in @($Report.Replace("`r`n", "`n").Replace("`r", "`n").TrimEnd("`n") -split "`n")) { $Lines.Add($Line) }
                $Lines.Add('END_FILE_CONTENT')
            }
            'CREATE_PLAN' {
                $Output = $OutputMap["$Prefix/02-story-plan.md"]
                $Lines.Add("inputPromptSha256: $($InputMap["$Prefix/00-prompt.md"].sha256)")
                $Lines.Add("inputCanonBriefSha256: $($InputMap["$Prefix/01-canon-brief.md"].sha256)")
                $Lines.Add("beforePlanSha256: $($Output.beforeSha256)")
                $Lines.Add("planScaffoldSha256: $($Output.beforeSha256)")
                $Lines.Add("newPlanSha256: $($Output.afterSha256)")
            }
            'CREATE_DRAFT' {
                $Output = $OutputMap["$Prefix/03-draft.md"]
                $Lines.Add("beforeDraftSha256: $($Output.beforeSha256)")
                $Lines.Add("draftScaffoldSha256: $($Output.beforeSha256)")
                $Lines.Add("newDraftSha256: $($Output.afterSha256)")
            }
            'CREATE_FINAL' {
                $StoryOutput = $OutputMap["$Prefix/05-story.md"]
                $DeltaOutput = $OutputMap["$Prefix/06-canon-delta.md"]
                $Lines.Add("inputPlanSha256: $($InputMap["$Prefix/02-story-plan.md"].sha256)")
                $Lines.Add("inputDraftSha256: $($InputMap["$Prefix/03-draft.md"].sha256)")
                $Lines.Add("beforeStorySha256: $($StoryOutput.beforeSha256)")
                $Lines.Add("beforeCanonDeltaSha256: $($DeltaOutput.beforeSha256)")
                $Lines.Add("storyScaffoldSha256: $($StoryOutput.beforeSha256)")
                $Lines.Add("canonDeltaScaffoldSha256: $($DeltaOutput.beforeSha256)")
                $Lines.Add("newStorySha256: $($StoryOutput.afterSha256)")
                $Lines.Add("newCanonDeltaSha256: $($DeltaOutput.afterSha256)")
            }
        }
        $Report = ($Lines -join "`n") + "`n"
    }
    $NormalizedReport = $Report.Replace("`r`n", "`n").Replace("`r", "`n")
    $Entry = [pscustomobject][ordered]@{
        sequence = $Sequence
        story = $Story
        actor = $Actor
        mode = $Mode
        status = 'READY'
        recordedAt = ('2026-08-01T12:{0:D2}:00.0000000+00:00' -f $Sequence)
        guardId = ('{0:x32}' -f $Sequence)
        persister = if ($Actor -in @('continuity_critic', 'canon_librarian')) {
            'coordinator'
        }
        else { $Actor }
        report = $NormalizedReport
        reportSha256 = Get-TextSha256 $NormalizedReport
        inputs = @($Inputs)
        outputs = @($Outputs)
        previousEntrySha256 = $PreviousEntrySha256
        entrySha256 = $null
    }
    $Entry.entrySha256 = Get-HandoffEntrySha256 $Entry
    return $Entry
}

function New-HandoffInput {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Sha256
    )

    return [pscustomobject][ordered]@{ path = $Path; sha256 = $Sha256 }
}

function New-HandoffOutput {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [AllowNull()][object]$BeforeSha256,
        [Parameter(Mandatory = $true)][string]$AfterSha256
    )

    return [pscustomobject][ordered]@{
        path = $Path
        beforeSha256 = $BeforeSha256
        afterSha256 = $AfterSha256
    }
}

function New-ReviewPassPayload {
    param(
        [Parameter(Mandatory = $true)][string]$Story,
        [Parameter(Mandatory = $true)][int]$Pass,
        [Parameter(Mandatory = $true)][ValidateSet('REVIEW_DRAFT', 'REVIEW_FINAL')][string]$Mode,
        [Parameter(Mandatory = $true)][string]$ArtifactSha256,
        [Parameter(Mandatory = $true)][string]$CanonDeltaSha256,
        [Parameter(Mandatory = $true)][string]$CanonBriefSha256,
        [Parameter(Mandatory = $true)][string]$PlanSha256,
        [Parameter(Mandatory = $true)][string]$ScopedRegistrySha256,
        [Parameter(Mandatory = $true)][string]$AuthorityManifestSha256,
        [Parameter(Mandatory = $true)][string]$HandoffLedgerSha256,
        [Parameter(Mandatory = $true)][string]$HandoffLedgerChainHead
    )

    $Artifact = if ($Mode -ceq 'REVIEW_DRAFT') { '03-draft.md' } else { '05-story.md' }
    $ReviewedAt = if ($Mode -ceq 'REVIEW_DRAFT') {
        '2026-08-01T12:04:00Z'
    }
    else { '2026-08-01T12:06:00Z' }
    $Fields = @(
        "story: $Story",
        "mode: $Mode",
        'status: READY',
        "pass: $Pass",
        "reviewedArtifact: $Artifact",
        "artifactSha256: $ArtifactSha256",
        "canonDeltaSha256: $CanonDeltaSha256",
        "canonBriefSha256: $CanonBriefSha256",
        "planSha256: $PlanSha256",
        "scopedRegistrySha256: $ScopedRegistrySha256",
        "authorityManifest: stories/$Story/authority.json",
        "authorityManifestSha256: $AuthorityManifestSha256",
        "handoffLedger: stories/$Story/handoffs.json",
        "handoffLedgerSha256: $HandoffLedgerSha256",
        "handoffLedgerChainHead: $HandoffLedgerChainHead",
        'reviewer: continuity_critic',
        "reviewedAt: $ReviewedAt",
        'reviewBasis: fixture current-authority and bounded production snapshot',
        'verdict: PASS',
        'blockType: NONE',
        'resolutionOwner: coordinator',
        'resolutionQuestion: none',
        'errorCode: none',
        'unresolvedCounts: { critical: 0, major: 0, minor: 0 }',
        'priorFindingDispositions: none',
        'findings: none',
        'certificationEligible: true',
        'changeReport: read-only; no files changed'
    )
    $CanonicalPayload = "REVIEW_PASS_PAYLOAD`n$($Fields -join "`n")`nEND_REVIEW_PASS_PAYLOAD`n"
    return [pscustomobject][ordered]@{
        Pass = $Pass
        Mode = $Mode
        ReviewedArtifact = $Artifact
        ArtifactSha256 = $ArtifactSha256
        CanonDeltaSha256 = $CanonDeltaSha256
        Reviewer = 'continuity_critic'
        ReviewedAt = $ReviewedAt
        Verdict = 'PASS'
        UnresolvedCritical = 0
        UnresolvedMajor = 0
        CanonicalPayload = $CanonicalPayload
    }
}

function New-ReviewDocument {
    param(
        [Parameter(Mandatory = $true)][object[]]$Passes,
        [Parameter(Mandatory = $true)][object]$Latest
    )

    $History = @($Passes | ForEach-Object {
        $Label = if ($_.Mode -ceq 'REVIEW_DRAFT') { 'draft' } else { 'final' }
        "### Pass $($_.Pass) — $Label`n`n$($_.CanonicalPayload)"
    }) -join "`n"
    return @(
        '# Continuity and story review', '',
        '## Current certification', '',
        "- Reviewed artifact: ``$($Latest.ReviewedArtifact)``",
        "- Artifact SHA-256: $($Latest.ArtifactSha256)",
        "- Canon delta SHA-256: $($Latest.CanonDeltaSha256)",
        "- Review pass: $($Latest.Pass)",
        "- Verdict: $($Latest.Verdict)",
        "- Reviewer: $($Latest.Reviewer)",
        "- Unresolved Critical findings: $($Latest.UnresolvedCritical)",
        "- Unresolved Major findings: $($Latest.UnresolvedMajor)",
        "- Updated: $($Latest.ReviewedAt)", '',
        '## Review passes', '', $History
    ) -join "`n"
}

function Set-ReadyPromotionFixture {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$PromotionDate
    )

    $StoryDirectory = Join-Path $Root "stories/$Slug"
    $AuthorityPath = Join-Path $StoryDirectory 'authority.json'
    $AuthorityManifest = Get-Content -LiteralPath $AuthorityPath -Raw | ConvertFrom-Json
    $Inventory = [Collections.Generic.List[object]]::new()
    foreach ($File in @(Get-ChildItem -LiteralPath (Join-Path $Root 'universe') `
        -Recurse -File -Filter '*.md')) {
        $Relative = [IO.Path]::GetRelativePath($Root, $File.FullName).Replace('\', '/')
        $Inventory.Add([pscustomobject][ordered]@{
            path = $Relative
            sha256 = Get-FileSha256 $File.FullName
        })
    }
    $Inventory.Add([pscustomobject][ordered]@{
        path = 'stories/INDEX.md'
        sha256 = Get-FileSha256 (Join-Path $Root 'stories/INDEX.md')
    })
    $SortedInventory = @($Inventory)
    [Array]::Sort($SortedInventory, [Comparison[object]]{
        param($Left, $Right)
        return [StringComparer]::Ordinal.Compare($Left.path, $Right.path)
    })
    [string[]]$AuthorityLines = @($SortedInventory | ForEach-Object {
        "$($_.path)`t$($_.sha256)"
    })
    $AuthorityInventorySha256 = Get-TextSha256 (
        ($AuthorityLines -join "`n") + "`n"
    )

    $ReleaseSha256 = Get-FileSha256 (Join-Path $StoryDirectory 'release.json')
    $StorySha256 = Get-FileSha256 (Join-Path $StoryDirectory '05-story.md')
    $DeltaSha256 = Get-FileSha256 (Join-Path $StoryDirectory '06-canon-delta.md')
    $AuthoritySha256 = Get-FileSha256 $AuthorityPath
    $Disposition = [ordered]@{
        id = 'fixture-character'
        disposition = 'story-local'
        target = $null
        rationale = 'Fixture character remains story-local.'
    }
    $DispositionSha256 = Get-TextSha256 (
        "fixture-character`tstory-local`tnone`tFixture character remains story-local.`n"
    )
    $AuthorizationReference = 'fixture-user-authorization'
    $StewardIdentity = 'canon_steward'
    $StewardResult = 'NO_CANON_CHANGES_AWAITING_PRIMARY'
    $HandoffText = @(
        'STEWARDSHIP_HANDOFF',
        "story: $Slug",
        "authorization: $AuthorizationReference",
        "steward: $StewardIdentity",
        'candidateRelease: VERIFIED',
        "candidateReleaseSha256: $ReleaseSha256",
        'authorityRecheck: PASS',
        "authorityManifestSha256: $AuthoritySha256",
        'nameCheckReceipt: VERIFIED',
        "storySha256: $StorySha256",
        "canonDeltaSha256: $DeltaSha256",
        "deltaDispositionsSha256: $DispositionSha256",
        "result: $StewardResult",
        'retconEvidenceSha256: none',
        ''
    ) -join "`n"
    $Manifest = [ordered]@{
        schemaVersion = 1
        state = 'ready'
        storySlug = $Slug
        promotionDate = $PromotionDate
        preparedAt = '2026-08-02T12:00:00Z'
        preparationSha256 = $null
        authorization = [ordered]@{
            approved = $true
            scope = 'canon-promotion'
            storySlug = $Slug
            reference = $AuthorizationReference
        }
        stewardship = [ordered]@{
            identity = $StewardIdentity
            handoffText = $HandoffText
            handoffSha256 = Get-TextSha256 $HandoffText
            candidateRelease = 'VERIFIED'
            authorityRecheck = 'PASS'
            nameCheckReceipt = 'VERIFIED'
            result = $StewardResult
        }
        authority = [ordered]@{
            path = "stories/$Slug/authority.json"
            sha256 = $AuthoritySha256
            authoritySetSha256 = [string]$AuthorityManifest.manifestSha256
            capturedAt = '2026-08-02T12:00:00Z'
            fileCount = $SortedInventory.Count
            manifestSha256 = $AuthorityInventorySha256
            files = $SortedInventory
        }
        bundle = [ordered]@{
            release = [ordered]@{
                path = "stories/$Slug/release.json"; sha256 = $ReleaseSha256
            }
            story = [ordered]@{
                path = "stories/$Slug/05-story.md"; sha256 = $StorySha256
            }
            canonDelta = [ordered]@{
                path = "stories/$Slug/06-canon-delta.md"; sha256 = $DeltaSha256
            }
        }
        deltaInventory = [ordered]@{
            sourceArtifactSha256 = $DeltaSha256
            itemCount = 1
            dispositionsSha256 = $DispositionSha256
        }
        deltaDispositions = @($Disposition)
        universeChanges = @()
        retcon = $null
        completion = $null
    }
    $Manifest.preparationSha256 = Get-PromotionPreparationSha256 $Manifest
    Write-Utf8File (Join-Path $StoryDirectory 'promotion.json') (
        ($Manifest | ConvertTo-Json -Depth 16) + "`n"
    )
}

function Invoke-Test {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Body
    )
    try {
        & $Body
        $script:Passed++
        Write-Host "PASS $Name" -ForegroundColor Green
    }
    catch {
        $script:Failed++
        Write-Host "FAIL $Name" -ForegroundColor Red
        Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    }
}

function New-FixtureRepository {
    param([Parameter(Mandatory = $true)][string]$Name)

    $Root = Join-Path $TestRoot $Name
    New-Item -ItemType Directory -Path (Join-Path $Root 'stories') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $RepoRoot 'stories/_template') -Destination (Join-Path $Root 'stories/_template') -Recurse
    New-Item -ItemType Directory -Path (Join-Path $Root 'universe') -Force | Out-Null
    Write-Utf8File (Join-Path $Root 'universe/README.md') "# Fixture universe`n"
    foreach ($UniverseFile in @(
        'premise.md', 'rules.md', 'timeline.md', 'characters.md',
        'locations.md', 'factions.md', 'glossary.md', 'style-guide.md'
    )) {
        Write-Utf8File (Join-Path $Root "universe/$UniverseFile") @"
# Fixture $UniverseFile

## Fixture entry

- Status: PROVISIONAL
- Summary: Isolated integrity-test authority entry.
- First established: fixture setup
- Aliases: none
- Notes: Test-only structured universe content.
"@
    }
    Write-Utf8File (Join-Path $Root 'universe/retcons.md') "# Fixture retcons`n"
    Copy-Item -LiteralPath (Join-Path $RepoRoot 'sources') -Destination (Join-Path $Root 'sources') -Recurse
    Copy-Item -LiteralPath (Join-Path $RepoRoot 'schemas') -Destination (Join-Path $Root 'schemas') -Recurse
    foreach ($Skill in @('story-room', 'story-name-validation', 'story-integrity')) {
        $TargetParent = Join-Path $Root '.agents/skills'
        New-Item -ItemType Directory -Path $TargetParent -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $RepoRoot ".agents/skills/$Skill") -Destination (Join-Path $TargetParent $Skill) -Recurse
    }
    $PromotionSchemaRoot = Join-Path $Root '.agents/skills/canon-maintenance/schemas'
    New-Item -ItemType Directory -Path $PromotionSchemaRoot -Force | Out-Null
    Copy-Item -LiteralPath (
        Join-Path $RepoRoot '.agents/skills/canon-maintenance/schemas/promotion.schema.json'
    ) -Destination (Join-Path $PromotionSchemaRoot 'promotion.schema.json')
    return $Root
}

function Get-ReleaseTemplateObject {
    param([Parameter(Mandatory = $true)][string]$Slug)
    return [ordered]@{
        schemaVersion = 2; certified = $false; storySlug = $Slug; certifiedAt = $null
        artifacts = [ordered]@{
            story = [ordered]@{ path = '05-story.md'; sha256 = $null }
            canonDelta = [ordered]@{ path = '06-canon-delta.md'; sha256 = $null }
        }
        review = [ordered]@{
            artifact = $null; pass = 0; verdict = 'PENDING'; reviewer = $null
            unresolvedCritical = $null; unresolvedMajor = $null
            passSha256 = $null; historySha256 = $null; draftPass = 0
            draftPassSha256 = $null; reviewedAt = $null
        }
        nameCheck = [ordered]@{
            story = $Slug; phase = 'Final'; passed = $false; checkedAt = $null
            receiptId = $null; storySha256 = $null; canonDeltaSha256 = $null
            scopedRegistrySha256 = $null; activeRegistrySha256 = $null
            checkerVersion = $null; warnings = @()
        }
        provenance = [ordered]@{
            promptSha256 = $null; canonBriefSha256 = $null; planSha256 = $null
            draftSha256 = $null; authorityManifestSha256 = $null
            reviewAuthorityManifestSha256 = $null
            promotionPreparationSha256 = $null
            handoffLedgerSha256 = $null
        }
    }
}

function Write-Registry {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]]$Rows
    )
    $Content = @(
        '# Character name registry', '', '<!-- registry:start -->',
        '| Character / entity | Reserved forms | Story or source | State | Reuse status | Rationale / disambiguation |',
        '| --- | --- | --- | --- | --- | --- |'
    ) + $Rows + @('<!-- registry:end -->', '')
    Write-Utf8File (Join-Path $Root 'stories/NAMES.md') ($Content -join "`n")
}

function Write-Index {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string[]]$Rows
    )
    $Content = @(
        '# Story index', '',
        '| Story | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |'
    ) + $Rows + @('', 'Statuses: `in-progress`, `candidate`, `final`, or `abandoned`.')
    Write-Utf8File (Join-Path $Root 'stories/INDEX.md') ($Content -join "`n")
}

function New-ScaffoldedStory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title
    )
    $Result = Invoke-ExternalScript $NewStoryScript @(
        '-Slug', $Slug, '-Title', $Title, '-ProjectRoot', $Root
    )
    Assert-ExitCode $Result 0 "scaffold $Slug"
    return Join-Path $Root "stories/$Slug"
}

function Set-StoryJson {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][ValidateSet('in-progress', 'candidate', 'final', 'abandoned')][string]$Status,
        [Parameter(Mandatory = $true)][string]$Stage,
        [bool]$Canon = $false,
        [ValidateSet('pending', 'accepted', 'rejected')][string]$Disposition = 'pending',
        [bool]$Publish = $false,
        [AllowNull()][object]$PromotionDate = $null
    )
    $Metadata = [ordered]@{
        schemaVersion = 1; slug = $Slug; title = $Title; created = '2026-08-01'
        stage = $Stage; status = $Status; canon = $Canon
        userDisposition = $Disposition; publish = $Publish
        promotionDate = $PromotionDate
    }
    Write-Utf8File (Join-Path $Directory 'story.json') (($Metadata | ConvertTo-Json -Depth 6) + "`n")
}

function Set-ProductionReadme {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Canon,
        [Parameter(Mandatory = $true)][string]$Disposition,
        [Parameter(Mandatory = $true)][string]$Publish,
        [Parameter(Mandatory = $true)][string]$PromotionDate,
        [bool]$Complete = $false,
        [bool]$Promoted = $false
    )
    $Mark = if ($Complete) { 'x' } else { ' ' }
    $PromotionMark = if ($Promoted) { 'x' } else { ' ' }
    $Checklist = @(
        'Prompt contract captured', 'Canon brief completed', 'Story plan completed',
        'Plan name check passed', 'Complete draft written', 'Draft review passed',
        'Critical and major findings resolved', 'Final story written',
        'Canon delta recorded', 'Final story review passed', 'Final name check passed',
        'Name registry updated', 'Release certificate issued', 'Story index updated'
    ) | ForEach-Object { "- [$Mark] $_" }
    $Content = @(
        "# $Title — production record", '', "- Slug: ``$Slug``",
        '- Created: 2026-08-01', "- Current stage: $Stage", "- Status: $Status",
        "- Canon: $Canon", "- User disposition: $Disposition", "- Publish: $Publish",
        "- Promotion date: $PromotionDate", '', '## Checklist', ''
    ) + $Checklist + @("- [$PromotionMark] Canon promotion explicitly approved (optional)", '')
    Write-Utf8File (Join-Path $Directory 'README.md') ($Content -join "`n")
}

function Set-CompleteStory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title,
        [ValidateSet('candidate', 'final')][string]$Status = 'candidate'
    )
    $Directory = Join-Path $Root "stories/$Slug"
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        $Directory = New-ScaffoldedStory $Root $Slug $Title
    }
    $ReviewPath = Join-Path $Directory '04-review.md'
    $InitialReviewSha256 = Get-FileSha256 $ReviewPath
    $Canon = $Status -eq 'final'
    $PromotionDate = if ($Canon) { '2026-08-01' } else { $null }
    Set-StoryJson $Directory $Slug $Title $Status $Status $Canon 'accepted' $true $PromotionDate
    Set-ProductionReadme $Directory $Slug $Title $Status $Status $(if ($Canon) { 'yes' } else { 'no' }) 'accepted' 'yes' $(if ($Canon) { '2026-08-01' } else { '—' }) $true $Canon

    $PromptPath = Join-Path $Directory '00-prompt.md'
    $CanonBriefPath = Join-Path $Directory '01-canon-brief.md'
    $PlanPath = Join-Path $Directory '02-story-plan.md'
    $DraftPath = Join-Path $Directory '03-draft.md'
    $StoryPath = Join-Path $Directory '05-story.md'
    $DeltaPath = Join-Path $Directory '06-canon-delta.md'
    $AuthorityPath = Join-Path $Directory 'authority.json'
    $HandoffPath = Join-Path $Directory 'handoffs.json'
    $PromptContent = @(
        '# Prompt contract', '', '## Verbatim writing prompt', '',
        '> A complete fixture prompt.', '', '## Story controls', '',
        "- Working title: $Title", '- Target length: 130 words',
        '- POV: third person', '- Tense: present',
        '- Tone and genre: neutral fixture',
        '- Audience/content rating: general',
        '- Required elements: Ada Vale completes the fixture',
        '- Prohibited elements: none', '', '## Assumptions', '',
        '- All inventions remain story-local.', '', '## Completion tests', '',
        '- The release and integrity gates pass.', ''
    ) -join "`n"
    Write-Utf8File $PromptPath $PromptContent
    Write-Utf8File $CanonBriefPath "# Canon brief`n`nNo conflicts."
    Write-Utf8File $PlanPath @'
# Story plan

## Story controls

- Follow the captured fixture controls.

## Character engine

- Ada Vale wants to complete a deterministic validation task.

## Causal arc

- Ada produces evidence, the critic reviews it, and the release binds it.

## Scene plan

| # | Purpose | Conflict | Turn | Canon used | Word budget |
| --- | --- | --- | --- | --- | --- |
| 1 | Complete the fixture | Validation is strict | The receipt binds | None | 130 |

## Setup and payoff

- The initial task is paid off by a passing receipt.

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Ada Vale | `Ada Vale`; `Ada` | unique | Distinct fixture identity. |

## Failure modes to watch

- Stale hashes must fail closed.

## Proposed inventions

None.
'@
    Write-Utf8File $DraftPath "# $Title`n`nAda Vale completes a full working draft."
    $Words = (@('Ada Vale', 'Ada') + (1..130 | ForEach-Object { "word$_" })) -join ' '
    $Front = @(
        '---', ('title: ' + ($Title | ConvertTo-Json -Compress)), "slug: `"$Slug`"",
        'created: 2026-08-01',
        '---', '', "# $Title", '', $Words, ''
    ) -join "`n"
    Write-Utf8File $StoryPath $Front
    Write-Utf8File $DeltaPath @'
# Proposed canon delta

## New characters or character facts

- **Ada Vale** is the fixture protagonist.

## Final character-facing name inventory

- **Ada Vale** — Reserved forms: `Ada Vale`; `Ada`

## Reviewed prose name-audit allowlist

None.

## New locations

None.

## New factions or cultural facts

None.

## New rules, capabilities, or costs

None.

## Timeline events

None.

## New glossary terms or aliases

None.

## Name registry updates

- **Ada Vale:** register `Ada Vale`; `Ada`.

## Possible conflicts or retcons

None.

## Recommended promotions

None.
'@
    $RegistryState = if ($Canon) { 'canon' } else { 'candidate' }
    Write-Registry $Root @("| Ada Vale | ``Ada Vale``; ``Ada`` | ``$Slug`` | $RegistryState | unique | Distinct fixture identity. |")
    Write-Index $Root @("| ``$Slug`` | *$Title* | $Status | $(if ($Canon) { 'yes' } else { 'no' }) | accepted | yes | $(if ($Canon) { '2026-08-01' } else { '—' }) | Fixture. |")

    $Promotion = [ordered]@{
        schemaVersion = 1; state = 'not-prepared'; storySlug = $Slug
        promotionDate = $null; preparedAt = $null; preparationSha256 = $null; authorization = $null
        stewardship = $null; authority = $null; bundle = $null
        deltaInventory = $null; deltaDispositions = @(); universeChanges = @()
        retcon = $null; completion = $null
    }
    Write-Utf8File (Join-Path $Directory 'promotion.json') (
        ($Promotion | ConvertTo-Json -Depth 8) + "`n"
    )
    Write-Utf8File (Join-Path $Directory 'release.json') (
        ((Get-ReleaseTemplateObject $Slug) | ConvertTo-Json -Depth 8) + "`n"
    )

    $FixtureAuthorityScript = Join-Path $Root '.agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1'
    $AuthorityResult = Invoke-ExternalScript $FixtureAuthorityScript @(
        '-Story', $Slug, '-OutputFormat', 'Json', '-ProjectRoot', $Root
    )
    Assert-ExitCode $AuthorityResult 0 "authority fixture $Slug"
    $AuthorityReceipt = $AuthorityResult.Output | ConvertFrom-Json
    Assert-True (
        $AuthorityReceipt.passed -eq $true -and
        $AuthorityReceipt.manifestSha256 -ceq (Get-FileSha256 $AuthorityPath)
    ) "Authority fixture for '$Slug' is incomplete."
    $FixturePromptSha256 = Get-FileSha256 $PromptPath
    $FixtureAuthoritySha256 = Get-FileSha256 $AuthorityPath
    $CanonBriefContent = @(
        '# Canon brief', '', '> Research status: READY',
        '> Resolution owner: coordinator',
        "> Prompt SHA-256: $FixturePromptSha256",
        "> Authority manifest SHA-256: $FixtureAuthoritySha256", '',
        '## Hard constraints', '', 'None.', '',
        '## Useful established context', '', 'None.', '',
        '## Conflicts or ambiguity', '', 'None.', '',
        '## Unknowns', '', 'None.', '',
        '## Safe invention space', '', 'None.', '',
        '## Name constraints', '', '- Reserve Ada Vale and Ada.', '',
        '## Required checks after drafting', '',
        '- Review the draft and final story.', '',
        '## Sources', '', 'None.', ''
    ) -join "`n"
    Write-Utf8File $CanonBriefPath $CanonBriefContent

    $NameResult = Invoke-ExternalScript $NameScript @(
        '-Story', $Slug, '-Phase', 'Final', '-OutputFormat', 'Json',
        '-ProjectRoot', $Root
    )
    Assert-ExitCode $NameResult 0 "final name fixture $Slug"
    $NameReceipt = $NameResult.Output | ConvertFrom-Json

    $PromptSha256 = Get-FileSha256 $PromptPath
    $CanonBriefSha256 = Get-FileSha256 $CanonBriefPath
    $PlanSha256 = Get-FileSha256 $PlanPath
    $DraftSha256 = Get-FileSha256 $DraftPath
    $StorySha256 = Get-FileSha256 $StoryPath
    $DeltaSha256 = Get-FileSha256 $DeltaPath
    $AuthoritySha256 = Get-FileSha256 $AuthorityPath
    $StoryMetadataSha256 = Get-FileSha256 (Join-Path $Directory 'story.json')
    # Handoffs bind the lifecycle bytes current at that historical stage. The
    # terminal fixture's current candidate metadata is intentionally distinct.
    $ResearchMetadataSha256 = Get-TextSha256 'fixture story.json at canon-research stage'
    $PlanMetadataSha256 = Get-TextSha256 'fixture story.json at planning stage'
    $DraftMetadataSha256 = Get-TextSha256 'fixture story.json at drafting stage'
    $DraftReviewMetadataSha256 = Get-TextSha256 'fixture story.json at draft-review stage'
    $FinalEditMetadataSha256 = Get-TextSha256 'fixture story.json at final-edit stage'
    $FinalReviewMetadataSha256 = Get-TextSha256 'fixture story.json at final-review stage'
    $RegistrySha256 = Get-FileSha256 (Join-Path $Root 'stories/NAMES.md')
    $Entries = [Collections.Generic.List[object]]::new()
    $Previous = $null
    $PrefixSha256 = Get-HandoffLedgerSnapshotSha256 `
        -Story $Slug -Entries @($Entries) -ChainHead $Previous

    $Entry = New-HandoffEntry -Sequence 1 -Story $Slug `
        -Actor 'canon_librarian' -Mode 'RESEARCH_CANON' `
        -Report $CanonBriefContent `
        -Inputs @(
            (New-HandoffInput "stories/$Slug/00-prompt.md" $PromptSha256),
            (New-HandoffInput "stories/$Slug/story.json" $ResearchMetadataSha256),
            (New-HandoffInput "stories/$Slug/authority.json" $AuthoritySha256),
            (New-HandoffInput "stories/$Slug/handoffs.json" $PrefixSha256)
        ) -Outputs @(
            (New-HandoffOutput "stories/$Slug/01-canon-brief.md" $null $CanonBriefSha256)
        ) -PreviousEntrySha256 $Previous
    $Entries.Add($Entry); $Previous = $Entry.entrySha256
    $PrefixSha256 = Get-HandoffLedgerSnapshotSha256 `
        -Story $Slug -Entries @($Entries) -ChainHead $Previous

    $Entry = New-HandoffEntry -Sequence 2 -Story $Slug `
        -Actor 'story_architect' -Mode 'CREATE_PLAN' `
        -Report "story: $Slug`nmode: CREATE_PLAN`nstatus: READY`nfixture bounded plan`n" `
        -Inputs @(
            (New-HandoffInput "stories/$Slug/00-prompt.md" $PromptSha256),
            (New-HandoffInput "stories/$Slug/story.json" $PlanMetadataSha256),
            (New-HandoffInput "stories/$Slug/01-canon-brief.md" $CanonBriefSha256),
            (New-HandoffInput "stories/$Slug/authority.json" $AuthoritySha256),
            (New-HandoffInput "stories/$Slug/handoffs.json" $PrefixSha256),
            (New-HandoffInput 'stories/NAMES.md' $RegistrySha256)
        ) -Outputs @(
            (New-HandoffOutput "stories/$Slug/02-story-plan.md" ('0' * 64) $PlanSha256)
        ) -PreviousEntrySha256 $Previous
    $Entries.Add($Entry); $Previous = $Entry.entrySha256
    $PrefixSha256 = Get-HandoffLedgerSnapshotSha256 `
        -Story $Slug -Entries @($Entries) -ChainHead $Previous

    $Entry = New-HandoffEntry -Sequence 3 -Story $Slug `
        -Actor 'prose_writer' -Mode 'CREATE_DRAFT' `
        -Report "story: $Slug`nmode: CREATE_DRAFT`nstatus: READY`nfixture bounded draft`n" `
        -Inputs @(
            (New-HandoffInput "stories/$Slug/00-prompt.md" $PromptSha256),
            (New-HandoffInput "stories/$Slug/story.json" $DraftMetadataSha256),
            (New-HandoffInput "stories/$Slug/01-canon-brief.md" $CanonBriefSha256),
            (New-HandoffInput "stories/$Slug/02-story-plan.md" $PlanSha256),
            (New-HandoffInput "stories/$Slug/authority.json" $AuthoritySha256),
            (New-HandoffInput "stories/$Slug/handoffs.json" $PrefixSha256),
            (New-HandoffInput 'stories/NAMES.md' $RegistrySha256)
        ) -Outputs @(
            (New-HandoffOutput "stories/$Slug/03-draft.md" ('0' * 64) $DraftSha256)
        ) -PreviousEntrySha256 $Previous
    $Entries.Add($Entry); $Previous = $Entry.entrySha256

    $DraftLedgerSha256 = Get-HandoffLedgerSnapshotSha256 `
        -Story $Slug -Entries @($Entries) -ChainHead $Previous
    $DraftPass = New-ReviewPassPayload -Story $Slug -Pass 1 `
        -Mode REVIEW_DRAFT -ArtifactSha256 $DraftSha256 `
        -CanonDeltaSha256 'not-applicable' `
        -CanonBriefSha256 $CanonBriefSha256 -PlanSha256 $PlanSha256 `
        -ScopedRegistrySha256 $NameReceipt.scopedRegistrySha256 `
        -AuthorityManifestSha256 $AuthoritySha256 `
        -HandoffLedgerSha256 $DraftLedgerSha256 `
        -HandoffLedgerChainHead $Previous
    $DraftReviewContent = New-ReviewDocument -Passes @($DraftPass) -Latest $DraftPass
    $DraftReviewSha256 = Get-TextSha256 $DraftReviewContent

    $Entry = New-HandoffEntry -Sequence 4 -Story $Slug `
        -Actor 'continuity_critic' -Mode 'REVIEW_DRAFT' `
        -Report $DraftPass.CanonicalPayload `
        -Inputs @(
            (New-HandoffInput "stories/$Slug/00-prompt.md" $PromptSha256),
            (New-HandoffInput "stories/$Slug/story.json" $DraftReviewMetadataSha256),
            (New-HandoffInput "stories/$Slug/01-canon-brief.md" $CanonBriefSha256),
            (New-HandoffInput "stories/$Slug/02-story-plan.md" $PlanSha256),
            (New-HandoffInput "stories/$Slug/03-draft.md" $DraftSha256),
            (New-HandoffInput "stories/$Slug/04-review.md" $InitialReviewSha256),
            (New-HandoffInput "stories/$Slug/authority.json" $AuthoritySha256),
            (New-HandoffInput "stories/$Slug/handoffs.json" $DraftLedgerSha256),
            (New-HandoffInput 'stories/NAMES.md' $RegistrySha256)
        ) -Outputs @(
            (New-HandoffOutput "stories/$Slug/04-review.md" $InitialReviewSha256 $DraftReviewSha256)
        ) -PreviousEntrySha256 $Previous
    $Entries.Add($Entry); $Previous = $Entry.entrySha256
    $FinalEditLedgerSha256 = Get-HandoffLedgerSnapshotSha256 `
        -Story $Slug -Entries @($Entries) -ChainHead $Previous

    $Entry = New-HandoffEntry -Sequence 5 -Story $Slug `
        -Actor 'story_editor' -Mode 'CREATE_FINAL' `
        -Report "story: $Slug`nmode: CREATE_FINAL`nstatus: READY`nfixture bounded final edit`n" `
        -Inputs @(
            (New-HandoffInput "stories/$Slug/00-prompt.md" $PromptSha256),
            (New-HandoffInput "stories/$Slug/story.json" $FinalEditMetadataSha256),
            (New-HandoffInput "stories/$Slug/01-canon-brief.md" $CanonBriefSha256),
            (New-HandoffInput "stories/$Slug/02-story-plan.md" $PlanSha256),
            (New-HandoffInput "stories/$Slug/03-draft.md" $DraftSha256),
            (New-HandoffInput "stories/$Slug/04-review.md" $DraftReviewSha256),
            (New-HandoffInput "stories/$Slug/authority.json" $AuthoritySha256),
            (New-HandoffInput "stories/$Slug/handoffs.json" $FinalEditLedgerSha256),
            (New-HandoffInput 'stories/NAMES.md' $RegistrySha256)
        ) -Outputs @(
            (New-HandoffOutput "stories/$Slug/05-story.md" ('0' * 64) $StorySha256),
            (New-HandoffOutput "stories/$Slug/06-canon-delta.md" ('0' * 64) $DeltaSha256)
        ) -PreviousEntrySha256 $Previous
    $Entries.Add($Entry); $Previous = $Entry.entrySha256

    $FinalLedgerSha256 = Get-HandoffLedgerSnapshotSha256 `
        -Story $Slug -Entries @($Entries) -ChainHead $Previous
    $FinalPass = New-ReviewPassPayload -Story $Slug -Pass 2 `
        -Mode REVIEW_FINAL -ArtifactSha256 $StorySha256 `
        -CanonDeltaSha256 $DeltaSha256 `
        -CanonBriefSha256 $CanonBriefSha256 -PlanSha256 $PlanSha256 `
        -ScopedRegistrySha256 $NameReceipt.scopedRegistrySha256 `
        -AuthorityManifestSha256 $AuthoritySha256 `
        -HandoffLedgerSha256 $FinalLedgerSha256 `
        -HandoffLedgerChainHead $Previous
    $FinalReviewContent = New-ReviewDocument `
        -Passes @($DraftPass, $FinalPass) -Latest $FinalPass
    $FinalReviewSha256 = Get-TextSha256 $FinalReviewContent

    $Entry = New-HandoffEntry -Sequence 6 -Story $Slug `
        -Actor 'continuity_critic' -Mode 'REVIEW_FINAL' `
        -Report $FinalPass.CanonicalPayload `
        -Inputs @(
            (New-HandoffInput "stories/$Slug/00-prompt.md" $PromptSha256),
            (New-HandoffInput "stories/$Slug/story.json" $FinalReviewMetadataSha256),
            (New-HandoffInput "stories/$Slug/01-canon-brief.md" $CanonBriefSha256),
            (New-HandoffInput "stories/$Slug/02-story-plan.md" $PlanSha256),
            (New-HandoffInput "stories/$Slug/03-draft.md" $DraftSha256),
            (New-HandoffInput "stories/$Slug/04-review.md" $DraftReviewSha256),
            (New-HandoffInput "stories/$Slug/05-story.md" $StorySha256),
            (New-HandoffInput "stories/$Slug/06-canon-delta.md" $DeltaSha256),
            (New-HandoffInput "stories/$Slug/authority.json" $AuthoritySha256),
            (New-HandoffInput "stories/$Slug/handoffs.json" $FinalLedgerSha256),
            (New-HandoffInput 'stories/NAMES.md' $RegistrySha256)
        ) -Outputs @(
            (New-HandoffOutput "stories/$Slug/04-review.md" $DraftReviewSha256 $FinalReviewSha256)
        ) -PreviousEntrySha256 $Previous
    $Entries.Add($Entry); $Previous = $Entry.entrySha256

    Write-Utf8File $ReviewPath $FinalReviewContent
    $Ledger = [ordered]@{
        schemaVersion = 2
        storySlug = $Slug
        chainHead = $Previous
        entries = @($Entries)
    }
    Write-Utf8File $HandoffPath (
        (($Ledger | ConvertTo-Json -Depth 16).Replace("`r`n", "`n").Replace("`r", "`n")) + "`n"
    )
    return $Directory
}

New-Item -ItemType Directory -Path $TestRoot | Out-Null
try {
    Invoke-Test 'PowerShell 7 contract is explicit' {
        Assert-True ($PSVersionTable.PSVersion.Major -ge 7) 'Tests require PowerShell 7.'
        $FirstLine = Get-Content -LiteralPath $NewStoryScript -TotalCount 1
        Assert-True ($FirstLine -eq '#Requires -Version 7.0') 'new-story.ps1 lacks an explicit PowerShell 7 requirement.'
        $PromotionFirstLine = Get-Content -LiteralPath $PromotionScript -TotalCount 1
        Assert-True ($PromotionFirstLine -eq '#Requires -Version 7.0') 'Complete-CanonPromotion.ps1 lacks an explicit PowerShell 7 requirement.'
    }

    Invoke-Test 'new-story is transactional and rewrites every placeholder' {
        $Root = New-FixtureRepository 'transaction-success'
        $Result = Invoke-ExternalScript $NewStoryScript @('-Slug', 'safe-story', '-Title', 'Safe Story', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'transactional scaffold'
        $Directory = Join-Path $Root 'stories/safe-story'
        Assert-True (Test-Path -LiteralPath $Directory -PathType Container) 'Final story directory was not created.'
        $Unresolved = Get-ChildItem -LiteralPath $Directory -File | Where-Object Extension -in @('.md', '.json') |
            Select-String -Pattern '{{[^{}]+}}'
        Assert-True ($null -eq $Unresolved) 'Scaffold contains unresolved placeholders.'
        foreach ($File in Get-ChildItem -LiteralPath $Directory -File | Where-Object Extension -in @('.md', '.json')) {
            Assert-True (13 -notin [IO.File]::ReadAllBytes($File.FullName)) "Scaffold file $($File.Name) is not LF-only."
        }
        $Metadata = Get-Content -LiteralPath (Join-Path $Directory 'story.json') -Raw | ConvertFrom-Json
        Assert-True ($Metadata.stage -eq 'prompt' -and $Metadata.status -eq 'in-progress' -and -not $Metadata.canon -and $Metadata.userDisposition -eq 'pending' -and -not $Metadata.publish) 'Scaffold metadata does not use safe initial lifecycle values.'
        Assert-True ('sourceEditions' -notin @($Metadata.PSObject.Properties.Name)) 'Scaffold must not couple story lifecycle to source archives.'
    }

    Invoke-Test 'new-story cleans staging after a rewrite failure and is safely rerunnable' {
        $Root = New-FixtureRepository 'transaction-cleanup'
        Write-Utf8File (Join-Path $Root 'stories/_template/bad.md') '{{unknown-placeholder}}'
        $Failed = Invoke-ExternalScript $NewStoryScript @('-Slug', 'retry-me', '-Title', 'Retry Me', '-ProjectRoot', $Root)
        Assert-True ($Failed.ExitCode -ne 0) 'Expected unresolved placeholder to fail scaffolding.'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $Root 'stories/retry-me'))) 'Failed scaffold left a final directory.'
        $Temps = @(Get-ChildItem -LiteralPath (Join-Path $Root 'stories') -Directory -Filter '.retry-me.tmp.*')
        Assert-True ($Temps.Count -eq 0) 'Failed scaffold left a staging directory.'
        Remove-Item -LiteralPath (Join-Path $Root 'stories/_template/bad.md') -Force
        $Retried = Invoke-ExternalScript $NewStoryScript @('-Slug', 'retry-me', '-Title', 'Retry Me', '-ProjectRoot', $Root)
        Assert-ExitCode $Retried 0 'safe rerun'
    }

    Invoke-Test 'name checker rejects malformed registry rows' {
        $Root = New-FixtureRepository 'malformed-registry'
        $Directory = New-ScaffoldedStory $Root 'row-test' 'Row Test'
        Set-StoryJson $Directory 'row-test' 'Row Test' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') "# Story plan`n`n## Name check`n`nNone."
        Write-Registry $Root @('| Broken | `Broken` | `row-test` | in-progress | unique |')
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'row-test', '-Phase', 'Plan', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'expected 6 cells') 'Malformed registry row was not rejected clearly.'
    }

    Invoke-Test 'global name check emits a JSON receipt for an empty scope' {
        $Root = New-FixtureRepository 'global-name-receipt'
        Write-Registry $Root @('| Global Person | `Global Person` | `some-story` | candidate | unique | Fixture. |')
        $Result = Invoke-ExternalScript $NameScript @('-OutputFormat', 'Json', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'global JSON name check'
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.phase -eq 'Registry' -and $Receipt.scopedRegistrySha256 -match '^[a-f0-9]{64}$') 'Global receipt is incomplete.'
    }

    Invoke-Test 'name checker parses real delta syntax and final inventory' {
        $Root = New-FixtureRepository 'real-delta'
        $null = Set-CompleteStory $Root 'delta-story' 'Delta Story'
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'delta-story', '-Phase', 'Final', '-OutputFormat', 'Json', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'real delta final name check'
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.phase -eq 'Final' -and $Receipt.inventoryEntries -eq 1 -and $Receipt.storySha256 -match '^[a-f0-9]{64}$') 'Final name receipt is incomplete.'
    }

    Invoke-Test 'name checker rejects explanatory prose in final inventory rows' {
        $Root = New-FixtureRepository 'final-inventory-schema'
        $Directory = Set-CompleteStory $Root 'inventory-story' 'Inventory Story'
        $DeltaPath = Join-Path $Directory '06-canon-delta.md'
        $Delta = Get-Content -LiteralPath $DeltaPath -Raw
        $Delta = $Delta.Replace(
            '- **Ada Vale** — Reserved forms: `Ada Vale`; `Ada`',
            '- **Ada Vale** — Represented identity: protagonist. Reserved forms: `Ada Vale`; `Ada`'
        )
        Write-Utf8File $DeltaPath $Delta
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'inventory-story', '-Phase', 'Final', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'Malformed final name inventory row') 'Explanatory prose bypassed the strict final inventory schema.'
    }

    Invoke-Test 'name checker matches character forms case-insensitively' {
        $Root = New-FixtureRepository 'name-case'
        $Directory = Set-CompleteStory $Root 'case-story' 'Case Story'
        $FinalPath = Join-Path $Directory '05-story.md'
        $Final = (Get-Content -LiteralPath $FinalPath -Raw).Replace('Ada Vale', "ADA`nVALE")
        Write-Utf8File $FinalPath $Final
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'case-story', '-Phase', 'Final', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'case-insensitive final name check'
    }

    Invoke-Test 'name checker rejects inventory forms absent from prose and prose forms absent from inventory' {
        $Root = New-FixtureRepository 'missing-names'
        $Directory = Set-CompleteStory $Root 'missing-story' 'Missing Story'
        Write-Registry $Root @('| Ada Vale | `Ada Vale`; `Ada`; `Ace`; `Nightglass` | `missing-story` | candidate | unique | Distinct fixture identity. |')
        $Final = Get-Content -LiteralPath (Join-Path $Directory '05-story.md') -Raw
        Write-Utf8File (Join-Path $Directory '05-story.md') ($Final + "`nAce arrived.`n")
        $Delta = Get-Content -LiteralPath (Join-Path $Directory '06-canon-delta.md') -Raw
        $Delta = $Delta.Replace('`Ada Vale`; `Ada`', '`Ada Vale`; `Ada`; `Nightglass`')
        Write-Utf8File (Join-Path $Directory '06-canon-delta.md') $Delta
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'missing-story', '-Phase', 'Final', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match "Nightglass.*does not appear" -and
            $Result.Output -match "Ace.*inventory omits") 'Missing prose/inventory reconciliation defects were not both reported.'
    }

    Invoke-Test 'story scope matches exact slug rather than a prefix' {
        $Root = New-FixtureRepository 'exact-scope'
        $Directory = New-ScaffoldedStory $Root 'fox' 'Fox'
        Set-StoryJson $Directory 'fox' 'Fox' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Fara | `Fara` | unique | Exact story row. |
'@
        Write-Registry $Root @(
            '| Fara | `Fara` | `fox` | in-progress | unique | Exact story row. |',
            '| Sara | `Sara` | `unrelated-story` | candidate | unique | Close but distinct fixture form. |',
            '| Kai One | `Kai` | `foxglove` | candidate | unresolved | Unrelated collision one. |',
            '| Kai Two | `Kai` | `foxglove-two` | candidate | unresolved | Unrelated collision two. |'
        )
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'fox', '-Phase', 'Plan', '-Strict', '-ProjectRoot', $Root)
        Assert-True (
            $Result.ExitCode -ne 0 -and
            $Result.Output -match "close-spelling.*'Fara'.*'Sara'" -and
            $Result.Output -match 'Target-touching collisions require consistent deliberate reuse documentation'
        ) 'The exact target scope did not reject its own undocumented close-spelling collision.'
    }

    Invoke-Test 'released name reservations remain searchable without creating active collisions' {
        $Root = New-FixtureRepository 'released-name-reservation'
        $Directory = New-ScaffoldedStory $Root 'active-name' 'Active Name'
        Set-StoryJson $Directory 'active-name' 'Active Name' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Lena | `Lena` | unique | The released reservation does not create a live identity collision. |
'@
        Write-Registry $Root @(
            '| Active Lena | `Lena` | `active-name` | in-progress | unique | Current production identity. |',
            '| Retired Lena | `Lena` | released reservation | released | unique | Searchable production memory only. |'
        )
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'active-name', '-Phase', 'Plan', '-Strict', '-OutputFormat', 'Json', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'released reservation collision scope'
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.registryEntries -eq 2 -and $Receipt.inventoryEntries -eq 1) 'Released reservation disappeared from searchable registry memory.'
    }

    Invoke-Test 'name checker rejects prose in the architect Name check contract' {
        $Root = New-FixtureRepository 'architect-name-schema'
        $Directory = New-ScaffoldedStory $Root 'schema-story' 'Schema Story'
        Set-StoryJson $Directory 'schema-story' 'Schema Story' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

The names below were reviewed.

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Ada Vale | `Ada Vale`; `Ada` | unique | Fixture identity. |
'@
        Write-Registry $Root @('| Ada Vale | `Ada Vale`; `Ada` | `schema-story` | in-progress | unique | Fixture identity. |')
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'schema-story', '-Phase', 'Plan', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'Unexpected content in plan Name check table') 'Architect-shaped free text bypassed the exact Name check schema.'
    }

    Invoke-Test 'automatic name phase rejects unsynchronized lifecycle metadata' {
        $Root = New-FixtureRepository 'name-phase-lifecycle-sync'
        $Directory = Set-CompleteStory $Root 'phase-story' 'Phase Story'
        $MetadataPath = Join-Path $Directory 'story.json'
        $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
        $Metadata.stage = 'planning'
        Write-Utf8File $MetadataPath (($Metadata | ConvertTo-Json -Depth 6) + "`n")

        $Result = Invoke-ExternalScript $NameScript @(
            '-Story', 'phase-story', '-Phase', 'Auto', '-ProjectRoot', $Root
        )
        Assert-True (
            $Result.ExitCode -ne 0 -and
            $Result.Output -match 'Cannot infer a name-check phase from invalid lifecycle state'
        ) 'Auto name phase accepted a candidate status with a planning stage.'
    }

    Invoke-Test 'story metadata rejects unknown provenance-shaped properties' {
        $Root = New-FixtureRepository 'exact-story-schema'
        $Directory = New-ScaffoldedStory $Root 'schema-story' 'Schema Story'
        Write-Registry $Root @()
        Write-Index $Root @('| `schema-story` | *Schema Story* | in-progress | no | pending | no | — | Fixture. |')
        $MetadataPath = Join-Path $Directory 'story.json'
        $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
        $Metadata | Add-Member -NotePropertyName sourceProvenance -NotePropertyValue @{
            kind = 'archive'
        }
        Write-Utf8File $MetadataPath (($Metadata | ConvertTo-Json -Depth 6) + "`n")

        $Result = Invoke-ExternalScript $IntegrityScript @(
            '-Story', 'schema-story', '-ProjectRoot', $Root
        )
        Assert-True (
            $Result.ExitCode -ne 0 -and
            $Result.Output -match "story.json contains unknown property 'sourceProvenance'"
        ) 'Integrity accepted an arbitrary story provenance property.'
    }

    Invoke-Test 'uncertified release rejects unknown fields at every object level' {
        $Root = New-FixtureRepository 'exact-uncertified-release-schema'
        $Directory = New-ScaffoldedStory $Root 'release-schema-story' 'Release Schema Story'
        Write-Registry $Root @()
        Write-Index $Root @('| `release-schema-story` | *Release Schema Story* | in-progress | no | pending | no | — | Fixture. |')
        $ReleasePath = Join-Path $Directory 'release.json'
        $Baseline = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json

        $TopLevel = $Baseline | ConvertTo-Json -Depth 8 | ConvertFrom-Json
        $TopLevel | Add-Member -NotePropertyName sourceProvenance -NotePropertyValue 'archive'
        Write-Utf8File $ReleasePath (($TopLevel | ConvertTo-Json -Depth 8) + "`n")
        $TopResult = Invoke-ExternalScript $IntegrityScript @(
            '-Story', 'release-schema-story', '-ProjectRoot', $Root
        )
        Assert-True (
            $TopResult.ExitCode -ne 0 -and
            $TopResult.Output -match "release.json contains unknown property 'sourceProvenance'"
        ) 'Uncertified release accepted an unknown top-level field.'

        $Nested = $Baseline | ConvertTo-Json -Depth 8 | ConvertFrom-Json
        $Nested.review | Add-Member -NotePropertyName sourceClass -NotePropertyValue 'imported'
        Write-Utf8File $ReleasePath (($Nested | ConvertTo-Json -Depth 8) + "`n")
        $NestedResult = Invoke-ExternalScript $IntegrityScript @(
            '-Story', 'release-schema-story', '-ProjectRoot', $Root
        )
        Assert-True (
            $NestedResult.ExitCode -ne 0 -and
            $NestedResult.Output -match "release.json review contains unknown property 'sourceClass'"
        ) 'Uncertified release accepted an unknown nested field.'
    }

    Invoke-Test 'release certificate is invalidated by story-byte changes' {
        $Root = New-FixtureRepository 'hash-invalidation'
        $Directory = Set-CompleteStory $Root 'hash-story' 'Hash Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'hash-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'release issuance'
        $Valid = Invoke-ExternalScript $IntegrityScript @('-Story', 'hash-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Valid 0 'fresh release validation'
        $Final = Get-Content -LiteralPath (Join-Path $Directory '05-story.md') -Raw
        $FirstLf = $Final.IndexOf("`n", [StringComparison]::Ordinal)
        $Mixed = $Final.Substring(0, $FirstLf) + "`r`n" + $Final.Substring($FirstLf + 1) + "`nA harmless byte change.`n"
        Write-Utf8File (Join-Path $Directory '05-story.md') $Mixed
        $Stale = Invoke-ExternalScript $IntegrityScript @('-Story', 'hash-story', '-ProjectRoot', $Root)
        Assert-True ($Stale.ExitCode -ne 0 -and $Stale.Output -match 'certificate is stale' -and $Stale.Output -match 'LF only') 'Mixed-EOL story edit did not invalidate release hash and line-ending policy.'
    }

    Invoke-Test 'release issuer refuses bytes changed after review' {
        $Root = New-FixtureRepository 'review-hash-binding'
        $Directory = Set-CompleteStory $Root 'reviewed-story' 'Reviewed Story'
        $Final = Get-Content -LiteralPath (Join-Path $Directory '05-story.md') -Raw
        Write-Utf8File (Join-Path $Directory '05-story.md') ($Final + "`na harmless byte change after the recorded review.`n")
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'reviewed-story', '-ProjectRoot', $Root)
        Assert-True (
            $Issued.ExitCode -ne 0 -and
            $Issued.Output -match 'Release handoff chain failed validation' -and
            $Issued.Output -match '05-story\.md' -and
            $Issued.Output -match 'handoff output'
        ) "Issuer certified bytes that changed after review. Output:`n$($Issued.Output)"
    }

    Invoke-Test 'integrity and Pages share the UTC release timestamp contract' {
        $Root = New-FixtureRepository 'release-utc-contract'
        $null = Set-CompleteStory $Root 'utc-story' 'UTC Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'utc-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'UTC release issuance'
        $ReleasePath = Join-Path $Root 'stories/utc-story/release.json'
        $ReleaseRaw = Get-Content -LiteralPath $ReleasePath -Raw
        $ReleaseDocument = [Text.Json.JsonDocument]::Parse($ReleaseRaw)
        $CertifiedAtText = $ReleaseDocument.RootElement.GetProperty('certifiedAt').GetString()
        $NameCheckedAtText = $ReleaseDocument.RootElement.GetProperty('nameCheck').GetProperty('checkedAt').GetString()
        $ReleaseDocument.Dispose()
        Assert-True ([DateTimeOffset]::Parse($CertifiedAtText).Offset -eq [TimeSpan]::Zero) 'Release certifiedAt is not UTC.'
        Assert-True ([DateTimeOffset]::Parse($NameCheckedAtText).Offset -eq [TimeSpan]::Zero) 'Release nameCheck.checkedAt is not UTC.'
        $Release = $ReleaseRaw | ConvertFrom-Json
        $Release.nameCheck.checkedAt = '2026-08-01T12:00:00-04:00'
        Write-Utf8File $ReleasePath ($Release | ConvertTo-Json -Depth 8)
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-Story', 'utc-story', '-ProjectRoot', $Root)
        Assert-True ($Invalid.ExitCode -ne 0 -and $Invalid.Output -match 'nameCheck.checkedAt must be an ISO-8601 UTC timestamp') 'Integrity accepted a non-UTC release receipt that the Pages build rejects.'
    }

    Invoke-Test 'final frontmatter rejects mutable lifecycle fields' {
        $Root = New-FixtureRepository 'immutable-frontmatter'
        $Directory = Set-CompleteStory $Root 'immutable-story' 'Immutable Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'immutable-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'immutable-frontmatter release issuance'
        $StoryPath = Join-Path $Directory '05-story.md'
        $Content = Get-Content -LiteralPath $StoryPath -Raw
        $Content = $Content.Replace('created: 2026-08-01', "status: candidate`ncreated: 2026-08-01")
        Write-Utf8File $StoryPath $Content
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-Story', 'immutable-story', '-ProjectRoot', $Root)
        Assert-True ($Invalid.ExitCode -ne 0 -and $Invalid.Output -match "frontmatter contains mutable or unknown field 'status'") 'Integrity accepted lifecycle state inside reviewed story frontmatter.'
    }

    Invoke-Test 'repository validation rejects index and directory drift' {
        $Root = New-FixtureRepository 'index-drift'
        $null = Set-CompleteStory $Root 'indexed-story' 'Indexed Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'indexed-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'index fixture release issuance'
        Write-Index $Root @(
            '| `indexed-story` | *Indexed Story* | candidate | no | accepted | yes | — | Fixture. |',
            '| `orphan-story` | *Orphan Story* | in-progress | no | pending | no | — | Drift. |'
        )
        $Result = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match "row 'orphan-story'.*no story directory") 'Index-only story was not rejected.'
    }

    Invoke-Test 'neutral source archive enforces exact schemas and both current and reviewed digests' {
        $Root = New-FixtureRepository 'neutral-source-archive'
        $null = New-ScaffoldedStory $Root 'ordinary-story' 'Ordinary Story'
        Write-Registry $Root @('| Ordinary Person | `Ordinary Person` | `ordinary-story` | in-progress | unique | Fixture. |')
        Write-Index $Root @('| `ordinary-story` | *Ordinary Story* | in-progress | no | pending | no | — | Fixture. |')
        $DecisionPath = 'sources/decisions/2026-07-22-universe-grill.md'
        $RecordPath = Join-Path $Root 'sources/records/r1/record.md'
        Write-Utf8File $RecordPath "line one`nline two`n"
        $CurrentDigest = (Get-FileHash -LiteralPath $RecordPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $CrlfBytes = [Text.UTF8Encoding]::new($false).GetBytes("line one`r`nline two`r`n")
        $HistoricalDigest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($CrlfBytes)).ToLowerInvariant()
        $Manifest = [ordered]@{
            schemaVersion = 2; prepared = '2026-08-01'; authority = 'none'
            decisionRecord = $DecisionPath
            records = @([ordered]@{
                recordId = 'R1'; workTitle = 'Record One'; reviewedForm = 'Fixture source'
                path = 'sources/records/r1/record.md'; sha256 = $CurrentDigest
                reviewedSha256 = $HistoricalDigest
                authority = 'none'; historicalRevision = ('a' * 40)
                historicalBlobOid = ('b' * 40)
            })
            externalRecords = @([ordered]@{
                recordId = 'R2'; workTitle = 'External Record'; reviewedForm = 'Fixture source'
                logicalLocator = 'archive/external-record.md'; authority = 'none'
                verificationStatus = 'descriptive-only'; version = $null; sha256 = $null
                accessRequirements = 'Provide exact source bytes before reliance.'
            })
        }
        Write-Utf8File (Join-Path $Root 'sources/MANIFEST.json') (($Manifest | ConvertTo-Json -Depth 8) + "`n")
        $Valid = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-ExitCode $Valid 0 'neutral archive exact-schema validation'
        $Manifest.records[0].sha256 = ('0' * 64)
        Write-Utf8File (Join-Path $Root 'sources/MANIFEST.json') (($Manifest | ConvertTo-Json -Depth 8) + "`n")
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-True (
            $Invalid.ExitCode -ne 0 -and
            $Invalid.Output -match 'source manifest validator did not pass'
        ) 'Invalid neutral archive current-byte digest was not rejected.'

        $Manifest.records[0].sha256 = $CurrentDigest
        $Manifest.externalRecords[0]['intendedUse'] = 'classified input'
        Write-Utf8File (Join-Path $Root 'sources/MANIFEST.json') (($Manifest | ConvertTo-Json -Depth 8) + "`n")
        $Classified = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-True (
            $Classified.ExitCode -ne 0 -and
            $Classified.Output -match 'source manifest validator did not pass'
        ) 'Neutral external source record accepted a classification field.'
    }

    Invoke-Test 'canon promotion finalizer updates one exact story and preserves reviewed bytes' {
        $Root = New-FixtureRepository 'canon-promotion-success'
        $UniversePath = Join-Path $Root 'universe/sentinel.md'
        Write-Utf8File $UniversePath "# Sentinel`n`nUniverse bytes are outside primary finalization.`n"
        $UniverseBefore = [IO.File]::ReadAllBytes($UniversePath)
        $Directory = Set-CompleteStory $Root 'promotion-story' 'Promotion Story'
        $null = New-ScaffoldedStory $Root 'promotion-story-two' 'Promotion Story Two'
        Write-Registry $Root @(
            '| Ada Vale | `Ada Vale`; `Ada` | `promotion-story` | candidate | unique | Distinct fixture identity. |',
            '| Other Person | `Other Person` | `promotion-story-two` | in-progress | unique | Prefix-similar story must remain untouched. |'
        )
        $OtherIndexRow = '| `promotion-story-two` | *Promotion Story Two* | in-progress | no | pending | no | — | Unrelated fixture. |'
        Write-Index $Root @(
            '| `promotion-story` | *Promotion Story* | candidate | no | accepted | yes | — | Promotion fixture. |',
            $OtherIndexRow
        )
        $Issued = Invoke-ExternalScript $ReleaseScript @(
            '-Story', 'promotion-story', '-ProjectRoot', $Root
        )
        Assert-ExitCode $Issued 0 'candidate release issuance for promotion'
        Set-ReadyPromotionFixture $Root 'promotion-story' '2026-08-02'
        $ReleasePath = Join-Path $Directory 'release.json'
        $InitialReleaseBytes = [IO.File]::ReadAllBytes($ReleasePath)
        $InitialRelease = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json
        $StoryPath = Join-Path $Directory '05-story.md'
        $DeltaPath = Join-Path $Directory '06-canon-delta.md'
        $StoryBefore = [IO.File]::ReadAllBytes($StoryPath)
        $DeltaBefore = [IO.File]::ReadAllBytes($DeltaPath)
        $StoryHashBefore = (Get-FileHash -LiteralPath $StoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $DeltaHashBefore = (Get-FileHash -LiteralPath $DeltaPath -Algorithm SHA256).Hash.ToLowerInvariant()

        $Promoted = Invoke-ExternalScript $PromotionScript @(
            '-Story', 'promotion-story', '-PromotionDate', '2026-08-02',
            '-ProjectRoot', $Root
        )
        Assert-ExitCode $Promoted 0 'canon promotion finalization'
        Assert-True (
            $Promoted.Output -match 'Reviewed artifacts unchanged' -and
            $Promoted.Output -match 'result: PROMOTED'
        ) 'Promotion did not report its artifact immutability proof and promoted result.'

        $Metadata = Get-Content -LiteralPath (Join-Path $Directory 'story.json') -Raw | ConvertFrom-Json
        Assert-True (
            $Metadata.stage -eq 'final' -and $Metadata.status -eq 'final' -and
            $Metadata.canon -eq $true -and $Metadata.userDisposition -eq 'accepted' -and
            $Metadata.publish -eq $true -and $Metadata.promotionDate -eq '2026-08-02'
        ) 'Promoted story metadata is not the required final state or publish was not preserved.'
        $Readme = Get-Content -LiteralPath (Join-Path $Directory 'README.md') -Raw
        Assert-True (
            $Readme -match '(?m)^- Current stage: final$' -and
            $Readme -match '(?m)^- Status: final$' -and
            $Readme -match '(?m)^- Canon: yes$' -and
            $Readme -match '(?m)^- User disposition: accepted$' -and
            $Readme -match '(?m)^- Publish: yes$' -and
            $Readme -match '(?m)^- Promotion date: 2026-08-02$' -and
            $Readme -match '(?m)^- \[x\] Canon promotion explicitly approved \(optional\)$'
        ) 'Promoted README lifecycle or checklist is incomplete.'

        $Index = Get-Content -LiteralPath (Join-Path $Root 'stories/INDEX.md') -Raw
        Assert-True ($Index.Contains(
            '| `promotion-story` | *Promotion Story* | final | yes | accepted | yes | 2026-08-02 | Promotion fixture. |',
            [StringComparison]::Ordinal
        )) 'Exact promotion-story index row was not finalized.'
        Assert-True ($Index.Contains($OtherIndexRow, [StringComparison]::Ordinal)) 'Prefix-similar index row changed.'
        $Names = Get-Content -LiteralPath (Join-Path $Root 'stories/NAMES.md') -Raw
        Assert-True ($Names.Contains(
            '| Ada Vale | `Ada Vale`; `Ada` | `promotion-story` | canon | unique | Distinct fixture identity. |',
            [StringComparison]::Ordinal
        )) 'Exact story registry row was not promoted to canon.'
        Assert-True ($Names.Contains(
            '| Other Person | `Other Person` | `promotion-story-two` | in-progress | unique | Prefix-similar story must remain untouched. |',
            [StringComparison]::Ordinal
        )) 'Prefix-similar registry row changed.'

        Assert-FileBytesEqual $StoryBefore $StoryPath 'Promotion 05-story.md'
        Assert-FileBytesEqual $DeltaBefore $DeltaPath 'Promotion 06-canon-delta.md'
        Assert-FileBytesEqual $UniverseBefore $UniversePath 'Promotion universe sentinel'
        $FinalReleaseBytes = [IO.File]::ReadAllBytes($ReleasePath)
        Assert-True (
            [Convert]::ToBase64String($InitialReleaseBytes) -cne
                [Convert]::ToBase64String($FinalReleaseBytes)
        ) 'Promotion did not reissue release.json.'
        $FinalRelease = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json
        Assert-True (
            $FinalRelease.certified -eq $true -and
            $FinalRelease.artifacts.story.sha256 -ceq $StoryHashBefore -and
            $FinalRelease.artifacts.canonDelta.sha256 -ceq $DeltaHashBefore -and
            $FinalRelease.nameCheck.scopedRegistrySha256 -ceq
                $InitialRelease.nameCheck.scopedRegistrySha256
        ) 'Reissued release does not preserve unchanged artifacts and stable reservation identity.'

        foreach ($Path in @(
            (Join-Path $Directory 'story.json'), $ReleasePath,
            (Join-Path $Directory 'README.md'),
            (Join-Path $Root 'stories/INDEX.md'),
            (Join-Path $Root 'stories/NAMES.md')
        )) {
            $Bytes = [IO.File]::ReadAllBytes($Path)
            Assert-True (13 -notin $Bytes) "$Path was not written with LF-only line endings."
            Assert-True (-not ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xef -and
                $Bytes[1] -eq 0xbb -and $Bytes[2] -eq 0xbf)) "$Path contains a UTF-8 BOM."
        }
    }

    Invoke-Test 'canon promotion finalizer rolls every production record back after post-write failure' {
        $Root = New-FixtureRepository 'canon-promotion-rollback'
        $Directory = Set-CompleteStory $Root 'rollback-story' 'Rollback Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @(
            '-Story', 'rollback-story', '-ProjectRoot', $Root
        )
        Assert-ExitCode $Issued 0 'rollback candidate release issuance'
        Set-ReadyPromotionFixture $Root 'rollback-story' '2026-08-02'

        # Source verification is repository-scoped, so this reaches the final
        # repository gate without invalidating the story/authority preflight.
        Write-Utf8File (Join-Path $Root 'sources/MANIFEST.json') "{}`n"
        $ProductionPaths = @(
            (Join-Path $Directory 'story.json'),
            (Join-Path $Directory 'release.json'),
            (Join-Path $Directory 'README.md'),
            (Join-Path $Directory 'promotion.json'),
            (Join-Path $Directory 'authority.json'),
            (Join-Path $Root 'stories/INDEX.md'),
            (Join-Path $Root 'stories/NAMES.md')
        )
        $Snapshots = @($ProductionPaths | ForEach-Object {
            [pscustomobject]@{ Path = $_; Bytes = [IO.File]::ReadAllBytes($_) }
        })
        $StoryPath = Join-Path $Directory '05-story.md'
        $DeltaPath = Join-Path $Directory '06-canon-delta.md'
        $StoryBefore = [IO.File]::ReadAllBytes($StoryPath)
        $DeltaBefore = [IO.File]::ReadAllBytes($DeltaPath)

        $Failed = Invoke-ExternalScript $PromotionScript @(
            '-Story', 'rollback-story', '-PromotionDate', '2026-08-02',
            '-ProjectRoot', $Root
        )
        Assert-True ($Failed.ExitCode -ne 0) 'Repository-only post-write defect did not fail promotion.'
        Assert-True (
            $Failed.Output -match 'repository integrity validation failed' -and
            $Failed.Output -match 'restored byte-for-byte' -and
            $Failed.Output -match 'result: NO_CHANGES'
        ) 'Promotion failure did not reach the post-write repository gate and report rollback.'

        foreach ($Snapshot in $Snapshots) {
            Assert-FileBytesEqual $Snapshot.Bytes $Snapshot.Path "Rollback $($Snapshot.Path)"
        }
        Assert-FileBytesEqual $StoryBefore $StoryPath 'Rollback 05-story.md'
        Assert-FileBytesEqual $DeltaBefore $DeltaPath 'Rollback 06-canon-delta.md'
        $Metadata = Get-Content -LiteralPath (Join-Path $Directory 'story.json') -Raw | ConvertFrom-Json
        Assert-True (
            $Metadata.stage -eq 'candidate' -and $Metadata.status -eq 'candidate' -and
            $Metadata.canon -eq $false -and $null -eq $Metadata.promotionDate
        ) 'Rollback left story.json promoted.'
        $Temps = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter '*.tmp.*')
        Assert-True ($Temps.Count -eq 0) 'Promotion rollback left atomic-write temporary files.'
    }

    Invoke-Test 'state-combination rules reject unsafe lifecycle flags' {
        $Root = New-FixtureRepository 'state-combinations'
        $Directory = New-ScaffoldedStory $Root 'state-story' 'State Story'
        Write-Registry $Root @('| State Person | `State Person` | `state-story` | in-progress | unique | Fixture. |')
        Write-Index $Root @('| `state-story` | *State Story* | in-progress | no | pending | no | — | Fixture. |')
        $Valid = Invoke-ExternalScript $IntegrityScript @('-Story', 'state-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Valid 0 'safe in-progress state'
        Set-StoryJson $Directory 'state-story' 'State Story' 'in-progress' 'prompt' $true 'pending' $false $null
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-Story', 'state-story', '-ProjectRoot', $Root)
        Assert-True (
            $Invalid.ExitCode -ne 0 -and
            $Invalid.Output -match "lifecycle fields do not satisfy the central 'in-progress' state rule"
        ) 'Unsafe in-progress canon state was not rejected.'
    }
}
finally {
    if (Test-Path -LiteralPath $TestRoot -PathType Container) {
        Remove-Item -LiteralPath $TestRoot -Recurse -Force
    }
}

Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
