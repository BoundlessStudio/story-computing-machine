#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [switch]$RequireReleaseChain,

    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

function Get-RawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Utf8Sha256 {
    param([Parameter(Mandatory = $true)][string]$Text)
    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Text)
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Bytes)
    ).ToLowerInvariant()
}

function ConvertFrom-StableJson {
    param(
        [Parameter(Mandatory = $true)][string]$Json,
        [Parameter(Mandatory = $true)][string]$Context
    )
    try {
        $Parameters = @{}
        if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
            $Parameters.DateKind = 'String'
        }
        return $Json | ConvertFrom-Json @Parameters
    }
    catch { throw "$Context is invalid JSON: $($_.Exception.Message)" }
}

function Test-JsonInteger {
    param([object]$Value)
    return $Value -is [byte] -or $Value -is [sbyte] -or
        $Value -is [int16] -or $Value -is [uint16] -or
        $Value -is [int32] -or $Value -is [uint32] -or
        $Value -is [int64] -or $Value -is [uint64]
}

function Get-CanonicalEntryHash {
    param([Parameter(Mandatory = $true)][object]$Entry)
    $Copy = [ordered]@{}
    foreach ($Property in $Entry.PSObject.Properties) {
        if ($Property.Name -cne 'entrySha256') { $Copy[$Property.Name] = $Property.Value }
    }
    $Json = ($Copy | ConvertTo-Json -Depth 16 -Compress).
        Replace("`r`n", "`n").Replace("`r", "`n")
    return Get-Utf8Sha256 $Json
}

function Get-LedgerSnapshotSha256 {
    param(
        [Parameter(Mandatory = $true)][int64]$SchemaVersion,
        [Parameter(Mandatory = $true)][string]$StorySlug,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Entries,
        [AllowNull()][object]$ChainHead
    )
    $Snapshot = [ordered]@{
        schemaVersion = $SchemaVersion
        storySlug = $StorySlug
        chainHead = $ChainHead
        entries = @($Entries)
    }
    $Json = (($Snapshot | ConvertTo-Json -Depth 16) + "`n").
        Replace("`r`n", "`n").Replace("`r", "`n")
    return Get-Utf8Sha256 $Json
}

function Assert-ExactProperties {
    param(
        [object]$Value,
        [Parameter(Mandatory = $true)][string[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )
    if ($null -eq $Value) { throw "$Context is null." }
    $Actual = @($Value.PSObject.Properties.Name)
    if ($Actual.Count -ne $Expected.Count) {
        throw "$Context property count is invalid; expected $($Expected.Count), found $($Actual.Count)."
    }
    for ($Index = 0; $Index -lt $Expected.Count; $Index++) {
        if ($Actual[$Index] -cne $Expected[$Index]) {
            throw "$Context property order/schema mismatch at position $($Index + 1); expected '$($Expected[$Index])', found '$($Actual[$Index])'."
        }
    }
}

function Assert-JsonArray {
    param([object]$Value, [Parameter(Mandatory = $true)][string]$Context)
    if ($null -eq $Value -or -not ($Value -is [array])) {
        throw "$Context must be a JSON array."
    }
}

function Assert-ExactStringSet {
    param(
        [Parameter(Mandatory = $true)][string[]]$Actual,
        [Parameter(Mandatory = $true)][string[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )
    $Seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($Item in $Actual) {
        if ([string]::IsNullOrWhiteSpace($Item) -or -not $Seen.Add($Item)) {
            throw "$Context contains an empty or duplicate value '$Item'."
        }
    }
    $Missing = @($Expected | Where-Object { $_ -cnotin $Actual })
    $Extra = @($Actual | Where-Object { $_ -cnotin $Expected })
    if ($Missing.Count -gt 0 -or $Extra.Count -gt 0) {
        throw "$Context mismatch; missing=[$($Missing -join ', ')], extra=[$($Extra -join ', ')]."
    }
}

function Get-ReportField {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][int]$Sequence
    )
    $Matches = @([regex]::Matches(
        $Text,
        '(?m)^' + [regex]::Escape($Name) + ':[ \t]*(?<value>[^\r\n]+)[ \t]*$'
    ))
    if ($Matches.Count -ne 1) {
        throw "Handoff report at entry $Sequence must contain exactly one '${Name}:' field."
    }
    return $Matches[0].Groups['value'].Value.Trim().Trim('`')
}

function Assert-ReportValue {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][int]$Sequence
    )
    $Actual = Get-ReportField $Text $Name $Sequence
    if ($Actual -cne $Expected) {
        throw "Handoff report '$Name' at entry $Sequence does not bind the ledger receipt."
    }
}

function Expand-StoryPath {
    param(
        [Parameter(Mandatory = $true)][string]$Template,
        [Parameter(Mandatory = $true)][string]$StorySlug
    )
    return $Template.Replace('{story}', $StorySlug)
}

function Get-SafeRepositoryPath {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$Context
    )
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value -cne $Value.Trim()) {
        throw "$Context is empty or padded."
    }
    if ($Value.Contains('\') -or $Value.Contains(':') -or
        $Value.StartsWith('/', [StringComparison]::Ordinal) -or
        [IO.Path]::IsPathRooted($Value)) {
        throw "$Context is not a canonical project-relative path: $Value"
    }
    $Segments = @($Value.Split('/'))
    if ($Segments.Count -eq 0 -or @($Segments | Where-Object {
        [string]::IsNullOrEmpty($_) -or $_ -ceq '.' -or $_ -ceq '..' -or
        $_.EndsWith('.', [StringComparison]::Ordinal) -or
        $_.EndsWith(' ', [StringComparison]::Ordinal)
    }).Count -gt 0) {
        throw "$Context contains an unsafe or incomplete path segment: $Value"
    }
    try { $Full = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Value)) }
    catch { throw "$Context is not a valid path '$Value': $($_.Exception.Message)" }
    $RootPrefix = [IO.Path]::GetFullPath($ProjectRoot) + [IO.Path]::DirectorySeparatorChar
    if (-not $Full.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Context escapes the project root: $Value"
    }
    $Canonical = [IO.Path]::GetRelativePath($ProjectRoot, $Full).Replace('\', '/')
    if ($Canonical -cne $Value) {
        throw "$Context is not in canonical repository form; expected '$Canonical', found '$Value'."
    }

    $Walk = [IO.Path]::GetFullPath($ProjectRoot)
    foreach ($Segment in $Segments) {
        $Walk = Join-Path $Walk $Segment
        if (Test-Path -LiteralPath $Walk) {
            $Item = Get-Item -LiteralPath $Walk -Force
            if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "$Context traverses a reparse point: $Value"
            }
        }
    }
    return $Full
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$ContractPath = Join-Path $ProjectRoot 'schemas/pipeline-contract.json'
if (-not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) {
    throw "Pipeline contract not found: $ContractPath"
}
$Contract = ConvertFrom-StableJson (Get-Content -LiteralPath $ContractPath -Raw) 'Pipeline contract'
$HandoffContract = $Contract.handoffLedger
Assert-ExactProperties $HandoffContract @(
    'schemaVersion', 'fields', 'entryFields', 'statuses', 'modeContracts',
    'releaseFamilies'
) 'Pipeline handoff contract'
if (-not (Test-JsonInteger $HandoffContract.schemaVersion) -or
    [int64]$HandoffContract.schemaVersion -ne 2) {
    throw 'The active handoff ledger contract must be schema version 2.'
}
$LedgerSchemaVersion = [int64]$HandoffContract.schemaVersion
$ExpectedLedgerFields = @('schemaVersion', 'storySlug', 'chainHead', 'entries')
$ExpectedEntryFields = @(
    'sequence', 'story', 'actor', 'mode', 'status', 'recordedAt', 'guardId',
    'persister', 'report', 'reportSha256', 'inputs', 'outputs',
    'previousEntrySha256', 'entrySha256'
)
Assert-ExactStringSet @($HandoffContract.fields | ForEach-Object { [string]$_ }) `
    $ExpectedLedgerFields 'Pipeline handoff ledger fields'
Assert-ExactStringSet @($HandoffContract.entryFields | ForEach-Object { [string]$_ }) `
    $ExpectedEntryFields 'Pipeline handoff entry fields'

$GlobalStatuses = @($HandoffContract.statuses | ForEach-Object { [string]$_ })
Assert-ExactStringSet $GlobalStatuses @(
    'READY', 'HANDOFF_ERROR', 'USER_RULING_REQUIRED',
    'NAME_REGISTRATION_REQUIRED'
) 'Pipeline handoff statuses'

$ModeByName = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($Property in @($HandoffContract.modeContracts.PSObject.Properties)) {
    $ModeName = [string]$Property.Name
    $ModeContract = $Property.Value
    Assert-ExactProperties $ModeContract @(
        'actor', 'persister', 'allowedStages', 'allowedOutputs', 'requiredInputs',
        'statuses', 'requireAllReadyOutputs'
    ) "Pipeline mode contract '$ModeName'"
    if ([string]::IsNullOrWhiteSpace([string]$ModeContract.actor) -or
        [string]::IsNullOrWhiteSpace([string]$ModeContract.persister) -or
        -not ($ModeContract.requireAllReadyOutputs -is [bool])) {
        throw "Pipeline mode contract '$ModeName' has invalid identity or output policy."
    }
    foreach ($Status in @($ModeContract.statuses | ForEach-Object { [string]$_ })) {
        if ($Status -cnotin $GlobalStatuses) {
            throw "Pipeline mode contract '$ModeName' references unsupported status '$Status'."
        }
    }
    foreach ($Template in @(
        @($ModeContract.allowedOutputs) + @($ModeContract.requiredInputs)
    )) {
        $Expanded = Expand-StoryPath ([string]$Template) $Story
        $null = Get-SafeRepositoryPath $Expanded "Pipeline mode '$ModeName' path"
    }
    $ModeByName.Add($ModeName, $ModeContract)
}

$FamilyByMode = [Collections.Generic.Dictionary[string,int]]::new([StringComparer]::Ordinal)
$FamilyModes = [Collections.Generic.List[object]]::new()
$FamilyIndex = 0
foreach ($FamilyValue in @($HandoffContract.releaseFamilies)) {
    if (-not ($FamilyValue -is [array])) {
        throw "Pipeline release family $FamilyIndex must be a JSON array."
    }
    $Modes = @($FamilyValue | ForEach-Object { [string]$_ })
    if ($Modes.Count -eq 0) { throw "Pipeline release family $FamilyIndex is empty." }
    foreach ($ModeName in $Modes) {
        if (-not $ModeByName.ContainsKey($ModeName) -or $FamilyByMode.ContainsKey($ModeName)) {
            throw "Pipeline release family contains unknown or duplicate mode '$ModeName'."
        }
        $FamilyByMode.Add($ModeName, $FamilyIndex)
    }
    $FamilyModes.Add($Modes)
    $FamilyIndex++
}
if ($FamilyByMode.Count -ne $ModeByName.Count) {
    throw 'Every pipeline handoff mode must occur in exactly one release family.'
}

$LedgerPath = Join-Path $ProjectRoot "stories/$Story/handoffs.json"
if (-not (Test-Path -LiteralPath $LedgerPath -PathType Leaf)) {
    throw "Missing handoff ledger: $LedgerPath"
}
$Ledger = ConvertFrom-StableJson (Get-Content -LiteralPath $LedgerPath -Raw) 'handoffs.json'
Assert-ExactProperties $Ledger $ExpectedLedgerFields 'handoffs.json'
if (-not (Test-JsonInteger $Ledger.schemaVersion) -or
    [int64]$Ledger.schemaVersion -ne $LedgerSchemaVersion -or
    -not ($Ledger.storySlug -is [string]) -or $Ledger.storySlug -cne $Story) {
    throw 'handoffs.json identity/schema mismatch.'
}
Assert-JsonArray $Ledger.entries 'handoffs.json entries'

$CurrentStoryPath = Join-Path $ProjectRoot "stories/$Story/story.json"
$CurrentStoryHash = $null
$CurrentStory = $null
if (Test-Path -LiteralPath $CurrentStoryPath -PathType Leaf) {
    $CurrentStoryHash = Get-RawSha256 $CurrentStoryPath
    $CurrentStory = ConvertFrom-StableJson (
        Get-Content -LiteralPath $CurrentStoryPath -Raw
    ) 'Current story.json'
}

$Previous = $null
$Sequence = 0
$PrefixEntries = [Collections.Generic.List[object]]::new()
$GuardIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$KnownOutputs = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
$LatestOutputs = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
$ReadyModes = [Collections.Generic.List[string]]::new()
$Satisfied = [bool[]]::new($FamilyModes.Count)
$ArtifactEstablished = [bool[]]::new($FamilyModes.Count)
$Outstanding = [Collections.Generic.Dictionary[int,object]]::new()

foreach ($Entry in @($Ledger.entries)) {
    $Sequence++
    Assert-ExactProperties $Entry $ExpectedEntryFields "handoffs.json entry $Sequence"
    if (-not (Test-JsonInteger $Entry.sequence) -or [int64]$Entry.sequence -ne $Sequence -or
        -not ($Entry.story -is [string]) -or $Entry.story -cne $Story) {
        throw "Invalid handoff sequence/slug at entry $Sequence."
    }
    if (-not ($Entry.mode -is [string]) -or
        -not $ModeByName.ContainsKey([string]$Entry.mode)) {
        throw "Unsupported handoff mode '$($Entry.mode)' at entry $Sequence."
    }
    $Mode = [string]$Entry.mode
    $ModeContract = $ModeByName[$Mode]
    $Family = $FamilyByMode[$Mode]
    if (-not ($Entry.actor -is [string]) -or
        $Entry.actor -cne [string]$ModeContract.actor) {
        throw "Mode '$Mode' requires actor '$($ModeContract.actor)' at entry $Sequence."
    }
    if (-not ($Entry.persister -is [string]) -or
        $Entry.persister -cne [string]$ModeContract.persister) {
        throw "Mode '$Mode' requires persister '$($ModeContract.persister)' at entry $Sequence."
    }
    if (-not ($Entry.status -is [string]) -or
        [string]$Entry.status -cnotin @($ModeContract.statuses | ForEach-Object { [string]$_ })) {
        throw "Status '$($Entry.status)' is not permitted for mode '$Mode' at entry $Sequence."
    }
    $Status = [string]$Entry.status
    if (-not ($Entry.guardId -is [string]) -or
        [string]$Entry.guardId -cnotmatch '^[a-f0-9]{32}$' -or
        -not $GuardIds.Add([string]$Entry.guardId)) {
        throw "Invalid or duplicate guardId at entry $Sequence."
    }
    if ($Entry.previousEntrySha256 -cne $Previous) {
        throw "Broken handoff hash chain at entry $Sequence."
    }
    if (-not ($Entry.entrySha256 -is [string]) -or
        [string]$Entry.entrySha256 -cnotmatch '^[a-f0-9]{64}$' -or
        (Get-CanonicalEntryHash $Entry) -cne [string]$Entry.entrySha256) {
        throw "Invalid handoff entry digest at entry $Sequence."
    }
    if (-not ($Entry.recordedAt -is [string])) {
        throw "Invalid UTC handoff timestamp at entry $Sequence."
    }
    $Timestamp = [DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParseExact(
        [string]$Entry.recordedAt, 'o', [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::RoundtripKind, [ref]$Timestamp
    ) -or $Timestamp.Offset -ne [TimeSpan]::Zero) {
        throw "Invalid UTC handoff timestamp at entry $Sequence."
    }

    if (-not ($Entry.report -is [string])) {
        throw "Invalid durable handoff report at entry $Sequence."
    }
    $Report = [string]$Entry.report
    $NormalizedReport = $Report.Replace("`r`n", "`n").Replace("`r", "`n")
    if ($Report -cne $NormalizedReport -or [string]::IsNullOrWhiteSpace($Report) -or
        $Report.Length -gt 200000 -or
        -not $Report.EndsWith("`n", [StringComparison]::Ordinal) -or
        $Report.EndsWith("`n`n", [StringComparison]::Ordinal)) {
        throw "Handoff report at entry $Sequence must be LF-normalized, nonempty, and have exactly one trailing LF."
    }
    if (-not ($Entry.reportSha256 -is [string]) -or
        [string]$Entry.reportSha256 -cnotmatch '^[a-f0-9]{64}$' -or
        (Get-Utf8Sha256 $Report) -cne [string]$Entry.reportSha256) {
        throw "Handoff report digest mismatch at entry $Sequence."
    }
    if ((Get-ReportField $Report 'story' $Sequence) -cne $Story -or
        (Get-ReportField $Report 'mode' $Sequence) -cne $Mode -or
        (Get-ReportField $Report 'status' $Sequence) -cne $Status) {
        throw "Handoff report identity/status mismatch at entry $Sequence."
    }
    $ResolutionOwner = Get-ReportField $Report 'resolutionOwner' $Sequence
    $ErrorCode = Get-ReportField $Report 'errorCode' $Sequence
    $ResolutionQuestion = Get-ReportField $Report 'resolutionQuestion' $Sequence
    switch ($Status) {
        'READY' {
            if ($ErrorCode -cne 'none' -or $ResolutionQuestion -cne 'none' -or
                $ResolutionOwner -ceq 'user') {
                throw "READY report has unresolved resolution fields at entry $Sequence."
            }
        }
        'HANDOFF_ERROR' {
            if ($ErrorCode -ceq 'none' -or $ResolutionOwner -ceq 'user') {
                throw "HANDOFF_ERROR report lacks a mechanical error owner/code at entry $Sequence."
            }
        }
        'USER_RULING_REQUIRED' {
            if ($ResolutionOwner -cne 'user' -or $ResolutionQuestion -ceq 'none') {
                throw "USER_RULING_REQUIRED report lacks an exact user question at entry $Sequence."
            }
        }
        'NAME_REGISTRATION_REQUIRED' {
            if ($ResolutionOwner -cne 'coordinator' -or $ErrorCode -cne 'none' -or
                $ResolutionQuestion -cne 'none') {
                throw "NAME_REGISTRATION_REQUIRED report has invalid routing fields at entry $Sequence."
            }
        }
    }

    Assert-JsonArray $Entry.inputs "handoff inputs at entry $Sequence"
    Assert-JsonArray $Entry.outputs "handoff outputs at entry $Sequence"
    $InputsByPath = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach ($Input in @($Entry.inputs)) {
        Assert-ExactProperties $Input @('path', 'sha256') "handoff input at entry $Sequence"
        if (-not ($Input.path -is [string])) { throw "Invalid handoff input path at entry $Sequence." }
        $InputPath = [string]$Input.path
        $null = Get-SafeRepositoryPath $InputPath "Handoff input at entry $Sequence"
        if (-not $InputsByPath.TryAdd($InputPath, $Input)) {
            throw "Duplicate handoff input path '$InputPath' at entry $Sequence."
        }
        if (-not ($Input.sha256 -is [string]) -or
            [string]$Input.sha256 -cnotmatch '^[a-f0-9]{64}$') {
            throw "Invalid handoff input hash at entry $Sequence."
        }
        if ($KnownOutputs.ContainsKey($InputPath)) {
            $KnownHash = $KnownOutputs[$InputPath]
            if ($null -eq $KnownHash -or [string]$Input.sha256 -cne [string]$KnownHash) {
                throw "Handoff input '$InputPath' does not bind the latest prior output at entry $Sequence."
            }
        }
    }
    $ExpectedInputs = @($ModeContract.requiredInputs | ForEach-Object {
        Expand-StoryPath ([string]$_) $Story
    })
    Assert-ExactStringSet @($InputsByPath.Keys) $ExpectedInputs `
        "Mode '$Mode' inputs at entry $Sequence"

    $LedgerInputPath = "stories/$Story/handoffs.json"
    $LedgerInput = $InputsByPath[$LedgerInputPath]
    $ExpectedPrefixHash = Get-LedgerSnapshotSha256 -SchemaVersion $LedgerSchemaVersion `
        -StorySlug $Story -Entries @($PrefixEntries) -ChainHead $Previous
    if ([string]$LedgerInput.sha256 -cne $ExpectedPrefixHash) {
        throw "Handoff ledger input at entry $Sequence does not bind the exact previous-ledger snapshot."
    }
    Assert-ReportValue $Report 'handoffLedger' $LedgerInputPath $Sequence
    Assert-ReportValue $Report 'handoffLedgerSha256' ([string]$LedgerInput.sha256) $Sequence
    if ($Mode -cin @('RESEARCH_CANON', 'REVIEW_DRAFT', 'REVIEW_FINAL')) {
        $ExpectedReportHead = if ($null -eq $Previous) { 'none' } else { [string]$Previous }
        Assert-ReportValue $Report 'handoffLedgerChainHead' $ExpectedReportHead $Sequence
    }
    $StoryInput = $InputsByPath["stories/$Story/story.json"]
    if ($null -ne $CurrentStoryHash -and [string]$StoryInput.sha256 -ceq $CurrentStoryHash) {
        if ($null -eq $CurrentStory -or $CurrentStory.slug -cne $Story -or
            [string]$CurrentStory.stage -cnotin @($ModeContract.allowedStages | ForEach-Object { [string]$_ })) {
            throw "Current story.json snapshot is not in an allowed stage for mode '$Mode' at entry $Sequence."
        }
    }

    $AllowedOutputs = @($ModeContract.allowedOutputs | ForEach-Object {
        Expand-StoryPath ([string]$_) $Story
    })
    $OutputsByPath = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
    foreach ($Output in @($Entry.outputs)) {
        Assert-ExactProperties $Output @('path', 'beforeSha256', 'afterSha256') `
            "handoff output at entry $Sequence"
        if (-not ($Output.path -is [string])) { throw "Invalid handoff output path at entry $Sequence." }
        $OutputPath = [string]$Output.path
        $null = Get-SafeRepositoryPath $OutputPath "Handoff output at entry $Sequence"
        if ($OutputPath -cnotin $AllowedOutputs) {
            throw "Mode '$Mode' recorded unauthorized output '$OutputPath' at entry $Sequence."
        }
        if (-not $OutputsByPath.TryAdd($OutputPath, $Output)) {
            throw "Duplicate handoff output path '$OutputPath' at entry $Sequence."
        }
        foreach ($DigestProperty in @('beforeSha256', 'afterSha256')) {
            $Digest = $Output.$DigestProperty
            if ($null -ne $Digest -and
                (-not ($Digest -is [string]) -or [string]$Digest -cnotmatch '^[a-f0-9]{64}$')) {
                throw "Invalid handoff output $DigestProperty at entry $Sequence."
            }
        }
        if ($Output.beforeSha256 -ceq $Output.afterSha256) {
            throw "Handoff output '$OutputPath' does not describe a byte change at entry $Sequence."
        }
        if ($KnownOutputs.ContainsKey($OutputPath) -and
            $Output.beforeSha256 -cne $KnownOutputs[$OutputPath]) {
            throw "Handoff output '$OutputPath' has a discontinuous beforeSha256 at entry $Sequence."
        }
        if ($InputsByPath.ContainsKey($OutputPath) -and
            $Output.beforeSha256 -cne $InputsByPath[$OutputPath].sha256) {
            throw "Handoff output '$OutputPath' does not bind its input bytes at entry $Sequence."
        }
    }

    if ($Status -ceq 'READY') {
        if ($OutputsByPath.Count -eq 0) {
            throw "READY mode '$Mode' has no changed output at entry $Sequence."
        }
        if (@($OutputsByPath.Values | Where-Object { $null -eq $_.afterSha256 }).Count -gt 0) {
            throw "READY mode '$Mode' cannot delete a production output at entry $Sequence."
        }
        if ([bool]$ModeContract.requireAllReadyOutputs) {
            Assert-ExactStringSet @($OutputsByPath.Keys) $AllowedOutputs `
                "READY mode '$Mode' outputs at entry $Sequence"
        }
    }
    elseif ($Status -ceq 'HANDOFF_ERROR' -and $OutputsByPath.Count -gt 0) {
        throw "HANDOFF_ERROR cannot carry production outputs at entry $Sequence."
    }
    elseif ($Status -ceq 'USER_RULING_REQUIRED' -and
        $Mode -cnotin @('REVIEW_DRAFT', 'REVIEW_FINAL') -and $OutputsByPath.Count -gt 0) {
        throw "Only review modes may persist USER_RULING_REQUIRED output at entry $Sequence."
    }
    elseif ($Status -ceq 'NAME_REGISTRATION_REQUIRED' -and
        $Mode -cnotin @('CREATE_PLAN', 'REVISE_PLAN') -and $OutputsByPath.Count -gt 0) {
        throw "Only plan modes may persist NAME_REGISTRATION_REQUIRED output at entry $Sequence."
    }

    $StoryPrefix = "stories/$Story"
    switch -Regex ($Mode) {
        '^RESEARCH_CANON$' {
            Assert-ReportValue $Report 'sourcePromptSha256' `
                ([string]$InputsByPath["$StoryPrefix/00-prompt.md"].sha256) $Sequence
            Assert-ReportValue $Report 'authorityManifestSha256' `
                ([string]$InputsByPath["$StoryPrefix/authority.json"].sha256) $Sequence
            $Bodies = @([regex]::Matches(
                $Report,
                '(?ms)^BEGIN_FILE_CONTENT[ \t]*\n(?<body>.*?)^END_FILE_CONTENT[ \t]*(?:\n|\z)'
            ))
            if ($Status -ceq 'READY') {
                if ($Bodies.Count -ne 1) {
                    throw "READY canon research report must contain one bounded file body at entry $Sequence."
                }
                $BriefPath = "$StoryPrefix/01-canon-brief.md"
                if (-not $OutputsByPath.ContainsKey($BriefPath) -or
                    (Get-Utf8Sha256 $Bodies[0].Groups['body'].Value) -cne
                        [string]$OutputsByPath[$BriefPath].afterSha256) {
                    throw "Canon research body does not equal the persisted brief output at entry $Sequence."
                }
            }
            elseif ($Bodies.Count -ne 0) {
                throw "Non-READY canon research report contains a speculative file body at entry $Sequence."
            }
        }
        '^(CREATE|REVISE)_PLAN$' {
            Assert-ReportValue $Report 'inputPromptSha256' `
                ([string]$InputsByPath["$StoryPrefix/00-prompt.md"].sha256) $Sequence
            Assert-ReportValue $Report 'inputCanonBriefSha256' `
                ([string]$InputsByPath["$StoryPrefix/01-canon-brief.md"].sha256) $Sequence
            $PlanPath = "$StoryPrefix/02-story-plan.md"
            if ($OutputsByPath.ContainsKey($PlanPath)) {
                Assert-ReportValue $Report 'beforePlanSha256' `
                    ([string]$OutputsByPath[$PlanPath].beforeSha256) $Sequence
                Assert-ReportValue $Report 'newPlanSha256' `
                    ([string]$OutputsByPath[$PlanPath].afterSha256) $Sequence
                if ($Mode -ceq 'CREATE_PLAN') {
                    Assert-ReportValue $Report 'planScaffoldSha256' `
                        ([string]$OutputsByPath[$PlanPath].beforeSha256) $Sequence
                }
            }
            elseif ((Get-ReportField $Report 'newPlanSha256' $Sequence) -cnotmatch '^[a-f0-9]{64}$') {
                throw "Plan report newPlanSha256 is not a digest at entry $Sequence."
            }
            if ($Mode -ceq 'REVISE_PLAN' -and
                $Status -cin @('READY', 'NAME_REGISTRATION_REQUIRED') -and
                (Get-ReportField $Report 'repairAuthorization' $Sequence) -ceq 'none') {
                throw "REVISE_PLAN report lacks repair authorization at entry $Sequence."
            }
        }
        '^(CREATE|REVISE)_DRAFT$' {
            $DraftPath = "$StoryPrefix/03-draft.md"
            if ($OutputsByPath.ContainsKey($DraftPath)) {
                Assert-ReportValue $Report 'beforeDraftSha256' `
                    ([string]$OutputsByPath[$DraftPath].beforeSha256) $Sequence
                Assert-ReportValue $Report 'newDraftSha256' `
                    ([string]$OutputsByPath[$DraftPath].afterSha256) $Sequence
                if ($Mode -ceq 'CREATE_DRAFT') {
                    Assert-ReportValue $Report 'draftScaffoldSha256' `
                        ([string]$OutputsByPath[$DraftPath].beforeSha256) $Sequence
                }
            }
            elseif ((Get-ReportField $Report 'newDraftSha256' $Sequence) -cnotmatch '^[a-f0-9]{64}$') {
                throw "Draft report newDraftSha256 is not a digest at entry $Sequence."
            }
            if ($Mode -ceq 'REVISE_DRAFT' -and $Status -ceq 'READY' -and
                $Report -cnotmatch '(?m)^-[ \t]+findingId:[ \t]*[^\r\n]+') {
                throw "REVISE_DRAFT report lacks an authorizing finding at entry $Sequence."
            }
        }
        '^(CREATE|REVISE)_FINAL$' {
            Assert-ReportValue $Report 'inputPlanSha256' `
                ([string]$InputsByPath["$StoryPrefix/02-story-plan.md"].sha256) $Sequence
            Assert-ReportValue $Report 'inputDraftSha256' `
                ([string]$InputsByPath["$StoryPrefix/03-draft.md"].sha256) $Sequence
            foreach ($Binding in @(
                [pscustomobject]@{
                    path = "$StoryPrefix/05-story.md"; before = 'beforeStorySha256'
                    scaffold = 'storyScaffoldSha256'; after = 'newStorySha256'
                },
                [pscustomobject]@{
                    path = "$StoryPrefix/06-canon-delta.md"; before = 'beforeCanonDeltaSha256'
                    scaffold = 'canonDeltaScaffoldSha256'; after = 'newCanonDeltaSha256'
                }
            )) {
                if ($OutputsByPath.ContainsKey($Binding.path)) {
                    Assert-ReportValue $Report $Binding.before `
                        ([string]$OutputsByPath[$Binding.path].beforeSha256) $Sequence
                    Assert-ReportValue $Report $Binding.after `
                        ([string]$OutputsByPath[$Binding.path].afterSha256) $Sequence
                    if ($Mode -ceq 'CREATE_FINAL') {
                        Assert-ReportValue $Report $Binding.scaffold `
                            ([string]$OutputsByPath[$Binding.path].beforeSha256) $Sequence
                    }
                }
                elseif ((Get-ReportField $Report $Binding.after $Sequence) -cnotmatch '^[a-f0-9]{64}$') {
                    throw "Final-edit report '$($Binding.after)' is not a digest at entry $Sequence."
                }
            }
            if ($Mode -ceq 'REVISE_FINAL' -and $Status -ceq 'READY' -and
                $Report -cnotmatch '(?m)^-[ \t]+findingId:[ \t]*[^\r\n]+') {
                throw "REVISE_FINAL report lacks an authorizing finding at entry $Sequence."
            }
        }
        '^REVIEW_(DRAFT|FINAL)$' {
            $ArtifactPath = if ($Mode -ceq 'REVIEW_DRAFT') {
                "$StoryPrefix/03-draft.md"
            }
            else { "$StoryPrefix/05-story.md" }
            Assert-ReportValue $Report 'artifactSha256' `
                ([string]$InputsByPath[$ArtifactPath].sha256) $Sequence
            Assert-ReportValue $Report 'canonBriefSha256' `
                ([string]$InputsByPath["$StoryPrefix/01-canon-brief.md"].sha256) $Sequence
            Assert-ReportValue $Report 'planSha256' `
                ([string]$InputsByPath["$StoryPrefix/02-story-plan.md"].sha256) $Sequence
            Assert-ReportValue $Report 'authorityManifestSha256' `
                ([string]$InputsByPath["$StoryPrefix/authority.json"].sha256) $Sequence
            if ($Mode -ceq 'REVIEW_FINAL') {
                Assert-ReportValue $Report 'canonDeltaSha256' `
                    ([string]$InputsByPath["$StoryPrefix/06-canon-delta.md"].sha256) $Sequence
            }
            if ($Status -cin @('READY', 'USER_RULING_REQUIRED')) {
                $ReviewPath = Join-Path $ProjectRoot "$StoryPrefix/04-review.md"
                if (-not (Test-Path -LiteralPath $ReviewPath -PathType Leaf) -or
                    [regex]::Matches(
                        (Get-Content -LiteralPath $ReviewPath -Raw),
                        [regex]::Escape($Report)
                    ).Count -ne 1) {
                    throw "Persisted review history does not contain the exact critic payload once for entry $Sequence."
                }
            }
        }
    }

    $BlockingFamilies = @($Outstanding.Values | Where-Object {
        $_.status -cne 'NAME_REGISTRATION_REQUIRED'
    } | ForEach-Object { [int]$_.family } | Sort-Object -Unique)
    if ($BlockingFamilies.Count -gt 0 -and
        ($BlockingFamilies.Count -ne 1 -or $Family -ne $BlockingFamilies[0])) {
        throw "Entry $Sequence must repair unresolved family $($BlockingFamilies -join ', ') before another family may run."
    }
    $AwaitingNamePlan = @($Outstanding.Values | Where-Object {
        $_.status -ceq 'NAME_REGISTRATION_REQUIRED' -and $_.phase -ceq 'awaiting-plan'
    })
    if ($AwaitingNamePlan.Count -gt 0 -and $Mode -cne 'REVISE_PLAN') {
        throw "Entry $Sequence must route unresolved name registration through READY REVISE_PLAN."
    }
    for ($PriorFamily = 0; $PriorFamily -lt $Family; $PriorFamily++) {
        if (-not $Satisfied[$PriorFamily]) {
            throw "Illegal causal handoff order at entry $Sequence; family $Family requires READY family $PriorFamily."
        }
    }

    $IsCreate = $Mode.StartsWith('CREATE_', [StringComparison]::Ordinal)
    $IsRevise = $Mode.StartsWith('REVISE_', [StringComparison]::Ordinal)
    if ($IsRevise -and -not $ArtifactEstablished[$Family]) {
        throw "Mode '$Mode' cannot revise before its family has established an output."
    }
    if ($IsCreate -and $ArtifactEstablished[$Family]) {
        throw "Mode '$Mode' cannot recreate an established family output; use the REVISE mode."
    }

    foreach ($Output in @($OutputsByPath.Values)) {
        $KnownOutputs[[string]$Output.path] = $Output.afterSha256
        $LatestOutputs[[string]$Output.path] = [pscustomobject]@{
            status = $Status
            sha256 = $Output.afterSha256
            sequence = $Sequence
        }
    }
    if ($OutputsByPath.Count -gt 0) { $ArtifactEstablished[$Family] = $true }

    if ($Status -ceq 'READY') {
        $ReadyModes.Add($Mode)
        $Satisfied[$Family] = $true
        for ($LaterFamily = $Family + 1; $LaterFamily -lt $Satisfied.Count; $LaterFamily++) {
            $Satisfied[$LaterFamily] = $false
        }

        if ($Outstanding.ContainsKey($Family)) {
            $Pending = $Outstanding[$Family]
            if ($Pending.status -cne 'NAME_REGISTRATION_REQUIRED' -or
                $Family -eq 1 -or $Pending.phase -ceq 'returning') {
                $null = $Outstanding.Remove($Family)
            }
        }
        if ($Mode -ceq 'REVISE_PLAN') {
            foreach ($Pending in @($Outstanding.Values)) {
                if ($Pending.status -ceq 'NAME_REGISTRATION_REQUIRED' -and
                    $Pending.phase -ceq 'awaiting-plan') {
                    $Pending.phase = 'returning'
                }
            }
        }
    }
    else {
        $Satisfied[$Family] = $false
        for ($LaterFamily = $Family + 1; $LaterFamily -lt $Satisfied.Count; $LaterFamily++) {
            $Satisfied[$LaterFamily] = $false
        }
        $Outstanding[$Family] = [pscustomobject][ordered]@{
            sequence = $Sequence
            family = $Family
            mode = $Mode
            status = $Status
            phase = if ($Status -ceq 'NAME_REGISTRATION_REQUIRED') {
                'awaiting-plan'
            }
            else { 'same-family' }
        }
    }

    $PrefixEntries.Add($Entry)
    $Previous = [string]$Entry.entrySha256
}
if ($Ledger.chainHead -cne $Previous) {
    throw 'handoffs.json chainHead does not match the final entry.'
}
if ($Sequence -eq 0 -and $null -ne $Ledger.chainHead) {
    throw 'An empty handoff ledger must have a null chainHead.'
}

foreach ($Pair in $LatestOutputs.GetEnumerator()) {
    if ($Pair.Value.status -cne 'READY') { continue }
    $Full = Get-SafeRepositoryPath $Pair.Key "Latest READY output '$($Pair.Key)'"
    if (-not (Test-Path -LiteralPath $Full -PathType Leaf) -or
        (Get-RawSha256 $Full) -cne [string]$Pair.Value.sha256) {
        throw "Current file '$($Pair.Key)' differs from its latest READY handoff output."
    }
}

$Unresolved = @($Outstanding.Values | Sort-Object family, sequence | ForEach-Object {
    [ordered]@{
        sequence = [int64]$_.sequence
        family = [int64]$_.family
        mode = [string]$_.mode
        status = [string]$_.status
    }
})
$ReleaseReady = $Unresolved.Count -eq 0 -and
    @($Satisfied | Where-Object { -not $_ }).Count -eq 0
if ($RequireReleaseChain -and $Unresolved.Count -gt 0) {
    $Descriptions = @($Unresolved | ForEach-Object {
        "family $($_.family) $($_.mode)/$($_.status) at entry $($_.sequence)"
    })
    throw "Release handoff ledger has unresolved status requiring a later READY repair in the same family: $($Descriptions -join '; ')."
}
if ($RequireReleaseChain) {
    for ($Index = 0; $Index -lt $Satisfied.Count; $Index++) {
        if (-not $Satisfied[$Index]) {
            throw "Release handoff ledger lacks a current READY family: $(@($FamilyModes[$Index]) -join ' or ')."
        }
    }
}

$Result = [ordered]@{
    schemaVersion = 1
    story = $Story
    passed = $true
    entries = $Sequence
    chainHead = $Previous
    ledgerSha256 = Get-RawSha256 $LedgerPath
    readyModes = @($ReadyModes)
    releaseReady = $ReleaseReady
    unresolved = $Unresolved
}
if ($OutputFormat -eq 'Json') { $Result | ConvertTo-Json -Depth 8 }
elseif ($Unresolved.Count -gt 0) {
    "Handoff ledger is structurally valid for '$Story' with $($Unresolved.Count) unresolved family receipt(s)."
}
else { "Handoff ledger passed for '$Story' ($Sequence entries, chain $Previous)." }
