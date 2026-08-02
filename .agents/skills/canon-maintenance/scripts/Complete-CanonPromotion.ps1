#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
    [string]$PromotionDate,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

function Get-Sha256ForBytes {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    $Hash = [Security.Cryptography.SHA256]::HashData($Bytes)
    return [Convert]::ToHexString($Hash).ToLowerInvariant()
}

function Test-ByteArraysEqual {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Left,
        [Parameter(Mandatory = $true)][byte[]]$Right
    )

    if ($Left.Length -ne $Right.Length) { return $false }
    for ($Index = 0; $Index -lt $Left.Length; $Index++) {
        if ($Left[$Index] -ne $Right[$Index]) { return $false }
    }
    return $true
}

function ConvertFrom-Utf8Bytes {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $Offset = 0
    if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xef -and
        $Bytes[1] -eq 0xbb -and $Bytes[2] -eq 0xbf) {
        $Offset = 3
    }
    try {
        return [Text.UTF8Encoding]::new($false, $true).GetString(
            $Bytes,
            $Offset,
            $Bytes.Length - $Offset
        )
    }
    catch {
        throw "$Label is not valid UTF-8: $($_.Exception.Message)"
    }
}

function ConvertTo-LfText {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content)

    return $Content.Replace("`r`n", "`n").Replace("`r", "`n")
}

function ConvertTo-Utf8LfBytes {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content)

    $Normalized = ConvertTo-LfText $Content
    return [Text.UTF8Encoding]::new($false).GetBytes($Normalized)
}

function Write-BytesAtomically {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][byte[]]$Bytes
    )

    $TemporaryPath = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllBytes($TemporaryPath, $Bytes)
        [IO.File]::Move($TemporaryPath, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryPath -PathType Leaf) {
            Remove-Item -LiteralPath $TemporaryPath -Force
        }
    }
}

function Write-Utf8LfAtomically {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )

    Write-BytesAtomically -Path $Path -Bytes (ConvertTo-Utf8LfBytes $Content)
}

function Assert-RequiredProperties {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string[]]$Properties,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ($null -eq $Value) { throw "$Label is null." }
    $Names = @($Value.PSObject.Properties.Name)
    foreach ($Property in $Properties) {
        if ($Property -notin $Names) {
            throw "$Label is missing required property '$Property'."
        }
    }
}

function ConvertFrom-JsonBytes {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][string]$Label
    )

    try {
        return (ConvertFrom-Utf8Bytes -Bytes $Bytes -Label $Label) |
            ConvertFrom-Json
    }
    catch {
        throw "$Label is invalid JSON: $($_.Exception.Message)"
    }
}

function Split-NormalizedLines {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content)

    return ,([regex]::Split((ConvertTo-LfText $Content), "`n"))
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
    $Cells = @($Line.Trim().Trim('|').Split('|') |
        ForEach-Object { $_.Trim() })
    if ($Cells.Count -ne $ExpectedCells) {
        throw "Malformed Markdown row in $Context (expected $ExpectedCells cells, found $($Cells.Count)): $Line"
    }
    return ,$Cells
}

function Set-RawMarkdownCell {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$RawCell,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $Leading = [regex]::Match($RawCell, '^\s*').Value
    $Trailing = [regex]::Match($RawCell, '\s*$').Value
    return $Leading + $Value + $Trailing
}

function ConvertFrom-MarkdownCell {
    param([Parameter(Mandatory = $true)][string]$Value)

    return ($Value.Trim() -replace '`', '').Trim()
}

function Test-SourceReferencesStory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Slug
    )

    $CodeReferences = @([regex]::Matches($Source, '`([^`]+)`') |
        ForEach-Object { $_.Groups[1].Value.Trim() })
    if ($CodeReferences.Count -gt 0) {
        return $CodeReferences -ccontains $Slug
    }
    $Pattern = '(?i)(?<![a-z0-9-])' + [regex]::Escape($Slug) +
        '(?![a-z0-9-])'
    return [regex]::IsMatch($Source, $Pattern)
}

function Set-ReadmeField {
    param(
        [AllowEmptyString()][string[]]$Lines,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $Pattern = '^-\s+' + [regex]::Escape($Label) + ':\s*.*$'
    $LineIndexes = @()
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index] -match $Pattern) { $LineIndexes += $Index }
    }
    if ($LineIndexes.Count -ne 1) {
        throw "README must contain exactly one '$Label' lifecycle field; found $($LineIndexes.Count)."
    }
    $Lines[$LineIndexes[0]] = "- ${Label}: $Value"
}

function Get-UpdatedReadme {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Date
    )

    [string[]]$Lines = Split-NormalizedLines $Content
    Set-ReadmeField $Lines 'Current stage' 'final'
    Set-ReadmeField $Lines 'Status' 'final'
    Set-ReadmeField $Lines 'Canon' 'yes'
    Set-ReadmeField $Lines 'User disposition' 'accepted'
    Set-ReadmeField $Lines 'Promotion date' $Date

    $PromotionPattern = '^-\s+\[([ xX])\]\s+Canon promotion explicitly approved \(optional\)\s*$'
    $PromotionMatches = @()
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index] -match $PromotionPattern) { $PromotionMatches += $Index }
    }
    if ($PromotionMatches.Count -ne 1) {
        throw "README must contain exactly one canon-promotion checklist item; found $($PromotionMatches.Count)."
    }
    $Lines[$PromotionMatches[0]] = '- [x] Canon promotion explicitly approved (optional)'
    return $Lines -join "`n"
}

function Get-UpdatedIndex {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Date,
        [Parameter(Mandatory = $true)][bool]$Publish
    )

    [string[]]$Lines = Split-NormalizedLines $Content
    $HeaderMatches = @()
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index] -match '^\|\s*Story\s*\|\s*Title\s*\|\s*Status\s*\|\s*Canon\s*\|\s*User disposition\s*\|\s*Publish\s*\|\s*Promotion date\s*\|\s*Notes\s*\|$') {
            $HeaderMatches += $Index
        }
    }
    if ($HeaderMatches.Count -ne 1) {
        throw "stories/INDEX.md must contain exactly one eight-column story table; found $($HeaderMatches.Count)."
    }
    $HeaderIndex = $HeaderMatches[0]
    if ($HeaderIndex + 1 -ge $Lines.Count) {
        throw 'stories/INDEX.md story table has no separator row.'
    }
    $Separator = Split-MarkdownRow $Lines[$HeaderIndex + 1] 8 'stories/INDEX.md separator'
    if (($Separator | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -ne 0) {
        throw 'stories/INDEX.md has an invalid table separator.'
    }

    $Seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $TargetLines = @()
    for ($Index = $HeaderIndex + 2; $Index -lt $Lines.Count; $Index++) {
        $Line = $Lines[$Index]
        if ([string]::IsNullOrWhiteSpace($Line) -or $Line -notmatch '^\s*\|') { break }
        $Cells = Split-MarkdownRow $Line 8 "stories/INDEX.md line $($Index + 1)"
        if ($Cells[0] -notmatch '^`([a-z0-9]+(?:-[a-z0-9]+)*)`$') {
            throw "Invalid story slug cell at stories/INDEX.md line $($Index + 1): $($Cells[0])"
        }
        $RowSlug = $Matches[1]
        if (-not $Seen.Add($RowSlug)) {
            throw "stories/INDEX.md contains duplicate slug '$RowSlug'."
        }
        if ($RowSlug -ceq $Slug) { $TargetLines += $Index }
    }
    if ($TargetLines.Count -ne 1) {
        throw "stories/INDEX.md must contain exactly one row for '$Slug'; found $($TargetLines.Count)."
    }

    $TargetIndex = $TargetLines[0]
    $TargetCells = Split-MarkdownRow $Lines[$TargetIndex] 8 "stories/INDEX.md row '$Slug'"
    $ExpectedPublish = if ($Publish) { 'yes' } else { 'no' }
    if ($TargetCells[2] -cne 'candidate' -or $TargetCells[3] -cne 'no' -or
        $TargetCells[4] -notin @('pending', 'accepted') -or
        $TargetCells[5] -cne $ExpectedPublish -or $TargetCells[6] -cne '—') {
        throw "stories/INDEX.md row '$Slug' is not an eligible candidate row matching story.json."
    }

    $RawParts = $Lines[$TargetIndex].Split('|')
    if ($RawParts.Count -ne 10) {
        throw "Malformed raw Markdown row for '$Slug' in stories/INDEX.md."
    }
    $RawParts[3] = Set-RawMarkdownCell $RawParts[3] 'final'
    $RawParts[4] = Set-RawMarkdownCell $RawParts[4] 'yes'
    $RawParts[5] = Set-RawMarkdownCell $RawParts[5] 'accepted'
    $RawParts[7] = Set-RawMarkdownCell $RawParts[7] $Date
    $Lines[$TargetIndex] = $RawParts -join '|'
    return $Lines -join "`n"
}

function Get-UpdatedRegistry {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Slug
    )

    [string[]]$Lines = Split-NormalizedLines $Content
    $Starts = @()
    $Ends = @()
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index].Contains('<!-- registry:start -->', [StringComparison]::Ordinal)) {
            $Starts += $Index
        }
        if ($Lines[$Index].Contains('<!-- registry:end -->', [StringComparison]::Ordinal)) {
            $Ends += $Index
        }
    }
    if ($Starts.Count -ne 1 -or $Ends.Count -ne 1 -or $Ends[0] -le $Starts[0] + 2) {
        throw 'stories/NAMES.md must contain one valid registry marker pair and table.'
    }

    $HeaderSeen = $false
    $SeparatorSeen = $false
    $TargetCount = 0
    for ($Index = $Starts[0] + 1; $Index -lt $Ends[0]; $Index++) {
        $Line = $Lines[$Index]
        if ([string]::IsNullOrWhiteSpace($Line)) { continue }
        if ($Line -notmatch '^\s*\|') {
            throw "Unexpected non-table content inside stories/NAMES.md registry markers at line $($Index + 1)."
        }
        $Cells = Split-MarkdownRow $Line 6 "stories/NAMES.md line $($Index + 1)"
        if ($Cells[0] -eq 'Character / entity') {
            if ($HeaderSeen -or $Index -ne $Starts[0] + 1) {
                throw "Unexpected or duplicate stories/NAMES.md header at line $($Index + 1)."
            }
            $HeaderSeen = $true
            continue
        }
        if (($Cells | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -eq 0) {
            if (-not $HeaderSeen -or $SeparatorSeen) {
                throw "Unexpected or duplicate stories/NAMES.md separator at line $($Index + 1)."
            }
            $SeparatorSeen = $true
            continue
        }
        if (-not $HeaderSeen -or -not $SeparatorSeen) {
            throw "Registry data appears before its header and separator at stories/NAMES.md line $($Index + 1)."
        }

        if (Test-SourceReferencesStory -Source $Cells[2] -Slug $Slug) {
            $State = (ConvertFrom-MarkdownCell $Cells[3]).ToLowerInvariant()
            if ($State -cne 'candidate') {
                throw "Exact story row at stories/NAMES.md line $($Index + 1) has state '$State', not 'candidate'."
            }
            $RawParts = $Line.Split('|')
            if ($RawParts.Count -ne 8) {
                throw "Malformed raw registry row at stories/NAMES.md line $($Index + 1)."
            }
            $RawParts[4] = Set-RawMarkdownCell $RawParts[4] 'canon'
            $Lines[$Index] = $RawParts -join '|'
            $TargetCount++
        }
    }
    if (-not $HeaderSeen -or -not $SeparatorSeen) {
        throw 'stories/NAMES.md registry is missing its header or separator.'
    }
    return [pscustomobject]@{
        Content = $Lines -join "`n"
        UpdatedRows = $TargetCount
    }
}

function Invoke-ExternalScript {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label,
        [string[]]$Arguments = @()
    )

    $OutputItems = @(& $script:Pwsh -NoLogo -NoProfile -NonInteractive -File $Path @Arguments 2>&1)
    $ExitCode = $LASTEXITCODE
    $Output = ($OutputItems | Out-String).Trim()
    if ($ExitCode -ne 0) {
        throw "$Label failed with exit code ${ExitCode}:`n$Output"
    }
    return $Output
}

function Invoke-JsonContract {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label,
        [string[]]$Arguments = @()
    )

    $Output = Invoke-ExternalScript -Path $Path -Label $Label -Arguments $Arguments
    try { return $Output | ConvertFrom-Json }
    catch { throw "$Label did not return valid JSON: $($_.Exception.Message)" }
}

function Assert-FilesMatchSnapshot {
    param(
        [Parameter(Mandatory = $true)][object[]]$Snapshot,
        [Parameter(Mandatory = $true)][string]$Context
    )

    foreach ($Entry in $Snapshot) {
        if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf)) {
            throw "$Context file is missing: $($Entry.Path)"
        }
        $Current = [IO.File]::ReadAllBytes($Entry.Path)
        if (-not (Test-ByteArraysEqual $Entry.Bytes $Current)) {
            throw "$Context bytes changed unexpectedly: $($Entry.Path)"
        }
    }
}

$ParsedDate = [datetime]::MinValue
if (-not [datetime]::TryParseExact(
    $PromotionDate,
    'yyyy-MM-dd',
    [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::None,
    [ref]$ParsedDate
)) {
    throw "PromotionDate '$PromotionDate' is not a valid calendar date in YYYY-MM-DD form."
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$script:Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
    throw "Story directory not found: $StoryDirectory"
}

$StoryJsonPath = Join-Path $StoryDirectory 'story.json'
$ReleasePath = Join-Path $StoryDirectory 'release.json'
$ReadmePath = Join-Path $StoryDirectory 'README.md'
$IndexPath = Join-Path $ProjectRoot 'stories/INDEX.md'
$NamesPath = Join-Path $ProjectRoot 'stories/NAMES.md'
$FinalStoryPath = Join-Path $StoryDirectory '05-story.md'
$CanonDeltaPath = Join-Path $StoryDirectory '06-canon-delta.md'
$NameScript = Join-Path $ProjectRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
$ReleaseScript = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/New-StoryRelease.ps1'
$IntegrityScript = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1'

$ProductionPaths = @(
    $StoryJsonPath, $ReleasePath, $ReadmePath, $IndexPath, $NamesPath
)
foreach ($Path in @($ProductionPaths + @(
    $FinalStoryPath, $CanonDeltaPath, $NameScript, $ReleaseScript,
    $IntegrityScript
))) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required promotion file not found: $Path"
    }
}

$ProductionSnapshot = @($ProductionPaths | ForEach-Object {
    [pscustomobject]@{ Path = $_; Bytes = [IO.File]::ReadAllBytes($_) }
})
$ArtifactSnapshot = @($FinalStoryPath, $CanonDeltaPath | ForEach-Object {
    [pscustomobject]@{ Path = $_; Bytes = [IO.File]::ReadAllBytes($_) }
})
$StoryHash = Get-Sha256ForBytes $ArtifactSnapshot[0].Bytes
$DeltaHash = Get-Sha256ForBytes $ArtifactSnapshot[1].Bytes
$MutationStarted = $false

try {
    $Metadata = ConvertFrom-JsonBytes $ProductionSnapshot[0].Bytes 'story.json'
    Assert-RequiredProperties $Metadata @(
        'schemaVersion', 'slug', 'stage', 'status', 'canon',
        'userDisposition', 'publish', 'promotionDate'
    ) 'story.json'
    if ($Metadata.schemaVersion -ne 1 -or $Metadata.slug -cne $Story) {
        throw "story.json must use schemaVersion 1 and exact slug '$Story'."
    }
    if ($Metadata.stage -cne 'candidate' -or $Metadata.status -cne 'candidate' -or
        $Metadata.canon -ne $false -or
        @('pending', 'accepted') -cnotcontains $Metadata.userDisposition -or
        $null -ne $Metadata.promotionDate -or -not ($Metadata.publish -is [bool])) {
        throw "Story '$Story' is not an eligible candidate."
    }
    $OriginalPublish = [bool]$Metadata.publish

    $Release = ConvertFrom-JsonBytes $ProductionSnapshot[1].Bytes 'release.json'
    Assert-RequiredProperties $Release @(
        'schemaVersion', 'certified', 'storySlug', 'artifacts', 'review',
        'nameCheck'
    ) 'release.json'
    Assert-RequiredProperties $Release.artifacts @('story', 'canonDelta') 'release.json artifacts'
    Assert-RequiredProperties $Release.artifacts.story @('path', 'sha256') 'release.json artifacts.story'
    Assert-RequiredProperties $Release.artifacts.canonDelta @('path', 'sha256') 'release.json artifacts.canonDelta'
    Assert-RequiredProperties $Release.nameCheck @(
        'story', 'passed', 'scopedRegistrySha256'
    ) 'release.json nameCheck'
    if ($Release.schemaVersion -ne 1 -or $Release.certified -ne $true -or
        $Release.storySlug -cne $Story) {
        throw "release.json is not a supported certified release for exact story '$Story'."
    }
    if ($Release.artifacts.story.path -cne '05-story.md' -or
        $Release.artifacts.canonDelta.path -cne '06-canon-delta.md' -or
        $Release.artifacts.story.sha256 -cne $StoryHash -or
        $Release.artifacts.canonDelta.sha256 -cne $DeltaHash) {
        throw 'release.json does not bind the current reviewed story and canon-delta bytes.'
    }

    $ScopedIntegrity = Invoke-JsonContract $IntegrityScript 'candidate story integrity preflight' @(
        '-Story', $Story, '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    if ($ScopedIntegrity.passed -ne $true -or $ScopedIntegrity.mode -cne 'story' -or
        $ScopedIntegrity.story -cne $Story -or $ScopedIntegrity.checkedStories -ne 1) {
        throw 'Candidate story integrity preflight returned an invalid passing receipt.'
    }

    $NameReceipt = Invoke-JsonContract $NameScript 'candidate final-name preflight' @(
        '-Story', $Story, '-Phase', 'Final', '-OutputFormat', 'Json',
        '-ProjectRoot', $ProjectRoot
    )
    if ($NameReceipt.passed -ne $true -or $NameReceipt.story -cne $Story -or
        $NameReceipt.phase -cne 'Final' -or
        $NameReceipt.storySha256 -cne $StoryHash -or
        $NameReceipt.canonDeltaSha256 -cne $DeltaHash -or
        $NameReceipt.scopedRegistrySha256 -cne
            $Release.nameCheck.scopedRegistrySha256) {
        throw 'Candidate final-name receipt does not match the certified release bundle.'
    }

    Assert-FilesMatchSnapshot $ProductionSnapshot 'preflight production snapshot'
    Assert-FilesMatchSnapshot $ArtifactSnapshot 'reviewed artifact snapshot'

    $ReadmeContent = ConvertFrom-Utf8Bytes $ProductionSnapshot[2].Bytes 'story README'
    $IndexContent = ConvertFrom-Utf8Bytes $ProductionSnapshot[3].Bytes 'stories/INDEX.md'
    $NamesContent = ConvertFrom-Utf8Bytes $ProductionSnapshot[4].Bytes 'stories/NAMES.md'
    $UpdatedReadme = Get-UpdatedReadme $ReadmeContent $PromotionDate
    $UpdatedIndex = Get-UpdatedIndex $IndexContent $Story $PromotionDate $OriginalPublish
    $UpdatedRegistry = Get-UpdatedRegistry $NamesContent $Story

    $Metadata.stage = 'final'
    $Metadata.status = 'final'
    $Metadata.canon = $true
    $Metadata.userDisposition = 'accepted'
    $Metadata.promotionDate = $PromotionDate
    if ([bool]$Metadata.publish -ne $OriginalPublish) {
        throw 'Internal error: story.json publish changed while preparing promotion.'
    }
    $UpdatedMetadata = (($Metadata | ConvertTo-Json -Depth 100) + "`n")

    $MutationStarted = $true
    Write-Utf8LfAtomically $StoryJsonPath $UpdatedMetadata
    Write-Utf8LfAtomically $ReadmePath $UpdatedReadme
    Write-Utf8LfAtomically $IndexPath $UpdatedIndex
    Write-Utf8LfAtomically $NamesPath $UpdatedRegistry.Content
    Assert-FilesMatchSnapshot $ArtifactSnapshot 'reviewed artifact snapshot'

    $null = Invoke-ExternalScript $ReleaseScript 'final release reissue' @(
        '-Story', $Story, '-ProjectRoot', $ProjectRoot
    )
    Assert-FilesMatchSnapshot $ArtifactSnapshot 'reviewed artifact snapshot'

    $FinalIntegrity = Invoke-JsonContract $IntegrityScript 'final story integrity validation' @(
        '-Story', $Story, '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    if ($FinalIntegrity.passed -ne $true -or $FinalIntegrity.story -cne $Story) {
        throw 'Final story integrity validation returned an invalid passing receipt.'
    }
    Assert-FilesMatchSnapshot $ArtifactSnapshot 'reviewed artifact snapshot'

    $RepositoryIntegrity = Invoke-JsonContract $IntegrityScript 'repository integrity validation' @(
        '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    if ($RepositoryIntegrity.passed -ne $true -or
        $RepositoryIntegrity.mode -cne 'repository') {
        throw 'Repository integrity validation returned an invalid passing receipt.'
    }
    Assert-FilesMatchSnapshot $ArtifactSnapshot 'reviewed artifact snapshot'

    $FinalReleaseBytes = [IO.File]::ReadAllBytes($ReleasePath)
    $FinalRelease = ConvertFrom-JsonBytes $FinalReleaseBytes 'reissued release.json'
    if ($FinalRelease.certified -ne $true -or $FinalRelease.storySlug -cne $Story -or
        $FinalRelease.artifacts.story.sha256 -cne $StoryHash -or
        $FinalRelease.artifacts.canonDelta.sha256 -cne $DeltaHash) {
        throw 'Reissued release.json no longer binds the reviewed artifact bytes.'
    }

    Write-Output "Canon promotion production records finalized: $Story ($PromotionDate)"
    Write-Output "Reviewed artifacts unchanged: 05-story.md $StoryHash; 06-canon-delta.md $DeltaHash"
    Write-Output "Registry rows promoted: $($UpdatedRegistry.UpdatedRows)"
    Write-Output 'result: PROMOTED'
}
catch {
    $FailureMessage = $_.Exception.Message
    $RollbackErrors = [Collections.Generic.List[string]]::new()
    if ($MutationStarted) {
        foreach ($Entry in $ProductionSnapshot) {
            try { Write-BytesAtomically -Path $Entry.Path -Bytes $Entry.Bytes }
            catch { $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)") }
        }
        foreach ($Entry in $ProductionSnapshot) {
            try {
                if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf) -or
                    -not (Test-ByteArraysEqual $Entry.Bytes ([IO.File]::ReadAllBytes($Entry.Path)))) {
                    $RollbackErrors.Add("$($Entry.Path): restored bytes do not match snapshot")
                }
            }
            catch { $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)") }
        }
    }
    foreach ($Entry in $ArtifactSnapshot) {
        try {
            if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf) -or
                -not (Test-ByteArraysEqual $Entry.Bytes ([IO.File]::ReadAllBytes($Entry.Path)))) {
                $RollbackErrors.Add("$($Entry.Path): reviewed artifact bytes changed unexpectedly")
            }
        }
        catch { $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)") }
    }

    if ($RollbackErrors.Count -gt 0) {
        throw "Canon promotion finalization failed: $FailureMessage`nRollback verification failed:`n- $($RollbackErrors -join "`n- ")"
    }
    if ($MutationStarted) {
        throw "Canon promotion finalization failed: $FailureMessage`nAll captured production records were restored byte-for-byte; reviewed artifacts were unchanged.`nresult: NO_CHANGES"
    }
    throw "Canon promotion preflight failed: $FailureMessage`nNo production writes were attempted; reviewed artifacts were unchanged.`nresult: NO_CHANGES"
}
