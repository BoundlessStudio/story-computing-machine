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
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
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
    if (($Separator | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -ne 0) {
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

function Get-MarkdownSection {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    $Pattern = '(?ms)^##\s+' + [regex]::Escape($Heading) +
        '\s*\r?\n(.*?)(?=^##\s+|\z)'
    $Match = [regex]::Match($Content, $Pattern)
    if (-not $Match.Success) { return $null }
    return $Match.Groups[1].Value.Trim()
}

function Get-CertificationValue {
    param(
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $Match = [regex]::Match(
        $Section,
        '(?im)^-\s+' + [regex]::Escape($Label) + ':\s*(.+?)\s*$'
    )
    if (-not $Match.Success) { return $null }
    return ($Match.Groups[1].Value.Trim() -replace '`', '')
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

    $Required = @(
        'schemaVersion', 'slug', 'title', 'created', 'stage', 'status',
        'canon', 'userDisposition', 'publish', 'promotionDate'
    )
    Test-ExactProperties $Metadata $Required "$Slug/story.json"
    if ($Metadata.schemaVersion -ne 1) { Add-IntegrityError "$Slug/story.json schemaVersion must be 1." }
    if ($Metadata.slug -cne $Slug) { Add-IntegrityError "$Slug/story.json slug must exactly match its directory." }
    if (-not ($Metadata.title -is [string]) -or [string]::IsNullOrWhiteSpace($Metadata.title)) {
        Add-IntegrityError "$Slug/story.json title must be a nonempty string."
    }
    if (-not ($Metadata.created -is [string]) -or $Metadata.created -notmatch '^\d{4}-\d{2}-\d{2}$') {
        Add-IntegrityError "$Slug/story.json created must be YYYY-MM-DD."
    }
    $AllowedStages = @(
        'prompt', 'canon-research', 'planning', 'drafting', 'draft-review',
        'final-edit', 'final-review', 'candidate', 'final', 'abandoned'
    )
    if ($Metadata.stage -notin $AllowedStages) {
        Add-IntegrityError "$Slug/story.json stage '$($Metadata.stage)' is not allowed."
    }
    if ($Metadata.status -notin @('in-progress', 'candidate', 'final', 'abandoned')) {
        Add-IntegrityError "$Slug/story.json status '$($Metadata.status)' is not allowed."
    }
    if (-not ($Metadata.canon -is [bool])) { Add-IntegrityError "$Slug/story.json canon must be boolean." }
    if (-not ($Metadata.publish -is [bool])) { Add-IntegrityError "$Slug/story.json publish must be boolean." }
    if ($Metadata.userDisposition -notin @('pending', 'accepted', 'rejected')) {
        Add-IntegrityError "$Slug/story.json userDisposition '$($Metadata.userDisposition)' is not allowed."
    }
    if ($null -ne $Metadata.promotionDate -and
        (-not ($Metadata.promotionDate -is [string]) -or
        $Metadata.promotionDate -notmatch '^\d{4}-\d{2}-\d{2}$')) {
        Add-IntegrityError "$Slug/story.json promotionDate must be null or YYYY-MM-DD."
    }
    switch ($Metadata.status) {
        'in-progress' {
            if ($Metadata.stage -in @('candidate', 'final', 'abandoned')) {
                Add-IntegrityError "$Slug in-progress status cannot use terminal stage '$($Metadata.stage)'."
            }
            if ($Metadata.canon -ne $false -or $Metadata.userDisposition -ne 'pending' -or
                $Metadata.publish -ne $false -or $null -ne $Metadata.promotionDate) {
                Add-IntegrityError "$Slug in-progress state requires canon=false, userDisposition=pending, publish=false, promotionDate=null."
            }
        }
        'candidate' {
            if ($Metadata.stage -ne 'candidate' -or $Metadata.canon -ne $false -or
                $Metadata.userDisposition -notin @('pending', 'accepted') -or
                $null -ne $Metadata.promotionDate) {
                Add-IntegrityError "$Slug candidate state requires stage=candidate, canon=false, pending/accepted disposition, promotionDate=null."
            }
        }
        'final' {
            if ($Metadata.stage -ne 'final' -or $Metadata.canon -ne $true -or
                $Metadata.userDisposition -ne 'accepted' -or
                $null -eq $Metadata.promotionDate) {
                Add-IntegrityError "$Slug final state requires stage=final, canon=true, accepted disposition, and promotionDate."
            }
        }
        'abandoned' {
            if ($Metadata.stage -ne 'abandoned' -or $Metadata.canon -ne $false -or
                $Metadata.userDisposition -ne 'rejected' -or $Metadata.publish -ne $false -or
                $null -ne $Metadata.promotionDate) {
                Add-IntegrityError "$Slug abandoned state requires stage=abandoned, canon=false, rejected disposition, publish=false, promotionDate=null."
            }
        }
    }
}

function Test-ReleaseCertificate {
    param(
        [Parameter(Mandatory = $true)][object]$Release,
        [Parameter(Mandatory = $true)][object]$Metadata,
        [Parameter(Mandatory = $true)][string]$StoryDirectory,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][hashtable]$ReviewCertification,
        [Parameter(Mandatory = $true)][AllowNull()][object]$NameReceipt
    )

    Test-ExactProperties $Release @(
        'schemaVersion', 'certified', 'storySlug', 'certifiedAt', 'artifacts',
        'review', 'nameCheck'
    ) "$Slug/release.json"
    if ($null -ne $Release.artifacts) {
        Test-ExactProperties -Object $Release.artifacts -Properties @('story', 'canonDelta') -Context "$Slug/release.json artifacts"
        foreach ($ArtifactKey in @('story', 'canonDelta')) {
            $Artifact = $Release.artifacts.$ArtifactKey
            Test-ExactProperties -Object $Artifact -Properties @('path', 'sha256') -Context "$Slug/release.json artifacts.$ArtifactKey"
        }
    }
    else {
        Add-IntegrityError "$Slug/release.json artifacts must be an object."
    }
    Test-ExactProperties $Release.review @(
        'artifact', 'pass', 'verdict', 'reviewer', 'unresolvedCritical',
        'unresolvedMajor'
    ) "$Slug/release.json review"
    Test-ExactProperties $Release.nameCheck @(
        'story', 'passed', 'checkedAt', 'scopedRegistrySha256'
    ) "$Slug/release.json nameCheck"
    if ($Release.schemaVersion -ne 1) { Add-IntegrityError "$Slug/release.json schemaVersion must be 1." }
    if ($Release.storySlug -cne $Slug) { Add-IntegrityError "$Slug/release.json storySlug mismatch." }
    if (-not ($Release.certified -is [bool])) { Add-IntegrityError "$Slug/release.json certified must be boolean."; return }

    $RequiresCertificate = $Metadata.status -in @('candidate', 'final')
    if ($RequiresCertificate -and $Release.certified -ne $true) {
        Add-IntegrityError "$Slug status '$($Metadata.status)' requires a certified release.json."
        return
    }
    if (-not $Release.certified) {
        if ($Metadata.status -ne 'in-progress' -and $Metadata.status -ne 'abandoned') {
            Add-IntegrityError "$Slug has an uncertified release in an invalid lifecycle state."
        }
        return
    }
    if (-not $RequiresCertificate) {
        Add-IntegrityError "$Slug may be certified only while candidate or final."
    }
    $ReleasePath = Join-Path $StoryDirectory 'release.json'
    try {
        $ReleaseDocument = [Text.Json.JsonDocument]::Parse(
            [IO.File]::ReadAllText($ReleasePath)
        )
        $CertifiedAtText = $ReleaseDocument.RootElement.GetProperty('certifiedAt').GetString()
        $NameCheckedAtText = $ReleaseDocument.RootElement.GetProperty('nameCheck').GetProperty('checkedAt').GetString()
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

    if ($null -eq $Release.artifacts -or $null -eq $Release.review -or $null -eq $Release.nameCheck) {
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
    $CriticalIsInteger = $Release.review.unresolvedCritical -is [long] -or
        $Release.review.unresolvedCritical -is [int]
    $MajorIsInteger = $Release.review.unresolvedMajor -is [long] -or
        $Release.review.unresolvedMajor -is [int]
    if ($Release.review.artifact -cne '05-story.md' -or
        $Release.review.verdict -cne 'PASS' -or
        -not $ReviewPassIsInteger -or
        [int]$Release.review.pass -lt 1 -or
        -not $CriticalIsInteger -or
        -not $MajorIsInteger -or
        $Release.review.unresolvedCritical -ne 0 -or
        $Release.review.unresolvedMajor -ne 0 -or
        -not ($Release.review.reviewer -is [string]) -or
        [string]::IsNullOrWhiteSpace($Release.review.reviewer)) {
        Add-IntegrityError "$Slug/release.json review receipt is not a zero-blocker 05-story.md PASS."
    }
    if ($ReviewCertification.Count -gt 0) {
        foreach ($Field in @('artifact', 'pass', 'verdict', 'reviewer', 'unresolvedCritical', 'unresolvedMajor')) {
            if ($Release.review.$Field -cne $ReviewCertification[$Field]) {
                Add-IntegrityError "$Slug release review.$Field does not match 04-review.md Current certification."
            }
        }
        if ($Release.artifacts.story.sha256 -cne $ReviewCertification.artifactSha256 -or
            $Release.artifacts.canonDelta.sha256 -cne $ReviewCertification.canonDeltaSha256) {
            Add-IntegrityError "$Slug release artifact hashes do not match the hashes certified in 04-review.md."
        }
    }
    if ($Release.nameCheck.story -cne $Slug -or $Release.nameCheck.passed -ne $true -or
        $Release.nameCheck.scopedRegistrySha256 -cnotmatch '^[a-f0-9]{64}$') {
        Add-IntegrityError "$Slug/release.json nameCheck receipt is invalid."
    }
    $ParsedNameCheckedAt = [DateTimeOffset]::MinValue
    $NameCheckedAtIsValid = [DateTimeOffset]::TryParse(
        $NameCheckedAtText,
        [ref]$ParsedNameCheckedAt
    )
    if (-not $NameCheckedAtIsValid -or $ParsedNameCheckedAt.Offset -ne [TimeSpan]::Zero) {
        Add-IntegrityError "$Slug/release.json nameCheck.checkedAt must be an ISO-8601 UTC timestamp."
    }
    if ($null -ne $NameReceipt -and
        $Release.nameCheck.scopedRegistrySha256 -cne $NameReceipt.scopedRegistrySha256) {
        Add-IntegrityError "$Slug release name receipt is stale relative to the scoped registry."
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
$StoriesRoot = Join-Path $ProjectRoot 'stories'
$IndexPath = Join-Path $StoriesRoot 'INDEX.md'
$NameChecker = Join-Path $ProjectRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'

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

$ManifestPath = Join-Path $ProjectRoot 'sources/MANIFEST.json'
$Manifest = $null
$ManifestEntries = @()
if (Test-Path -LiteralPath $ManifestPath -PathType Leaf) {
    $Manifest = Get-JsonFile $ManifestPath 'sources/MANIFEST.json'
    if ($null -ne $Manifest) {
        Test-ExactProperties $Manifest @(
            'schemaVersion', 'prepared', 'authority', 'decisionRecord',
            'records', 'externalRecords'
        ) 'sources/MANIFEST.json'
        if ($Manifest.schemaVersion -ne 1) { Add-IntegrityError 'sources/MANIFEST.json schemaVersion must be 1.' }
        if ($Manifest.authority -cne 'none') { Add-IntegrityError "sources/MANIFEST.json authority must be 'none'." }
        $DecisionPath = ([string]$Manifest.decisionRecord).Replace('\', '/')
        if ($DecisionPath -notmatch '^sources/decisions/[^\x00-\x1f:]+$' -or
            $DecisionPath -match '(^|/)\.\.(/|$)' -or
            -not (Test-Path -LiteralPath (Join-Path $ProjectRoot $DecisionPath) -PathType Leaf)) {
            Add-IntegrityError 'sources/MANIFEST.json decisionRecord is missing or unsafe.'
        }
        $ManifestEntries = @($Manifest.records)
        $ExternalEntries = @($Manifest.externalRecords)
        foreach ($Duplicate in @((@($ManifestEntries.recordId) + @($ExternalEntries.recordId)) |
            Group-Object | Where-Object Count -gt 1)) {
            Add-IntegrityError "sources/MANIFEST.json contains duplicate recordId '$($Duplicate.Name)'."
        }
        foreach ($External in $ExternalEntries) {
            Test-ExactProperties $External @(
                'recordId', 'workTitle', 'reviewedForm', 'logicalLocator',
                'authority'
            ) "sources/MANIFEST.json external record '$($External.recordId)'"
            if ($External.recordId -notmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$' -or
                $External.authority -cne 'none') {
                Add-IntegrityError "sources/MANIFEST.json external record '$($External.recordId)' has invalid ID or authority."
            }
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
        'story.json', 'release.json'
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

    $ReviewCertification = @{}
    $ReviewContent = Get-Content -LiteralPath (Join-Path $Directory.FullName '04-review.md') -Raw
    $CurrentCertification = Get-MarkdownSection $ReviewContent 'Current certification'
    if ($Metadata.status -in @('candidate', 'final')) {
        foreach ($BoundName in @('05-story.md', '06-canon-delta.md')) {
            $BoundPath = Join-Path $Directory.FullName $BoundName
            if (13 -in [IO.File]::ReadAllBytes($BoundPath)) {
                Add-IntegrityError "$Prefix $BoundName contains CR or CRLF bytes; release artifacts must use LF only."
            }
        }
        if ($null -eq $CurrentCertification) {
            Add-IntegrityError "$Prefix 04-review.md is missing Current certification."
        }
        else {
            $Artifact = Get-CertificationValue $CurrentCertification 'Reviewed artifact'
            $ReviewedStoryHash = Get-CertificationValue $CurrentCertification 'Artifact SHA-256'
            $ReviewedDeltaHash = Get-CertificationValue $CurrentCertification 'Canon delta SHA-256'
            $PassText = Get-CertificationValue $CurrentCertification 'Review pass'
            $Verdict = Get-CertificationValue $CurrentCertification 'Verdict'
            $Reviewer = Get-CertificationValue $CurrentCertification 'Reviewer'
            $Critical = Get-CertificationValue $CurrentCertification 'Unresolved Critical findings'
            $Major = Get-CertificationValue $CurrentCertification 'Unresolved Major findings'
            $NormalizedArtifact = if ($Artifact) { $Artifact.Replace('\', '/') } else { '' }
            if ($NormalizedArtifact -ne '05-story.md' -and
                -not $NormalizedArtifact.EndsWith("/$Slug/05-story.md", [StringComparison]::Ordinal)) {
                Add-IntegrityError "$Prefix current review does not certify this story's 05-story.md."
            }
            if ($ReviewedStoryHash -cnotmatch '^[a-f0-9]{64}$' -or
                $ReviewedDeltaHash -cnotmatch '^[a-f0-9]{64}$') {
                Add-IntegrityError "$Prefix current review must record lowercase story and canon-delta SHA-256 hashes."
            }
            else {
                if ($ReviewedStoryHash -cne (Get-RawSha256 (Join-Path $Directory.FullName '05-story.md'))) {
                    Add-IntegrityError "$Prefix 05-story.md differs from the currently reviewed artifact hash."
                }
                if ($ReviewedDeltaHash -cne (Get-RawSha256 (Join-Path $Directory.FullName '06-canon-delta.md'))) {
                    Add-IntegrityError "$Prefix 06-canon-delta.md differs from the currently reviewed canon-delta hash."
                }
            }
            if ($PassText -notmatch '^(\d+)(?:\s|$)') { Add-IntegrityError "$Prefix current review pass is invalid."; $PassNumber = 0 }
            else { $PassNumber = [int]$Matches[1] }
            if ($Verdict -cne 'PASS') { Add-IntegrityError "$Prefix current review verdict is not PASS." }
            if (-not $Reviewer -or $Reviewer -in @('None', 'unknown')) { Add-IntegrityError "$Prefix current review lacks a reviewer." }
            if ($Critical -cnotmatch '^\d+$' -or $Major -cnotmatch '^\d+$') {
                Add-IntegrityError "$Prefix current review blocker counts must be integers."
            }
            elseif ([int]$Critical -ne 0 -or [int]$Major -ne 0) {
                Add-IntegrityError "$Prefix current review has unresolved Critical or Major findings."
            }
            $ReviewCertification = @{
                artifact = '05-story.md'; pass = $PassNumber; verdict = $Verdict
                reviewer = $Reviewer; unresolvedCritical = if ($Critical -match '^\d+$') { [int]$Critical } else { -1 }
                unresolvedMajor = if ($Major -match '^\d+$') { [int]$Major } else { -1 }
                artifactSha256 = $ReviewedStoryHash; canonDeltaSha256 = $ReviewedDeltaHash
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
                if ($NameReceipt.passed -ne $true) { Add-IntegrityError "$Prefix scoped name check did not pass." }
            }
            catch { Add-IntegrityError "$Prefix scoped name check failed: $($_.Exception.Message)" }
        }
    }

    $Release = Get-JsonFile (Join-Path $Directory.FullName 'release.json') "$Slug/release.json"
    if ($null -ne $Release) {
        Test-ReleaseCertificate $Release $Metadata $Directory.FullName $Slug $ReviewCertification $NameReceipt
    }

}

if (-not $Story -and $null -ne $Manifest) {
    foreach ($Entry in $ManifestEntries) {
        Test-SourceRecord $Entry $ProjectRoot
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
