#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9]{32}$')]
    [string]$GuardId,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9]{64}$')]
    [string]$GuardSha256,

    [ValidateSet('READY', 'HANDOFF_ERROR', 'USER_RULING_REQUIRED', 'NAME_REGISTRATION_REQUIRED')]
    [string]$Status = 'READY',

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ReportText,

    [switch]$RecoverCommittedGuard,

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

function Get-CanonicalEntryHash {
    param([Parameter(Mandatory = $true)][object]$Entry)
    $Copy = [ordered]@{}
    foreach ($Property in $Entry.PSObject.Properties) {
        if ($Property.Name -cne 'entrySha256') { $Copy[$Property.Name] = $Property.Value }
    }
    $Json = ($Copy | ConvertTo-Json -Depth 10 -Compress).Replace("`r`n", "`n").Replace("`r", "`n")
    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Json)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function Assert-ExactProperties {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )
    $Actual = @($Value.PSObject.Properties.Name)
    $Missing = @($Expected | Where-Object { $_ -cnotin $Actual })
    $Extra = @($Actual | Where-Object { $_ -cnotin $Expected })
    if ($Missing.Count -gt 0 -or $Extra.Count -gt 0) {
        throw "$Context property mismatch; missing=[$($Missing -join ', ')], extra=[$($Extra -join ', ')]."
    }
}

function Get-ReportField {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Name
    )
    $Found = @([regex]::Matches(
        $Text,
        '(?m)^' + [regex]::Escape($Name) + ':[ \t]*(?<value>[^\r\n]+)[ \t]*$'
    ))
    if ($Found.Count -ne 1) {
        throw "ReportText must contain exactly one '${Name}:' field."
    }
    return $Found[0].Groups['value'].Value.Trim().Trim('`')
}

function Expand-StoryPath {
    param([string]$Template, [string]$StorySlug)
    return $Template.Replace('{story}', $StorySlug)
}

function Get-SafeRelativePath {
    param([string]$Root, [string]$Value, [string]$Label)
    if ([string]::IsNullOrWhiteSpace($Value)) { throw "$Label path is empty." }
    $Full = [IO.Path]::GetFullPath((Join-Path $Root $Value))
    $Prefix = [IO.Path]::GetFullPath($Root) + [IO.Path]::DirectorySeparatorChar
    if (-not $Full.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label path escapes the project root: $Value"
    }
    return [IO.Path]::GetRelativePath($Root, $Full).Replace('\', '/')
}

function Get-GuardInputSha256 {
    param([object]$GuardValue, [string]$Path)
    $InputMatches = @($GuardValue.inputs | Where-Object path -CEQ $Path)
    if ($InputMatches.Count -ne 1 -or [string]$InputMatches[0].sha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw "Guard must bind input '$Path' exactly once."
    }
    return [string]($InputMatches[0].sha256)
}

function Get-GuardBaselineSha256 {
    param([object]$GuardValue, [string]$Path)
    $BaselineMatches = @($GuardValue.workspace | Where-Object path -CEQ $Path)
    if ($BaselineMatches.Count -gt 1) { throw "Guard workspace repeats '$Path'." }
    if ($BaselineMatches.Count -eq 0) { return $null }
    if ([string]$BaselineMatches[0].sha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw "Guard workspace digest is invalid for '$Path'."
    }
    return [string]($BaselineMatches[0].sha256)
}

function Assert-ReportDigestField {
    param([string]$Text, [string]$Name, [string]$Expected)
    $Actual = Get-ReportField $Text $Name
    if ($Actual -cne $Expected) {
        throw "ReportText '$Name' does not match the guarded byte snapshot (expected '$Expected', found '$Actual')."
    }
}

function Write-RawBytesAtomically {
    param([byte[]]$Bytes, [string]$Path)
    $Temporary = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllBytes($Temporary, $Bytes)
        [IO.File]::Move($Temporary, $Path, $true)
    }
    finally { if (Test-Path -LiteralPath $Temporary) { Remove-Item -LiteralPath $Temporary -Force } }
}

function Invoke-JsonChecker {
    param([string]$Path, [string[]]$Arguments, [string]$Label)
    $Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
    $Output = & $Pwsh -NoLogo -NoProfile -File $Path @Arguments 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed: $($Output.Trim())"
    }
    try { return ConvertFrom-StableJson ([string]$Output) }
    catch { throw "$Label returned invalid JSON: $($_.Exception.Message)" }
}

function Write-JsonAtomically {
    param([object]$Value, [string]$Path)
    $Temporary = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        $Json = ($Value | ConvertTo-Json -Depth 12).Replace("`r`n", "`n").Replace("`r", "`n") + "`n"
        [IO.File]::WriteAllText($Temporary, $Json, [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($Temporary, $Path, $true)
    }
    finally { if (Test-Path -LiteralPath $Temporary) { Remove-Item -LiteralPath $Temporary -Force } }
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
    throw "Guard '$GuardId' digest/lock binding is invalid; keep the lock active and investigate tampering."
}

$Guard = ConvertFrom-StableJson (Get-Content -LiteralPath $GuardPath -Raw)
Assert-ExactProperties $Guard @(
    'schemaVersion', 'guardId', 'story', 'actor', 'mode', 'createdAt',
    'allowedPaths', 'inputs', 'workspace'
) 'handoff guard'
if ($Guard.schemaVersion -ne 1 -or $Guard.guardId -cne $GuardId -or
    $Guard.story -cnotmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
    throw 'Handoff guard identity/schema is invalid.'
}
$ContractPath = Join-Path $ProjectRoot 'schemas/pipeline-contract.json'
if (-not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) {
    throw "Pipeline contract not found: $ContractPath"
}
$Contract = ConvertFrom-StableJson (Get-Content -LiteralPath $ContractPath -Raw)
$ContractChecker = Join-Path $PSScriptRoot 'Test-PipelineContract.ps1'
if (-not (Test-Path -LiteralPath $ContractChecker -PathType Leaf)) {
    throw "Pipeline contract validator not found: $ContractChecker"
}
$ContractReceipt = Invoke-JsonChecker $ContractChecker @(
    '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
) 'pipeline contract validation'
if ($ContractReceipt.passed -ne $true) {
    throw 'Pipeline contract failed strict schema/semantic validation.'
}
$ModeProperty = @($Contract.handoffLedger.modeContracts.PSObject.Properties |
    Where-Object Name -CEQ ([string]$Guard.mode))
if ($ModeProperty.Count -ne 1) { throw "Guard uses unsupported mode '$($Guard.mode)'." }
$ModeContract = $ModeProperty[0].Value
if ($Guard.actor -cne [string]$ModeContract.actor -or
    $Status -cnotin @($ModeContract.statuses)) {
    throw "Guard actor/status is not permitted for mode '$($Guard.mode)'."
}
$ExpectedAllowed = @($ModeContract.allowedOutputs | ForEach-Object {
    Expand-StoryPath ([string]$_) ([string]$Guard.story)
} | Sort-Object -Unique)
$ActualAllowed = @($Guard.allowedPaths | ForEach-Object { [string]$_ } | Sort-Object -Unique)
if (@($ExpectedAllowed | Where-Object { $_ -cnotin $ActualAllowed }).Count -gt 0 -or
    @($ActualAllowed | Where-Object { $_ -cnotin $ExpectedAllowed }).Count -gt 0) {
    throw 'Persisted guard output allowlist no longer matches the central mode contract.'
}
$InputPaths = [Collections.Generic.List[string]]::new()
foreach ($Input in @($Guard.inputs)) {
    Assert-ExactProperties $Input @('path', 'sha256') 'handoff guard input'
    $Relative = Get-SafeRelativePath $ProjectRoot ([string]$Input.path) 'Handoff input'
    if ($Relative -cne [string]$Input.path -or
        [string]$Input.sha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw "Guard contains an unsafe or invalid input record '$($Input.path)'."
    }
    $InputPaths.Add($Relative)
}
if (@($InputPaths | Group-Object -CaseSensitive | Where-Object Count -gt 1).Count -gt 0) {
    throw 'Guard contains duplicate input paths.'
}
$ExpectedInputs = @($ModeContract.requiredInputs | ForEach-Object {
    Expand-StoryPath ([string]$_) ([string]$Guard.story)
} | Sort-Object)
$ActualInputs = @($InputPaths | Sort-Object)
if (@($ExpectedInputs | Where-Object { $_ -cnotin $ActualInputs }).Count -gt 0 -or
    @($ActualInputs | Where-Object { $_ -cnotin $ExpectedInputs }).Count -gt 0) {
    throw 'Persisted guard inputs no longer match the central mode contract.'
}
foreach ($Snapshot in @($Guard.workspace)) {
    Assert-ExactProperties $Snapshot @('path', 'sha256') 'handoff guard workspace item'
    $Relative = Get-SafeRelativePath $ProjectRoot ([string]$Snapshot.path) 'Workspace snapshot'
    if ($Relative -cne [string]$Snapshot.path -or
        [string]$Snapshot.sha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw "Guard contains an unsafe or invalid workspace record '$($Snapshot.path)'."
    }
}
if (@($Guard.workspace | Group-Object path -CaseSensitive | Where-Object Count -gt 1).Count -gt 0) {
    throw 'Guard contains duplicate workspace paths.'
}
$NormalizedReport = $ReportText.Replace("`r`n", "`n").Replace("`r", "`n")
if ([string]::IsNullOrWhiteSpace($NormalizedReport) -or
    $NormalizedReport.Length -gt 200000) {
    throw 'ReportText must contain 1-200000 characters of exact handoff content.'
}
if (-not $NormalizedReport.EndsWith("`n", [StringComparison]::Ordinal) -or
    $NormalizedReport.EndsWith("`n`n", [StringComparison]::Ordinal)) {
    throw 'ReportText must use exactly one trailing LF terminator.'
}
if ((Get-ReportField $NormalizedReport 'story') -cne [string]$Guard.story -or
    (Get-ReportField $NormalizedReport 'mode') -cne [string]$Guard.mode -or
    (Get-ReportField $NormalizedReport 'status') -cne $Status) {
    throw 'ReportText story/mode/status does not match the active guard completion.'
}
$ResolutionOwner = Get-ReportField $NormalizedReport 'resolutionOwner'
$ErrorCode = Get-ReportField $NormalizedReport 'errorCode'
$ResolutionQuestion = Get-ReportField $NormalizedReport 'resolutionQuestion'
switch ($Status) {
    'READY' {
        if ($ErrorCode -cne 'none' -or $ResolutionQuestion -cne 'none' -or
            $ResolutionOwner -ceq 'user') {
            throw 'READY report must be mechanically resolved with errorCode/resolutionQuestion none.'
        }
    }
    'HANDOFF_ERROR' {
        if ($ErrorCode -ceq 'none' -or $ResolutionOwner -ceq 'user') {
            throw 'HANDOFF_ERROR must identify a mechanical error code and non-user owner.'
        }
    }
    'USER_RULING_REQUIRED' {
        if ($ResolutionOwner -cne 'user' -or $ResolutionQuestion -ceq 'none') {
            throw 'USER_RULING_REQUIRED must assign one exact non-empty question to the user.'
        }
    }
    'NAME_REGISTRATION_REQUIRED' {
        if ($ResolutionOwner -cne 'coordinator' -or $ErrorCode -cne 'none' -or
            $ResolutionQuestion -cne 'none') {
            throw 'NAME_REGISTRATION_REQUIRED must route exact proposals to the coordinator.'
        }
    }
}
$ExpectedLedgerPath = "stories/$($Guard.story)/handoffs.json"
if ((Get-ReportField $NormalizedReport 'handoffLedger') -cne $ExpectedLedgerPath) {
    throw 'ReportText handoffLedger path does not match the guarded story.'
}
$GuardLedgerSha256 = Get-GuardInputSha256 $Guard $ExpectedLedgerPath
Assert-ReportDigestField $NormalizedReport 'handoffLedgerSha256' $GuardLedgerSha256
$GuardLedgerFullPath = Join-Path $ProjectRoot $ExpectedLedgerPath
$ReportBytes = [Text.UTF8Encoding]::new($false).GetBytes($NormalizedReport)
$ReportSha256 = [Convert]::ToHexString(
    [Security.Cryptography.SHA256]::HashData($ReportBytes)
).ToLowerInvariant()
if ((Get-RawSha256 $GuardLedgerFullPath) -cne $GuardLedgerSha256) {
    if (-not $RecoverCommittedGuard) {
        throw 'The handoff ledger changed after the guard opened. Use -RecoverCommittedGuard only to verify and clean up a fully committed prior append.'
    }
    $RecoveredLedger = ConvertFrom-StableJson (Get-Content -LiteralPath $GuardLedgerFullPath -Raw)
    Assert-ExactProperties $RecoveredLedger @('schemaVersion', 'storySlug', 'chainHead', 'entries') 'recovery handoffs.json'
    $RecoveredEntries = @($RecoveredLedger.entries | Where-Object guardId -CEQ $GuardId)
    if ($RecoveredLedger.schemaVersion -ne $Contract.handoffLedger.schemaVersion -or
        $RecoveredLedger.storySlug -cne [string]$Guard.story -or
        $RecoveredEntries.Count -ne 1) {
        throw 'Committed-guard recovery found no unique schema-current ledger entry.'
    }
    $RecoveredEntry = $RecoveredEntries[0]
    Assert-ExactProperties $RecoveredEntry @($Contract.handoffLedger.entryFields) 'recovery ledger entry'
    if ($RecoveredEntry.story -cne [string]$Guard.story -or
        $RecoveredEntry.actor -cne [string]$Guard.actor -or
        $RecoveredEntry.persister -cne [string]$ModeContract.persister -or
        $RecoveredEntry.mode -cne [string]$Guard.mode -or
        $RecoveredEntry.status -cne $Status -or
        $RecoveredEntry.report -cne $NormalizedReport -or
        $RecoveredEntry.reportSha256 -cne $ReportSha256) {
        throw 'Committed-guard recovery entry does not match the retained guard/report.'
    }
    $RecoveredInputMap = @{}; foreach ($Item in @($RecoveredEntry.inputs)) {
        $RecoveredInputMap[[string]$Item.path] = [string]$Item.sha256
    }
    foreach ($Item in @($Guard.inputs)) {
        if (-not $RecoveredInputMap.ContainsKey([string]$Item.path) -or
            $RecoveredInputMap[[string]$Item.path] -cne [string]$Item.sha256) {
            throw 'Committed-guard recovery entry does not preserve the guarded inputs.'
        }
    }
    $RecoveryBefore = @{}; foreach ($Item in @($Guard.workspace)) {
        $RecoveryBefore[[string]$Item.path] = [string]$Item.sha256
    }
    $RecoveryAfter = @{}; foreach ($Item in @(Get-WorkspaceSnapshot $ProjectRoot)) {
        $RecoveryAfter[[string]$Item.path] = [string]$Item.sha256
    }
    $RecoveryChanged = @(@($RecoveryBefore.Keys) + @($RecoveryAfter.Keys) |
        Sort-Object -Unique | Where-Object {
            -not $RecoveryBefore.ContainsKey($_) -or -not $RecoveryAfter.ContainsKey($_) -or
            $RecoveryBefore[$_] -cne $RecoveryAfter[$_]
        })
    $RecoveryAllowed = @(@($Guard.allowedPaths) + $ExpectedLedgerPath)
    $RecoveryUnauthorized = @($RecoveryChanged | Where-Object { $_ -cnotin $RecoveryAllowed })
    if ($RecoveryUnauthorized.Count -gt 0) {
        throw "Committed-guard recovery found unrelated changes: $($RecoveryUnauthorized -join ', ')."
    }
    foreach ($Output in @($RecoveredEntry.outputs)) {
        if ([string]$Output.path -cnotin @($Guard.allowedPaths) -or
            $Output.beforeSha256 -cne $(if ($RecoveryBefore.ContainsKey([string]$Output.path)) {
                $RecoveryBefore[[string]$Output.path]
            } else { $null }) -or
            $Output.afterSha256 -cne $(if ($RecoveryAfter.ContainsKey([string]$Output.path)) {
                $RecoveryAfter[[string]$Output.path]
            } else { $null })) {
            throw 'Committed-guard recovery output does not match retained before/current bytes.'
        }
    }
    $RecoveryChecker = Join-Path $PSScriptRoot 'Test-StoryHandoffs.ps1'
    $RecoveryReceipt = Invoke-JsonChecker $RecoveryChecker @(
        '-Story', [string]$Guard.story, '-OutputFormat', 'Json',
        '-ProjectRoot', $ProjectRoot
    ) 'committed-guard recovery validation'
    if ($RecoveryReceipt.passed -ne $true -or
        $RecoveryReceipt.ledgerSha256 -cne (Get-RawSha256 $GuardLedgerFullPath)) {
        throw 'Committed-guard recovery ledger failed complete strict validation.'
    }
    Remove-Item -LiteralPath $GuardPath -Force
    Remove-Item -LiteralPath $LockPath -Force
    [ordered]@{
        schemaVersion = 1
        story = [string]$Guard.story
        guardId = $GuardId
        recoveredCommittedAppend = $true
        ledgerSha256 = Get-RawSha256 $GuardLedgerFullPath
        chainHead = [string]$RecoveredLedger.chainHead
    } | ConvertTo-Json -Depth 5
    return
}
$GuardLedgerRaw = Get-Content -LiteralPath $GuardLedgerFullPath -Raw
$GuardLedgerSnapshot = ConvertFrom-StableJson $GuardLedgerRaw
if ($GuardLedgerSnapshot.schemaVersion -ne $Contract.handoffLedger.schemaVersion -or
    $GuardLedgerSnapshot.storySlug -cne [string]$Guard.story) {
    throw 'The guarded pre-handoff ledger has an invalid identity or schema.'
}
$ExpectedReportHead = if ($null -eq $GuardLedgerSnapshot.chainHead) { 'none' } else {
    [string]$GuardLedgerSnapshot.chainHead
}
if ($Guard.mode -in @('RESEARCH_CANON', 'REVIEW_DRAFT', 'REVIEW_FINAL') -and
    (Get-ReportField $NormalizedReport 'handoffLedgerChainHead') -cne $ExpectedReportHead) {
    throw 'ReportText handoffLedgerChainHead does not match the guarded pre-handoff ledger.'
}
$Before = @{}; foreach ($Item in @($Guard.workspace)) { $Before[[string]$Item.path] = [string]$Item.sha256 }
$AfterItems = @(Get-WorkspaceSnapshot $ProjectRoot)
$After = @{}; foreach ($Item in $AfterItems) { $After[[string]$Item.path] = [string]$Item.sha256 }
$AllPaths = @(@($Before.Keys) + @($After.Keys) | Sort-Object -Unique)
$Changed = @($AllPaths | Where-Object {
    -not $Before.ContainsKey($_) -or -not $After.ContainsKey($_) -or $Before[$_] -cne $After[$_]
})
$Unauthorized = @($Changed | Where-Object { $_ -cnotin @($Guard.allowedPaths) })
if ($Unauthorized.Count -gt 0) {
    throw "Guarded handoff modified unauthorized path(s): $($Unauthorized -join ', '). Guard remains active for repair or explicit abort."
}

$Outputs = @($Changed | Sort-Object | ForEach-Object {
    [ordered]@{
        path = $_
        beforeSha256 = if ($Before.ContainsKey($_)) { $Before[$_] } else { $null }
        afterSha256 = if ($After.ContainsKey($_)) { $After[$_] } else { $null }
    }
})
$OutputMap = @{}; foreach ($Output in $Outputs) { $OutputMap[[string]$Output.path] = $Output }
$StoryPrefix = "stories/$($Guard.story)"
switch -Regex ([string]$Guard.mode) {
    '^RESEARCH_CANON$' {
        Assert-ReportDigestField $NormalizedReport 'sourcePromptSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/00-prompt.md")
        Assert-ReportDigestField $NormalizedReport 'authorityManifestSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/authority.json")
        $Bodies = @([regex]::Matches(
            $NormalizedReport,
            '(?ms)^BEGIN_FILE_CONTENT[ \t]*\n(?<body>.*?)^END_FILE_CONTENT[ \t]*(?:\n|\z)'
        ))
        if ($Status -eq 'READY') {
            if ($Bodies.Count -ne 1) { throw 'READY canon research must contain one bounded file body.' }
            $ExpectedBodyBytes = [Text.UTF8Encoding]::new($false).GetBytes(
                $Bodies[0].Groups['body'].Value
            )
            $BodySha256 = [Convert]::ToHexString(
                [Security.Cryptography.SHA256]::HashData($ExpectedBodyBytes)
            ).ToLowerInvariant()
            if (-not $OutputMap.ContainsKey("$StoryPrefix/01-canon-brief.md") -or
                $OutputMap["$StoryPrefix/01-canon-brief.md"].afterSha256 -cne $BodySha256) {
                throw 'Persisted canon brief bytes do not equal the exact librarian payload body.'
            }
        }
        elseif ($Bodies.Count -ne 0) {
            throw 'Non-READY canon research cannot persist a speculative file body.'
        }
    }
    '^(CREATE|REVISE)_PLAN$' {
        $PlanPath = "$StoryPrefix/02-story-plan.md"
        $PlanBefore = Get-GuardBaselineSha256 $Guard $PlanPath
        Assert-ReportDigestField $NormalizedReport 'inputPromptSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/00-prompt.md")
        Assert-ReportDigestField $NormalizedReport 'inputCanonBriefSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/01-canon-brief.md")
        Assert-ReportDigestField $NormalizedReport 'beforePlanSha256' $PlanBefore
        if ($Guard.mode -ceq 'CREATE_PLAN') {
            Assert-ReportDigestField $NormalizedReport 'planScaffoldSha256' $PlanBefore
        }
        Assert-ReportDigestField $NormalizedReport 'newPlanSha256' `
            $(if ($After.ContainsKey($PlanPath)) { $After[$PlanPath] } else { $null })
        if ($Guard.mode -ceq 'REVISE_PLAN' -and $Status -in @('READY', 'NAME_REGISTRATION_REQUIRED') -and
            (Get-ReportField $NormalizedReport 'repairAuthorization') -ceq 'none') {
            throw 'REVISE_PLAN requires an exact accepted repair authorization.'
        }
    }
    '^(CREATE|REVISE)_DRAFT$' {
        $DraftPath = "$StoryPrefix/03-draft.md"
        $DraftBefore = Get-GuardBaselineSha256 $Guard $DraftPath
        Assert-ReportDigestField $NormalizedReport 'beforeDraftSha256' $DraftBefore
        if ($Guard.mode -ceq 'CREATE_DRAFT') {
            Assert-ReportDigestField $NormalizedReport 'draftScaffoldSha256' $DraftBefore
        }
        Assert-ReportDigestField $NormalizedReport 'newDraftSha256' `
            $(if ($After.ContainsKey($DraftPath)) { $After[$DraftPath] } else { $null })
        if ($Guard.mode -ceq 'REVISE_DRAFT' -and $Status -ceq 'READY' -and
            $NormalizedReport -cnotmatch '(?m)^-[ \t]+findingId:[ \t]*[^\r\n]+') {
            throw 'REVISE_DRAFT must disposition at least one authorizing finding.'
        }
    }
    '^(CREATE|REVISE)_FINAL$' {
        $FinalPath = "$StoryPrefix/05-story.md"
        $DeltaPath = "$StoryPrefix/06-canon-delta.md"
        $FinalBefore = Get-GuardBaselineSha256 $Guard $FinalPath
        $DeltaBefore = Get-GuardBaselineSha256 $Guard $DeltaPath
        Assert-ReportDigestField $NormalizedReport 'inputPlanSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/02-story-plan.md")
        Assert-ReportDigestField $NormalizedReport 'inputDraftSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/03-draft.md")
        Assert-ReportDigestField $NormalizedReport 'beforeStorySha256' $FinalBefore
        Assert-ReportDigestField $NormalizedReport 'beforeCanonDeltaSha256' $DeltaBefore
        if ($Guard.mode -ceq 'CREATE_FINAL') {
            Assert-ReportDigestField $NormalizedReport 'storyScaffoldSha256' $FinalBefore
            Assert-ReportDigestField $NormalizedReport 'canonDeltaScaffoldSha256' $DeltaBefore
        }
        Assert-ReportDigestField $NormalizedReport 'newStorySha256' `
            $(if ($After.ContainsKey($FinalPath)) { $After[$FinalPath] } else { $null })
        Assert-ReportDigestField $NormalizedReport 'newCanonDeltaSha256' `
            $(if ($After.ContainsKey($DeltaPath)) { $After[$DeltaPath] } else { $null })
        if ($Guard.mode -ceq 'REVISE_FINAL' -and $Status -ceq 'READY' -and
            $NormalizedReport -cnotmatch '(?m)^-[ \t]+findingId:[ \t]*[^\r\n]+') {
            throw 'REVISE_FINAL must disposition at least one authorizing finding.'
        }
    }
    '^REVIEW_(DRAFT|FINAL)$' {
        $ArtifactPath = if ($Guard.mode -ceq 'REVIEW_DRAFT') {
            "$StoryPrefix/03-draft.md"
        }
        else { "$StoryPrefix/05-story.md" }
        Assert-ReportDigestField $NormalizedReport 'artifactSha256' `
            (Get-GuardInputSha256 $Guard $ArtifactPath)
        Assert-ReportDigestField $NormalizedReport 'canonBriefSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/01-canon-brief.md")
        Assert-ReportDigestField $NormalizedReport 'planSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/02-story-plan.md")
        Assert-ReportDigestField $NormalizedReport 'authorityManifestSha256' `
            (Get-GuardInputSha256 $Guard "$StoryPrefix/authority.json")
        if ($Guard.mode -ceq 'REVIEW_FINAL') {
            Assert-ReportDigestField $NormalizedReport 'canonDeltaSha256' `
                (Get-GuardInputSha256 $Guard "$StoryPrefix/06-canon-delta.md")
        }
        if ($Status -in @('READY', 'USER_RULING_REQUIRED')) {
            $ReviewContent = Get-Content -LiteralPath (Join-Path $ProjectRoot "$StoryPrefix/04-review.md") -Raw
            if ([regex]::Matches($ReviewContent, [regex]::Escape($NormalizedReport)).Count -ne 1) {
                throw 'Persisted review history must contain the exact complete critic payload once.'
            }
        }
    }
}
if ($Status -eq 'READY' -and $Outputs.Count -eq 0) {
    throw 'A READY guarded handoff must produce at least one allowed output change.'
}
if ($Status -eq 'READY' -and [bool]$ModeContract.requireAllReadyOutputs) {
    $ChangedOutputPaths = @($Outputs | ForEach-Object { [string]$_.path })
    $MissingReadyOutputs = @($ExpectedAllowed | Where-Object { $_ -cnotin $ChangedOutputPaths })
    if ($MissingReadyOutputs.Count -gt 0) {
        throw "READY mode '$($Guard.mode)' did not change required output(s): $($MissingReadyOutputs -join ', ')."
    }
}
if ($Status -eq 'HANDOFF_ERROR' -and $Outputs.Count -gt 0) {
    throw 'HANDOFF_ERROR cannot accept modified production outputs; restore them before completion.'
}
if ($Status -eq 'NAME_REGISTRATION_REQUIRED' -and
    $Guard.mode -in @('CREATE_PLAN', 'REVISE_PLAN') -and $Outputs.Count -ne 1) {
    throw 'Plan NAME_REGISTRATION_REQUIRED must persist exactly one hash-bound proposal plan.'
}
if ($Status -eq 'USER_RULING_REQUIRED' -and
    $Guard.mode -in @('REVIEW_DRAFT', 'REVIEW_FINAL') -and $Outputs.Count -ne 1) {
    throw 'Review USER_RULING_REQUIRED must persist exactly one append-only review-history update.'
}
if ($Status -eq 'NAME_REGISTRATION_REQUIRED' -and
    $Guard.mode -cne 'CREATE_PLAN' -and $Guard.mode -cne 'REVISE_PLAN' -and
    $Outputs.Count -gt 0) {
    throw 'Only plan modes may persist an output with NAME_REGISTRATION_REQUIRED.'
}
if ($Status -eq 'USER_RULING_REQUIRED' -and
    $Guard.mode -notin @('REVIEW_DRAFT', 'REVIEW_FINAL') -and
    $Outputs.Count -gt 0) {
    throw 'Only review modes may persist an output with USER_RULING_REQUIRED.'
}

$LedgerPath = Join-Path $ProjectRoot "stories/$($Guard.story)/handoffs.json"
if (-not (Test-Path -LiteralPath $LedgerPath -PathType Leaf)) {
    throw "Handoff ledger not found: $LedgerPath"
}
$HandoffChecker = Join-Path $PSScriptRoot 'Test-StoryHandoffs.ps1'
if (-not (Test-Path -LiteralPath $HandoffChecker -PathType Leaf)) {
    throw "Handoff validator not found: $HandoffChecker"
}
$Preflight = Invoke-JsonChecker $HandoffChecker @(
    '-Story', [string]$Guard.story, '-OutputFormat', 'Json',
    '-ProjectRoot', $ProjectRoot
) 'handoff ledger preflight'
if ($Preflight.passed -ne $true -or
    $Preflight.ledgerSha256 -cne $GuardLedgerSha256) {
    throw 'Existing handoff ledger failed preflight or no longer matches the guarded snapshot.'
}
$OriginalLedgerBytes = [IO.File]::ReadAllBytes($LedgerPath)
$Ledger = ConvertFrom-StableJson (Get-Content -LiteralPath $LedgerPath -Raw)
Assert-ExactProperties $Ledger @('schemaVersion', 'storySlug', 'chainHead', 'entries') 'handoffs.json'
if ($Ledger.schemaVersion -ne $Contract.handoffLedger.schemaVersion -or
    $Ledger.storySlug -cne $Guard.story) {
    throw 'Handoff ledger identity or schema is invalid.'
}
$Previous = if ($null -eq $Ledger.chainHead) { $null } else { [string]$Ledger.chainHead }
$Entry = [pscustomobject][ordered]@{
    sequence = @($Ledger.entries).Count + 1
    story = [string]$Guard.story
    actor = [string]$Guard.actor
    mode = [string]$Guard.mode
    status = $Status
    recordedAt = [DateTimeOffset]::UtcNow.ToString('o')
    guardId = $GuardId
    persister = [string]$ModeContract.persister
    report = $NormalizedReport
    reportSha256 = $ReportSha256
    inputs = @($Guard.inputs)
    outputs = $Outputs
    previousEntrySha256 = $Previous
    entrySha256 = $null
}
$Entry.entrySha256 = Get-CanonicalEntryHash $Entry
$Entries = [Collections.Generic.List[object]]::new()
foreach ($Existing in @($Ledger.entries)) { $Entries.Add($Existing) }
$Entries.Add($Entry)
$Updated = [ordered]@{
    schemaVersion = [int]$Contract.handoffLedger.schemaVersion
    storySlug = [string]$Ledger.storySlug
    chainHead = [string]$Entry.entrySha256
    entries = @($Entries)
}
try {
    Write-JsonAtomically $Updated $LedgerPath
    $Postflight = Invoke-JsonChecker $HandoffChecker @(
        '-Story', [string]$Guard.story, '-OutputFormat', 'Json',
        '-ProjectRoot', $ProjectRoot
    ) 'handoff ledger postflight'
    if ($Postflight.passed -ne $true -or
        $Postflight.ledgerSha256 -cne (Get-RawSha256 $LedgerPath) -or
        $Postflight.chainHead -cne [string]$Entry.entrySha256) {
        throw 'Appended handoff ledger failed strict postflight validation.'
    }
    if ($Guard.mode -in @('REVIEW_DRAFT', 'REVIEW_FINAL')) {
        $ReviewContractsPath = Join-Path $PSScriptRoot 'ReviewContracts.ps1'
        if (-not (Test-Path -LiteralPath $ReviewContractsPath -PathType Leaf)) {
            throw 'Review contract validator is unavailable.'
        }
        . $ReviewContractsPath
        $ReviewContract = Get-StoryReviewContract `
            -Content (Get-Content -LiteralPath (Join-Path $ProjectRoot "$StoryPrefix/04-review.md") -Raw) `
            -StorySlug ([string]$Guard.story)
        $CurrentLedger = ConvertFrom-ReviewStableJson (Get-Content -LiteralPath $LedgerPath -Raw)
        Assert-ReviewLedgerBindings -ReviewContract $ReviewContract `
            -Ledger $CurrentLedger -StorySlug ([string]$Guard.story)
    }
}
catch {
    $AppendFailure = $_.Exception.Message
    try { Write-RawBytesAtomically $OriginalLedgerBytes $LedgerPath }
    catch { throw "Handoff append failed ($AppendFailure) and ledger rollback failed: $($_.Exception.Message)" }
    throw "Handoff append failed strict validation and was rolled back: $AppendFailure"
}

Remove-Item -LiteralPath $GuardPath -Force
Remove-Item -LiteralPath $LockPath -Force
[ordered]@{
    schemaVersion = 1
    story = [string]$Guard.story
    mode = [string]$Guard.mode
    status = $Status
    changedPaths = $Changed
    ledgerSha256 = Get-RawSha256 $LedgerPath
    chainHead = [string]$Entry.entrySha256
    reportSha256 = $ReportSha256
} | ConvertTo-Json -Depth 5
