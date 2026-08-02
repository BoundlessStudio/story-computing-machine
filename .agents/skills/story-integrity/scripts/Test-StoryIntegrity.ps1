#Requires -Version 7.0

[CmdletBinding()]
param(
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$script:Errors = [System.Collections.Generic.List[string]]::new()
$script:Warnings = [System.Collections.Generic.List[string]]::new()
. (Join-Path $PSScriptRoot 'ReviewContracts.ps1')
. (Join-Path $PSScriptRoot 'PromotionContracts.ps1')

function Add-IntegrityError {
    param([Parameter(Mandatory = $true)][string]$Message)
    $script:Errors.Add($Message)
}

function Add-IntegrityWarning {
    param([Parameter(Mandatory = $true)][string]$Message)
    $script:Warnings.Add($Message)
}

function Get-RawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-CrlfExpandedSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    $Bytes = [IO.File]::ReadAllBytes($Path)
    for ($Index = 0; $Index -lt $Bytes.Length - 1; $Index++) {
        if ($Bytes[$Index] -eq 13 -and $Bytes[$Index + 1] -eq 10) {
            return $null
        }
    }
    if (10 -notin $Bytes) { return $null }

    $Expanded = [System.Collections.Generic.List[byte]]::new($Bytes.Length + 128)
    foreach ($Byte in $Bytes) {
        if ($Byte -eq 10) { $Expanded.Add(13) }
        $Expanded.Add($Byte)
    }
    $Hash = [Security.Cryptography.SHA256]::HashData($Expanded.ToArray())
    return [Convert]::ToHexString($Hash).ToLowerInvariant()
}

function Get-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Add-IntegrityError "$Label is missing: $Path"
        return $null
    }
    try {
        $Json = Get-Content -LiteralPath $Path -Raw
        if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
            return $Json | ConvertFrom-Json -DateKind String
        }
        return $Json | ConvertFrom-Json
    }
    catch {
        Add-IntegrityError "$Label is invalid JSON: $($_.Exception.Message)"
        return $null
    }
}

function Test-ExactProperties {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][object]$Object,
        [Parameter(Mandatory = $true)][string[]]$Properties,
        [Parameter(Mandatory = $true)][string]$Context
    )

    if ($null -eq $Object) {
        Add-IntegrityError "$Context must be an object."
        return
    }
    $Names = @($Object.PSObject.Properties.Name)
    foreach ($Property in $Properties) {
        if ($Property -notin $Names) {
            Add-IntegrityError "$Context is missing required property '$Property'."
        }
    }
    foreach ($Property in $Names) {
        if ($Property -notin $Properties) {
            Add-IntegrityError "$Context contains unknown property '$Property'."
        }
    }
}

function Split-MarkdownRow {
    param(
        [Parameter(Mandatory = $true)][string]$Line,
        [Parameter(Mandatory = $true)][int]$ExpectedCells,
        [Parameter(Mandatory = $true)][string]$Context
    )

    if ($Line -notmatch '^\s*\|.*\|\s*$') {
        throw "Malformed Markdown row in ${Context}: $Line"
    }
    $Cells = @($Line.Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
    if ($Cells.Count -ne $ExpectedCells) {
        throw "Malformed Markdown row in $Context (expected $ExpectedCells cells, found $($Cells.Count)): $Line"
    }
    return ,$Cells
}

function Get-IndexRows {
    param([Parameter(Mandatory = $true)][string]$Path)

    $Lines = @(Get-Content -LiteralPath $Path)
    $HeaderIndex = -1
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index] -match '^\|\s*Story\s*\|\s*Title\s*\|\s*Status\s*\|\s*Canon\s*\|\s*User disposition\s*\|\s*Publish\s*\|\s*Promotion date\s*\|\s*Notes\s*\|$') {
            $HeaderIndex = $Index
            break
        }
    }
    if ($HeaderIndex -lt 0 -or $HeaderIndex + 1 -ge $Lines.Count) {
        throw 'stories/INDEX.md is missing its eight-column story table.'
    }
    $Separator = Split-MarkdownRow $Lines[$HeaderIndex + 1] 8 'stories/INDEX.md separator'
    if (@($Separator | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -ne 0) {
        throw 'stories/INDEX.md has an invalid table separator.'
    }

    $Rows = [System.Collections.Generic.List[object]]::new()
    for ($Index = $HeaderIndex + 2; $Index -lt $Lines.Count; $Index++) {
        $Line = $Lines[$Index]
        if ([string]::IsNullOrWhiteSpace($Line)) { break }
        if ($Line -notmatch '^\s*\|') { break }
        $Cells = Split-MarkdownRow $Line 8 "stories/INDEX.md line $($Index + 1)"
        if ($Cells[0] -notmatch '^`([a-z0-9]+(?:-[a-z0-9]+)*)`$') {
            throw "Invalid story slug cell at stories/INDEX.md line $($Index + 1): $($Cells[0])"
        }
        $Slug = $Matches[1]
        if ($Cells[1] -notmatch '^\*(.+)\*$') {
            throw "Invalid title cell at stories/INDEX.md line $($Index + 1): $($Cells[1])"
        }
        $Title = $Matches[1]
        if ($Cells[2] -notin @('in-progress', 'candidate', 'final', 'abandoned')) {
            throw "Invalid status '$($Cells[2])' at stories/INDEX.md line $($Index + 1)."
        }
        if ($Cells[3] -notin @('yes', 'no')) {
            throw "Invalid canon value '$($Cells[3])' at stories/INDEX.md line $($Index + 1)."
        }
        if ($Cells[4] -notin @('pending', 'accepted', 'rejected')) {
            throw "Invalid user disposition '$($Cells[4])' at stories/INDEX.md line $($Index + 1)."
        }
        if ($Cells[5] -notin @('yes', 'no')) {
            throw "Invalid publish value '$($Cells[5])' at stories/INDEX.md line $($Index + 1)."
        }
        if ($Cells[6] -ne '—' -and $Cells[6] -notmatch '^\d{4}-\d{2}-\d{2}$') {
            throw "Invalid promotion date '$($Cells[6])' at stories/INDEX.md line $($Index + 1)."
        }
        $Rows.Add([pscustomobject]@{
            Slug = $Slug
            Title = $Title
            Status = $Cells[2]
            Canon = $Cells[3]
            UserDisposition = $Cells[4]
            Publish = $Cells[5]
            PromotionDate = $Cells[6]
            LineNumber = $Index + 1
        })
    }
    if ($Rows.Count -eq 0) { throw 'stories/INDEX.md contains no story rows.' }
    foreach ($Duplicate in @($Rows | Group-Object Slug | Where-Object Count -gt 1)) {
        throw "stories/INDEX.md contains duplicate slug '$($Duplicate.Name)'."
    }
    return @($Rows)
}

function Get-FrontMatter {
    param([Parameter(Mandatory = $true)][string]$Content)

    $Match = [regex]::Match($Content, '(?s)\A---\r?\n(.*?)\r?\n---(?:\r?\n|\z)')
    if (-not $Match.Success) { throw '05-story.md is missing leading YAML frontmatter.' }
    $Values = @{}
    foreach ($Line in @($Match.Groups[1].Value -split '\r?\n')) {
        if ($Line -notmatch '^([A-Za-z][A-Za-z0-9]*):\s*(.*?)\s*$') {
            throw "Unsupported or malformed 05-story.md frontmatter line: $Line"
        }
        $Key = $Matches[1]
        $RawValue = $Matches[2]
        if ($Values.ContainsKey($Key)) { throw "Duplicate frontmatter key '$Key'." }
        $Value = switch -Regex ($RawValue) {
            '^".*"$' {
                try { $RawValue | ConvertFrom-Json } catch { throw "Invalid quoted value for '$Key'." }
                break
            }
            '^(true|false)$' { $RawValue -eq 'true'; break }
            '^null$' { $null; break }
            default { $RawValue }
        }
        $Values[$Key] = $Value
    }
    return $Values
}

function Get-ReadmeValue {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $Match = [regex]::Match(
        $Content,
        '(?im)^-\s+' + [regex]::Escape($Label) + ':\s*(.+?)\s*$'
    )
    if (-not $Match.Success) { return $null }
    return ($Match.Groups[1].Value.Trim() -replace '`', '')
}

function Test-StoryMetadata {
    param(
        [Parameter(Mandatory = $true)][object]$Metadata,
        [Parameter(Mandatory = $true)][string]$Slug
    )

    $StoryProperty = if ($null -ne $script:PipelineContract) {
        $script:PipelineContract.PSObject.Properties['story']
    }
    $LifecycleProperty = if ($null -ne $script:PipelineContract) {
        $script:PipelineContract.PSObject.Properties['lifecycle']
    }
    $StoryContract = if ($null -ne $StoryProperty) { $StoryProperty.Value } else { $null }
    $LifecycleContract = if ($null -ne $LifecycleProperty) { $LifecycleProperty.Value } else { $null }
    $LifecycleStatesProperty = if ($null -ne $LifecycleContract) {
        $LifecycleContract.PSObject.Properties['states']
    }
    if ($null -eq $StoryContract -or $null -eq $LifecycleContract -or
        $null -eq $LifecycleStatesProperty -or $null -eq $LifecycleStatesProperty.Value) {
        Add-IntegrityError 'schemas/pipeline-contract.json lacks story/lifecycle contract structure.'
        return
    }
    $Required = @($StoryContract.fields)
    $AllowedStages = @($StoryContract.stages)
    $AllowedStatuses = @($StoryContract.statuses)
    $AllowedDispositions = @($StoryContract.userDispositions)
    $PublishableStatuses = @($LifecycleContract.publishableStatuses)
    if ($Required.Count -eq 0 -or $AllowedStages.Count -eq 0 -or
        $AllowedStatuses.Count -eq 0 -or $AllowedDispositions.Count -eq 0 -or
        $PublishableStatuses.Count -eq 0 -or
        @($Required + $AllowedStages + $AllowedStatuses + $AllowedDispositions +
            $PublishableStatuses | Where-Object {
                -not ($_ -is [string]) -or [string]::IsNullOrWhiteSpace($_)
            }).Count -gt 0) {
        Add-IntegrityError 'schemas/pipeline-contract.json story/lifecycle arrays are missing or malformed.'
        return
    }
    Test-ExactProperties $Metadata $Required "$Slug/story.json"
    if ($Metadata.schemaVersion -ne 1) { Add-IntegrityError "$Slug/story.json schemaVersion must be 1." }
    if ($Metadata.slug -cne $Slug) { Add-IntegrityError "$Slug/story.json slug must exactly match its directory." }
    if (-not ($Metadata.title -is [string]) -or [string]::IsNullOrWhiteSpace($Metadata.title)) {
        Add-IntegrityError "$Slug/story.json title must be a nonempty string."
    }
    if (-not ($Metadata.created -is [string]) -or $Metadata.created -notmatch '^\d{4}-\d{2}-\d{2}$') {
        Add-IntegrityError "$Slug/story.json created must be YYYY-MM-DD."
    }
    if ($Metadata.stage -cnotin $AllowedStages) {
        Add-IntegrityError "$Slug/story.json stage '$($Metadata.stage)' is not allowed."
    }
    if ($Metadata.status -cnotin $AllowedStatuses) {
        Add-IntegrityError "$Slug/story.json status '$($Metadata.status)' is not allowed."
    }
    if (-not ($Metadata.canon -is [bool])) { Add-IntegrityError "$Slug/story.json canon must be boolean." }
    if (-not ($Metadata.publish -is [bool])) { Add-IntegrityError "$Slug/story.json publish must be boolean." }
    if ($Metadata.userDisposition -cnotin $AllowedDispositions) {
        Add-IntegrityError "$Slug/story.json userDisposition '$($Metadata.userDisposition)' is not allowed."
    }
    if ($null -ne $Metadata.promotionDate -and
        (-not ($Metadata.promotionDate -is [string]) -or
        $Metadata.promotionDate -notmatch '^\d{4}-\d{2}-\d{2}$')) {
        Add-IntegrityError "$Slug/story.json promotionDate must be null or YYYY-MM-DD."
    }
    $StateProperty = @($LifecycleStatesProperty.Value.PSObject.Properties | Where-Object {
        $_.Name -ceq [string]$Metadata.status
    })
    if ($StateProperty.Count -ne 1) {
        Add-IntegrityError "schemas/pipeline-contract.json has no exact lifecycle rule for status '$($Metadata.status)'."
        return
    }
    $StateRule = $StateProperty[0].Value
    $RuleProperties = @($StateRule.PSObject.Properties.Name)
    if (@('stages', 'canon', 'userDispositions', 'publish', 'promotionDate' |
        Where-Object { $_ -cnotin $RuleProperties }).Count -gt 0) {
        Add-IntegrityError "schemas/pipeline-contract.json lifecycle rule '$($Metadata.status)' is malformed."
        return
    }
    $RuleStages = @($StateRule.stages)
    $RuleDispositions = @($StateRule.userDispositions)
    $RulePublish = @($StateRule.publish)
    if ($RuleStages.Count -eq 0 -or $RuleDispositions.Count -eq 0 -or
        $RulePublish.Count -eq 0 -or -not ($StateRule.canon -is [bool]) -or
        @($RuleStages + $RuleDispositions | Where-Object {
            -not ($_ -is [string]) -or [string]::IsNullOrWhiteSpace($_)
        }).Count -gt 0 -or @($RulePublish | Where-Object {
            -not ($_ -is [bool])
        }).Count -gt 0 -or $StateRule.promotionDate -cnotin @('null', 'required')) {
        Add-IntegrityError "schemas/pipeline-contract.json lifecycle rule '$($Metadata.status)' is malformed."
        return
    }
    if ($Metadata.stage -cnotin $RuleStages -or
        $Metadata.canon -cne $StateRule.canon -or
        $Metadata.userDisposition -cnotin $RuleDispositions -or
        $Metadata.publish -cnotin $RulePublish) {
        Add-IntegrityError "$Slug lifecycle fields do not satisfy the central '$($Metadata.status)' state rule."
    }
    if ($StateRule.promotionDate -ceq 'null' -and $null -ne $Metadata.promotionDate) {
        Add-IntegrityError "$Slug lifecycle state '$($Metadata.status)' requires promotionDate=null."
    }
    if ($StateRule.promotionDate -ceq 'required' -and $null -eq $Metadata.promotionDate) {
        Add-IntegrityError "$Slug lifecycle state '$($Metadata.status)' requires a promotionDate."
    }
    if ($Metadata.publish -eq $true -and
        $Metadata.status -cnotin $PublishableStatuses) {
        Add-IntegrityError "$Slug status '$($Metadata.status)' is not publishable under the central lifecycle contract."
    }
}

function Get-CanonicalAuthorityManifestHash {
    param([Parameter(Mandatory = $true)][object]$Manifest)

    $Payload = [ordered]@{
        schemaVersion = 1
        storySlug = [string]$Manifest.storySlug
        generatedAt = [string]$Manifest.generatedAt
        universeFiles = @($Manifest.universeFiles)
        canonStories = @($Manifest.canonStories)
    }
    $Json = $Payload | ConvertTo-Json -Depth 12 -Compress
    $Json = $Json.Replace("`r`n", "`n").Replace("`r", "`n")
    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Json)
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Bytes)
    ).ToLowerInvariant()
}

function Test-AuthorityManifestInternal {
    param(
        [Parameter(Mandatory = $true)][object]$Manifest,
        [Parameter(Mandatory = $true)][string]$Slug,
        [switch]$AllowPending
    )

    Test-ExactProperties $Manifest @(
        'schemaVersion', 'storySlug', 'generatedAt', 'universeFiles',
        'canonStories', 'manifestSha256'
    ) "$Slug/authority.json"
    if ($Manifest.schemaVersion -ne 1 -or $Manifest.storySlug -cne $Slug) {
        Add-IntegrityError "$Slug/authority.json identity or schema is invalid."
    }
    $IsPending = $null -eq $Manifest.generatedAt -and
        $null -eq $Manifest.manifestSha256 -and
        @($Manifest.universeFiles).Count -eq 0 -and
        @($Manifest.canonStories).Count -eq 0
    if ($IsPending -and $AllowPending) { return }
    if ($null -eq $Manifest.generatedAt -or $null -eq $Manifest.manifestSha256) {
        Add-IntegrityError "$Slug/authority.json has a partially initialized authority snapshot."
        return
    }
    $GeneratedAt = [DateTimeOffset]::MinValue
    if (-not ($Manifest.generatedAt -is [string]) -or
        -not [DateTimeOffset]::TryParseExact(
            [string]$Manifest.generatedAt,
            'o',
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind,
            [ref]$GeneratedAt
        ) -or $GeneratedAt.Offset -ne [TimeSpan]::Zero) {
        Add-IntegrityError "$Slug/authority.json generatedAt must be an ISO-8601 UTC timestamp."
    }

    $UniversePaths = [System.Collections.Generic.HashSet[string]]::new(
        [StringComparer]::Ordinal
    )
    foreach ($Entry in @($Manifest.universeFiles)) {
        Test-ExactProperties $Entry @('path', 'sha256') "$Slug/authority.json universeFiles entry"
        $Path = [string]$Entry.path
        if ($Path -cnotmatch '^universe/[A-Za-z0-9._/-]+\.md$' -or
            $Path -match '(^|/)\.\.(/|$)' -or $Path -match '\\') {
            Add-IntegrityError "$Slug/authority.json contains unsafe universe path '$Path'."
        }
        elseif (-not $UniversePaths.Add($Path)) {
            Add-IntegrityError "$Slug/authority.json duplicates universe path '$Path'."
        }
        if ($Entry.sha256 -cnotmatch '^[a-f0-9]{64}$') {
            Add-IntegrityError "$Slug/authority.json universe digest for '$Path' is invalid."
        }
    }

    $CanonSlugs = [System.Collections.Generic.HashSet[string]]::new(
        [StringComparer]::Ordinal
    )
    foreach ($Entry in @($Manifest.canonStories)) {
        Test-ExactProperties $Entry @(
            'slug', 'promotionDate', 'storySha256', 'canonDeltaSha256'
        ) "$Slug/authority.json canonStories entry"
        $CanonSlug = [string]$Entry.slug
        if ($CanonSlug -cnotmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
            Add-IntegrityError "$Slug/authority.json has invalid canon story slug '$CanonSlug'."
        }
        elseif (-not $CanonSlugs.Add($CanonSlug)) {
            Add-IntegrityError "$Slug/authority.json duplicates canon story '$CanonSlug'."
        }
        $PromotionDate = [DateTime]::MinValue
        if (-not ($Entry.promotionDate -is [string]) -or
            -not [DateTime]::TryParseExact(
                [string]$Entry.promotionDate,
                'yyyy-MM-dd',
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::None,
                [ref]$PromotionDate
            )) {
            Add-IntegrityError "$Slug/authority.json canon story '$CanonSlug' has an invalid promotionDate."
        }
        foreach ($DigestField in @('storySha256', 'canonDeltaSha256')) {
            if ($Entry.$DigestField -cnotmatch '^[a-f0-9]{64}$') {
                Add-IntegrityError "$Slug/authority.json canon story '$CanonSlug' has invalid $DigestField."
            }
        }
    }
    if ($Manifest.manifestSha256 -cnotmatch '^[a-f0-9]{64}$' -or
        (Get-CanonicalAuthorityManifestHash $Manifest) -cne $Manifest.manifestSha256) {
        Add-IntegrityError "$Slug/authority.json manifestSha256 does not match its canonical content."
    }
}

function Test-ReviewLedgerBindings {
    param(
        [Parameter(Mandatory = $true)][object]$ReviewContract,
        [Parameter(Mandatory = $true)][object]$Ledger,
        [Parameter(Mandatory = $true)][string]$Slug
    )

    try {
        Assert-ReviewLedgerBindings -ReviewContract $ReviewContract `
            -Ledger $Ledger -StorySlug $Slug -RequireLatestReviewAtChainHead
    }
    catch {
        Add-IntegrityError "$Slug review ledger binding failed: $($_.Exception.Message)"
    }
}

function Test-ReleaseCertificate {
    param(
        [Parameter(Mandatory = $true)][object]$Release,
        [Parameter(Mandatory = $true)][object]$Metadata,
        [Parameter(Mandatory = $true)][string]$StoryDirectory,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][AllowNull()][object]$ReviewContract,
        [Parameter(Mandatory = $true)][AllowNull()][object]$NameReceipt
    )

    $ReleaseProperty = if ($null -ne $script:PipelineContract) {
        $script:PipelineContract.PSObject.Properties['release']
    }
    $LifecycleProperty = if ($null -ne $script:PipelineContract) {
        $script:PipelineContract.PSObject.Properties['lifecycle']
    }
    $ReleaseContract = if ($null -ne $ReleaseProperty) { $ReleaseProperty.Value } else { $null }
    $LifecycleContract = if ($null -ne $LifecycleProperty) { $LifecycleProperty.Value } else { $null }
    $RequiredContractArrays = @(
        'fields', 'artifactContainerFields', 'artifactFields', 'reviewFields',
        'nameCheckFields', 'provenanceFields'
    )
    if ($null -eq $ReleaseContract) {
        Add-IntegrityError 'schemas/pipeline-contract.json lacks a valid release contract.'
        return
    }
    if ($ReleaseContract.schemaVersion -isnot [long] -and
        $ReleaseContract.schemaVersion -isnot [int]) {
        Add-IntegrityError 'schemas/pipeline-contract.json lacks a valid release contract.'
        return
    }
    foreach ($ContractField in $RequiredContractArrays) {
        $Values = @($ReleaseContract.$ContractField)
        if ($Values.Count -eq 0 -or @($Values | Where-Object {
            -not ($_ -is [string]) -or [string]::IsNullOrWhiteSpace($_)
        }).Count -gt 0) {
            Add-IntegrityError "schemas/pipeline-contract.json release.$ContractField is missing or malformed."
            return
        }
    }
    $PublishableStatuses = if ($null -ne $LifecycleContract -and
        $null -ne $LifecycleContract.PSObject.Properties['publishableStatuses']) {
        @($LifecycleContract.publishableStatuses)
    }
    else { @() }
    if ($PublishableStatuses.Count -eq 0 -or
        @($PublishableStatuses | Where-Object {
            -not ($_ -is [string]) -or [string]::IsNullOrWhiteSpace($_)
        }).Count -gt 0) {
        Add-IntegrityError 'schemas/pipeline-contract.json lifecycle.publishableStatuses is missing or malformed.'
        return
    }

    Test-ExactProperties $Release @($ReleaseContract.fields) `
        "$Slug/release.json"
    if ($null -ne $Release.artifacts) {
        Test-ExactProperties -Object $Release.artifacts `
            -Properties @($ReleaseContract.artifactContainerFields) `
            -Context "$Slug/release.json artifacts"
        foreach ($ArtifactKey in @('story', 'canonDelta')) {
            $Artifact = $Release.artifacts.$ArtifactKey
            Test-ExactProperties -Object $Artifact `
                -Properties @($ReleaseContract.artifactFields) `
                -Context "$Slug/release.json artifacts.$ArtifactKey"
        }
    }
    else {
        Add-IntegrityError "$Slug/release.json artifacts must be an object."
    }
    Test-ExactProperties $Release.review `
        @($ReleaseContract.reviewFields) `
        "$Slug/release.json review"
    Test-ExactProperties $Release.nameCheck `
        @($ReleaseContract.nameCheckFields) `
        "$Slug/release.json nameCheck"
    Test-ExactProperties $Release.provenance `
        @($ReleaseContract.provenanceFields) `
        "$Slug/release.json provenance"
    if ($Release.schemaVersion -ne $ReleaseContract.schemaVersion) {
        Add-IntegrityError "$Slug/release.json schemaVersion must be $($ReleaseContract.schemaVersion)."
    }
    if ($Release.storySlug -cne $Slug) { Add-IntegrityError "$Slug/release.json storySlug mismatch." }
    if (-not ($Release.certified -is [bool])) { Add-IntegrityError "$Slug/release.json certified must be boolean."; return }

    $RequiresCertificate = $Metadata.status -cin $PublishableStatuses
    if ($RequiresCertificate -and $Release.certified -ne $true) {
        Add-IntegrityError "$Slug status '$($Metadata.status)' requires a certified release.json."
        return
    }
    if (-not $Release.certified) {
        return
    }
    if (-not $RequiresCertificate) {
        Add-IntegrityError "$Slug may be certified only in a centrally publishable lifecycle status."
    }
    $ReleasePath = Join-Path $StoryDirectory 'release.json'
    try {
        $ReleaseDocument = [Text.Json.JsonDocument]::Parse(
            [IO.File]::ReadAllText($ReleasePath)
        )
        $CertifiedAtText = $ReleaseDocument.RootElement.GetProperty('certifiedAt').GetString()
        $NameCheckedAtText = $ReleaseDocument.RootElement.GetProperty('nameCheck').GetProperty('checkedAt').GetString()
        $ReviewReviewedAtText = $ReleaseDocument.RootElement.GetProperty('review').GetProperty('reviewedAt').GetString()
    }
    catch {
        Add-IntegrityError "$Slug/release.json timestamp fields must be JSON strings."
        return
    }
    finally {
        if ($null -ne $ReleaseDocument) { $ReleaseDocument.Dispose() }
    }
    $ParsedCertifiedAt = [DateTimeOffset]::MinValue
    $CertifiedAtIsValid = [DateTimeOffset]::TryParse(
        $CertifiedAtText,
        [ref]$ParsedCertifiedAt
    )
    if (-not $CertifiedAtIsValid -or $ParsedCertifiedAt.Offset -ne [TimeSpan]::Zero) {
        Add-IntegrityError "$Slug/release.json certifiedAt must be an ISO-8601 UTC timestamp."
    }

    if ($null -eq $Release.artifacts -or $null -eq $Release.review -or
        $null -eq $Release.nameCheck -or $null -eq $Release.provenance) {
        Add-IntegrityError "$Slug/release.json has null certificate sections."
        return
    }
    foreach ($ArtifactSpec in @(
        [pscustomobject]@{ Key = 'story'; Path = '05-story.md' },
        [pscustomobject]@{ Key = 'canonDelta'; Path = '06-canon-delta.md' }
    )) {
        $Artifact = $Release.artifacts.($ArtifactSpec.Key)
        if ($null -eq $Artifact) {
            Add-IntegrityError "$Slug/release.json is missing artifacts.$($ArtifactSpec.Key)."
            continue
        }
        if ($Artifact.path -cne $ArtifactSpec.Path) {
            Add-IntegrityError "$Slug/release.json artifacts.$($ArtifactSpec.Key).path must be '$($ArtifactSpec.Path)'."
        }
        if ($Artifact.sha256 -cnotmatch '^[a-f0-9]{64}$') {
            Add-IntegrityError "$Slug/release.json artifacts.$($ArtifactSpec.Key).sha256 is invalid."
            continue
        }
        $ArtifactPath = Join-Path $StoryDirectory $ArtifactSpec.Path
        if ((Get-RawSha256 $ArtifactPath) -cne $Artifact.sha256) {
            Add-IntegrityError "$Slug release hash mismatch for $($ArtifactSpec.Path); certificate is stale."
        }
    }

    $ReviewPassIsInteger = $Release.review.pass -is [long] -or
        $Release.review.pass -is [int]
    $DraftPassIsInteger = $Release.review.draftPass -is [long] -or
        $Release.review.draftPass -is [int]
    $CriticalIsInteger = $Release.review.unresolvedCritical -is [long] -or
        $Release.review.unresolvedCritical -is [int]
    $MajorIsInteger = $Release.review.unresolvedMajor -is [long] -or
        $Release.review.unresolvedMajor -is [int]
    if ($Release.review.artifact -cne '05-story.md' -or
        $Release.review.verdict -cne 'PASS' -or
        -not $ReviewPassIsInteger -or
        [int]$Release.review.pass -lt 1 -or
        -not $DraftPassIsInteger -or
        [int]$Release.review.draftPass -lt 1 -or
        [int]$Release.review.draftPass -ge [int]$Release.review.pass -or
        -not $CriticalIsInteger -or
        -not $MajorIsInteger -or
        $Release.review.unresolvedCritical -ne 0 -or
        $Release.review.unresolvedMajor -ne 0 -or
        -not ($Release.review.reviewer -is [string]) -or
        [string]::IsNullOrWhiteSpace($Release.review.reviewer) -or
        $Release.review.passSha256 -cnotmatch '^[a-f0-9]{64}$' -or
        $Release.review.historySha256 -cnotmatch '^[a-f0-9]{64}$' -or
        $Release.review.draftPassSha256 -cnotmatch '^[a-f0-9]{64}$') {
        Add-IntegrityError "$Slug/release.json review receipt is not a zero-blocker 05-story.md PASS."
    }
    $ParsedReviewAt = [DateTimeOffset]::MinValue
    $ReviewAtIsValid = [DateTimeOffset]::TryParse(
        $ReviewReviewedAtText,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::RoundtripKind,
        [ref]$ParsedReviewAt
    )
    if (-not $ReviewAtIsValid -or
        $ReviewReviewedAtText -cnotmatch '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$') {
        Add-IntegrityError "$Slug/release.json review.reviewedAt must be an ISO-8601 timestamp with an explicit offset."
    }
    if ($null -ne $ReviewContract -and $null -ne $ReviewContract.ReleaseReview) {
        try {
            Assert-ReviewReleaseBinding -ReleaseReview $Release.review `
                -ReviewContract $ReviewContract
        }
        catch {
            Add-IntegrityError "$Slug $($_.Exception.Message)"
        }
        if ($Release.artifacts.story.sha256 -cne $ReviewContract.LatestPass.ArtifactSha256 -or
            $Release.artifacts.canonDelta.sha256 -cne $ReviewContract.LatestPass.CanonDeltaSha256) {
            Add-IntegrityError "$Slug release artifact hashes do not match the hashes certified in 04-review.md."
        }
    }
    foreach ($ProvenanceSpec in @(
        [pscustomobject]@{ Field = 'promptSha256'; Path = '00-prompt.md' },
        [pscustomobject]@{ Field = 'canonBriefSha256'; Path = '01-canon-brief.md' },
        [pscustomobject]@{ Field = 'planSha256'; Path = '02-story-plan.md' },
        [pscustomobject]@{ Field = 'draftSha256'; Path = '03-draft.md' },
        [pscustomobject]@{ Field = 'authorityManifestSha256'; Path = 'authority.json' },
        [pscustomobject]@{ Field = 'handoffLedgerSha256'; Path = 'handoffs.json' }
    )) {
        $Digest = $Release.provenance.($ProvenanceSpec.Field)
        if ($Digest -cnotmatch '^[a-f0-9]{64}$') {
            Add-IntegrityError "$Slug/release.json provenance.$($ProvenanceSpec.Field) is invalid."
            continue
        }
        $ProvenancePath = Join-Path $StoryDirectory $ProvenanceSpec.Path
        if (-not (Test-Path -LiteralPath $ProvenancePath -PathType Leaf) -or
            (Get-RawSha256 $ProvenancePath) -cne $Digest) {
            Add-IntegrityError "$Slug release provenance is stale for $($ProvenanceSpec.Path)."
        }
    }
    $CurrentAuthoritySha256 = Get-RawSha256 (Join-Path $StoryDirectory 'authority.json')
    $ReviewAuthoritySha256 = [string]$Release.provenance.reviewAuthorityManifestSha256
    $PreparationSha256 = $Release.provenance.promotionPreparationSha256
    if ($ReviewAuthoritySha256 -cnotmatch '^[a-f0-9]{64}$') {
        Add-IntegrityError "$Slug/release.json provenance.reviewAuthorityManifestSha256 is invalid."
    }
    if ($null -eq $PreparationSha256) {
        if ($ReviewAuthoritySha256 -cne $CurrentAuthoritySha256) {
            Add-IntegrityError "$Slug unbridged release must review the current authority.json bytes."
        }
    }
    elseif ($PreparationSha256 -cnotmatch '^[a-f0-9]{64}$') {
        Add-IntegrityError "$Slug/release.json provenance.promotionPreparationSha256 is invalid."
    }
    else {
        $PromotionPath = Join-Path $StoryDirectory 'promotion.json'
        try {
            $Promotion = Get-Content -LiteralPath $PromotionPath -Raw | ConvertFrom-Json
            $ExpectedPreparationSha256 = Assert-PromotionPreparationSha256 $Promotion
            if ($Metadata.status -cne 'final' -or $Metadata.canon -ne $true -or
                $Promotion.state -cne 'completed' -or $Promotion.storySlug -cne $Slug -or
                $PreparationSha256 -cne $ExpectedPreparationSha256 -or
                $ReviewAuthoritySha256 -cne $Promotion.authority.sha256 -or
                $Promotion.bundle.story.sha256 -cne $Release.artifacts.story.sha256 -or
                $Promotion.bundle.canonDelta.sha256 -cne $Release.artifacts.canonDelta.sha256 -or
                $Promotion.completion.candidateAuthorityManifestSha256 -cne $ReviewAuthoritySha256 -or
                $Promotion.completion.finalAuthorityManifestSha256 -cne $CurrentAuthoritySha256 -or
                $Promotion.completion.finalReleaseSha256 -cne (Get-RawSha256 $ReleasePath)) {
                Add-IntegrityError "$Slug release promotion authority bridge is stale or incomplete."
            }
        }
        catch {
            Add-IntegrityError "$Slug release promotion authority bridge is invalid: $($_.Exception.Message)"
        }
    }
    if ($Release.nameCheck.story -cne $Slug -or
        $Release.nameCheck.phase -cne 'Final' -or
        $Release.nameCheck.passed -ne $true -or
        $Release.nameCheck.receiptId -cnotmatch '^[a-f0-9]{64}$' -or
        $Release.nameCheck.storySha256 -cnotmatch '^[a-f0-9]{64}$' -or
        $Release.nameCheck.canonDeltaSha256 -cnotmatch '^[a-f0-9]{64}$' -or
        $Release.nameCheck.scopedRegistrySha256 -cnotmatch '^[a-f0-9]{64}$' -or
        $Release.nameCheck.activeRegistrySha256 -cnotmatch '^[a-f0-9]{64}$' -or
        $Release.nameCheck.checkerVersion -cne 'story-names/2' -or
        $null -eq $Release.nameCheck.warnings) {
        Add-IntegrityError "$Slug/release.json nameCheck receipt is invalid."
    }
    if ($Release.nameCheck.storySha256 -cne $Release.artifacts.story.sha256 -or
        $Release.nameCheck.canonDeltaSha256 -cne $Release.artifacts.canonDelta.sha256) {
        Add-IntegrityError "$Slug release name receipt does not bind the certified story and canon-delta hashes."
    }
    if ($Release.nameCheck.receiptId -cmatch '^[a-f0-9]{64}$' -and
        $Release.nameCheck.storySha256 -cmatch '^[a-f0-9]{64}$' -and
        $Release.nameCheck.canonDeltaSha256 -cmatch '^[a-f0-9]{64}$' -and
        $Release.nameCheck.scopedRegistrySha256 -cmatch '^[a-f0-9]{64}$' -and
        $Release.nameCheck.activeRegistrySha256 -cmatch '^[a-f0-9]{64}$' -and
        $Release.provenance.planSha256 -cmatch '^[a-f0-9]{64}$' -and
        $Release.nameCheck.checkerVersion -is [string]) {
        $WarningsJson = ConvertTo-Json -InputObject @($Release.nameCheck.warnings) -Compress
        $WarningsHash = Get-ReviewTextSha256 $WarningsJson
        $ArtifactHashes = @(
            Get-ReviewTextSha256 (
                "$($Release.nameCheck.storySha256)`n$($Release.nameCheck.canonDeltaSha256)"
            )
            Get-ReviewTextSha256 (
                "$($Release.nameCheck.storySha256)`n$($Release.nameCheck.canonDeltaSha256)`n$($Release.provenance.planSha256)"
            )
        )
        $ExpectedReceiptIds = @($ArtifactHashes | ForEach-Object {
            Get-ReviewTextSha256 (
                "$($Release.nameCheck.checkerVersion)`n$Slug`nfinal`n$_`n" +
                "$($Release.nameCheck.scopedRegistrySha256)`n" +
                "$($Release.nameCheck.activeRegistrySha256)`n$WarningsHash"
            )
        })
        if ($Release.nameCheck.receiptId -cnotin $ExpectedReceiptIds) {
            Add-IntegrityError "$Slug release name receiptId checksum is inconsistent with its stored historical fields."
        }
    }
    $ParsedNameCheckedAt = [DateTimeOffset]::MinValue
    $NameCheckedAtIsValid = [DateTimeOffset]::TryParse(
        $NameCheckedAtText,
        [ref]$ParsedNameCheckedAt
    )
    if (-not $NameCheckedAtIsValid -or $ParsedNameCheckedAt.Offset -ne [TimeSpan]::Zero) {
        Add-IntegrityError "$Slug/release.json nameCheck.checkedAt must be an ISO-8601 UTC timestamp."
    }
    if ($null -ne $NameReceipt) {
        foreach ($Field in @(
            'story', 'phase', 'passed', 'storySha256', 'canonDeltaSha256',
            'scopedRegistrySha256', 'checkerVersion'
        )) {
            if ($Release.nameCheck.$Field -cne $NameReceipt.$Field) {
                Add-IntegrityError "$Slug release name receipt field '$Field' is stale."
            }
        }
        if ($null -ne $ReviewContract -and
            $null -ne $ReviewContract.LatestPass -and
            $ReviewContract.LatestPass.ScopedRegistrySha256 -cne
                $NameReceipt.scopedRegistrySha256) {
            Add-IntegrityError "$Slug latest final review did not bind the current scoped name-registry digest."
        }
    }
}

function Test-SourceRecord {
    param(
        [Parameter(Mandatory = $true)][object]$Entry,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $Context = "sources/MANIFEST.json record '$($Entry.recordId)'"
    Test-ExactProperties $Entry @(
        'recordId', 'workTitle', 'reviewedForm', 'path', 'sha256',
        'reviewedSha256', 'authority', 'historicalRevision', 'historicalBlobOid'
    ) $Context
    if (-not ($Entry.recordId -is [string]) -or
        $Entry.recordId -notmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$') {
        Add-IntegrityError "$Context recordId is invalid."
    }
    if ($Entry.authority -cne 'none') { Add-IntegrityError "$Context authority must be 'none'." }
    if ($Entry.sha256 -cnotmatch '^[a-f0-9]{64}$') { Add-IntegrityError "$Context sha256 is invalid."; return }
    if ($Entry.reviewedSha256 -cnotmatch '^[a-f0-9]{64}$') {
        Add-IntegrityError "$Context reviewedSha256 is invalid."
    }
    if ($Entry.historicalRevision -cnotmatch '^[a-f0-9]{40,64}$' -or
        $Entry.historicalRevision.Length -notin @(40, 64)) {
        Add-IntegrityError "$Context historicalRevision must be a full lowercase Git object ID."
    }
    if ($Entry.historicalBlobOid -cnotmatch '^[a-f0-9]{40,64}$' -or
        $Entry.historicalBlobOid.Length -notin @(40, 64)) {
        Add-IntegrityError "$Context historicalBlobOid must be a full lowercase Git object ID."
    }

    $RelativePath = ([string]$Entry.path).Replace('\', '/')
    if ($RelativePath -notmatch '^sources/records/[^\x00-\x1f:]+$' -or
        $RelativePath -match '(^|/)\.\.(/|$)') {
        Add-IntegrityError "$Context path is not a safe path below sources/records/."
        return
    }
    $FullPath = [IO.Path]::GetFullPath((Join-Path $Root $RelativePath))
    $ImportRoot = [IO.Path]::GetFullPath((Join-Path $Root 'sources/records')) +
        [IO.Path]::DirectorySeparatorChar
    if (-not $FullPath.StartsWith($ImportRoot, [StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $FullPath -PathType Leaf)) {
        Add-IntegrityError "$Context path is missing or escapes sources/records/."
        return
    }
    $RawHash = Get-RawSha256 $FullPath
    if ($RawHash -cne $Entry.sha256) {
        Add-IntegrityError "$Context sha256 digest does not match current raw bytes."
    }
    if ($Entry.reviewedSha256 -cmatch '^[a-f0-9]{64}$' -and
        $RawHash -cne $Entry.reviewedSha256) {
        $CrlfHash = Get-CrlfExpandedSha256 $FullPath
        if ($CrlfHash -cne $Entry.reviewedSha256) {
            Add-IntegrityError "$Context reviewedSha256 does not match raw bytes or the permitted historical LF-to-CRLF normalization."
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
$PipelineContractPath = Join-Path $ProjectRoot 'schemas/pipeline-contract.json'
$script:PipelineContract = Get-JsonFile $PipelineContractPath 'pipeline contract'
if ($null -eq $script:PipelineContract -or
    $script:PipelineContract.schemaVersion -ne 1) {
    Add-IntegrityError 'schemas/pipeline-contract.json is missing or unsupported.'
}
$StoriesRoot = Join-Path $ProjectRoot 'stories'
$IndexPath = Join-Path $StoriesRoot 'INDEX.md'
$NameChecker = Join-Path $ProjectRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
$PipelineArtifactChecker = Join-Path $ProjectRoot `
    '.agents/skills/story-integrity/scripts/Test-PipelineArtifacts.ps1'

try { $IndexRows = @(Get-IndexRows $IndexPath) }
catch { Add-IntegrityError $_.Exception.Message; $IndexRows = @() }

$StoryDirectories = @()
if (Test-Path -LiteralPath $StoriesRoot -PathType Container) {
    $StoryDirectories = @(Get-ChildItem -LiteralPath $StoriesRoot -Directory |
        Where-Object { $_.Name -notmatch '^[_.]' })
}
else { Add-IntegrityError "Stories directory not found: $StoriesRoot" }

if ($Story) {
    $StoryDirectories = @($StoryDirectories | Where-Object Name -ceq $Story)
    $IndexRows = @($IndexRows | Where-Object Slug -ceq $Story)
    if ($StoryDirectories.Count -ne 1) { Add-IntegrityError "Story directory '$Story' is missing." }
    if ($IndexRows.Count -ne 1) { Add-IntegrityError "Story index row '$Story' is missing or duplicated." }
}
else {
    $DirectorySlugs = @($StoryDirectories.Name | Sort-Object)
    $IndexSlugs = @($IndexRows.Slug | Sort-Object)
    foreach ($Slug in @($DirectorySlugs | Where-Object { $_ -notin $IndexSlugs })) {
        Add-IntegrityError "Story directory '$Slug' has no stories/INDEX.md row."
    }
    foreach ($Slug in @($IndexSlugs | Where-Object { $_ -notin $DirectorySlugs })) {
        Add-IntegrityError "stories/INDEX.md row '$Slug' has no story directory."
    }
}

if (-not $Story) {
    $PipelineContractChecker = Join-Path $ProjectRoot `
        '.agents/skills/story-integrity/scripts/Test-PipelineContract.ps1'
    if (-not (Test-Path -LiteralPath $PipelineContractChecker -PathType Leaf)) {
        Add-IntegrityError "Pipeline contract validator is missing: $PipelineContractChecker"
    }
    else {
        try {
            $PipelineContractReceipt = & $PipelineContractChecker `
                -OutputFormat Json -ProjectRoot $ProjectRoot | ConvertFrom-Json
            Test-ExactProperties -Object $PipelineContractReceipt `
                -Properties @('schemaVersion', 'passed', 'errors') `
                -Context 'pipeline contract validator receipt'
            if (($PipelineContractReceipt.schemaVersion -isnot [long] -and
                    $PipelineContractReceipt.schemaVersion -isnot [int]) -or
                $PipelineContractReceipt.schemaVersion -ne 1 -or
                $PipelineContractReceipt.passed -isnot [bool] -or
                $PipelineContractReceipt.passed -ne $true -or
                $PipelineContractReceipt.errors -isnot [array] -or
                @($PipelineContractReceipt.errors).Count -ne 0) {
                Add-IntegrityError 'Pipeline contract validator did not return an exact passing receipt.'
            }
        }
        catch {
            Add-IntegrityError "Pipeline contract validation failed: $($_.Exception.Message)"
        }
    }
    foreach ($RepositoryCheck in @(
        [pscustomobject]@{
            Name = 'source manifest'
            Path = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-SourceManifest.ps1'
        },
        [pscustomobject]@{
            Name = 'universe authority'
            Path = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-UniverseIntegrity.ps1'
        }
    )) {
        if (-not (Test-Path -LiteralPath $RepositoryCheck.Path -PathType Leaf)) {
            Add-IntegrityError "$($RepositoryCheck.Name) validator is missing: $($RepositoryCheck.Path)"
            continue
        }
        try {
            $Receipt = & $RepositoryCheck.Path -OutputFormat Json `
                -ProjectRoot $ProjectRoot | ConvertFrom-Json
            if ($Receipt.passed -ne $true) {
                Add-IntegrityError "$($RepositoryCheck.Name) validator did not pass."
            }
        }
        catch {
            Add-IntegrityError "$($RepositoryCheck.Name) validation failed: $($_.Exception.Message)"
        }
    }
}

if (-not $Story -and (Test-Path -LiteralPath $NameChecker -PathType Leaf)) {
    try {
        $null = & $NameChecker -OutputFormat Json -SkipConfusable -ProjectRoot $ProjectRoot |
            ConvertFrom-Json
    }
    catch {
        Add-IntegrityError "Global name registry validation failed: $($_.Exception.Message)"
    }
}
foreach ($Directory in $StoryDirectories) {
    $Slug = $Directory.Name
    $Prefix = "${Slug}:"
    $RequiredArtifacts = @(
        '00-prompt.md', '01-canon-brief.md', '02-story-plan.md', '03-draft.md',
        '04-review.md', '05-story.md', '06-canon-delta.md', 'README.md',
        'story.json', 'release.json', 'authority.json', 'handoffs.json',
        'promotion.json'
    )
    foreach ($Artifact in $RequiredArtifacts) {
        if (-not (Test-Path -LiteralPath (Join-Path $Directory.FullName $Artifact) -PathType Leaf)) {
            Add-IntegrityError "$Prefix required artifact '$Artifact' is missing."
        }
    }
    $MissingRequired = @($RequiredArtifacts | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $Directory.FullName $_) -PathType Leaf)
    })
    if ($MissingRequired.Count -gt 0) { continue }

    $Metadata = Get-JsonFile (Join-Path $Directory.FullName 'story.json') "$Slug/story.json"
    if ($null -eq $Metadata) { continue }
    Test-StoryMetadata $Metadata $Slug

    if (-not (Test-Path -LiteralPath $PipelineArtifactChecker -PathType Leaf)) {
        Add-IntegrityError "Pipeline artifact validator is missing: $PipelineArtifactChecker"
    }
    else {
        try {
            $ArtifactCheckerArguments = @{
                Story = $Slug
                OutputFormat = 'Json'
                ProjectRoot = $ProjectRoot
            }
            if ($Metadata.status -ceq 'final') {
                $PromotionPreviewPath = Join-Path $Directory.FullName 'promotion.json'
                if (Test-Path -LiteralPath $PromotionPreviewPath -PathType Leaf) {
                    $PromotionPreview = Get-Content -LiteralPath $PromotionPreviewPath -Raw | ConvertFrom-Json
                    if ($PromotionPreview.state -ceq 'completed') {
                        $PreviewPreparation = Assert-PromotionPreparationSha256 $PromotionPreview
                        if ($PromotionPreview.preparationSha256 -cne $PreviewPreparation -or
                            [string]$PromotionPreview.authority.sha256 -cnotmatch '^[a-f0-9]{64}$') {
                            throw 'Completed promotion preview has an invalid authority bridge.'
                        }
                        $ArtifactCheckerArguments.ResearchAuthorityManifestSha256 = [string]$PromotionPreview.authority.sha256
                    }
                }
            }
            $PipelineArtifactReceipt = & $PipelineArtifactChecker @ArtifactCheckerArguments | ConvertFrom-Json
            Test-ExactProperties -Object $PipelineArtifactReceipt `
                -Properties @('schemaVersion', 'story', 'passed', 'errors') `
                -Context "$Prefix pipeline artifact validator receipt"
            if (($PipelineArtifactReceipt.schemaVersion -isnot [long] -and
                    $PipelineArtifactReceipt.schemaVersion -isnot [int]) -or
                $PipelineArtifactReceipt.schemaVersion -ne 1 -or
                $PipelineArtifactReceipt.story -cne $Slug -or
                $PipelineArtifactReceipt.passed -isnot [bool] -or
                $PipelineArtifactReceipt.passed -ne $true -or
                $PipelineArtifactReceipt.errors -isnot [array] -or
                @($PipelineArtifactReceipt.errors).Count -ne 0) {
                Add-IntegrityError "$Prefix pipeline artifact validator did not return an exact passing receipt."
                foreach ($ArtifactError in @($PipelineArtifactReceipt.errors)) {
                    if ($ArtifactError -is [string] -and
                        -not [string]::IsNullOrWhiteSpace($ArtifactError)) {
                        Add-IntegrityError "$Prefix pipeline artifact: $ArtifactError"
                    }
                }
            }
        }
        catch {
            Add-IntegrityError "$Prefix pipeline artifact validation failed: $($_.Exception.Message)"
        }
    }

    $PromotionPath = Join-Path $Directory.FullName 'promotion.json'
    $Promotion = Get-JsonFile $PromotionPath "$Slug/promotion.json"
    if ($null -ne $Promotion) {
        $PromotionSchemaPath = Join-Path $ProjectRoot `
            '.agents/skills/canon-maintenance/schemas/promotion.schema.json'
        if (-not (Test-Path -LiteralPath $PromotionSchemaPath -PathType Leaf)) {
            Add-IntegrityError "Promotion schema not found: $PromotionSchemaPath"
        }
        else {
            $SchemaErrors = @()
            if (-not (Test-Json -Json (Get-Content -LiteralPath $PromotionPath -Raw) `
                -SchemaFile $PromotionSchemaPath -ErrorVariable +SchemaErrors `
                -ErrorAction SilentlyContinue)) {
                Add-IntegrityError "$Prefix promotion.json failed its strict schema."
            }
        }
        if ($Promotion.storySlug -cne $Slug) {
            Add-IntegrityError "$Prefix promotion.json storySlug mismatch."
        }
        $AllowedPromotionStates = switch ([string]$Metadata.status) {
            'final' { @('completed') }
            'candidate' { @('not-prepared', 'ready') }
            default { @('not-prepared') }
        }
        if ($Promotion.state -notin $AllowedPromotionStates) {
            Add-IntegrityError "$Prefix promotion state '$($Promotion.state)' is invalid for lifecycle '$($Metadata.status)'."
        }
    }

    $Authority = Get-JsonFile (Join-Path $Directory.FullName 'authority.json') "$Slug/authority.json"
    if ($null -ne $Authority) {
        Test-AuthorityManifestInternal -Manifest $Authority -Slug $Slug `
            -AllowPending:($Metadata.status -in @('in-progress', 'abandoned'))
    }
    if ($Metadata.status -ceq 'candidate') {
        $AuthorityVerifier = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1'
        if (-not (Test-Path -LiteralPath $AuthorityVerifier -PathType Leaf)) {
            Add-IntegrityError "Authority manifest verifier not found: $AuthorityVerifier"
        }
        else {
            try {
                $AuthorityReceipt = & $AuthorityVerifier -Story $Slug -Verify `
                    -OutputFormat Json -ProjectRoot $ProjectRoot | ConvertFrom-Json
                if ($AuthorityReceipt.passed -ne $true -or
                    $AuthorityReceipt.story -cne $Slug -or
                    $AuthorityReceipt.manifestSha256 -cnotmatch '^[a-f0-9]{64}$') {
                    Add-IntegrityError "$Prefix authority verifier did not return a valid passing receipt."
                }
            }
            catch {
                Add-IntegrityError "$Prefix current authority manifest validation failed: $($_.Exception.Message)"
            }
        }
    }
    $HandoffLedger = $null
    if ($Metadata.status -in @('candidate', 'final')) {
        $HandoffLedger = Get-JsonFile `
            (Join-Path $Directory.FullName 'handoffs.json') `
            "$Slug/handoffs.json"
        $HandoffChecker = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-StoryHandoffs.ps1'
        if (-not (Test-Path -LiteralPath $HandoffChecker -PathType Leaf)) {
            Add-IntegrityError "Handoff checker not found: $HandoffChecker"
        }
        else {
            try {
                $HandoffReceipt = & $HandoffChecker -Story $Slug -RequireReleaseChain `
                    -OutputFormat Json -ProjectRoot $ProjectRoot | ConvertFrom-Json
                if ($HandoffReceipt.passed -ne $true -or
                    $HandoffReceipt.story -cne $Slug -or
                    $HandoffReceipt.ledgerSha256 -cnotmatch '^[a-f0-9]{64}$') {
                    Add-IntegrityError "$Prefix handoff checker did not return a valid passing receipt."
                }
            }
            catch {
                Add-IntegrityError "$Prefix release handoff chain validation failed: $($_.Exception.Message)"
            }
        }
    }

    foreach ($MarkdownName in @(
        '00-prompt.md', '01-canon-brief.md', '02-story-plan.md', '03-draft.md',
        '04-review.md', '05-story.md', '06-canon-delta.md', 'README.md'
    )) {
        $Markdown = Get-Content -LiteralPath (Join-Path $Directory.FullName $MarkdownName) -Raw
        if ($Markdown -match '{{[^{}]+}}') {
            Add-IntegrityError "$Prefix $MarkdownName contains unresolved template placeholder '$($Matches[0])'."
        }
        if ($Metadata.status -in @('candidate', 'final') -and
            ([string]::IsNullOrWhiteSpace($Markdown) -or $Markdown -match
                '(?i)capture the verbatim writing prompt here|complete working prose goes here|polished reader-facing prose goes here|reviewed artifact:\s*None|verdict:\s*PENDING|Pass 1\s+—\s+pending')) {
            Add-IntegrityError "$Prefix $MarkdownName still contains incomplete template content."
        }
    }

    $ReadmePath = Join-Path $Directory.FullName 'README.md'
    $Readme = Get-Content -LiteralPath $ReadmePath -Raw
    $HeadingMatch = [regex]::Match($Readme, '(?m)^#\s+(.+?)\s+—\s+production record\s*$')
    if (-not $HeadingMatch.Success) { Add-IntegrityError "$Prefix README heading is malformed." }
    elseif ($HeadingMatch.Groups[1].Value -cne $Metadata.title) { Add-IntegrityError "$Prefix README title disagrees with story.json." }
    $ReadmeExpected = [ordered]@{
        'Slug' = $Slug
        'Created' = [string]$Metadata.created
        'Current stage' = [string]$Metadata.stage
        'Status' = [string]$Metadata.status
        'Canon' = if ($Metadata.canon) { 'yes' } else { 'no' }
        'User disposition' = [string]$Metadata.userDisposition
        'Publish' = if ($Metadata.publish) { 'yes' } else { 'no' }
        'Promotion date' = if ($null -eq $Metadata.promotionDate) { '—' } else { [string]$Metadata.promotionDate }
    }
    foreach ($Pair in $ReadmeExpected.GetEnumerator()) {
        $Actual = Get-ReadmeValue $Readme $Pair.Key
        if ($null -eq $Actual) { Add-IntegrityError "$Prefix README is missing '$($Pair.Key)'." }
        elseif ($Actual -cne $Pair.Value) { Add-IntegrityError "$Prefix README '$($Pair.Key)' disagrees with story.json." }
    }

    $ChecklistMatches = @([regex]::Matches($Readme, '(?m)^- \[([ xX])\] (.+?)\s*$'))
    $Checklist = @{}
    foreach ($Match in $ChecklistMatches) {
        $Label = $Match.Groups[2].Value
        if ($Checklist.ContainsKey($Label)) { Add-IntegrityError "$Prefix README duplicates checklist item '$Label'." }
        $Checklist[$Label] = $Match.Groups[1].Value -match '[xX]'
    }
    $ChecklistLabels = @(
        'Prompt contract captured', 'Canon brief completed', 'Story plan completed',
        'Plan name check passed', 'Complete draft written', 'Draft review passed',
        'Critical and major findings resolved', 'Final story written',
        'Canon delta recorded', 'Final story review passed', 'Final name check passed',
        'Name registry updated', 'Release certificate issued', 'Story index updated',
        'Canon promotion explicitly approved (optional)'
    )
    foreach ($Label in $ChecklistLabels) {
        if (-not $Checklist.ContainsKey($Label)) { Add-IntegrityError "$Prefix README is missing checklist item '$Label'." }
    }
    if ($Metadata.status -in @('candidate', 'final')) {
        foreach ($Label in $ChecklistLabels | Where-Object { $_ -notlike '*promotion explicitly*' }) {
            if ($Checklist.ContainsKey($Label) -and -not $Checklist[$Label]) {
                Add-IntegrityError "$Prefix release-ready checklist item '$Label' is not checked."
            }
        }
    }
    if ($Checklist.ContainsKey('Canon promotion explicitly approved (optional)') -and
        $Checklist['Canon promotion explicitly approved (optional)'] -ne ($Metadata.status -eq 'final')) {
        Add-IntegrityError "$Prefix canon-promotion checklist does not match final status."
    }

    $FinalPath = Join-Path $Directory.FullName '05-story.md'
    $FinalContent = Get-Content -LiteralPath $FinalPath -Raw
    try { $FrontMatter = Get-FrontMatter $FinalContent }
    catch { Add-IntegrityError "$Prefix $($_.Exception.Message)"; $FrontMatter = @{} }
    $FrontExpected = [ordered]@{
        title = $Metadata.title
        slug = $Slug
        created = $Metadata.created
    }
    foreach ($Pair in $FrontExpected.GetEnumerator()) {
        if (-not $FrontMatter.ContainsKey($Pair.Key)) { Add-IntegrityError "$Prefix 05-story.md frontmatter is missing '$($Pair.Key)'." }
        elseif ($FrontMatter[$Pair.Key] -cne $Pair.Value) { Add-IntegrityError "$Prefix 05-story.md frontmatter '$($Pair.Key)' disagrees with story.json." }
    }
    foreach ($UnexpectedKey in @($FrontMatter.Keys | Where-Object { $_ -notin $FrontExpected.Keys })) {
        Add-IntegrityError "$Prefix 05-story.md frontmatter contains mutable or unknown field '$UnexpectedKey'."
    }

    $IndexRow = @($IndexRows | Where-Object Slug -ceq $Slug)
    if ($IndexRow.Count -eq 1) {
        $ExpectedCanon = if ($Metadata.canon) { 'yes' } else { 'no' }
        $ExpectedPromotion = if ($null -eq $Metadata.promotionDate) { '—' } else { $Metadata.promotionDate }
        if ($IndexRow[0].Title -cne $Metadata.title) { Add-IntegrityError "$Prefix index title disagrees with story.json." }
        if ($IndexRow[0].Status -cne $Metadata.status) { Add-IntegrityError "$Prefix index status disagrees with story.json." }
        if ($IndexRow[0].Canon -cne $ExpectedCanon) { Add-IntegrityError "$Prefix index canon disagrees with story.json." }
        if ($IndexRow[0].UserDisposition -cne $Metadata.userDisposition) { Add-IntegrityError "$Prefix index user disposition disagrees with story.json." }
        $ExpectedPublish = if ($Metadata.publish) { 'yes' } else { 'no' }
        if ($IndexRow[0].Publish -cne $ExpectedPublish) { Add-IntegrityError "$Prefix index publish disagrees with story.json." }
        if ($IndexRow[0].PromotionDate -cne $ExpectedPromotion) { Add-IntegrityError "$Prefix index promotion date disagrees with story.json." }
    }

    $NameReceipt = $null
    $StageOrder = @('prompt', 'canon-research', 'planning', 'drafting', 'draft-review', 'final-edit', 'final-review', 'candidate', 'final')
    $ShouldCheckNames = $Metadata.status -in @('candidate', 'final') -or
        [array]::IndexOf($StageOrder, [string]$Metadata.stage) -ge [array]::IndexOf($StageOrder, 'planning')
    if ($ShouldCheckNames) {
        if (-not (Test-Path -LiteralPath $NameChecker -PathType Leaf)) {
            Add-IntegrityError "Name checker not found: $NameChecker"
        }
        else {
            $NamePhase = if ($Metadata.status -in @('candidate', 'final')) { 'Final' } else { 'Plan' }
            try {
                $NameJson = & $NameChecker -Story $Slug -Phase $NamePhase -OutputFormat Json -ProjectRoot $ProjectRoot
                $NameReceipt = $NameJson | ConvertFrom-Json
                if ($NameReceipt.schemaVersion -ne 1 -or
                    $NameReceipt.passed -ne $true -or
                    $NameReceipt.story -cne $Slug -or
                    $NameReceipt.phase -cne $NamePhase -or
                    $NameReceipt.checkerVersion -cne 'story-names/2') {
                    Add-IntegrityError "$Prefix scoped name check did not return an exact passing receipt."
                }
            }
            catch { Add-IntegrityError "$Prefix scoped name check failed: $($_.Exception.Message)" }
        }
    }

    $ReviewContract = $null
    $ReviewContent = Get-Content -LiteralPath (Join-Path $Directory.FullName '04-review.md') -Raw
    if ($Metadata.status -in @('candidate', 'final')) {
        foreach ($BoundName in @('05-story.md', '06-canon-delta.md')) {
            $BoundPath = Join-Path $Directory.FullName $BoundName
            if (13 -in [IO.File]::ReadAllBytes($BoundPath)) {
                Add-IntegrityError "$Prefix $BoundName contains CR or CRLF bytes; release artifacts must use LF only."
            }
        }
        $Body = [regex]::Replace($FinalContent, '(?s)\A---\s*.*?\s*---\s*', '')
        $Body = [regex]::Replace($Body, '(?ms)<!--.*?-->', '')
        $WordCount = [regex]::Matches($Body, "[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*").Count
        if ($WordCount -lt 100 -or $Body -match '(?i)polished reader-facing prose goes here') {
            Add-IntegrityError "$Prefix candidate/final 05-story.md is placeholder or implausibly short ($WordCount words)."
        }
        $DeltaContent = Get-Content -LiteralPath (Join-Path $Directory.FullName '06-canon-delta.md') -Raw
        if ($DeltaContent -notmatch '(?m)^## Final character-facing name inventory\s*$') {
            Add-IntegrityError "$Prefix 06-canon-delta.md lacks the final name inventory."
        }
    }
    try {
        $ReviewArguments = @{
            Content = $ReviewContent
            StorySlug = $Slug
        }
        if ($Metadata.status -in @('candidate', 'final')) {
            $ReviewArguments.DraftSha256 = Get-RawSha256 (Join-Path $Directory.FullName '03-draft.md')
            $ReviewArguments.FinalSha256 = Get-RawSha256 (Join-Path $Directory.FullName '05-story.md')
            $ReviewArguments.CanonDeltaSha256 = Get-RawSha256 (Join-Path $Directory.FullName '06-canon-delta.md')
            $ReviewArguments.CanonBriefSha256 = Get-RawSha256 (Join-Path $Directory.FullName '01-canon-brief.md')
            $ReviewArguments.PlanSha256 = Get-RawSha256 (Join-Path $Directory.FullName '02-story-plan.md')
            $CurrentAuthoritySha256 = Get-RawSha256 (Join-Path $Directory.FullName 'authority.json')
            $ReleaseForReview = Get-Content -LiteralPath (Join-Path $Directory.FullName 'release.json') -Raw | ConvertFrom-Json
            $BoundReviewAuthoritySha256 = [string]$ReleaseForReview.provenance.reviewAuthorityManifestSha256
            if ($BoundReviewAuthoritySha256 -cnotmatch '^[a-f0-9]{64}$') {
                throw 'release.json lacks a valid review-authority provenance binding.'
            }
            if ($null -eq $ReleaseForReview.provenance.promotionPreparationSha256 -and
                $BoundReviewAuthoritySha256 -cne $CurrentAuthoritySha256) {
                throw 'An unbridged release must bind its review to current authority.json.'
            }
            $ReviewArguments.AuthorityManifestSha256 = $BoundReviewAuthoritySha256
            if ($null -ne $NameReceipt) {
                $ReviewArguments.ScopedRegistrySha256 = [string]$NameReceipt.scopedRegistrySha256
            }
            $ReviewArguments.RequireReleaseReady = $true
        }
        $ReviewContract = Get-StoryReviewContract @ReviewArguments
        if ($null -ne $HandoffLedger -and $Metadata.status -in @('candidate', 'final')) {
            Test-ReviewLedgerBindings -ReviewContract $ReviewContract `
                -Ledger $HandoffLedger -Slug $Slug
        }
    }
    catch {
        Add-IntegrityError "$Prefix review history contract failed: $($_.Exception.Message)"
    }

    $Release = Get-JsonFile (Join-Path $Directory.FullName 'release.json') "$Slug/release.json"
    if ($null -ne $Release) {
        try {
            Test-ReleaseCertificate $Release $Metadata $Directory.FullName $Slug $ReviewContract $NameReceipt
        }
        catch {
            $Trace = if ([string]::IsNullOrWhiteSpace($_.ScriptStackTrace)) {
                ''
            }
            else { " at $($_.ScriptStackTrace -replace '[\r\n]+', ' <- ')" }
            Add-IntegrityError "$Prefix release certificate validation failed: $($_.Exception.Message)$Trace"
        }
    }

}

$UniqueErrors = @($script:Errors | Sort-Object -Unique)
$UniqueWarnings = @($script:Warnings | Sort-Object -Unique)
$Result = [ordered]@{
    schemaVersion = 1
    passed = $UniqueErrors.Count -eq 0
    mode = if ($Story) { 'story' } else { 'repository' }
    story = if ($Story) { $Story } else { $null }
    checkedStories = $StoryDirectories.Count
    errors = $UniqueErrors
    warnings = $UniqueWarnings
}

if ($OutputFormat -eq 'Json') {
    Write-Output ($Result | ConvertTo-Json -Depth 6)
}
else {
    foreach ($Warning in $UniqueWarnings) { Write-Warning $Warning }
    if ($UniqueErrors.Count -gt 0) {
        Write-Host "Story integrity check failed with $($UniqueErrors.Count) error(s):" -ForegroundColor Red
        foreach ($Message in $UniqueErrors) { Write-Host "- $Message" -ForegroundColor Red }
    }
    else {
        Write-Output "Story integrity check passed for $($Result.mode) mode ($($Result.checkedStories) stor$(if ($Result.checkedStories -eq 1) { 'y' } else { 'ies' }))."
    }
}

if ($UniqueErrors.Count -gt 0) { exit 1 }
