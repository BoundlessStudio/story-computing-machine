#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [Parameter(Mandatory = $true)]
    [string]$Actor,

    [Parameter(Mandatory = $true)]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string[]]$AllowedPath,

    [string[]]$InputPath = @(),

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

function Get-RawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
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

function Get-SafeRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ([string]::IsNullOrWhiteSpace($Value)) { throw "$Label path is empty." }
    $Full = [IO.Path]::GetFullPath((Join-Path $Root $Value))
    $RootPrefix = [IO.Path]::GetFullPath($Root) + [IO.Path]::DirectorySeparatorChar
    if (-not $Full.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label path escapes the project root: $Value"
    }
    $Cursor = if (Test-Path -LiteralPath $Full) { $Full } else { Split-Path -Parent $Full }
    while (-not [string]::IsNullOrWhiteSpace($Cursor) -and
        $Cursor.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        if ((Get-Item -LiteralPath $Cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "$Label path traverses a reparse point: $Value"
        }
        $Cursor = Split-Path -Parent $Cursor
    }
    return [IO.Path]::GetRelativePath($Root, $Full).Replace('\', '/')
}

function Expand-StoryPath {
    param(
        [Parameter(Mandatory = $true)][string]$Template,
        [Parameter(Mandatory = $true)][string]$StorySlug
    )
    return $Template.Replace('{story}', $StorySlug)
}

function Get-LedgerReportField {
    param([object]$Entry, [string]$Name, [switch]$AllowMissing)
    $Matches = @([regex]::Matches(
        [string]$Entry.report,
        '(?m)^' + [regex]::Escape($Name) + ':[ \t]*(?<value>[^\r\n]+)[ \t]*$'
    ))
    if ($Matches.Count -eq 0 -and $AllowMissing) { return $null }
    if ($Matches.Count -ne 1) {
        throw "Ledger entry $($Entry.sequence) must contain exactly one '${Name}:' report field."
    }
    return $Matches[0].Groups['value'].Value.Trim().Trim('`')
}

function Get-LatestReadyEntry {
    param([object[]]$Entries, [string[]]$Modes)
    $Matches = @($Entries | Where-Object {
        $_.status -ceq 'READY' -and $_.mode -cin $Modes
    })
    if ($Matches.Count -eq 0) { return $null }
    return $Matches[-1]
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
    throw "Story directory not found: $StoryDirectory"
}

$ContractPath = Join-Path $ProjectRoot 'schemas/pipeline-contract.json'
if (-not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) {
    throw "Pipeline contract not found: $ContractPath"
}
try {
    $Parameters = @{}
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        $Parameters.DateKind = 'String'
    }
    $Contract = Get-Content -LiteralPath $ContractPath -Raw | ConvertFrom-Json @Parameters
}
catch { throw "Pipeline contract is invalid: $($_.Exception.Message)" }
$ContractChecker = Join-Path $PSScriptRoot 'Test-PipelineContract.ps1'
if (-not (Test-Path -LiteralPath $ContractChecker -PathType Leaf)) {
    throw "Pipeline contract validator not found: $ContractChecker"
}
$ContractReceipt = & $ContractChecker -OutputFormat Json -ProjectRoot $ProjectRoot |
    ConvertFrom-Json @Parameters
if ($ContractReceipt.passed -ne $true) {
    throw 'Pipeline contract failed strict schema/semantic validation.'
}
$ModeProperty = @($Contract.handoffLedger.modeContracts.PSObject.Properties |
    Where-Object Name -CEQ $Mode)
if ($ModeProperty.Count -ne 1) { throw "Unsupported guarded handoff mode '$Mode'." }
$ModeContract = $ModeProperty[0].Value
if ($Actor -cne [string]$ModeContract.actor) {
    throw "Mode '$Mode' requires actor '$($ModeContract.actor)', not '$Actor'."
}

$StoryMetadataPath = Join-Path $StoryDirectory 'story.json'
if (-not (Test-Path -LiteralPath $StoryMetadataPath -PathType Leaf)) {
    throw "Story lifecycle record not found: $StoryMetadataPath"
}
try {
    $StoryMetadata = Get-Content -LiteralPath $StoryMetadataPath -Raw | ConvertFrom-Json @Parameters
}
catch { throw "Story lifecycle record is invalid: $($_.Exception.Message)" }
$MetadataProperties = @($StoryMetadata.PSObject.Properties.Name)
$MissingMetadata = @($Contract.story.fields | Where-Object { $_ -cnotin $MetadataProperties })
$ExtraMetadata = @($MetadataProperties | Where-Object { $_ -cnotin @($Contract.story.fields) })
if ($MissingMetadata.Count -gt 0 -or $ExtraMetadata.Count -gt 0 -or
    $StoryMetadata.schemaVersion -ne $Contract.story.schemaVersion -or $StoryMetadata.slug -cne $Story -or
    $StoryMetadata.status -cne 'in-progress' -or
    $StoryMetadata.stage -cnotin @($ModeContract.allowedStages) -or
    $StoryMetadata.canon -ne $false -or
    $StoryMetadata.userDisposition -cne 'pending' -or
    $StoryMetadata.publish -ne $false -or $null -ne $StoryMetadata.promotionDate) {
    throw "Mode '$Mode' is illegal for lifecycle state '$($StoryMetadata.status)/$($StoryMetadata.stage)'; reopen/project the story to an allowed in-progress state first."
}

$RawNormalizedAllowed = @($AllowedPath | ForEach-Object {
    Get-SafeRelativePath -Root $ProjectRoot -Value $_ -Label 'Allowed output'
})
if (@($RawNormalizedAllowed | Group-Object -CaseSensitive | Where-Object Count -gt 1).Count -gt 0) {
    throw 'Allowed output paths contain a duplicate.'
}
$NormalizedAllowed = @($RawNormalizedAllowed | Sort-Object)
if ($NormalizedAllowed.Count -eq 0) { throw 'At least one allowed output path is required.' }
$ExpectedAllowed = @($ModeContract.allowedOutputs | ForEach-Object {
    Expand-StoryPath -Template ([string]$_) -StorySlug $Story
} | Sort-Object -Unique)
$MissingAllowed = @($ExpectedAllowed | Where-Object { $_ -cnotin $NormalizedAllowed })
$ExtraAllowed = @($NormalizedAllowed | Where-Object { $_ -cnotin $ExpectedAllowed })
if ($MissingAllowed.Count -gt 0 -or $ExtraAllowed.Count -gt 0) {
    throw "Mode '$Mode' output allowlist mismatch; missing=[$($MissingAllowed -join ', ')], extra=[$($ExtraAllowed -join ', ')]."
}

$Inputs = @($InputPath | ForEach-Object {
    $Relative = Get-SafeRelativePath -Root $ProjectRoot -Value $_ -Label 'Handoff input'
    $Full = Join-Path $ProjectRoot $Relative
    if (-not (Test-Path -LiteralPath $Full -PathType Leaf)) {
        throw "Handoff input is missing: $_"
    }
    [ordered]@{
        path = $Relative
        sha256 = Get-RawSha256 $Full
    }
})
$InputPaths = @($Inputs | ForEach-Object { [string]$_.path })
if (@($InputPaths | Group-Object | Where-Object Count -gt 1).Count -gt 0) {
    throw 'Handoff inputs contain a duplicate path.'
}
$RequiredInputs = @($ModeContract.requiredInputs | ForEach-Object {
    Expand-StoryPath -Template ([string]$_) -StorySlug $Story
})
$MissingInputs = @($RequiredInputs | Where-Object { $_ -cnotin $InputPaths })
$ExtraInputs = @($InputPaths | Where-Object { $_ -cnotin $RequiredInputs })
if ($MissingInputs.Count -gt 0 -or $ExtraInputs.Count -gt 0) {
    throw "Mode '$Mode' input contract mismatch; missing=[$($MissingInputs -join ', ')], extra=[$($ExtraInputs -join ', ')]."
}

$LedgerInput = @($Inputs | Where-Object path -CEQ "stories/$Story/handoffs.json")
if ($LedgerInput.Count -ne 1) { throw 'The current handoff ledger must be bound exactly once.' }
try {
    $Ledger = Get-Content -LiteralPath (Join-Path $ProjectRoot $LedgerInput[0].path) -Raw |
        ConvertFrom-Json @Parameters
}
catch { throw "Current handoff ledger is invalid: $($_.Exception.Message)" }
$LedgerProperties = @($Ledger.PSObject.Properties.Name)
if (@('schemaVersion', 'storySlug', 'chainHead', 'entries' |
    Where-Object { $_ -cnotin $LedgerProperties }).Count -gt 0 -or
    @($LedgerProperties | Where-Object {
        $_ -cnotin @('schemaVersion', 'storySlug', 'chainHead', 'entries')
    }).Count -gt 0 -or $Ledger.schemaVersion -ne $Contract.handoffLedger.schemaVersion -or
    $Ledger.storySlug -cne $Story -or
    @($Ledger.entries).Count -ne ($(if ($null -eq $Ledger.chainHead) { 0 } else { @($Ledger.entries).Count }))) {
    throw 'Current handoff ledger identity/schema is invalid.'
}
$ExpectedHead = if (@($Ledger.entries).Count -eq 0) { $null } else {
    [string]@($Ledger.entries)[-1].entrySha256
}
if ($Ledger.chainHead -cne $ExpectedHead) {
    throw 'Current handoff ledger chainHead does not identify its final entry.'
}
$HandoffChecker = Join-Path $PSScriptRoot 'Test-StoryHandoffs.ps1'
if (-not (Test-Path -LiteralPath $HandoffChecker -PathType Leaf)) {
    throw "Handoff validator not found: $HandoffChecker"
}
$LedgerReceipt = & $HandoffChecker -Story $Story -OutputFormat Json `
    -ProjectRoot $ProjectRoot | ConvertFrom-Json @Parameters
if ($LedgerReceipt.passed -ne $true -or
    $LedgerReceipt.ledgerSha256 -cne [string]$LedgerInput[0].sha256) {
    throw 'Current handoff ledger failed strict structural preflight.'
}

$Entries = @($Ledger.entries)
$Tail = if ($Entries.Count -eq 0) { $null } else { $Entries[-1] }
if ($null -ne $Tail -and $Tail.status -cne 'READY') {
    $AllowedRecoveryModes = if ($Tail.status -ceq 'NAME_REGISTRATION_REQUIRED') {
        @('REVISE_PLAN')
    }
    else { @([string]$Tail.mode) }
    if ($Mode -cnotin $AllowedRecoveryModes) {
        throw "Unresolved $($Tail.status) in $($Tail.mode) permits only recovery mode(s): $($AllowedRecoveryModes -join ', ')."
    }
}

$LatestResearch = Get-LatestReadyEntry $Entries @('RESEARCH_CANON')
$LatestPlan = Get-LatestReadyEntry $Entries @('CREATE_PLAN', 'REVISE_PLAN')
$LatestDraft = Get-LatestReadyEntry $Entries @('CREATE_DRAFT', 'REVISE_DRAFT')
$LatestDraftReview = Get-LatestReadyEntry $Entries @('REVIEW_DRAFT')
$LatestFinal = Get-LatestReadyEntry $Entries @('CREATE_FINAL', 'REVISE_FINAL')
switch ($Mode) {
    'CREATE_PLAN' {
        if ($null -eq $LatestResearch) { throw 'CREATE_PLAN requires a prior READY RESEARCH_CANON handoff.' }
        if ($null -ne (Get-LatestReadyEntry $Entries @('CREATE_PLAN'))) {
            throw 'CREATE_PLAN is single-use; use an authorized REVISE_PLAN handoff.'
        }
    }
    'REVISE_PLAN' {
        if ($null -eq $LatestPlan) { throw 'REVISE_PLAN requires an existing READY plan handoff.' }
        $Authorization = @($Entries | Where-Object {
            ($_.status -ceq 'NAME_REGISTRATION_REQUIRED') -or
            ($_.status -ceq 'READY' -and
                (Get-LedgerReportField $_ 'resolutionOwner' -AllowMissing) -ceq 'story_architect' -and
                (Get-LedgerReportField $_ 'verdict' -AllowMissing) -in @('REVISE', 'BLOCK'))
        })
        if ($Authorization.Count -eq 0 -or
            [int]$Authorization[-1].sequence -le [int]$LatestPlan.sequence) {
            throw 'REVISE_PLAN lacks a later accepted name/review repair authorization.'
        }
    }
    'CREATE_DRAFT' {
        if ($null -eq $LatestPlan) { throw 'CREATE_DRAFT requires a prior READY plan handoff.' }
        if ($null -ne (Get-LatestReadyEntry $Entries @('CREATE_DRAFT'))) {
            throw 'CREATE_DRAFT is single-use; use an authorized REVISE_DRAFT handoff.'
        }
    }
    'REVISE_DRAFT' {
        if ($null -eq $LatestDraft -or $null -eq $LatestDraftReview -or
            [int]$LatestDraftReview.sequence -le [int]$LatestDraft.sequence -or
            (Get-LedgerReportField $LatestDraftReview 'resolutionOwner') -cne 'prose_writer' -or
            (Get-LedgerReportField $LatestDraftReview 'verdict') -notin @('REVISE', 'BLOCK')) {
            throw 'REVISE_DRAFT requires the latest later draft review to assign a repairable finding to prose_writer.'
        }
    }
    'REVIEW_DRAFT' {
        if ($null -eq $LatestPlan -or $null -eq $LatestDraft) {
            throw 'REVIEW_DRAFT requires current READY plan and draft handoffs; the guard binds both exact byte versions.'
        }
    }
    'CREATE_FINAL' {
        if ($null -eq $LatestPlan -or $null -eq $LatestDraft -or
            $null -eq $LatestDraftReview -or
            [int]$LatestDraftReview.sequence -le [int]$LatestDraft.sequence -or
            [int]$LatestDraftReview.sequence -le [int]$LatestPlan.sequence -or
            (Get-LedgerReportField $LatestDraftReview 'verdict') -cne 'PASS') {
            throw 'CREATE_FINAL requires a later draft-review PASS that binds both the current plan and current draft.'
        }
        if ($null -ne (Get-LatestReadyEntry $Entries @('CREATE_FINAL'))) {
            throw 'CREATE_FINAL is single-use; use an authorized REVISE_FINAL handoff.'
        }
    }
    'REVISE_FINAL' {
        $LatestFinalReview = Get-LatestReadyEntry $Entries @('REVIEW_FINAL')
        if ($null -eq $LatestFinal -or $null -eq $LatestFinalReview -or
            [int]$LatestFinalReview.sequence -le [int]$LatestFinal.sequence -or
            (Get-LedgerReportField $LatestFinalReview 'resolutionOwner') -cne 'story_editor' -or
            (Get-LedgerReportField $LatestFinalReview 'verdict') -notin @('REVISE', 'BLOCK')) {
            throw 'REVISE_FINAL requires the latest later final review to assign a repairable finding to story_editor.'
        }
    }
    'REVIEW_FINAL' {
        if ($null -eq $LatestFinal) {
            throw 'REVIEW_FINAL requires a prior READY final-edit handoff.'
        }
    }
}

$LockDirectory = Join-Path $ProjectRoot '.story-locks'
New-Item -ItemType Directory -Path $LockDirectory -Force | Out-Null
$LockPath = Join-Path $LockDirectory 'repository.lock'
$GuardId = [guid]::NewGuid().ToString('N')
try {
    $Stream = [IO.File]::Open($LockPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($GuardId)
        $Stream.Write($Bytes, 0, $Bytes.Length)
    }
    finally { $Stream.Dispose() }
}
catch {
    $Owner = if (Test-Path -LiteralPath $LockPath) {
        ((Get-Content -LiteralPath $LockPath -Raw) -split "`r?`n")[0]
    }
    else { 'unknown' }
    throw "Another guarded pipeline mutation is active (guard $Owner). Complete or abort it before starting another."
}

$GuardPath = Join-Path $LockDirectory "$GuardId.json"
try {
    $Guard = [ordered]@{
        schemaVersion = 1
        guardId = $GuardId
        story = $Story
        actor = $Actor
        mode = $Mode
        createdAt = [DateTimeOffset]::UtcNow.ToString('o')
        allowedPaths = $NormalizedAllowed
        inputs = $Inputs
        workspace = Get-WorkspaceSnapshot $ProjectRoot
    }
    $Json = ($Guard | ConvertTo-Json -Depth 8).Replace("`r`n", "`n").Replace("`r", "`n") + "`n"
    [IO.File]::WriteAllText($GuardPath, $Json, [Text.UTF8Encoding]::new($false))
    $GuardSha256 = Get-RawSha256 $GuardPath
    [IO.File]::WriteAllText(
        $LockPath,
        "$GuardId`n$GuardSha256`n",
        [Text.UTF8Encoding]::new($false)
    )
}
catch {
    if (Test-Path -LiteralPath $GuardPath) { Remove-Item -LiteralPath $GuardPath -Force }
    if (Test-Path -LiteralPath $LockPath) { Remove-Item -LiteralPath $LockPath -Force }
    throw
}

[ordered]@{
    schemaVersion = 1
    guardId = $GuardId
    guardSha256 = $GuardSha256
    guardPath = [IO.Path]::GetRelativePath($ProjectRoot, $GuardPath).Replace('\', '/')
    story = $Story
    actor = $Actor
    persister = [string]$ModeContract.persister
    mode = $Mode
    allowedPaths = $NormalizedAllowed
    storyStage = [string]$StoryMetadata.stage
    handoffLedgerSha256 = [string]$LedgerInput[0].sha256
    handoffLedgerChainHead = $ExpectedHead
} | ConvertTo-Json -Depth 5
