#Requires -Version 7.0

$ErrorActionPreference = 'Stop'
$RepositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$Validator = Join-Path $RepositoryRoot '.agents/skills/story-integrity/scripts/Test-StoryHandoffs.ps1'
$ContractSource = Join-Path $RepositoryRoot 'schemas/pipeline-contract.json'
$ScratchRoot = Join-Path ([IO.Path]::GetTempPath()) (
    'story-handoff-ledger-' + [guid]::NewGuid().ToString('N')
)
$script:Passed = 0
$script:Failed = 0

function Write-Utf8LfFile {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Text)
    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }
    $Normalized = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    [IO.File]::WriteAllText($Path, $Normalized, [Text.UTF8Encoding]::new($false))
}

function Get-Hash {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-TextHash {
    param([Parameter(Mandatory = $true)][string]$Text)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.UTF8Encoding]::new($false).GetBytes($Text)
    )).ToLowerInvariant()
}

function Get-EntryHash {
    param([Parameter(Mandatory = $true)][object]$Entry)
    $Payload = [ordered]@{}
    foreach ($Property in $Entry.PSObject.Properties) {
        if ($Property.Name -cne 'entrySha256') { $Payload[$Property.Name] = $Property.Value }
    }
    $Json = ($Payload | ConvertTo-Json -Depth 16 -Compress).
        Replace("`r`n", "`n").Replace("`r", "`n")
    return Get-TextHash $Json
}

function Write-Ledger {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][object]$Ledger)
    $Json = (($Ledger | ConvertTo-Json -Depth 16) + "`n").
        Replace("`r`n", "`n").Replace("`r", "`n")
    Write-Utf8LfFile $Path $Json
}

function Write-StoryMetadata {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Stage,
        [string]$Status = 'in-progress'
    )
    $Terminal = $Status -eq 'candidate'
    $Metadata = [ordered]@{
        schemaVersion = 1
        slug = $Slug
        title = 'Handoff ledger fixture'
        created = '2026-08-02'
        stage = if ($Terminal) { 'candidate' } else { $Stage }
        status = $Status
        canon = $false
        userDisposition = 'pending'
        publish = $false
        promotionDate = $null
    }
    Write-Utf8LfFile $Path ((($Metadata | ConvertTo-Json -Depth 5) + "`n"))
}

function Expand-FixturePath {
    param([Parameter(Mandatory = $true)][string]$Template, [Parameter(Mandatory = $true)][string]$Slug)
    return $Template.Replace('{story}', $Slug)
}

function New-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Mode,
        [ValidateSet('READY', 'HANDOFF_ERROR', 'USER_RULING_REQUIRED', 'NAME_REGISTRATION_REQUIRED')]
        [string]$Status = 'READY'
    )
    return [pscustomobject]@{ mode = $Mode; status = $Status }
}

function New-LedgerFixture {
    param(
        [Parameter(Mandatory = $true)][string]$Tag,
        [Parameter(Mandatory = $true)][object[]]$Steps
    )
    $Root = Join-Path $ScratchRoot $Tag
    $Slug = 'handoff-fixture'
    $Prefix = "stories/$Slug"
    $StoryDirectory = Join-Path $Root $Prefix
    New-Item -ItemType Directory -Path (Join-Path $Root 'schemas') -Force | Out-Null
    New-Item -ItemType Directory -Path $StoryDirectory -Force | Out-Null
    [IO.File]::Copy($ContractSource, (Join-Path $Root 'schemas/pipeline-contract.json'), $true)
    $Contract = Get-Content -LiteralPath $ContractSource -Raw | ConvertFrom-Json
    $LedgerPath = Join-Path $StoryDirectory 'handoffs.json'
    $StoryPath = Join-Path $StoryDirectory 'story.json'

    $ArtifactPaths = @(
        'stories/NAMES.md', "$Prefix/00-prompt.md", "$Prefix/01-canon-brief.md",
        "$Prefix/02-story-plan.md", "$Prefix/03-draft.md", "$Prefix/04-review.md",
        "$Prefix/05-story.md", "$Prefix/06-canon-delta.md", "$Prefix/authority.json"
    )
    foreach ($Relative in $ArtifactPaths) {
        Write-Utf8LfFile (Join-Path $Root $Relative) "initial bytes for $Relative`n"
    }
    Write-StoryMetadata $StoryPath $Slug 'prompt'

    $Ledger = [ordered]@{
        schemaVersion = [int64]$Contract.handoffLedger.schemaVersion
        storySlug = $Slug
        chainHead = $null
        entries = [Collections.Generic.List[object]]::new()
    }
    Write-Ledger $LedgerPath $Ledger

    $Sequence = 0
    foreach ($Step in $Steps) {
        $Sequence++
        $Mode = [string]$Step.mode
        $Status = [string]$Step.status
        $ModeContract = $Contract.handoffLedger.modeContracts.$Mode
        if ($null -eq $ModeContract) { throw "Fixture requested unknown mode '$Mode'." }
        $Stage = [string]@($ModeContract.allowedStages)[0]
        Write-StoryMetadata $StoryPath $Slug $Stage

        # The on-disk ledger at this point is the exact prefix bound by this entry.
        $Inputs = @($ModeContract.requiredInputs | ForEach-Object {
            $Relative = Expand-FixturePath ([string]$_) $Slug
            [pscustomobject][ordered]@{
                path = $Relative
                sha256 = Get-Hash (Join-Path $Root $Relative)
            }
        })

        $PersistOutput = $Status -ceq 'READY' -or
            ($Status -ceq 'USER_RULING_REQUIRED' -and $Mode -in @('REVIEW_DRAFT', 'REVIEW_FINAL')) -or
            ($Status -ceq 'NAME_REGISTRATION_REQUIRED' -and $Mode -in @('CREATE_PLAN', 'REVISE_PLAN'))
        $PriorReviewContent = if ($PersistOutput -and $Mode -in @('REVIEW_DRAFT', 'REVIEW_FINAL')) {
            Get-Content -LiteralPath (Join-Path $StoryDirectory '04-review.md') -Raw
        }
        else { $null }
        $Outputs = @()
        if ($PersistOutput) {
            $Outputs = @($ModeContract.allowedOutputs | ForEach-Object {
                $Relative = Expand-FixturePath ([string]$_) $Slug
                $Full = Join-Path $Root $Relative
                $Before = Get-Hash $Full
                Write-Utf8LfFile $Full "entry $Sequence $Mode $Status output for $Relative`n"
                [pscustomobject][ordered]@{
                    path = $Relative
                    beforeSha256 = $Before
                    afterSha256 = Get-Hash $Full
                }
            })
        }
        $InputMap = @{}; foreach ($Input in $Inputs) { $InputMap[[string]$Input.path] = $Input }
        $OutputMap = @{}; foreach ($Output in $Outputs) { $OutputMap[[string]$Output.path] = $Output }
        $ResolutionOwner = if ($Status -ceq 'USER_RULING_REQUIRED') {
            'user'
        }
        elseif ($Status -ceq 'NAME_REGISTRATION_REQUIRED') { 'coordinator' }
        else { [string]$ModeContract.persister }
        $ErrorCode = if ($Status -ceq 'HANDOFF_ERROR') { 'E_FIXTURE' } else { 'none' }
        $ResolutionQuestion = if ($Status -ceq 'USER_RULING_REQUIRED') {
            'Choose the fixture ruling.'
        }
        else { 'none' }
        $HandoffInput = $InputMap["$Prefix/handoffs.json"]
        $ReportLines = [Collections.Generic.List[string]]::new()
        foreach ($Line in @(
            'HANDOFF_REPORT', "story: $Slug", "mode: $Mode", "status: $Status",
            "resolutionOwner: $ResolutionOwner", "errorCode: $ErrorCode",
            "resolutionQuestion: $ResolutionQuestion", "handoffLedger: $Prefix/handoffs.json",
            "handoffLedgerSha256: $($HandoffInput.sha256)"
        )) { $ReportLines.Add($Line) }
        if ($Mode -in @('RESEARCH_CANON', 'REVIEW_DRAFT', 'REVIEW_FINAL')) {
            $ReportLines.Add("handoffLedgerChainHead: $(if ($null -eq $Ledger.chainHead) { 'none' } else { $Ledger.chainHead })")
        }

        switch -Regex ($Mode) {
            '^RESEARCH_CANON$' {
                $ReportLines.Add("sourcePromptSha256: $($InputMap["$Prefix/00-prompt.md"].sha256)")
                $ReportLines.Add("authorityManifestSha256: $($InputMap["$Prefix/authority.json"].sha256)")
            }
            '^(CREATE|REVISE)_PLAN$' {
                $PlanRelative = "$Prefix/02-story-plan.md"
                $PlanOutput = $OutputMap[$PlanRelative]
                $BeforePlan = if ($null -ne $PlanOutput) { $PlanOutput.beforeSha256 } else {
                    Get-Hash (Join-Path $Root $PlanRelative)
                }
                $ReportLines.Add("inputPromptSha256: $($InputMap["$Prefix/00-prompt.md"].sha256)")
                $ReportLines.Add("inputCanonBriefSha256: $($InputMap["$Prefix/01-canon-brief.md"].sha256)")
                $ReportLines.Add("beforePlanSha256: $BeforePlan")
                if ($Mode -ceq 'CREATE_PLAN') { $ReportLines.Add("planScaffoldSha256: $BeforePlan") }
                $ReportLines.Add("newPlanSha256: $(Get-Hash (Join-Path $Root $PlanRelative))")
                if ($Mode -ceq 'REVISE_PLAN') { $ReportLines.Add("repairAuthorization: finding-plan-$Sequence") }
            }
            '^(CREATE|REVISE)_DRAFT$' {
                $DraftRelative = "$Prefix/03-draft.md"
                $DraftOutput = $OutputMap[$DraftRelative]
                $BeforeDraft = if ($null -ne $DraftOutput) { $DraftOutput.beforeSha256 } else {
                    Get-Hash (Join-Path $Root $DraftRelative)
                }
                $ReportLines.Add("beforeDraftSha256: $BeforeDraft")
                if ($Mode -ceq 'CREATE_DRAFT') { $ReportLines.Add("draftScaffoldSha256: $BeforeDraft") }
                $ReportLines.Add("newDraftSha256: $(Get-Hash (Join-Path $Root $DraftRelative))")
                if ($Mode -ceq 'REVISE_DRAFT') { $ReportLines.Add("- findingId: draft-finding-$Sequence") }
            }
            '^(CREATE|REVISE)_FINAL$' {
                $StoryRelative = "$Prefix/05-story.md"
                $DeltaRelative = "$Prefix/06-canon-delta.md"
                $StoryOutput = $OutputMap[$StoryRelative]
                $DeltaOutput = $OutputMap[$DeltaRelative]
                $BeforeStory = if ($null -ne $StoryOutput) { $StoryOutput.beforeSha256 } else {
                    Get-Hash (Join-Path $Root $StoryRelative)
                }
                $BeforeDelta = if ($null -ne $DeltaOutput) { $DeltaOutput.beforeSha256 } else {
                    Get-Hash (Join-Path $Root $DeltaRelative)
                }
                $ReportLines.Add("inputPlanSha256: $($InputMap["$Prefix/02-story-plan.md"].sha256)")
                $ReportLines.Add("inputDraftSha256: $($InputMap["$Prefix/03-draft.md"].sha256)")
                $ReportLines.Add("beforeStorySha256: $BeforeStory")
                $ReportLines.Add("beforeCanonDeltaSha256: $BeforeDelta")
                if ($Mode -ceq 'CREATE_FINAL') {
                    $ReportLines.Add("storyScaffoldSha256: $BeforeStory")
                    $ReportLines.Add("canonDeltaScaffoldSha256: $BeforeDelta")
                }
                $ReportLines.Add("newStorySha256: $(Get-Hash (Join-Path $Root $StoryRelative))")
                $ReportLines.Add("newCanonDeltaSha256: $(Get-Hash (Join-Path $Root $DeltaRelative))")
                if ($Mode -ceq 'REVISE_FINAL') { $ReportLines.Add("- findingId: final-finding-$Sequence") }
            }
            '^REVIEW_(DRAFT|FINAL)$' {
                $ArtifactRelative = if ($Mode -ceq 'REVIEW_DRAFT') {
                    "$Prefix/03-draft.md"
                }
                else { "$Prefix/05-story.md" }
                $ReportLines.Add("artifactSha256: $($InputMap[$ArtifactRelative].sha256)")
                $ReportLines.Add("canonBriefSha256: $($InputMap["$Prefix/01-canon-brief.md"].sha256)")
                $ReportLines.Add("planSha256: $($InputMap["$Prefix/02-story-plan.md"].sha256)")
                $ReportLines.Add("authorityManifestSha256: $($InputMap["$Prefix/authority.json"].sha256)")
                if ($Mode -ceq 'REVIEW_FINAL') {
                    $ReportLines.Add("canonDeltaSha256: $($InputMap["$Prefix/06-canon-delta.md"].sha256)")
                }
            }
        }
        if ($Mode -ceq 'RESEARCH_CANON' -and $Status -ceq 'READY') {
            $BriefBody = Get-Content -LiteralPath (Join-Path $Root "$Prefix/01-canon-brief.md") -Raw
            $Report = ($ReportLines -join "`n") + "`nBEGIN_FILE_CONTENT`n" +
                $BriefBody + "END_FILE_CONTENT`n"
        }
        else { $Report = ($ReportLines -join "`n") + "`n" }

        if ($PersistOutput -and $Mode -in @('REVIEW_DRAFT', 'REVIEW_FINAL')) {
            $ReviewRelative = "$Prefix/04-review.md"
            $ReviewPath = Join-Path $Root $ReviewRelative
            $ReviewText = $PriorReviewContent.TrimEnd("`r", "`n") + "`n`n" + $Report
            Write-Utf8LfFile $ReviewPath $ReviewText
            $OutputMap[$ReviewRelative].afterSha256 = Get-Hash $ReviewPath
        }
        $Entry = [pscustomobject][ordered]@{
            sequence = $Sequence
            story = $Slug
            actor = [string]$ModeContract.actor
            mode = $Mode
            status = $Status
            recordedAt = ('2026-08-02T12:{0:D2}:00.0000000+00:00' -f $Sequence)
            guardId = ('{0:x32}' -f $Sequence)
            persister = [string]$ModeContract.persister
            report = $Report
            reportSha256 = Get-TextHash $Report
            inputs = @($Inputs)
            outputs = @($Outputs)
            previousEntrySha256 = $Ledger.chainHead
            entrySha256 = $null
        }
        $Entry.entrySha256 = Get-EntryHash $Entry
        $Ledger.entries.Add($Entry)
        $Ledger.chainHead = $Entry.entrySha256
        Write-Ledger $LedgerPath $Ledger
    }

    # Candidate projection occurs after all specialist snapshots and is not a handoff input.
    Write-StoryMetadata $StoryPath $Slug 'candidate' 'candidate'
    return [pscustomobject]@{
        Root = $Root
        Slug = $Slug
        Directory = $StoryDirectory
        LedgerPath = $LedgerPath
    }
}

function Invoke-Validator {
    param([Parameter(Mandatory = $true)][object]$Fixture, [switch]$Release)
    $Arguments = @(
        '-NoProfile', '-File', $Validator,
        '-Story', $Fixture.Slug, '-ProjectRoot', $Fixture.Root,
        '-OutputFormat', 'Json'
    )
    if ($Release) { $Arguments += '-RequireReleaseChain' }
    $Output = (& pwsh @Arguments 2>&1 | Out-String).Trim()
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $Output }
}

function Read-Ledger {
    param([Parameter(Mandatory = $true)][object]$Fixture)
    $Parameters = @{}
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        $Parameters.DateKind = 'String'
    }
    return Get-Content -LiteralPath $Fixture.LedgerPath -Raw | ConvertFrom-Json @Parameters
}

function Write-MutatedLedger {
    param([Parameter(Mandatory = $true)][object]$Fixture, [Parameter(Mandatory = $true)][object]$Ledger)
    Write-Ledger $Fixture.LedgerPath $Ledger
}

function Repair-LastEntryHash {
    param([Parameter(Mandatory = $true)][object]$Ledger)
    $Last = @($Ledger.entries)[-1]
    $Last.entrySha256 = Get-EntryHash $Last
    $Ledger.chainHead = $Last.entrySha256
}

function Assert-True {
    param([bool]$Condition, [Parameter(Mandatory = $true)][string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Rejected {
    param(
        [Parameter(Mandatory = $true)][object]$Fixture,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [switch]$Release
    )
    $Result = Invoke-Validator $Fixture -Release:$Release
    Assert-True ($Result.ExitCode -ne 0) "Validator unexpectedly accepted fixture. Output: $($Result.Output)"
    Assert-True ($Result.Output -match $Pattern) "Rejection did not match '$Pattern'. Output: $($Result.Output)"
}

function Invoke-Case {
    param([Parameter(Mandatory = $true)][string]$Name, [Parameter(Mandatory = $true)][scriptblock]$Body)
    try {
        & $Body
        $script:Passed++
        Write-Host "PASS $Name"
    }
    catch {
        $script:Failed++
        Write-Host "FAIL $Name`n  $($_.Exception.Message)" -ForegroundColor Red
    }
}

$StraightChain = @(
    (New-Step RESEARCH_CANON), (New-Step CREATE_PLAN),
    (New-Step CREATE_DRAFT), (New-Step REVIEW_DRAFT),
    (New-Step CREATE_FINAL), (New-Step REVIEW_FINAL)
)

New-Item -ItemType Directory -Path $ScratchRoot -Force | Out-Null
try {
    Invoke-Case 'accepts a strict v2 release chain' {
        $Fixture = New-LedgerFixture 'valid' $StraightChain
        $Result = Invoke-Validator $Fixture -Release
        Assert-True ($Result.ExitCode -eq 0) "Valid chain failed: $($Result.Output)"
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.releaseReady -eq $true -and @($Receipt.unresolved).Count -eq 0) `
            'Valid receipt is not release-ready.'
    }

    Invoke-Case 'accepts legal draft and final revision loops' {
        $Fixture = New-LedgerFixture 'revision-loops' @(
            (New-Step RESEARCH_CANON), (New-Step CREATE_PLAN),
            (New-Step CREATE_DRAFT), (New-Step REVIEW_DRAFT),
            (New-Step REVISE_DRAFT), (New-Step REVIEW_DRAFT),
            (New-Step CREATE_FINAL), (New-Step REVIEW_FINAL),
            (New-Step REVISE_FINAL), (New-Step REVIEW_FINAL)
        )
        $Result = Invoke-Validator $Fixture -Release
        Assert-True ($Result.ExitCode -eq 0) "Legal revision chain failed: $($Result.Output)"
    }

    Invoke-Case 'rejects a mutated report' {
        $Fixture = New-LedgerFixture 'mutated-report' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].report = $Ledger.entries[-1].report.Replace(
            'resolutionOwner: coordinator', 'resolutionOwner: forged'
        )
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'Invalid handoff entry digest|report digest mismatch' -Release
    }

    foreach ($Mutation in @(
        [pscustomobject]@{ Name = 'unknown actor'; Field = 'actor'; Value = 'pipeline_migration'; Pattern = 'requires actor' },
        [pscustomobject]@{ Name = 'wrong persister'; Field = 'persister'; Value = 'continuity_critic'; Pattern = 'requires persister' },
        [pscustomobject]@{ Name = 'unknown mode'; Field = 'mode'; Value = 'REVIEW_UNKNOWN'; Pattern = 'Unsupported handoff mode' },
        [pscustomobject]@{ Name = 'wrong-case status'; Field = 'status'; Value = 'ready'; Pattern = 'is not permitted' }
    )) {
        Invoke-Case "rejects $($Mutation.Name)" {
            $Fixture = New-LedgerFixture ('identity-' + $Mutation.Field) $StraightChain
            $Ledger = Read-Ledger $Fixture
            $Ledger.entries[-1].$($Mutation.Field) = $Mutation.Value
            Repair-LastEntryHash $Ledger
            Write-MutatedLedger $Fixture $Ledger
            Assert-Rejected $Fixture $Mutation.Pattern -Release
        }
    }

    Invoke-Case 'rejects schema-v1 ambiguity' {
        $Fixture = New-LedgerFixture 'old-schema' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.schemaVersion = 1
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'identity/schema mismatch' -Release
    }

    Invoke-Case 'rejects a forged migration marker without explicit authority' {
        $Fixture = New-LedgerFixture 'migration-spoof' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].guardId = "pipeline-migration-$($Fixture.Slug)-6"
        $Ledger.entries[-1].actor = 'pipeline_migration'
        $Ledger.entries[-1].persister = 'pipeline_migration'
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'requires actor|Invalid or duplicate guardId' -Release
    }

    Invoke-Case 'rejects a path escape' {
        $Fixture = New-LedgerFixture 'path-escape' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].outputs[0].path = "stories/$($Fixture.Slug)/../escape.md"
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'unsafe or incomplete path segment|unauthorized output' -Release
    }

    Invoke-Case 'rejects a noncanonical incomplete path' {
        $Fixture = New-LedgerFixture 'path-incomplete' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].inputs[0].path = "stories/$($Fixture.Slug)//00-prompt.md"
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'unsafe or incomplete path segment' -Release
    }

    Invoke-Case 'rejects a missing required input' {
        $Fixture = New-LedgerFixture 'missing-input' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].inputs = @($Ledger.entries[-1].inputs | Where-Object {
            $_.path -cne "stories/$($Fixture.Slug)/story.json"
        })
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'inputs at entry 6 mismatch' -Release
    }

    Invoke-Case 'rejects current output-byte mismatch' {
        $Fixture = New-LedgerFixture 'output-current-mismatch' $StraightChain
        Write-Utf8LfFile (Join-Path $Fixture.Directory '04-review.md') "unlogged mutation`n"
        Assert-Rejected $Fixture 'exact critic payload|differs from its latest READY handoff output' -Release
    }

    Invoke-Case 'rejects output before/input mismatch' {
        $Fixture = New-LedgerFixture 'output-before-mismatch' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].outputs[0].beforeSha256 = ('0' * 64)
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'discontinuous beforeSha256|does not bind its input bytes' -Release
    }

    Invoke-Case 'rejects report handoff-prehash mismatch' {
        $Fixture = New-LedgerFixture 'report-prehash-mismatch' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Last = $Ledger.entries[-1]
        $LedgerInput = $Last.inputs | Where-Object {
            $_.path -ceq "stories/$($Fixture.Slug)/handoffs.json"
        }
        $Last.report = $Last.report.Replace(
            "handoffLedgerSha256: $($LedgerInput.sha256)",
            ('handoffLedgerSha256: ' + ('0' * 64))
        )
        $Last.reportSha256 = Get-TextHash $Last.report
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'handoffLedgerSha256.*does not bind the ledger receipt' -Release
    }

    Invoke-Case 'rejects READY research body/output mismatch' {
        $Fixture = New-LedgerFixture 'research-body-mismatch' @((New-Step RESEARCH_CANON))
        $Ledger = Read-Ledger $Fixture
        $Last = $Ledger.entries[-1]
        $Last.report = $Last.report.Replace('entry 1 RESEARCH_CANON', 'forged research body')
        $Last.reportSha256 = Get-TextHash $Last.report
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'body does not equal the persisted brief output'
    }

    Invoke-Case 'rejects final-editor report/output mismatch' {
        $Fixture = New-LedgerFixture 'editor-report-mismatch' @($StraightChain[0..4])
        $Ledger = Read-Ledger $Fixture
        $Last = $Ledger.entries[-1]
        $StoryOutput = $Last.outputs | Where-Object {
            $_.path -ceq "stories/$($Fixture.Slug)/05-story.md"
        }
        $Last.report = $Last.report.Replace(
            "newStorySha256: $($StoryOutput.afterSha256)",
            ('newStorySha256: ' + ('0' * 64))
        )
        $Last.reportSha256 = Get-TextHash $Last.report
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture "newStorySha256.*does not bind the ledger receipt"
    }

    Invoke-Case 'rejects critic report/artifact mismatch' {
        $Fixture = New-LedgerFixture 'critic-report-mismatch' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Last = $Ledger.entries[-1]
        $ArtifactInput = $Last.inputs | Where-Object {
            $_.path -ceq "stories/$($Fixture.Slug)/05-story.md"
        }
        $Last.report = $Last.report.Replace(
            "artifactSha256: $($ArtifactInput.sha256)",
            ('artifactSha256: ' + ('0' * 64))
        )
        $Last.reportSha256 = Get-TextHash $Last.report
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'artifactSha256.*does not bind the ledger receipt' -Release
    }

    foreach ($Status in @('HANDOFF_ERROR', 'USER_RULING_REQUIRED')) {
        Invoke-Case "default receipt preserves unresolved $Status but release rejects it" {
            $Fixture = New-LedgerFixture ('unresolved-' + $Status.ToLowerInvariant()) @(
                $StraightChain + (New-Step REVIEW_FINAL $Status)
            )
            $Default = Invoke-Validator $Fixture
            Assert-True ($Default.ExitCode -eq 0) "Structurally valid unresolved ledger failed: $($Default.Output)"
            $Receipt = $Default.Output | ConvertFrom-Json
            Assert-True ($Receipt.releaseReady -eq $false -and
                @($Receipt.unresolved).Count -eq 1 -and
                $Receipt.unresolved[0].status -ceq $Status) 'Unresolved receipt is incomplete.'
            Assert-Rejected $Fixture 'unresolved status requiring a later READY repair' -Release
        }
    }

    Invoke-Case 'same-family READY repairs an unresolved review block' {
        $Fixture = New-LedgerFixture 'resolved-block' @(
            $StraightChain +
            (New-Step REVIEW_FINAL USER_RULING_REQUIRED) +
            (New-Step REVIEW_FINAL READY)
        )
        $Result = Invoke-Validator $Fixture -Release
        Assert-True ($Result.ExitCode -eq 0) "Repaired block failed: $($Result.Output)"
    }

    Invoke-Case 'name registration plan repair does not alone clear the original family' {
        $Fixture = New-LedgerFixture 'name-plan-only' @(
            (New-Step RESEARCH_CANON), (New-Step CREATE_PLAN),
            (New-Step CREATE_DRAFT NAME_REGISTRATION_REQUIRED),
            (New-Step REVISE_PLAN)
        )
        $Default = Invoke-Validator $Fixture
        Assert-True ($Default.ExitCode -eq 0) "Name-routing prefix failed: $($Default.Output)"
        $Receipt = $Default.Output | ConvertFrom-Json
        Assert-True (@($Receipt.unresolved).Count -eq 1 -and
            $Receipt.unresolved[0].family -eq 2) 'Original name-blocked family was cleared early.'
        Assert-Rejected $Fixture 'unresolved status requiring a later READY repair' -Release
    }

    Invoke-Case 'name registration route closes only after original-family READY repair' {
        $Fixture = New-LedgerFixture 'name-full-repair' @(
            (New-Step RESEARCH_CANON), (New-Step CREATE_PLAN),
            (New-Step CREATE_DRAFT NAME_REGISTRATION_REQUIRED),
            (New-Step REVISE_PLAN), (New-Step CREATE_DRAFT),
            (New-Step REVIEW_DRAFT), (New-Step CREATE_FINAL), (New-Step REVIEW_FINAL)
        )
        $Result = Invoke-Validator $Fixture -Release
        Assert-True ($Result.ExitCode -eq 0) "Name repair chain failed: $($Result.Output)"
    }

    Invoke-Case 'rejects illegal causal family order' {
        $Fixture = New-LedgerFixture 'illegal-order' @(
            (New-Step RESEARCH_CANON), (New-Step CREATE_PLAN), (New-Step REVIEW_DRAFT)
        )
        Assert-Rejected $Fixture 'Illegal causal handoff order' -Release
    }

    Invoke-Case 'rejects REVISE before CREATE establishes the family' {
        $Fixture = New-LedgerFixture 'revise-first' @(
            (New-Step RESEARCH_CANON), (New-Step REVISE_PLAN)
        )
        Assert-Rejected $Fixture 'cannot revise before its family has established an output'
    }

    Invoke-Case 'rejects CREATE after a family output is established' {
        $Fixture = New-LedgerFixture 'create-twice' @(
            (New-Step RESEARCH_CANON), (New-Step CREATE_PLAN), (New-Step CREATE_PLAN)
        )
        Assert-Rejected $Fixture 'cannot recreate an established family output'
    }

    Invoke-Case 'rejects duplicate guardId' {
        $Fixture = New-LedgerFixture 'duplicate-guard' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].guardId = $Ledger.entries[0].guardId
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'duplicate guardId' -Release
    }

    Invoke-Case 'rejects chain-link tampering' {
        $Fixture = New-LedgerFixture 'chain-tamper' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].previousEntrySha256 = ('f' * 64)
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'Broken handoff hash chain' -Release
    }

    Invoke-Case 'rejects previous-ledger snapshot tampering' {
        $Fixture = New-LedgerFixture 'prefix-tamper' $StraightChain
        $Ledger = Read-Ledger $Fixture
        $Ledger.entries[-1].inputs | Where-Object {
            $_.path -ceq "stories/$($Fixture.Slug)/handoffs.json"
        } | ForEach-Object { $_.sha256 = ('e' * 64) }
        Repair-LastEntryHash $Ledger
        Write-MutatedLedger $Fixture $Ledger
        Assert-Rejected $Fixture 'does not bind the exact previous-ledger snapshot' -Release
    }
}
finally {
    if (Test-Path -LiteralPath $ScratchRoot -PathType Container) {
        Remove-Item -LiteralPath $ScratchRoot -Recurse -Force
    }
}

Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
