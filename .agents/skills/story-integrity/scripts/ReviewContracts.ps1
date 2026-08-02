#Requires -Version 7.0

$script:ReviewPayloadFieldOrder = @(
    'story', 'mode', 'status', 'pass', 'reviewedArtifact',
    'artifactSha256', 'canonDeltaSha256', 'canonBriefSha256',
    'planSha256', 'scopedRegistrySha256', 'authorityManifest',
    'authorityManifestSha256', 'handoffLedger', 'handoffLedgerSha256',
    'handoffLedgerChainHead', 'reviewer', 'reviewedAt', 'reviewBasis',
    'verdict', 'blockType', 'resolutionOwner', 'resolutionQuestion',
    'errorCode', 'unresolvedCounts', 'priorFindingDispositions',
    'findings', 'certificationEligible', 'changeReport'
)

function ConvertTo-ReviewLf {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    return $Text.Replace("`r`n", "`n").Replace("`r", "`n")
}

function Get-ReviewTextSha256 {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    $Utf8 = [Text.UTF8Encoding]::new($false)
    $Hash = [Security.Cryptography.SHA256]::HashData($Utf8.GetBytes($Text))
    return [Convert]::ToHexString($Hash).ToLowerInvariant()
}

function ConvertFrom-ReviewStableJson {
    param([Parameter(Mandatory = $true)][string]$Json)

    $Parameters = @{}
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        $Parameters.DateKind = 'String'
    }
    return $Json | ConvertFrom-Json @Parameters
}

function Get-UniqueReviewSection {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    $Pattern = '(?ms)^##[ \t]+' + [regex]::Escape($Heading) +
        '[ \t]*\r?\n(?<body>.*?)(?=^##[ \t]+|\z)'
    $Matches = @([regex]::Matches($Content, $Pattern))
    if ($Matches.Count -ne 1) {
        throw "04-review.md must contain exactly one '$Heading' section; found $($Matches.Count)."
    }
    return $Matches[0].Groups['body'].Value
}

function Remove-ReviewCodeTicks {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value)

    $Trimmed = $Value.Trim()
    if ($Trimmed.Length -ge 2 -and $Trimmed.StartsWith('`') -and
        $Trimmed.EndsWith('`')) {
        return $Trimmed.Substring(1, $Trimmed.Length - 2)
    }
    return $Trimmed
}

function Get-ReviewCertificationMap {
    param([Parameter(Mandatory = $true)][string]$Section)

    $RequiredLabels = @(
        'Reviewed artifact', 'Artifact SHA-256', 'Canon delta SHA-256',
        'Review pass', 'Verdict', 'Reviewer',
        'Unresolved Critical findings', 'Unresolved Major findings', 'Updated'
    )
    $Map = @{}
    $BulletMatches = @([regex]::Matches(
        $Section,
        '(?m)^-[ \t]+(?<label>[^:\r\n]+):[ \t]*(?<value>[^\r\n]*)\r?$'
    ))
    foreach ($Match in $BulletMatches) {
        $Label = $Match.Groups['label'].Value.Trim()
        if ($Label -cnotin $RequiredLabels) {
            throw "Current certification contains unknown field '$Label'."
        }
        if ($Map.ContainsKey($Label)) {
            throw "Current certification duplicates field '$Label'."
        }
        $Map[$Label] = Remove-ReviewCodeTicks $Match.Groups['value'].Value
    }
    foreach ($Label in $RequiredLabels) {
        if (-not $Map.ContainsKey($Label)) {
            throw "Current certification is missing '$Label'."
        }
    }
    if ($Map.Count -ne $RequiredLabels.Count) {
        throw 'Current certification has an ambiguous field set.'
    }
    return $Map
}

function Get-ReviewPayloadFields {
    param([Parameter(Mandatory = $true)][string]$Body)

    $RequiredKeys = @($script:ReviewPayloadFieldOrder)
    $Normalized = ConvertTo-ReviewLf $Body
    $Fields = [System.Collections.Generic.List[object]]::new()
    $Current = $null
    foreach ($Line in @($Normalized.Split([char]10))) {
        if ($Line -match '^(?<key>[A-Za-z][A-Za-z0-9]*):[ \t]*(?<value>.*)$') {
            $Current = [pscustomobject]@{
                Key = $Matches['key']
                Inline = $Matches['value']
                Continuation = [System.Collections.Generic.List[string]]::new()
            }
            $Fields.Add($Current)
            continue
        }
        if ($null -eq $Current) {
            if (-not [string]::IsNullOrWhiteSpace($Line)) {
                throw "Review payload has content before its first machine field: '$Line'."
            }
            continue
        }
        $Current.Continuation.Add($Line)
    }

    if ($Fields.Count -ne $RequiredKeys.Count) {
        throw "Review payload must contain exactly $($RequiredKeys.Count) machine fields; found $($Fields.Count)."
    }
    $Map = @{}
    for ($Index = 0; $Index -lt $RequiredKeys.Count; $Index++) {
        $Expected = $RequiredKeys[$Index]
        $Field = $Fields[$Index]
        if ($Field.Key -cne $Expected) {
            throw "Review payload field $($Index + 1) must be '$Expected'; found '$($Field.Key)'."
        }
        if ($Map.ContainsKey($Field.Key)) {
            throw "Review payload duplicates field '$($Field.Key)'."
        }

        $ContinuationLines = @($Field.Continuation)
        while ($ContinuationLines.Count -gt 0 -and
            [string]::IsNullOrWhiteSpace($ContinuationLines[-1])) {
            if ($ContinuationLines.Count -eq 1) { $ContinuationLines = @() }
            else { $ContinuationLines = @($ContinuationLines[0..($ContinuationLines.Count - 2)]) }
        }
        $Map[$Field.Key] = [pscustomobject]@{
            Inline = $Field.Inline.Trim()
            Continuation = $ContinuationLines
        }
    }
    return $Map
}

function Get-ReviewScalarValue {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Fields,
        [Parameter(Mandatory = $true)][string]$Key,
        [switch]$AllowWrapped
    )

    $Field = $Fields[$Key]
    $NonblankContinuation = @($Field.Continuation | Where-Object {
        -not [string]::IsNullOrWhiteSpace($_)
    })
    if (-not $AllowWrapped -and $NonblankContinuation.Count -gt 0) {
        throw "Review payload scalar '$Key' must be on one line."
    }
    if ($AllowWrapped) {
        foreach ($Line in $NonblankContinuation) {
            if ($Line -notmatch '^[ \t]+') {
                throw "Wrapped review payload scalar '$Key' must indent continuation lines."
            }
        }
    }
    $Parts = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($Field.Inline)) {
        $Parts.Add($Field.Inline.Trim())
    }
    foreach ($Line in $NonblankContinuation) { $Parts.Add($Line.Trim()) }
    $Value = ($Parts -join ' ').Trim()
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Review payload field '$Key' must not be empty."
    }
    return $Value
}

function Get-ReviewStructuredValue {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Fields,
        [Parameter(Mandatory = $true)][string]$Key
    )

    $Field = $Fields[$Key]
    $Lines = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($Field.Inline)) {
        $Lines.Add($Field.Inline.Trim())
    }
    foreach ($Line in @($Field.Continuation)) {
        if (-not [string]::IsNullOrWhiteSpace($Line)) { $Lines.Add($Line) }
    }
    $Value = ($Lines -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "Review payload field '$Key' must contain an explicit list or 'none'."
    }
    return $Value
}

function Get-ReviewStructuredItemBlocks {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$ItemLabel,
        [Parameter(Mandatory = $true)][string]$Context
    )

    if ($Value -ceq 'none') { return @() }
    $Pattern = '(?ms)^[ \t]*-[ \t]+' + [regex]::Escape($ItemLabel) +
        ':[ \t]*[^;\r\n]+.*?(?=^[ \t]*-[ \t]+' +
        [regex]::Escape($ItemLabel) + ':|\z)'
    $ItemMatches = @([regex]::Matches($Value, $Pattern))
    if ($ItemMatches.Count -eq 0) {
        throw "$Context must be 'none' or a structured list of '$ItemLabel' items."
    }
    $Prefix = $Value.Substring(0, $ItemMatches[0].Index)
    if (-not [string]::IsNullOrWhiteSpace($Prefix)) {
        throw "$Context contains prose outside its structured item list."
    }
    return @($ItemMatches | ForEach-Object { $_.Value.Trim() })
}

function Get-ReviewStructuredItemField {
    param(
        [Parameter(Mandatory = $true)][string]$Block,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Context
    )

    $Pattern = '(?m)(?:^[ \t]*(?:-[ \t]+)?|;[ \t]*)' +
        [regex]::Escape($Label) + ':[ \t]*(?<value>[^;\r\n]+)'
    $FieldMatches = @([regex]::Matches($Block, $Pattern))
    if ($FieldMatches.Count -ne 1) {
        throw "$Context must contain exactly one '$Label' field."
    }
    $Result = $FieldMatches[0].Groups['value'].Value.Trim()
    if ([string]::IsNullOrWhiteSpace($Result) -or $Result -match '^<.*>$') {
        throw "$Context field '$Label' must not be empty or placeholder text."
    }
    return $Result
}

function ConvertFrom-ReviewFindings {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][int]$Pass
    )

    $Blocks = @(Get-ReviewStructuredItemBlocks -Value $Value `
        -ItemLabel 'findingId' -Context "Review pass $Pass findings")
    $Ids = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $Items = [Collections.Generic.List[object]]::new()
    foreach ($Block in $Blocks) {
        $Context = "Review pass $Pass finding"
        $Id = Get-ReviewStructuredItemField $Block 'findingId' $Context
        if ($Id -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$') {
            throw "$Context has invalid findingId '$Id'."
        }
        if (-not $Ids.Add($Id)) {
            throw "Review pass $Pass duplicates findingId '$Id'."
        }
        $Lane = Get-ReviewStructuredItemField $Block 'lane' "$Context '$Id'"
        $Severity = Get-ReviewStructuredItemField $Block 'severity' "$Context '$Id'"
        if ($Severity -cnotin @('Critical', 'Major', 'Minor', 'Optional')) {
            throw "Review pass $Pass finding '$Id' has invalid severity '$Severity'."
        }
        $Location = Get-ReviewStructuredItemField $Block 'location' "$Context '$Id'"
        $Evidence = Get-ReviewStructuredItemField $Block 'evidence' "$Context '$Id'"
        $Why = Get-ReviewStructuredItemField $Block 'whyItMatters' "$Context '$Id'"
        $Fix = Get-ReviewStructuredItemField $Block 'smallestEffectiveFix' "$Context '$Id'"
        $Items.Add([pscustomobject][ordered]@{
            FindingId = $Id
            Lane = $Lane
            Severity = $Severity
            Location = $Location
            Evidence = $Evidence
            WhyItMatters = $Why
            SmallestEffectiveFix = $Fix
        })
    }
    return @($Items)
}

function ConvertFrom-ReviewPriorFindingDispositions {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][int]$Pass
    )

    $Blocks = @(Get-ReviewStructuredItemBlocks -Value $Value `
        -ItemLabel 'findingId' `
        -Context "Review pass $Pass priorFindingDispositions")
    $Ids = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $Items = [Collections.Generic.List[object]]::new()
    foreach ($Block in $Blocks) {
        $Context = "Review pass $Pass prior finding disposition"
        $Id = Get-ReviewStructuredItemField $Block 'findingId' $Context
        if ($Id -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$') {
            throw "$Context has invalid findingId '$Id'."
        }
        if (-not $Ids.Add($Id)) {
            throw "Review pass $Pass duplicates prior findingId '$Id'."
        }
        $Disposition = Get-ReviewStructuredItemField `
            $Block 'disposition' "$Context '$Id'"
        if ($Disposition -cnotin @('RESOLVED', 'STILL_OPEN', 'SUPERSEDED')) {
            throw "Review pass $Pass prior finding '$Id' has invalid disposition '$Disposition'."
        }
        $Evidence = Get-ReviewStructuredItemField $Block 'evidence' "$Context '$Id'"
        $Items.Add([pscustomobject][ordered]@{
            FindingId = $Id
            Disposition = $Disposition
            Evidence = $Evidence
        })
    }
    return @($Items)
}

function Test-ReviewTimestamp {
    param(
        [Parameter(Mandatory = $true)][string]$Value,
        [Parameter(Mandatory = $true)][string]$Context
    )

    if ($Value -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$') {
        throw "$Context must be an ISO-8601 timestamp with an explicit offset."
    }
    $Parsed = [DateTimeOffset]::MinValue
    $Valid = [DateTimeOffset]::TryParse(
        $Value,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::RoundtripKind,
        [ref]$Parsed
    )
    if (-not $Valid) {
        throw "$Context is not a valid calendar timestamp."
    }
}

function ConvertFrom-ReviewPassPayload {
    param(
        [Parameter(Mandatory = $true)][string]$StorySlug,
        [Parameter(Mandatory = $true)][int]$HeadingPass,
        [Parameter(Mandatory = $true)][string]$PayloadBody
    )

    $Fields = Get-ReviewPayloadFields $PayloadBody
    $Story = Get-ReviewScalarValue $Fields 'story'
    $Mode = Get-ReviewScalarValue $Fields 'mode'
    $Status = Get-ReviewScalarValue $Fields 'status'
    $PassText = Get-ReviewScalarValue $Fields 'pass'
    $ReviewedArtifact = Get-ReviewScalarValue $Fields 'reviewedArtifact'
    $ArtifactSha256 = Get-ReviewScalarValue $Fields 'artifactSha256'
    $CanonDeltaSha256 = Get-ReviewScalarValue $Fields 'canonDeltaSha256'
    $CanonBriefSha256 = Get-ReviewScalarValue $Fields 'canonBriefSha256'
    $PlanSha256 = Get-ReviewScalarValue $Fields 'planSha256'
    $ScopedRegistrySha256 = Get-ReviewScalarValue $Fields 'scopedRegistrySha256'
    $AuthorityManifest = Get-ReviewScalarValue $Fields 'authorityManifest'
    $AuthorityManifestSha256 = Get-ReviewScalarValue $Fields 'authorityManifestSha256'
    $HandoffLedger = Get-ReviewScalarValue $Fields 'handoffLedger'
    $HandoffLedgerSha256 = Get-ReviewScalarValue $Fields 'handoffLedgerSha256'
    $HandoffLedgerChainHead = Get-ReviewScalarValue $Fields 'handoffLedgerChainHead'
    $Reviewer = Get-ReviewScalarValue $Fields 'reviewer'
    $ReviewedAt = Get-ReviewScalarValue $Fields 'reviewedAt'
    $ReviewBasis = Get-ReviewScalarValue $Fields 'reviewBasis' -AllowWrapped
    $Verdict = Get-ReviewScalarValue $Fields 'verdict'
    $BlockType = Get-ReviewScalarValue $Fields 'blockType'
    $ResolutionOwner = Get-ReviewScalarValue $Fields 'resolutionOwner'
    $ResolutionQuestion = Get-ReviewScalarValue $Fields 'resolutionQuestion' -AllowWrapped
    $ErrorCode = Get-ReviewScalarValue $Fields 'errorCode'
    $UnresolvedCounts = Get-ReviewScalarValue $Fields 'unresolvedCounts'
    $PriorFindingDispositions = Get-ReviewStructuredValue $Fields 'priorFindingDispositions'
    $Findings = Get-ReviewStructuredValue $Fields 'findings'
    $CertificationEligibleText = Get-ReviewScalarValue $Fields 'certificationEligible'
    $ChangeReport = Get-ReviewScalarValue $Fields 'changeReport'

    if ($Story -cne $StorySlug) {
        throw "Review pass $HeadingPass belongs to story '$Story', not '$StorySlug'."
    }
    if ($Mode -cnotin @('REVIEW_DRAFT', 'REVIEW_FINAL')) {
        throw "Review pass $HeadingPass has invalid mode '$Mode'."
    }
    if ($Status -cnotin @('READY', 'USER_RULING_REQUIRED')) {
        throw "Persisted review pass $HeadingPass has non-persistable status '$Status'."
    }
    if ($PassText -cnotmatch '^[1-9]\d*$' -or [int64]$PassText -ne $HeadingPass) {
        throw "Review pass heading $HeadingPass does not exactly match payload pass '$PassText'."
    }
    if ($ReviewedArtifact -cnotin @('03-draft.md', '05-story.md')) {
        throw "Review pass $HeadingPass has invalid reviewedArtifact '$ReviewedArtifact'."
    }
    if ($ArtifactSha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw "Review pass $HeadingPass artifactSha256 must be a lowercase SHA-256 digest."
    }
    if ($ReviewedArtifact -ceq '03-draft.md') {
        if ($CanonDeltaSha256 -cne 'not-applicable') {
            throw "Draft review pass $HeadingPass must use canonDeltaSha256 'not-applicable'."
        }
    }
    elseif ($CanonDeltaSha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw "Final review pass $HeadingPass canonDeltaSha256 must be a lowercase SHA-256 digest."
    }
    $ExpectedArtifactForMode = if ($Mode -ceq 'REVIEW_DRAFT') {
        '03-draft.md'
    }
    else { '05-story.md' }
    if ($ReviewedArtifact -cne $ExpectedArtifactForMode) {
        throw "Review pass $HeadingPass mode '$Mode' does not match reviewedArtifact '$ReviewedArtifact'."
    }
    foreach ($DigestSpec in @(
        [pscustomobject]@{ Name = 'canonBriefSha256'; Value = $CanonBriefSha256 },
        [pscustomobject]@{ Name = 'planSha256'; Value = $PlanSha256 },
        [pscustomobject]@{ Name = 'scopedRegistrySha256'; Value = $ScopedRegistrySha256 },
        [pscustomobject]@{ Name = 'authorityManifestSha256'; Value = $AuthorityManifestSha256 },
        [pscustomobject]@{ Name = 'handoffLedgerSha256'; Value = $HandoffLedgerSha256 },
        [pscustomobject]@{ Name = 'handoffLedgerChainHead'; Value = $HandoffLedgerChainHead }
    )) {
        if ($DigestSpec.Value -cnotmatch '^[a-f0-9]{64}$') {
            throw "Review pass $HeadingPass $($DigestSpec.Name) must be a lowercase SHA-256 digest."
        }
    }
    if ($AuthorityManifest -cne "stories/$StorySlug/authority.json") {
        throw "Review pass $HeadingPass authorityManifest path is not exact."
    }
    if ($HandoffLedger -cne "stories/$StorySlug/handoffs.json") {
        throw "Review pass $HeadingPass handoffLedger path is not exact."
    }
    if ($Reviewer -cne 'continuity_critic') {
        throw "Review pass $HeadingPass reviewer must be continuity_critic."
    }
    Test-ReviewTimestamp $ReviewedAt "Review pass $HeadingPass reviewedAt"
    if ([string]::IsNullOrWhiteSpace($ReviewBasis) -or $ReviewBasis -match '^<.*>$') {
        throw "Review pass $HeadingPass reviewBasis is missing or placeholder text."
    }
    if ($Verdict -cnotin @('PASS', 'REVISE', 'BLOCK')) {
        throw "Review pass $HeadingPass has invalid verdict '$Verdict'."
    }
    if ($ErrorCode -cne 'none') {
        throw "Persisted review pass $HeadingPass errorCode must be none."
    }
    if ($UnresolvedCounts -cnotmatch '^\{\s*critical:\s*(?<critical>0|[1-9]\d*),\s*major:\s*(?<major>0|[1-9]\d*),\s*minor:\s*(?<minor>0|[1-9]\d*)\s*\}$') {
        throw "Review pass $HeadingPass unresolvedCounts is malformed."
    }
    $Critical = [int64]$Matches['critical']
    $Major = [int64]$Matches['major']
    $Minor = [int64]$Matches['minor']
    if ($CertificationEligibleText -cnotin @('true', 'false')) {
        throw "Review pass $HeadingPass certificationEligible must be lowercase true or false."
    }
    $CertificationEligible = $CertificationEligibleText -ceq 'true'
    if ($ChangeReport -cne 'read-only; no files changed') {
        throw "Review pass $HeadingPass changeReport must be 'read-only; no files changed'."
    }

    $RepairOwners = if ($Mode -ceq 'REVIEW_DRAFT') {
        @('coordinator', 'canon_librarian', 'story_architect', 'prose_writer')
    }
    else {
        @('coordinator', 'canon_librarian', 'story_architect', 'story_editor')
    }
    switch ($Verdict) {
        'PASS' {
            if ($Status -cne 'READY' -or $BlockType -cne 'NONE' -or
                $ResolutionOwner -cne 'coordinator' -or
                $ResolutionQuestion -cne 'none' -or $Critical -ne 0 -or
                $Major -ne 0 -or -not $CertificationEligible) {
                throw "Review pass $HeadingPass PASS has inconsistent blockers, ownership, counts, or eligibility."
            }
        }
        'REVISE' {
            if ($Status -cne 'READY' -or $BlockType -cne 'NONE' -or
                $ResolutionOwner -cnotin $RepairOwners -or
                $ResolutionQuestion -cne 'none' -or $Critical -ne 0 -or
                $Major -lt 1 -or $CertificationEligible) {
                throw "Review pass $HeadingPass REVISE has inconsistent blockers, ownership, counts, or eligibility."
            }
        }
        'BLOCK' {
            if ($CertificationEligible -or $Critical -lt 1 -or
                $BlockType -cnotin @('REPAIRABLE', 'USER_RULING_REQUIRED')) {
                throw "Review pass $HeadingPass BLOCK has inconsistent type, counts, or eligibility."
            }
            if ($BlockType -ceq 'REPAIRABLE' -and
                ($Status -cne 'READY' -or $ResolutionOwner -cnotin $RepairOwners -or
                $ResolutionQuestion -cne 'none')) {
                throw "Review pass $HeadingPass repairable BLOCK has inconsistent ownership or question."
            }
            if ($BlockType -ceq 'USER_RULING_REQUIRED' -and
                ($Status -cne 'USER_RULING_REQUIRED' -or
                $ResolutionOwner -cne 'user' -or $ResolutionQuestion -ceq 'none')) {
                throw "Review pass $HeadingPass user-ruling BLOCK lacks user ownership or an exact question."
            }
        }
    }
    $FindingItems = @(ConvertFrom-ReviewFindings -Value $Findings -Pass $HeadingPass)
    $PriorDispositionItems = @(ConvertFrom-ReviewPriorFindingDispositions `
        -Value $PriorFindingDispositions -Pass $HeadingPass)
    $ComputedCritical = @($FindingItems | Where-Object Severity -ceq 'Critical').Count
    $ComputedMajor = @($FindingItems | Where-Object Severity -ceq 'Major').Count
    $ComputedMinor = @($FindingItems | Where-Object Severity -ceq 'Minor').Count
    if ($Critical -ne $ComputedCritical -or $Major -ne $ComputedMajor -or
        $Minor -ne $ComputedMinor) {
        throw "Review pass $HeadingPass unresolvedCounts do not match its structured findings."
    }
    if ($Verdict -cne 'PASS' -and $FindingItems.Count -eq 0) {
        throw "Review pass $HeadingPass verdict '$Verdict' must contain structured findings."
    }
    $OpenPrior = @($PriorDispositionItems | Where-Object Disposition -ceq 'STILL_OPEN')
    if ($Verdict -ceq 'PASS' -and $OpenPrior.Count -gt 0) {
        throw "Review pass $HeadingPass cannot PASS with a STILL_OPEN prior finding."
    }
    $CurrentFindingIds = @($FindingItems | ForEach-Object { $_.FindingId })
    foreach ($Prior in $OpenPrior) {
        if ($Prior.FindingId -cnotin $CurrentFindingIds) {
            throw "Review pass $HeadingPass STILL_OPEN prior finding '$($Prior.FindingId)' is absent from current findings."
        }
    }

    $NormalizedBody = ConvertTo-ReviewLf $PayloadBody
    while ($NormalizedBody.StartsWith("`n")) { $NormalizedBody = $NormalizedBody.Substring(1) }
    while ($NormalizedBody.EndsWith("`n")) { $NormalizedBody = $NormalizedBody.Substring(0, $NormalizedBody.Length - 1) }
    $CanonicalPayload = "REVIEW_PASS_PAYLOAD`n$NormalizedBody`nEND_REVIEW_PASS_PAYLOAD`n"

    return [pscustomobject][ordered]@{
        Story = $Story
        Mode = $Mode
        Status = $Status
        Pass = [int64]$PassText
        ReviewedArtifact = $ReviewedArtifact
        ArtifactSha256 = $ArtifactSha256
        CanonDeltaSha256 = $CanonDeltaSha256
        CanonBriefSha256 = $CanonBriefSha256
        PlanSha256 = $PlanSha256
        ScopedRegistrySha256 = $ScopedRegistrySha256
        AuthorityManifest = $AuthorityManifest
        AuthorityManifestSha256 = $AuthorityManifestSha256
        HandoffLedger = $HandoffLedger
        HandoffLedgerSha256 = $HandoffLedgerSha256
        HandoffLedgerChainHead = $HandoffLedgerChainHead
        Reviewer = $Reviewer
        ReviewedAt = $ReviewedAt
        ReviewBasis = $ReviewBasis
        Verdict = $Verdict
        BlockType = $BlockType
        ResolutionOwner = $ResolutionOwner
        ResolutionQuestion = $ResolutionQuestion
        ErrorCode = $ErrorCode
        UnresolvedCritical = $Critical
        UnresolvedMajor = $Major
        UnresolvedMinor = $Minor
        PriorFindingDispositions = $PriorFindingDispositions
        PriorDispositionItems = @($PriorDispositionItems)
        Findings = $Findings
        FindingItems = @($FindingItems)
        CertificationEligible = $CertificationEligible
        CanonicalPayload = $CanonicalPayload
        PassSha256 = Get-ReviewTextSha256 $CanonicalPayload
    }
}

function Get-StoryReviewContract {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$StorySlug,
        [string]$DraftSha256,
        [string]$FinalSha256,
        [string]$CanonDeltaSha256,
        [string]$CanonBriefSha256,
        [string]$PlanSha256,
        [string]$AuthorityManifestSha256,
        [string]$ScopedRegistrySha256,
        [switch]$RequireReleaseReady
    )

    $CurrentSection = Get-UniqueReviewSection $Content 'Current certification'
    $HistorySection = Get-UniqueReviewSection $Content 'Review passes'
    $Current = Get-ReviewCertificationMap $CurrentSection
    $NormalizedHistory = ConvertTo-ReviewLf $HistorySection

    $AllLevelThree = @([regex]::Matches($NormalizedHistory, '(?m)^###[ \t]+[^\n]+$'))
    $HeadingMatches = @([regex]::Matches(
        $NormalizedHistory,
        '(?m)^###[ \t]+Pass[ \t]+(?<pass>[1-9]\d*)[ \t]+—[ \t]+(?<title>[^\n]+?)[ \t]*$'
    ))
    if ($AllLevelThree.Count -ne $HeadingMatches.Count) {
        throw 'Review history contains a malformed or unsupported level-three heading.'
    }
    if ($HeadingMatches.Count -eq 0) {
        throw 'Review history contains no pass heading.'
    }

    for ($Index = 0; $Index -lt $HeadingMatches.Count; $Index++) {
        $ExpectedPass = $Index + 1
        $ActualPass = [int64]$HeadingMatches[$Index].Groups['pass'].Value
        if ($ActualPass -ne $ExpectedPass) {
            throw "Review passes must be unique, monotonic, and contiguous from 1; expected pass $ExpectedPass, found $ActualPass."
        }
    }

    $Passes = [System.Collections.Generic.List[object]]::new()
    for ($Index = 0; $Index -lt $HeadingMatches.Count; $Index++) {
        $Heading = $HeadingMatches[$Index]
        $PassNumber = [int]$Heading.Groups['pass'].Value
        $Title = $Heading.Groups['title'].Value.Trim()
        $SegmentStart = $Heading.Index + $Heading.Length
        $SegmentEnd = if ($Index + 1 -lt $HeadingMatches.Count) {
            $HeadingMatches[$Index + 1].Index
        }
        else {
            $NormalizedHistory.Length
        }
        $Segment = $NormalizedHistory.Substring($SegmentStart, $SegmentEnd - $SegmentStart)
        $BeginCount = [regex]::Matches($Segment, '(?m)^REVIEW_PASS_PAYLOAD[ \t]*$').Count
        $EndCount = [regex]::Matches($Segment, '(?m)^END_REVIEW_PASS_PAYLOAD[ \t]*$').Count

        $IsPendingScaffold = $HeadingMatches.Count -eq 1 -and $PassNumber -eq 1 -and
            $Title -ceq 'pending' -and $BeginCount -eq 0 -and $EndCount -eq 0
        if ($IsPendingScaffold) { continue }
        if ($Title -ceq 'pending') {
            throw "Completed review pass $PassNumber cannot retain the pending heading."
        }
        if ($BeginCount -ne 1 -or $EndCount -ne 1) {
            throw "Review pass $PassNumber must contain exactly one bounded REVIEW_PASS_PAYLOAD."
        }
        $PayloadMatch = [regex]::Match(
            $Segment,
            '(?ms)^REVIEW_PASS_PAYLOAD[ \t]*\n(?<body>.*?)^END_REVIEW_PASS_PAYLOAD[ \t]*(?:\n|\z)'
        )
        if (-not $PayloadMatch.Success) {
            throw "Review pass $PassNumber has malformed REVIEW_PASS_PAYLOAD boundaries."
        }
        $OutsidePayload = $Segment.Remove($PayloadMatch.Index, $PayloadMatch.Length)
        if (-not [string]::IsNullOrWhiteSpace($OutsidePayload)) {
            throw "Review pass $PassNumber contains content outside its exact REVIEW_PASS_PAYLOAD."
        }
        $ParsedPass = ConvertFrom-ReviewPassPayload -StorySlug $StorySlug `
            -HeadingPass $PassNumber -PayloadBody $PayloadMatch.Groups['body'].Value
        $Passes.Add($ParsedPass)
    }

    $PreambleEnd = $HeadingMatches[0].Index
    if ($PreambleEnd -gt 0) {
        $Preamble = $NormalizedHistory.Substring(0, $PreambleEnd)
        if ($Preamble -match '(?m)^(?:END_)?REVIEW_PASS_PAYLOAD[ \t]*$') {
            throw 'Review history contains a payload boundary outside a pass heading.'
        }
    }

    $CompletedPasses = @($Passes.ToArray())
    if ($CompletedPasses.Count -eq 0) {
        $PendingExpected = [ordered]@{
            'Reviewed artifact' = 'None'
            'Artifact SHA-256' = 'unknown'
            'Canon delta SHA-256' = 'not-applicable'
            'Review pass' = '0'
            'Verdict' = 'PENDING'
            'Reviewer' = 'None'
            'Unresolved Critical findings' = 'unknown'
            'Unresolved Major findings' = 'unknown'
            'Updated' = 'Not yet reviewed'
        }
        foreach ($Pair in $PendingExpected.GetEnumerator()) {
            if ($Current[$Pair.Key] -cne $Pair.Value) {
                throw "Pending Current certification field '$($Pair.Key)' is not the untouched scaffold value."
            }
        }
        if ($RequireReleaseReady) {
            throw 'Release requires completed draft and final review passes.'
        }
        return [pscustomobject][ordered]@{
            Passes = @()
            LatestPass = $null
            DraftPass = $null
            HistorySha256 = $null
            ReleaseReview = $null
        }
    }

    $PreviousPassByMode = @{}
    foreach ($CompletedPass in $CompletedPasses) {
        $PreviousPass = if ($PreviousPassByMode.ContainsKey($CompletedPass.Mode)) {
            $PreviousPassByMode[$CompletedPass.Mode]
        }
        else { $null }
        $Dispositions = @($CompletedPass.PriorDispositionItems)
        if ($null -eq $PreviousPass) {
            if ($Dispositions.Count -ne 0) {
                throw "Review pass $($CompletedPass.Pass) records prior finding dispositions without a prior $($CompletedPass.Mode) pass."
            }
        }
        else {
            $PriorBlockers = @($PreviousPass.FindingItems | Where-Object {
                $_.Severity -cin @('Critical', 'Major')
            })
            $PriorBlockerIds = @($PriorBlockers | ForEach-Object { $_.FindingId })
            foreach ($PriorBlocker in $PriorBlockers) {
                $Matches = @($Dispositions | Where-Object {
                    $_.FindingId -ceq $PriorBlocker.FindingId
                })
                if ($Matches.Count -ne 1) {
                    throw "Review pass $($CompletedPass.Pass) must disposition prior $($PriorBlocker.Severity) finding '$($PriorBlocker.FindingId)'."
                }
                $StillCurrent = $PriorBlocker.FindingId -cin `
                    @($CompletedPass.FindingItems | ForEach-Object { $_.FindingId })
                if ($Matches[0].Disposition -ceq 'STILL_OPEN' -and -not $StillCurrent) {
                    throw "Review pass $($CompletedPass.Pass) marks prior finding '$($PriorBlocker.FindingId)' STILL_OPEN without carrying it into current findings."
                }
                if ($Matches[0].Disposition -cin @('RESOLVED', 'SUPERSEDED') -and
                    $StillCurrent) {
                    throw "Review pass $($CompletedPass.Pass) marks prior finding '$($PriorBlocker.FindingId)' closed while retaining it in current findings."
                }
            }
            foreach ($Disposition in $Dispositions) {
                if ($Disposition.FindingId -cnotin $PriorBlockerIds) {
                    throw "Review pass $($CompletedPass.Pass) dispositions unknown prior blocker '$($Disposition.FindingId)'."
                }
            }
        }
        $PreviousPassByMode[$CompletedPass.Mode] = $CompletedPass
    }

    $Latest = $CompletedPasses[-1]
    $ExpectedCurrent = [ordered]@{
        'Reviewed artifact' = $Latest.ReviewedArtifact
        'Artifact SHA-256' = $Latest.ArtifactSha256
        'Canon delta SHA-256' = $Latest.CanonDeltaSha256
        'Review pass' = [string]$Latest.Pass
        'Verdict' = $Latest.Verdict
        'Reviewer' = $Latest.Reviewer
        'Unresolved Critical findings' = [string]$Latest.UnresolvedCritical
        'Unresolved Major findings' = [string]$Latest.UnresolvedMajor
        'Updated' = $Latest.ReviewedAt
    }
    foreach ($Pair in $ExpectedCurrent.GetEnumerator()) {
        if ($Current[$Pair.Key] -cne $Pair.Value) {
            throw "Current certification '$($Pair.Key)' does not exactly match latest review pass $($Latest.Pass)."
        }
    }

    $CanonicalHistory = "REVIEW_HISTORY_V1`n" +
        (($CompletedPasses | ForEach-Object { $_.CanonicalPayload }) -join '')
    $HistorySha256 = Get-ReviewTextSha256 $CanonicalHistory
    $DraftPass = $null
    $ReleaseReview = $null
    if ($RequireReleaseReady) {
        foreach ($DigestSpec in @(
            [pscustomobject]@{ Name = '03-draft.md'; Value = $DraftSha256 },
            [pscustomobject]@{ Name = '05-story.md'; Value = $FinalSha256 },
            [pscustomobject]@{ Name = '06-canon-delta.md'; Value = $CanonDeltaSha256 },
            [pscustomobject]@{ Name = '01-canon-brief.md'; Value = $CanonBriefSha256 },
            [pscustomobject]@{ Name = '02-story-plan.md'; Value = $PlanSha256 },
            [pscustomobject]@{ Name = 'authority.json'; Value = $AuthorityManifestSha256 },
            [pscustomobject]@{ Name = 'scoped name registry'; Value = $ScopedRegistrySha256 }
        )) {
            if ($DigestSpec.Value -cnotmatch '^[a-f0-9]{64}$') {
                throw "Current $($DigestSpec.Name) SHA-256 is missing or invalid."
            }
        }
        if ($Latest.ReviewedArtifact -cne '05-story.md' -or
            $Latest.Mode -cne 'REVIEW_FINAL' -or
            $Latest.Verdict -cne 'PASS' -or -not $Latest.CertificationEligible -or
            $Latest.ArtifactSha256 -cne $FinalSha256 -or
            $Latest.CanonDeltaSha256 -cne $CanonDeltaSha256 -or
            $Latest.CanonBriefSha256 -cne $CanonBriefSha256 -or
            $Latest.PlanSha256 -cne $PlanSha256 -or
            $Latest.AuthorityManifestSha256 -cne $AuthorityManifestSha256 -or
            $Latest.ScopedRegistrySha256 -cne $ScopedRegistrySha256) {
            throw 'Latest review pass must be a certification-eligible PASS over the current 05-story.md and 06-canon-delta.md bytes.'
        }
        $DraftReviews = @($CompletedPasses | Where-Object {
            $_.Pass -lt $Latest.Pass -and $_.Mode -ceq 'REVIEW_DRAFT'
        })
        if ($DraftReviews.Count -eq 0) {
            throw 'Release requires a hash-current 03-draft.md PASS before the latest final PASS.'
        }
        $DraftPass = $DraftReviews[-1]
        if ($DraftPass.ReviewedArtifact -cne '03-draft.md' -or
            $DraftPass.Verdict -cne 'PASS' -or
            -not $DraftPass.CertificationEligible -or
            $DraftPass.ArtifactSha256 -cne $DraftSha256 -or
            $DraftPass.CanonBriefSha256 -cne $CanonBriefSha256 -or
            $DraftPass.PlanSha256 -cne $PlanSha256 -or
            $DraftPass.AuthorityManifestSha256 -cne $AuthorityManifestSha256) {
            throw 'Release requires the latest draft review before final review to be a hash-current 03-draft.md PASS.'
        }
        $ReleaseReview = [pscustomobject][ordered]@{
            artifact = '05-story.md'
            pass = $Latest.Pass
            verdict = 'PASS'
            reviewer = $Latest.Reviewer
            unresolvedCritical = $Latest.UnresolvedCritical
            unresolvedMajor = $Latest.UnresolvedMajor
            passSha256 = $Latest.PassSha256
            historySha256 = $HistorySha256
            draftPass = $DraftPass.Pass
            draftPassSha256 = $DraftPass.PassSha256
            reviewedAt = $Latest.ReviewedAt
        }
    }

    return [pscustomobject][ordered]@{
        Passes = $CompletedPasses
        LatestPass = $Latest
        DraftPass = $DraftPass
        HistorySha256 = $HistorySha256
        ReleaseReview = $ReleaseReview
    }
}

function Get-ReviewLedgerSnapshotSha256 {
    param(
        [Parameter(Mandatory = $true)][string]$StorySlug,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Entries,
        [Parameter(Mandatory = $true)][AllowNull()][object]$ChainHead
    )

    $Snapshot = [ordered]@{
        schemaVersion = 2
        storySlug = $StorySlug
        chainHead = $ChainHead
        entries = @($Entries)
    }
    $Json = ($Snapshot | ConvertTo-Json -Depth 16).Replace("`r`n", "`n").
        Replace("`r", "`n") + "`n"
    return Get-ReviewTextSha256 $Json
}

function Assert-ReviewLedgerBindings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]$ReviewContract,
        [Parameter(Mandatory = $true)][object]$Ledger,
        [Parameter(Mandatory = $true)][string]$StorySlug,
        [switch]$RequireLatestReviewAtChainHead
    )

    if ($Ledger.schemaVersion -ne 2 -or $Ledger.storySlug -cne $StorySlug) {
        throw 'Review handoff ledger identity or schema is invalid.'
    }
    $Entries = @($Ledger.entries)
    $ExpectedLedgerPath = "stories/$StorySlug/handoffs.json"
    $ExpectedReviewPath = "stories/$StorySlug/04-review.md"
    $ExpectedFinalHead = if ($Entries.Count -eq 0) { $null } else {
        [string]$Entries[-1].entrySha256
    }
    if ($Ledger.chainHead -cne $ExpectedFinalHead) {
        throw 'Review handoff ledger chainHead does not match its final entry.'
    }
    $UnexpectedCriticEntries = @($Entries | Where-Object {
        $_.actor -ceq 'continuity_critic' -and
        ($_.story -cne $StorySlug -or
            $_.persister -cne 'coordinator' -or
            $_.mode -cnotin @('REVIEW_DRAFT', 'REVIEW_FINAL') -or
            $_.status -cnotin @('READY', 'USER_RULING_REQUIRED', 'HANDOFF_ERROR'))
    })
    if ($UnexpectedCriticEntries.Count -gt 0) {
        throw 'Review handoff ledger contains an invalid continuity_critic mode or status.'
    }
    $PersistedCriticEntries = @($Entries | Where-Object {
        $_.actor -ceq 'continuity_critic' -and
        $_.mode -cin @('REVIEW_DRAFT', 'REVIEW_FINAL') -and
        $_.status -cin @('READY', 'USER_RULING_REQUIRED')
    })
    if ($PersistedCriticEntries.Count -ne @($ReviewContract.Passes).Count) {
        throw 'Persisted review history and accepted critic ledger entries are not one-to-one.'
    }
    for ($ErrorIndex = 0; $ErrorIndex -lt $Entries.Count; $ErrorIndex++) {
        $ErrorEntry = $Entries[$ErrorIndex]
        if ($ErrorEntry.actor -cne 'continuity_critic' -or
            $ErrorEntry.status -cne 'HANDOFF_ERROR') { continue }
        if (@($ErrorEntry.outputs).Count -ne 0) {
            throw 'A continuity_critic HANDOFF_ERROR ledger entry must not record artifact outputs.'
        }
        $Resolved = $false
        for ($LaterIndex = $ErrorIndex + 1; $LaterIndex -lt $Entries.Count; $LaterIndex++) {
            $LaterEntry = $Entries[$LaterIndex]
            if ($LaterEntry.actor -ceq 'continuity_critic' -and
                $LaterEntry.mode -ceq $ErrorEntry.mode -and
                $LaterEntry.status -cin @('READY', 'USER_RULING_REQUIRED')) {
                $Resolved = $true
                break
            }
        }
        if (-not $Resolved) {
            throw "Unresolved continuity_critic HANDOFF_ERROR remains for mode '$($ErrorEntry.mode)'."
        }
    }
    $MatchedEntryIndexes = [Collections.Generic.HashSet[int]]::new()
    $LastSequence = 0
    $LatestMatchedIndex = -1
    foreach ($Pass in @($ReviewContract.Passes)) {
        $CandidateMatches = [System.Collections.Generic.List[object]]::new()
        for ($Index = 0; $Index -lt $Entries.Count; $Index++) {
            $Entry = $Entries[$Index]
            if ($Entry.story -cne $StorySlug -or
                $Entry.actor -cne 'continuity_critic' -or
                $Entry.persister -cne 'coordinator' -or
                $Entry.mode -cne $Pass.Mode -or
                $Entry.status -cne $Pass.Status -or
                $Entry.previousEntrySha256 -cne $Pass.HandoffLedgerChainHead) {
                continue
            }
            $LedgerInputs = @($Entry.inputs | Where-Object {
                $_.path -ceq $ExpectedLedgerPath
            })
            if ($LedgerInputs.Count -ne 1 -or
                $LedgerInputs[0].sha256 -cne $Pass.HandoffLedgerSha256) { continue }
            if (-not ($Entry.report -is [string]) -or
                $Entry.reportSha256 -cnotmatch '^[a-f0-9]{64}$') {
                continue
            }
            $NormalizedReport = ConvertTo-ReviewLf ([string]$Entry.report)
            if ((Get-ReviewTextSha256 $NormalizedReport) -cne $Entry.reportSha256) {
                continue
            }
            if ($NormalizedReport -cne $Pass.CanonicalPayload) { continue }
            $CandidateMatches.Add([pscustomobject]@{ Entry = $Entry; Index = $Index })
        }
        if ($CandidateMatches.Count -ne 1) {
            throw "Review pass $($Pass.Pass) is not bound to exactly one accepted critic ledger report."
        }

        $Match = $CandidateMatches[0]
        $Entry = $Match.Entry
        $LatestMatchedIndex = [int]$Match.Index
        $ExpectedPassInputs = [Collections.Generic.List[object]]::new()
        $ExpectedPassInputs.Add([pscustomobject]@{
            Path = "stories/$StorySlug/$($Pass.ReviewedArtifact)"
            Sha256 = $Pass.ArtifactSha256
        })
        $ExpectedPassInputs.Add([pscustomobject]@{
            Path = "stories/$StorySlug/01-canon-brief.md"
            Sha256 = $Pass.CanonBriefSha256
        })
        $ExpectedPassInputs.Add([pscustomobject]@{
            Path = "stories/$StorySlug/02-story-plan.md"
            Sha256 = $Pass.PlanSha256
        })
        $ExpectedPassInputs.Add([pscustomobject]@{
            Path = $Pass.AuthorityManifest
            Sha256 = $Pass.AuthorityManifestSha256
        })
        if ($Pass.Mode -ceq 'REVIEW_FINAL') {
            $ExpectedPassInputs.Add([pscustomobject]@{
                Path = "stories/$StorySlug/06-canon-delta.md"
                Sha256 = $Pass.CanonDeltaSha256
            })
        }
        foreach ($ExpectedInput in $ExpectedPassInputs) {
            $BoundInputs = @($Entry.inputs | Where-Object {
                $_.path -ceq $ExpectedInput.Path
            })
            if ($BoundInputs.Count -ne 1 -or
                $BoundInputs[0].sha256 -cne $ExpectedInput.Sha256) {
                throw "Review pass $($Pass.Pass) ledger entry does not bind exact input '$($ExpectedInput.Path)'."
            }
        }
        if (-not $MatchedEntryIndexes.Add([int]$Match.Index)) {
            throw "Review pass $($Pass.Pass) reuses a critic ledger entry already bound to another pass."
        }
        if ([int64]$Entry.sequence -le $LastSequence) {
            throw 'Critic ledger entries do not preserve review-pass order.'
        }
        $LastSequence = [int64]$Entry.sequence
        $PriorEntries = if ($Match.Index -eq 0) {
            @()
        }
        else {
            @($Entries[0..($Match.Index - 1)])
        }
        $ExpectedPreviousHead = if ($PriorEntries.Count -eq 0) {
            $null
        }
        else {
            [string]$PriorEntries[-1].entrySha256
        }
        if ($Pass.HandoffLedgerChainHead -cne $ExpectedPreviousHead) {
            throw "Review pass $($Pass.Pass) pre-review chainHead is not the actual prior ledger head."
        }
        $SnapshotSha256 = Get-ReviewLedgerSnapshotSha256 `
            -StorySlug $StorySlug -Entries $PriorEntries `
            -ChainHead $Pass.HandoffLedgerChainHead
        if ($SnapshotSha256 -cne $Pass.HandoffLedgerSha256) {
            throw "Review pass $($Pass.Pass) pre-review ledger digest is not the actual prior ledger snapshot."
        }
        $ReviewOutputs = @($Entry.outputs | Where-Object {
            $_.path -ceq $ExpectedReviewPath
        })
        if ($ReviewOutputs.Count -ne 1 -or
            $ReviewOutputs[0].afterSha256 -cnotmatch '^[a-f0-9]{64}$') {
            throw "Review pass $($Pass.Pass) ledger entry does not record the persisted 04-review.md output."
        }
    }
    foreach ($Index in 0..($Entries.Count - 1)) {
        $Entry = $Entries[$Index]
        if ($Entry.actor -ceq 'continuity_critic' -and
            $Entry.mode -cin @('REVIEW_DRAFT', 'REVIEW_FINAL') -and
            $Entry.status -cin @('READY', 'USER_RULING_REQUIRED') -and
            -not $MatchedEntryIndexes.Contains($Index)) {
            throw 'An accepted critic ledger entry is absent from persisted review history.'
        }
    }
    if ($RequireLatestReviewAtChainHead -and
        $LatestMatchedIndex -ne $Entries.Count - 1) {
        throw 'The latest persisted review is not the current handoff ledger chain head.'
    }
}

function Assert-ReviewReleaseBinding {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][object]$ReleaseReview,
        [Parameter(Mandatory = $true)][object]$ReviewContract
    )

    if ($null -eq $ReviewContract.ReleaseReview) {
        throw 'Review history does not contain a release-ready review receipt.'
    }
    foreach ($Field in @(
        'artifact', 'pass', 'verdict', 'reviewer', 'unresolvedCritical',
        'unresolvedMajor', 'passSha256', 'historySha256', 'draftPass',
        'draftPassSha256', 'reviewedAt'
    )) {
        if ($ReleaseReview.$Field -cne $ReviewContract.ReleaseReview.$Field) {
            throw "release review.$Field does not match the canonical latest review history."
        }
    }
}
