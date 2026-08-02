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
. (Join-Path $PSScriptRoot '../../story-integrity/scripts/PromotionContracts.ps1')

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
        $Parameters = @{}
        if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
            $Parameters.DateKind = 'String'
        }
        return (ConvertFrom-Utf8Bytes -Bytes $Bytes -Label $Label) |
            ConvertFrom-Json @Parameters
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
    if (@($Separator | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -ne 0) {
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
        if (@($Cells | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -eq 0) {
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

function Get-Sha256ForText {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    return Get-Sha256ForBytes ([Text.UTF8Encoding]::new($false).GetBytes($Text))
}

function Assert-PromotionSchema {
    param(
        [Parameter(Mandatory = $true)][string]$Json,
        [Parameter(Mandatory = $true)][string]$SchemaPath,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $ValidationErrors = @()
    $Valid = Test-Json -Json $Json -SchemaFile $SchemaPath -ErrorVariable +ValidationErrors -ErrorAction SilentlyContinue
    if (-not $Valid) {
        $Details = @($ValidationErrors | ForEach-Object { $_.Exception.Message }) -join '; '
        throw "$Label failed schema validation: $Details"
    }
}

function Get-ProjectRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )

    return ([IO.Path]::GetRelativePath($Root, $Path)).Replace('\', '/')
}

function Resolve-ProjectRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if ([IO.Path]::IsPathRooted($RelativePath) -or $RelativePath.Contains('\') -or
        $RelativePath -match '(^|/)\.\.?(/|$)') {
        throw "$Label is not a canonical project-relative path: $RelativePath"
    }
    $FullPath = [IO.Path]::GetFullPath((Join-Path $Root $RelativePath))
    $RootPrefix = $Root.TrimEnd([IO.Path]::DirectorySeparatorChar) +
        [IO.Path]::DirectorySeparatorChar
    if (-not $FullPath.StartsWith($RootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the project root: $RelativePath"
    }
    $Canonical = Get-ProjectRelativePath -Root $Root -Path $FullPath
    if ($Canonical -cne $RelativePath) {
        throw "$Label is not canonical (expected '$Canonical'): $RelativePath"
    }
    return $FullPath
}

function New-TrackedFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Tracked promotion file is missing: $Path"
    }
    $Bytes = [IO.File]::ReadAllBytes($Path)
    return [pscustomobject]@{
        Path = $Path
        OriginalBytes = $Bytes
        ExpectedSha256 = Get-Sha256ForBytes $Bytes
    }
}

function Enter-PromotionMutationLock {
    param([Parameter(Mandatory = $true)][string]$Root)

    $Directory = Join-Path $Root '.story-locks'
    $Path = Join-Path $Directory 'repository.lock'
    $Id = "canon-promotion-$([guid]::NewGuid().ToString('N'))"
    $DirectoryExisted = Test-Path -LiteralPath $Directory -PathType Container
    $null = New-Item -ItemType Directory -Path $Directory -Force
    try {
        $Stream = [IO.File]::Open(
            $Path,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::Write,
            [IO.FileShare]::None
        )
        try {
            $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Id)
            $Stream.Write($Bytes, 0, $Bytes.Length)
        }
        finally { $Stream.Dispose() }
    }
    catch {
        $Owner = 'unknown'
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            try { $Owner = Get-Content -LiteralPath $Path -Raw }
            catch { $Owner = 'locked/unreadable' }
        }
        if (-not $DirectoryExisted -and
            (Test-Path -LiteralPath $Directory -PathType Container) -and
            @(Get-ChildItem -LiteralPath $Directory -Force).Count -eq 0) {
            Remove-Item -LiteralPath $Directory -Force
        }
        throw "Another pipeline mutation is active ($Owner); canon promotion was not started."
    }
    return [pscustomobject]@{
        Path = $Path
        Id = $Id
        Directory = $Directory
        RemoveDirectory = -not $DirectoryExisted
    }
}

function Exit-PromotionMutationLock {
    param([AllowNull()][object]$Lock)

    if ($null -eq $Lock) { return }
    if ((Test-Path -LiteralPath $Lock.Path -PathType Leaf) -and
        (Get-Content -LiteralPath $Lock.Path -Raw) -ceq $Lock.Id) {
        Remove-Item -LiteralPath $Lock.Path -Force
    }
    if ($Lock.RemoveDirectory -and
        (Test-Path -LiteralPath $Lock.Directory -PathType Container) -and
        @(Get-ChildItem -LiteralPath $Lock.Directory -Force).Count -eq 0) {
        Remove-Item -LiteralPath $Lock.Directory -Force
    }
}

function Assert-TrackedFilesCurrent {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Entries,
        [Parameter(Mandatory = $true)][string]$Context,
        [string]$ExceptPath
    )

    foreach ($Entry in $Entries) {
        if ($ExceptPath -and $Entry.Path -ceq $ExceptPath) { continue }
        if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf)) {
            throw "$Context compare-and-swap failed; file is missing: $($Entry.Path)"
        }
        $CurrentSha256 = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($Entry.Path))
        if ($CurrentSha256 -cne $Entry.ExpectedSha256) {
            throw "$Context compare-and-swap failed; bytes changed: $($Entry.Path)"
        }
    }
}

function Write-TrackedBytes {
    param(
        [Parameter(Mandatory = $true)][object]$Entry,
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][string]$Context
    )

    Assert-TrackedFilesCurrent -Entries @($Entry) -Context $Context
    Write-BytesAtomically -Path $Entry.Path -Bytes $Bytes
    $Expected = Get-Sha256ForBytes $Bytes
    $Actual = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($Entry.Path))
    if ($Actual -cne $Expected) {
        throw "$Context atomic write verification failed: $($Entry.Path)"
    }
    $Entry.ExpectedSha256 = $Expected
}

function Get-TrackedEntry {
    param(
        [Parameter(Mandatory = $true)][object[]]$Entries,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $Matches = @($Entries | Where-Object { $_.Path -ceq $Path })
    if ($Matches.Count -ne 1) {
        throw "Internal promotion tracking error for path: $Path"
    }
    return $Matches[0]
}

function Get-CanonicalDigestForRecords {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Records,
        [Parameter(Mandatory = $true)][scriptblock]$LineFactory
    )

    [string[]]$Lines = @($Records | ForEach-Object { & $LineFactory $_ })
    [Array]::Sort($Lines, [StringComparer]::Ordinal)
    $Canonical = if ($Lines.Count -eq 0) { '' } else { ($Lines -join "`n") + "`n" }
    return Get-Sha256ForText $Canonical
}

function Get-DispositionDigest {
    param([Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Dispositions)

    return Get-CanonicalDigestForRecords -Records $Dispositions -LineFactory {
        param($Item)
        $Target = if ($null -eq $Item.target) { 'none' } else { [string]$Item.target }
        return "$($Item.id)`t$($Item.disposition)`t$Target`t$($Item.rationale)"
    }
}

function Get-IndexCanonSlugs {
    param([Parameter(Mandatory = $true)][string]$IndexPath)

    $Content = ConvertFrom-Utf8Bytes ([IO.File]::ReadAllBytes($IndexPath)) 'stories/INDEX.md'
    [string[]]$Lines = Split-NormalizedLines $Content
    $HeaderIndexes = @()
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index] -match '^\|\s*Story\s*\|\s*Title\s*\|\s*Status\s*\|\s*Canon\s*\|\s*User disposition\s*\|\s*Publish\s*\|\s*Promotion date\s*\|\s*Notes\s*\|$') {
            $HeaderIndexes += $Index
        }
    }
    if ($HeaderIndexes.Count -ne 1) {
        throw "stories/INDEX.md must contain exactly one story table; found $($HeaderIndexes.Count)."
    }
    $CanonSlugs = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $Seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    for ($Index = $HeaderIndexes[0] + 2; $Index -lt $Lines.Count; $Index++) {
        if ([string]::IsNullOrWhiteSpace($Lines[$Index]) -or
            $Lines[$Index] -notmatch '^\s*\|') { break }
        $Cells = Split-MarkdownRow $Lines[$Index] 8 "stories/INDEX.md line $($Index + 1)"
        if ($Cells[0] -notmatch '^`([a-z0-9]+(?:-[a-z0-9]+)*)`$') {
            throw "Invalid story slug in stories/INDEX.md line $($Index + 1)."
        }
        $Slug = $Matches[1]
        if (-not $Seen.Add($Slug)) { throw "Duplicate story slug in stories/INDEX.md: $Slug" }
        if ($Cells[3] -notin @('yes', 'no')) {
            throw "Invalid canon value for '$Slug' in stories/INDEX.md: $($Cells[3])"
        }
        if ($Cells[3] -ceq 'yes') { $null = $CanonSlugs.Add($Slug) }
    }
    return ,$CanonSlugs
}

function Get-AuthorityInventory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][hashtable]$UniversePreHashes
    )

    $UniverseDirectory = Join-Path $Root 'universe'
    $StoriesDirectory = Join-Path $Root 'stories'
    $IndexPath = Join-Path $StoriesDirectory 'INDEX.md'
    if (-not (Test-Path -LiteralPath $UniverseDirectory -PathType Container) -or
        -not (Test-Path -LiteralPath $IndexPath -PathType Leaf)) {
        throw 'Current-authority inventory requires universe/ and stories/INDEX.md.'
    }

    $Records = [Collections.Generic.List[object]]::new()
    foreach ($File in @(Get-ChildItem -LiteralPath $UniverseDirectory -Recurse -File -Filter '*.md')) {
        $Relative = Get-ProjectRelativePath -Root $Root -Path $File.FullName
        $Sha256 = if ($UniversePreHashes.ContainsKey($Relative)) {
            [string]$UniversePreHashes[$Relative]
        }
        else {
            Get-Sha256ForBytes ([IO.File]::ReadAllBytes($File.FullName))
        }
        $Records.Add([pscustomobject]@{ path = $Relative; sha256 = $Sha256 })
    }
    $Records.Add([pscustomobject]@{
        path = 'stories/INDEX.md'
        sha256 = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($IndexPath))
    })

    $IndexCanonSlugs = Get-IndexCanonSlugs $IndexPath
    $MetadataCanonSlugs = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($Directory in @(Get-ChildItem -LiteralPath $StoriesDirectory -Directory | Where-Object {
        $_.Name -notmatch '^[_\.]'
    })) {
        $MetadataPath = Join-Path $Directory.FullName 'story.json'
        if (-not (Test-Path -LiteralPath $MetadataPath -PathType Leaf)) { continue }
        $Metadata = ConvertFrom-JsonBytes ([IO.File]::ReadAllBytes($MetadataPath)) "$($Directory.Name)/story.json"
        Assert-RequiredProperties $Metadata @('slug', 'canon') "$($Directory.Name)/story.json"
        if ($Metadata.slug -cne $Directory.Name -or -not ($Metadata.canon -is [bool])) {
            throw "Invalid authority classification metadata: $MetadataPath"
        }
        if ($Metadata.canon) {
            $null = $MetadataCanonSlugs.Add($Directory.Name)
            $StoryPath = Join-Path $Directory.FullName '05-story.md'
            if (-not (Test-Path -LiteralPath $StoryPath -PathType Leaf)) {
                throw "Canon story is missing 05-story.md: $($Directory.Name)"
            }
            $Records.Add([pscustomobject]@{
                path = "stories/$($Directory.Name)/story.json"
                sha256 = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($MetadataPath))
            })
            $Records.Add([pscustomobject]@{
                path = "stories/$($Directory.Name)/05-story.md"
                sha256 = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($StoryPath))
            })
        }
    }
    if (-not $IndexCanonSlugs.SetEquals($MetadataCanonSlugs)) {
        throw 'Current-authority inventory found disagreement between stories/INDEX.md and canonical story.json records.'
    }

    $Sorted = @($Records)
    [Array]::Sort($Sorted, [Comparison[object]]{
        param($Left, $Right)
        return [StringComparer]::Ordinal.Compare($Left.path, $Right.path)
    })
    return ,$Sorted
}

function Get-AuthorityDigest {
    param([Parameter(Mandatory = $true)][object[]]$Inventory)

    return Get-CanonicalDigestForRecords -Records $Inventory -LineFactory {
        param($Item)
        return "$($Item.path)`t$($Item.sha256)"
    }
}

function Assert-AuthorityManifest {
    param(
        [Parameter(Mandatory = $true)][object]$ManifestAuthority,
        [Parameter(Mandatory = $true)][object[]]$ActualInventory
    )

    if ([int]$ManifestAuthority.fileCount -ne @($ManifestAuthority.files).Count -or
        [int]$ManifestAuthority.fileCount -ne $ActualInventory.Count) {
        throw 'promotion.json current-authority fileCount is incomplete or stale.'
    }
    $ManifestByPath = @{}
    foreach ($Record in @($ManifestAuthority.files)) {
        if ($ManifestByPath.ContainsKey([string]$Record.path)) {
            throw "promotion.json current-authority inventory repeats path '$($Record.path)'."
        }
        $ManifestByPath[[string]$Record.path] = [string]$Record.sha256
    }
    foreach ($Record in $ActualInventory) {
        if (-not $ManifestByPath.ContainsKey($Record.path) -or
            $ManifestByPath[$Record.path] -cne $Record.sha256) {
            throw "promotion.json current-authority inventory is stale at '$($Record.path)'."
        }
    }
    $Digest = Get-AuthorityDigest @($ManifestAuthority.files)
    if ($Digest -cne $ManifestAuthority.manifestSha256) {
        throw 'promotion.json current-authority manifest digest is invalid.'
    }
    $ActualDigest = Get-AuthorityDigest $ActualInventory
    if ($ActualDigest -cne $ManifestAuthority.manifestSha256) {
        throw 'Current authority changed after stewardship began.'
    }
}

function Get-PersistedAuthoritySetDigest {
    param([Parameter(Mandatory = $true)][object]$AuthorityManifest)

    $Payload = [ordered]@{
        schemaVersion = 1
        storySlug = [string]$AuthorityManifest.storySlug
        generatedAt = [string]$AuthorityManifest.generatedAt
        universeFiles = @($AuthorityManifest.universeFiles)
        canonStories = @($AuthorityManifest.canonStories)
    }
    $Json = ($Payload | ConvertTo-Json -Depth 12 -Compress).Replace("`r`n", "`n").Replace("`r", "`n")
    return Get-Sha256ForText $Json
}

function Assert-PersistedAuthorityManifest {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$StorySlug,
        [Parameter(Mandatory = $true)][byte[]]$Bytes,
        [Parameter(Mandatory = $true)][string]$ExpectedRawSha256,
        [Parameter(Mandatory = $true)][string]$ExpectedSetSha256,
        [Parameter(Mandatory = $true)][hashtable]$UniversePreHashes
    )

    if ((Get-Sha256ForBytes $Bytes) -cne $ExpectedRawSha256) {
        throw 'promotion.json does not bind the current raw authority.json bytes.'
    }
    try {
        $AuthorityManifest = ConvertFrom-JsonBytes $Bytes 'authority.json'
    }
    catch {
        throw "authority.json is invalid JSON: $($_.Exception.Message)"
    }
    $ExpectedProperties = @(
        'schemaVersion', 'storySlug', 'generatedAt', 'universeFiles',
        'canonStories', 'manifestSha256'
    )
    $ActualProperties = @($AuthorityManifest.PSObject.Properties.Name)
    if (@($ExpectedProperties | Where-Object { $_ -cnotin $ActualProperties }).Count -gt 0 -or
        @($ActualProperties | Where-Object { $_ -cnotin $ExpectedProperties }).Count -gt 0 -or
        $AuthorityManifest.schemaVersion -ne 1 -or
        $AuthorityManifest.storySlug -cne $StorySlug) {
        throw "authority.json is not an exact schema-version-1 manifest for '$StorySlug'."
    }
    $ComputedSetSha256 = Get-PersistedAuthoritySetDigest $AuthorityManifest
    if ($AuthorityManifest.manifestSha256 -cne $ComputedSetSha256 -or
        $ComputedSetSha256 -cne $ExpectedSetSha256) {
        throw 'authority.json canonical authority-set digest is invalid or stale.'
    }

    $UniverseFiles = @($AuthorityManifest.universeFiles)
    $UniverseByPath = @{}
    foreach ($Record in $UniverseFiles) {
        Assert-RequiredProperties $Record @('path', 'sha256') 'authority.json universe file'
        if ($UniverseByPath.ContainsKey([string]$Record.path)) {
            throw "authority.json repeats universe path '$($Record.path)'."
        }
        $UniverseByPath[[string]$Record.path] = [string]$Record.sha256
    }
    $CurrentUniverseFiles = @(Get-ChildItem -LiteralPath (Join-Path $Root 'universe') -Recurse -File -Filter '*.md')
    if ($UniverseByPath.Count -ne $CurrentUniverseFiles.Count) {
        throw 'authority.json universe inventory is incomplete.'
    }
    foreach ($File in $CurrentUniverseFiles) {
        $Relative = Get-ProjectRelativePath $Root $File.FullName
        $ExpectedHash = if ($UniversePreHashes.ContainsKey($Relative)) {
            [string]$UniversePreHashes[$Relative]
        }
        else {
            Get-Sha256ForBytes ([IO.File]::ReadAllBytes($File.FullName))
        }
        if (-not $UniverseByPath.ContainsKey($Relative) -or
            $UniverseByPath[$Relative] -cne $ExpectedHash) {
            throw "authority.json is stale at '$Relative'."
        }
    }

    $ExpectedCanon = @{}
    $StoriesRoot = Join-Path $Root 'stories'
    foreach ($Directory in @(Get-ChildItem -LiteralPath $StoriesRoot -Directory | Where-Object {
        $_.Name -notmatch '^[_\.]'
    })) {
        $MetadataPath = Join-Path $Directory.FullName 'story.json'
        if (-not (Test-Path -LiteralPath $MetadataPath -PathType Leaf)) { continue }
        $Metadata = ConvertFrom-JsonBytes ([IO.File]::ReadAllBytes($MetadataPath)) "$($Directory.Name)/story.json"
        if ($Metadata.status -cne 'final' -or $Metadata.stage -cne 'final' -or
            $Metadata.canon -ne $true -or $Metadata.userDisposition -cne 'accepted') {
            continue
        }
        $FinalPath = Join-Path $Directory.FullName '05-story.md'
        $DeltaPath = Join-Path $Directory.FullName '06-canon-delta.md'
        $ReleasePath = Join-Path $Directory.FullName 'release.json'
        foreach ($Required in @($FinalPath, $DeltaPath, $ReleasePath)) {
            if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) {
                throw "Canon authority '$($Directory.Name)' is incomplete."
            }
        }
        $Release = ConvertFrom-JsonBytes ([IO.File]::ReadAllBytes($ReleasePath)) "$($Directory.Name)/release.json"
        $FinalHash = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($FinalPath))
        $DeltaHash = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($DeltaPath))
        if ($Release.certified -ne $true -or $Release.storySlug -cne $Directory.Name -or
            $Release.artifacts.story.sha256 -cne $FinalHash -or
            $Release.artifacts.canonDelta.sha256 -cne $DeltaHash) {
            throw "Canon authority '$($Directory.Name)' has a stale certified release."
        }
        $ExpectedCanon[$Directory.Name] = [pscustomobject]@{
            promotionDate = [string]$Metadata.promotionDate
            storySha256 = $FinalHash
            canonDeltaSha256 = $DeltaHash
        }
    }
    $StoredCanon = @($AuthorityManifest.canonStories)
    if ($StoredCanon.Count -ne $ExpectedCanon.Count) {
        throw 'authority.json canon-story inventory is incomplete.'
    }
    $SeenCanon = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($Record in $StoredCanon) {
        Assert-RequiredProperties $Record @(
            'slug', 'promotionDate', 'storySha256', 'canonDeltaSha256'
        ) 'authority.json canon story'
        if (-not $SeenCanon.Add([string]$Record.slug) -or
            -not $ExpectedCanon.ContainsKey([string]$Record.slug)) {
            throw "authority.json has an unexpected or repeated canon story '$($Record.slug)'."
        }
        $Expected = $ExpectedCanon[[string]$Record.slug]
        if ($Record.promotionDate -cne $Expected.promotionDate -or
            $Record.storySha256 -cne $Expected.storySha256 -or
            $Record.canonDeltaSha256 -cne $Expected.canonDeltaSha256) {
            throw "authority.json is stale for canon story '$($Record.slug)'."
        }
    }
    return $AuthorityManifest
}

function Get-HandoffField {
    param(
        [Parameter(Mandatory = $true)][string]$Handoff,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $Pattern = '(?m)^' + [regex]::Escape($Name) + ':\s*(.*)$'
    $Matches = @([regex]::Matches((ConvertTo-LfText $Handoff), $Pattern))
    if ($Matches.Count -ne 1) {
        throw "Stewardship handoff must contain exactly one '$Name' field."
    }
    return $Matches[0].Groups[1].Value.Trim()
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
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$script:Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$SchemaPath = Join-Path $PSScriptRoot '../schemas/promotion.schema.json'
$StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
$StoryJsonPath = Join-Path $StoryDirectory 'story.json'
$ReleasePath = Join-Path $StoryDirectory 'release.json'
$ReadmePath = Join-Path $StoryDirectory 'README.md'
$PromotionManifestPath = Join-Path $StoryDirectory 'promotion.json'
$AuthorityPath = Join-Path $StoryDirectory 'authority.json'
$IndexPath = Join-Path $ProjectRoot 'stories/INDEX.md'
$NamesPath = Join-Path $ProjectRoot 'stories/NAMES.md'
$ReviewPath = Join-Path $StoryDirectory '04-review.md'
$FinalStoryPath = Join-Path $StoryDirectory '05-story.md'
$CanonDeltaPath = Join-Path $StoryDirectory '06-canon-delta.md'
$NameScript = Join-Path $ProjectRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
$ReleaseScript = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/New-StoryRelease.ps1'
$IntegrityScript = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1'
$AuthorityScript = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1'

$ProductionPaths = @(
    $StoryJsonPath, $ReleasePath, $ReadmePath, $IndexPath, $NamesPath,
    $PromotionManifestPath, $AuthorityPath
)
$ReadOnlyPaths = @($ReviewPath, $FinalStoryPath, $CanonDeltaPath)
$ProductionSnapshot = @()
$ReadOnlySnapshot = @()
$UniverseSnapshot = @()
$UniversePreImages = @{}
$TransactionVerified = $false
$MutationStarted = $false
$MutationLock = $null

try {
    if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
        throw "Story directory not found: $StoryDirectory"
    }
    $MutationLock = Enter-PromotionMutationLock $ProjectRoot
    foreach ($Path in @($ProductionPaths + $ReadOnlyPaths + @(
        $NameScript, $ReleaseScript, $IntegrityScript, $AuthorityScript,
        $SchemaPath
    ))) {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
            throw "Required promotion file not found: $Path"
        }
    }

    $ProductionSnapshot = @($ProductionPaths | ForEach-Object { New-TrackedFile $_ })
    $ReadOnlySnapshot = @($ReadOnlyPaths | ForEach-Object { New-TrackedFile $_ })
    $UniverseDirectory = Join-Path $ProjectRoot 'universe'
    if (-not (Test-Path -LiteralPath $UniverseDirectory -PathType Container)) {
        throw "Required promotion directory not found: $UniverseDirectory"
    }
    $UniverseSnapshot = @(Get-ChildItem -LiteralPath $UniverseDirectory -Recurse -File -Filter '*.md' |
        ForEach-Object { New-TrackedFile $_.FullName })
    if ($UniverseSnapshot.Count -eq 0) { throw 'No authoritative universe Markdown files were found.' }

    $ManifestEntry = Get-TrackedEntry $ProductionSnapshot $PromotionManifestPath
    $ManifestJson = ConvertFrom-Utf8Bytes $ManifestEntry.OriginalBytes 'promotion.json'
    Assert-PromotionSchema -Json $ManifestJson -SchemaPath $SchemaPath -Label 'promotion.json'
    $Manifest = ConvertFrom-JsonBytes `
        ([Text.UTF8Encoding]::new($false).GetBytes($ManifestJson)) `
        'generated authority manifest'
    if ($Manifest.state -cne 'ready') {
        throw "promotion.json is not a current ready transaction manifest (state: $($Manifest.state))."
    }
    if ($Manifest.storySlug -cne $Story -or
        $Manifest.authorization.storySlug -cne $Story) {
        throw "promotion.json does not authorize exact story '$Story'."
    }
    if ($Manifest.promotionDate -cne $PromotionDate) {
        throw "promotion.json promotionDate does not match -PromotionDate '$PromotionDate'."
    }
    if ($Manifest.authority.path -cne "stories/$Story/authority.json") {
        throw "promotion.json authority.path must be 'stories/$Story/authority.json'."
    }
    $ResolvedAuthorityPath = Resolve-ProjectRelativePath $ProjectRoot $Manifest.authority.path 'authority.path'
    if ($ResolvedAuthorityPath -cne $AuthorityPath) {
        throw 'promotion.json authority.path does not resolve to the exact story authority manifest.'
    }
    if ($Manifest.authorization.approved -ne $true -or
        $Manifest.authorization.scope -cne 'canon-promotion' -or
        [string]::IsNullOrWhiteSpace([string]$Manifest.authorization.reference)) {
        throw "promotion.json lacks explicit canon-promotion authorization for '$Story'."
    }
    $PreparationSha256 = Assert-PromotionPreparationSha256 $Manifest

    $ExpectedBundlePaths = [ordered]@{
        release = "stories/$Story/release.json"
        story = "stories/$Story/05-story.md"
        canonDelta = "stories/$Story/06-canon-delta.md"
    }
    foreach ($Key in $ExpectedBundlePaths.Keys) {
        if ($Manifest.bundle.$Key.path -cne $ExpectedBundlePaths[$Key]) {
            throw "promotion.json bundle.$Key.path must be '$($ExpectedBundlePaths[$Key])'."
        }
        $null = Resolve-ProjectRelativePath $ProjectRoot $Manifest.bundle.$Key.path "bundle.$Key.path"
    }

    $StoryHash = (Get-TrackedEntry $ReadOnlySnapshot $FinalStoryPath).ExpectedSha256
    $DeltaHash = (Get-TrackedEntry $ReadOnlySnapshot $CanonDeltaPath).ExpectedSha256
    $CandidateReleaseHash = (Get-TrackedEntry $ProductionSnapshot $ReleasePath).ExpectedSha256

    $Dispositions = @($Manifest.deltaDispositions)
    if ([int]$Manifest.deltaInventory.itemCount -ne $Dispositions.Count -or
        $Manifest.deltaInventory.sourceArtifactSha256 -cne
            $Manifest.bundle.canonDelta.sha256) {
        throw 'promotion.json delta inventory is incomplete or bound to stale canon-delta bytes.'
    }
    $DispositionDigest = Get-DispositionDigest $Dispositions
    if ($Manifest.deltaInventory.dispositionsSha256 -cne $DispositionDigest) {
        throw 'promotion.json delta disposition digest is invalid.'
    }
    $DispositionById = @{}
    $PromoteIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($Disposition in $Dispositions) {
        if ($DispositionById.ContainsKey([string]$Disposition.id)) {
            throw "promotion.json repeats delta disposition ID '$($Disposition.id)'."
        }
        $DispositionById[[string]$Disposition.id] = $Disposition
        if ($Disposition.disposition -ceq 'promote') { $null = $PromoteIds.Add($Disposition.id) }
    }

    $ChangePaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $AssignedPromoteIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $UniversePreHashes = @{}
    foreach ($Change in @($Manifest.universeChanges)) {
        $RelativePath = [string]$Change.path
        if (-not $ChangePaths.Add($RelativePath)) {
            throw "promotion.json repeats universe change path '$RelativePath'."
        }
        $FullPath = Resolve-ProjectRelativePath $ProjectRoot $RelativePath 'universeChanges.path'
        $UniverseEntry = Get-TrackedEntry $UniverseSnapshot $FullPath
        if ($UniverseEntry.ExpectedSha256 -cne $Change.postSha256) {
            throw "Stewardship post-image does not match promotion.json for '$RelativePath'."
        }
        if ($Change.preSha256 -ceq $Change.postSha256) {
            throw "Universe change '$RelativePath' has identical pre/post hashes."
        }
        try { [byte[]]$PreImage = [Convert]::FromBase64String([string]$Change.preImageBase64) }
        catch { throw "Universe change '$RelativePath' has invalid preImageBase64: $($_.Exception.Message)" }
        if ((Get-Sha256ForBytes $PreImage) -cne $Change.preSha256) {
            throw "Universe change '$RelativePath' pre-image does not match preSha256."
        }
        $UniversePreImages[$RelativePath] = $PreImage
        $UniversePreHashes[$RelativePath] = [string]$Change.preSha256

        $LocalIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
        foreach ($DeltaId in @($Change.deltaIds)) {
            if (-not $LocalIds.Add([string]$DeltaId) -or
                -not $AssignedPromoteIds.Add([string]$DeltaId)) {
                throw "Promoted delta ID '$DeltaId' is assigned more than once."
            }
            if (-not $DispositionById.ContainsKey([string]$DeltaId) -or
                $DispositionById[[string]$DeltaId].disposition -cne 'promote') {
                throw "Universe change '$RelativePath' references non-promote delta ID '$DeltaId'."
            }
            $TargetPath = ([string]$DispositionById[[string]$DeltaId].target).Split('#', 2)[0]
            if ($TargetPath -cne $RelativePath) {
                throw "Promoted delta ID '$DeltaId' target does not match '$RelativePath'."
            }
        }
    }
    if (-not $PromoteIds.SetEquals($AssignedPromoteIds)) {
        throw 'promotion.json does not assign every promote disposition to exactly one universe change.'
    }
    $ExpectedStewardResult = if ($ChangePaths.Count -gt 0) {
        'CANON_APPLIED_AWAITING_PRIMARY'
    }
    else {
        'NO_CANON_CHANGES_AWAITING_PRIMARY'
    }
    if ($Manifest.stewardship.result -cne $ExpectedStewardResult) {
        throw 'promotion.json stewardship result disagrees with its universe changes.'
    }

    $HandoffText = [string]$Manifest.stewardship.handoffText
    if ((Get-Sha256ForText $HandoffText) -cne $Manifest.stewardship.handoffSha256) {
        throw 'promotion.json stewardship handoff digest is invalid.'
    }
    $HandoffExpectations = [ordered]@{
        story = $Story
        authorization = [string]$Manifest.authorization.reference
        steward = [string]$Manifest.stewardship.identity
        candidateRelease = 'VERIFIED'
        candidateReleaseSha256 = [string]$Manifest.bundle.release.sha256
        authorityRecheck = 'PASS'
        authorityManifestSha256 = [string]$Manifest.authority.sha256
        nameCheckReceipt = 'VERIFIED'
        storySha256 = [string]$Manifest.bundle.story.sha256
        canonDeltaSha256 = [string]$Manifest.bundle.canonDelta.sha256
        deltaDispositionsSha256 = [string]$Manifest.deltaInventory.dispositionsSha256
        result = [string]$Manifest.stewardship.result
    }
    foreach ($Field in $HandoffExpectations.Keys) {
        if ((Get-HandoffField $HandoffText $Field) -cne $HandoffExpectations[$Field]) {
            throw "Stewardship handoff field '$Field' does not match promotion.json."
        }
    }
    if ($Manifest.stewardship.candidateRelease -cne 'VERIFIED' -or
        $Manifest.stewardship.authorityRecheck -cne 'PASS' -or
        $Manifest.stewardship.nameCheckReceipt -cne 'VERIFIED') {
        throw 'promotion.json contains a non-passing stewardship gate.'
    }

    $RetconTargeted = $ChangePaths.Contains('universe/retcons.md')
    if ($null -eq $Manifest.retcon) {
        if ($RetconTargeted) {
            throw 'A universe/retcons.md change requires separately approved retcon evidence.'
        }
        $RetconEvidenceSha256 = 'none'
    }
    else {
        if (-not $RetconTargeted -or $Manifest.retcon.approved -ne $true -or
            $Manifest.retcon.scope -cne 'retcon' -or
            $Manifest.retcon.targetPath -cne 'universe/retcons.md' -or
            [string]::IsNullOrWhiteSpace([string]$Manifest.retcon.authorizationReference)) {
            throw 'promotion.json retcon evidence is not separately scoped to an approved retcon write.'
        }
        $RetconEvidenceSha256 = Get-Sha256ForText ([string]$Manifest.retcon.evidence)
        if ($RetconEvidenceSha256 -cne $Manifest.retcon.evidenceSha256) {
            throw 'promotion.json retcon evidence digest is invalid.'
        }
    }
    if ((Get-HandoffField $HandoffText 'retconEvidenceSha256') -cne $RetconEvidenceSha256) {
        throw 'Stewardship handoff retcon evidence does not match promotion.json.'
    }

    # From this point, the manifest has enough verified pre/post data to safely
    # undo the already-written stewardship changes on any later failure.
    $TransactionVerified = $true

    $PreAuthorityInventory = Get-AuthorityInventory $ProjectRoot $UniversePreHashes
    Assert-AuthorityManifest $Manifest.authority $PreAuthorityInventory
    $AuthorityEntry = Get-TrackedEntry $ProductionSnapshot $AuthorityPath
    $AuthorityAssertion = @{
        Root = $ProjectRoot
        StorySlug = $Story
        Bytes = $AuthorityEntry.OriginalBytes
        ExpectedRawSha256 = [string]$Manifest.authority.sha256
        ExpectedSetSha256 = [string]$Manifest.authority.authoritySetSha256
        UniversePreHashes = $UniversePreHashes
    }
    $null = Assert-PersistedAuthorityManifest @AuthorityAssertion
    if ($Manifest.bundle.story.sha256 -cne $StoryHash -or
        $Manifest.bundle.canonDelta.sha256 -cne $DeltaHash -or
        $Manifest.bundle.release.sha256 -cne $CandidateReleaseHash) {
        throw 'promotion.json bundle hashes are stale.'
    }

    $MetadataEntry = Get-TrackedEntry $ProductionSnapshot $StoryJsonPath
    $ReleaseEntry = Get-TrackedEntry $ProductionSnapshot $ReleasePath
    $ReadmeEntry = Get-TrackedEntry $ProductionSnapshot $ReadmePath
    $IndexEntry = Get-TrackedEntry $ProductionSnapshot $IndexPath
    $NamesEntry = Get-TrackedEntry $ProductionSnapshot $NamesPath
    $Metadata = ConvertFrom-JsonBytes $MetadataEntry.OriginalBytes 'story.json'
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

    $Release = ConvertFrom-JsonBytes $ReleaseEntry.OriginalBytes 'release.json'
    Assert-RequiredProperties $Release @(
        'schemaVersion', 'certified', 'storySlug', 'artifacts', 'review', 'nameCheck'
    ) 'release.json'
    Assert-RequiredProperties $Release.artifacts @('story', 'canonDelta') 'release.json artifacts'
    Assert-RequiredProperties $Release.artifacts.story @('path', 'sha256') 'release.json artifacts.story'
    Assert-RequiredProperties $Release.artifacts.canonDelta @('path', 'sha256') 'release.json artifacts.canonDelta'
    Assert-RequiredProperties $Release.nameCheck @('story', 'passed', 'scopedRegistrySha256') 'release.json nameCheck'
    if ($Release.schemaVersion -ne 2 -or $Release.certified -ne $true -or
        $Release.storySlug -cne $Story) {
        throw "release.json is not a schema-version-2 certified release for exact story '$Story'."
    }
    if ($Release.artifacts.story.path -cne '05-story.md' -or
        $Release.artifacts.canonDelta.path -cne '06-canon-delta.md' -or
        $Release.artifacts.story.sha256 -cne $StoryHash -or
        $Release.artifacts.canonDelta.sha256 -cne $DeltaHash) {
        throw 'release.json does not bind the current reviewed story and canon-delta bytes.'
    }
    Assert-RequiredProperties $Release @('provenance') 'release.json'
    Assert-RequiredProperties $Release.provenance @(
        'authorityManifestSha256', 'reviewAuthorityManifestSha256',
        'promotionPreparationSha256'
    ) 'release.json provenance'
    if ($Release.provenance.authorityManifestSha256 -cne $Manifest.authority.sha256 -or
        $Release.provenance.reviewAuthorityManifestSha256 -cne $Manifest.authority.sha256 -or
        $null -ne $Release.provenance.promotionPreparationSha256) {
        throw 'release.json does not bind the unbridged candidate authority.json bytes.'
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
        $NameReceipt.scopedRegistrySha256 -cne $Release.nameCheck.scopedRegistrySha256) {
        throw 'Candidate final-name receipt does not match the certified release bundle.'
    }

    $AllTracked = @($ProductionSnapshot + $ReadOnlySnapshot + $UniverseSnapshot)
    Assert-TrackedFilesCurrent $AllTracked 'pre-finalization'
    $UpdatedReadme = Get-UpdatedReadme (
        ConvertFrom-Utf8Bytes $ReadmeEntry.OriginalBytes 'story README'
    ) $PromotionDate
    $UpdatedIndex = Get-UpdatedIndex (
        ConvertFrom-Utf8Bytes $IndexEntry.OriginalBytes 'stories/INDEX.md'
    ) $Story $PromotionDate $OriginalPublish
    $UpdatedRegistry = Get-UpdatedRegistry (
        ConvertFrom-Utf8Bytes $NamesEntry.OriginalBytes 'stories/NAMES.md'
    ) $Story

    $Metadata.stage = 'final'
    $Metadata.status = 'final'
    $Metadata.canon = $true
    $Metadata.userDisposition = 'accepted'
    $Metadata.promotionDate = $PromotionDate
    if ([bool]$Metadata.publish -ne $OriginalPublish) {
        throw 'Internal error: story.json publish changed while preparing promotion.'
    }
    $UpdatedMetadataBytes = ConvertTo-Utf8LfBytes (($Metadata | ConvertTo-Json -Depth 100) + "`n")
    $UpdatedReadmeBytes = ConvertTo-Utf8LfBytes $UpdatedReadme
    $UpdatedIndexBytes = ConvertTo-Utf8LfBytes $UpdatedIndex
    $UpdatedNamesBytes = ConvertTo-Utf8LfBytes $UpdatedRegistry.Content

    $MutationStarted = $true
    foreach ($Write in @(
        [pscustomobject]@{ Entry = $MetadataEntry; Bytes = $UpdatedMetadataBytes; Label = 'story.json promotion' },
        [pscustomobject]@{ Entry = $ReadmeEntry; Bytes = $UpdatedReadmeBytes; Label = 'story README promotion' },
        [pscustomobject]@{ Entry = $IndexEntry; Bytes = $UpdatedIndexBytes; Label = 'story index promotion' },
        [pscustomobject]@{ Entry = $NamesEntry; Bytes = $UpdatedNamesBytes; Label = 'name registry promotion' }
    )) {
        Assert-TrackedFilesCurrent $AllTracked $Write.Label
        Write-TrackedBytes $Write.Entry $Write.Bytes $Write.Label
    }

    Assert-TrackedFilesCurrent $AllTracked 'before final authority manifest regeneration'
    try {
        $FinalAuthorityReceipt = Invoke-JsonContract $AuthorityScript 'final authority manifest regeneration' @(
            '-Story', $Story, '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
        )
    }
    finally {
        if (Test-Path -LiteralPath $AuthorityPath -PathType Leaf) {
            $AuthorityEntry.ExpectedSha256 = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($AuthorityPath))
        }
    }
    Assert-TrackedFilesCurrent $AllTracked 'after final authority manifest regeneration'
    if ($FinalAuthorityReceipt.passed -ne $true -or
        $FinalAuthorityReceipt.story -cne $Story -or
        $FinalAuthorityReceipt.manifestSha256 -cne $AuthorityEntry.ExpectedSha256 -or
        $FinalAuthorityReceipt.authoritySetSha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw 'Final authority manifest regeneration returned an invalid receipt.'
    }
    $FinalAuthorityAssertion = @{
        Root = $ProjectRoot
        StorySlug = $Story
        Bytes = [IO.File]::ReadAllBytes($AuthorityPath)
        ExpectedRawSha256 = [string]$FinalAuthorityReceipt.manifestSha256
        ExpectedSetSha256 = [string]$FinalAuthorityReceipt.authoritySetSha256
        UniversePreHashes = @{}
    }
    $null = Assert-PersistedAuthorityManifest @FinalAuthorityAssertion

    Assert-TrackedFilesCurrent $AllTracked 'before final release reissue'
    try {
        $null = Invoke-ExternalScript $ReleaseScript 'final release reissue' @(
            '-Story', $Story, '-ProjectRoot', $ProjectRoot, '-PromotionFinalize'
        )
    }
    finally {
        if (Test-Path -LiteralPath $ReleasePath -PathType Leaf) {
            $ReleaseEntry.ExpectedSha256 = Get-Sha256ForBytes ([IO.File]::ReadAllBytes($ReleasePath))
        }
    }
    Assert-TrackedFilesCurrent $AllTracked 'after final release reissue'

    $FinalReleaseBytes = [IO.File]::ReadAllBytes($ReleasePath)
    $FinalReleaseHash = Get-Sha256ForBytes $FinalReleaseBytes
    $FinalRelease = ConvertFrom-JsonBytes $FinalReleaseBytes 'reissued release.json'
    if ($FinalRelease.certified -ne $true -or $FinalRelease.storySlug -cne $Story -or
        $FinalRelease.artifacts.story.sha256 -cne $StoryHash -or
        $FinalRelease.artifacts.canonDelta.sha256 -cne $DeltaHash) {
        throw 'Reissued release.json no longer binds the reviewed artifact bytes.'
    }
    if ($FinalRelease.schemaVersion -ne 2 -or
        $FinalRelease.provenance.authorityManifestSha256 -cne $FinalAuthorityReceipt.manifestSha256 -or
        $FinalRelease.provenance.reviewAuthorityManifestSha256 -cne $Manifest.authority.sha256 -or
        $FinalRelease.provenance.promotionPreparationSha256 -cne $PreparationSha256) {
        throw 'Reissued release.json does not preserve the promotion authority bridge.'
    }

    $PostAuthorityInventory = Get-AuthorityInventory $ProjectRoot @{}
    $PostAuthorityDigest = Get-AuthorityDigest $PostAuthorityInventory
    [string[]]$ModifiedFiles = @(
        @($Manifest.universeChanges | ForEach-Object { [string]$_.path }) +
        @($ProductionPaths | ForEach-Object { Get-ProjectRelativePath $ProjectRoot $_ })
    ) | Sort-Object -Unique
    $CompletedAt = [datetime]::UtcNow.ToString('o', [Globalization.CultureInfo]::InvariantCulture)
    $TransactionText = @(
        "story=$Story",
        "promotionDate=$PromotionDate",
        "authorization=$($Manifest.authorization.reference)",
        "steward=$($Manifest.stewardship.identity)",
        "handoff=$($Manifest.stewardship.handoffSha256)",
        "preparation=$PreparationSha256",
        "candidateRelease=$CandidateReleaseHash",
        "finalRelease=$FinalReleaseHash",
        "preAuthority=$($Manifest.authority.sha256)",
        "postAuthority=$($FinalAuthorityReceipt.manifestSha256)",
        "preAuthoritySet=$($Manifest.authority.authoritySetSha256)",
        "postAuthoritySet=$($FinalAuthorityReceipt.authoritySetSha256)",
        "preTransactionInventory=$($Manifest.authority.manifestSha256)",
        "postTransactionInventory=$PostAuthorityDigest",
        "dispositions=$DispositionDigest"
    ) -join "`n"
    $TransactionDigest = Get-Sha256ForText ($TransactionText + "`n")
    $Manifest.state = 'completed'
    $Manifest.completion = [pscustomobject]@{
        completedAt = $CompletedAt
        completedBy = 'Complete-CanonPromotion.ps1'
        candidateReleaseSha256 = $CandidateReleaseHash
        finalReleaseSha256 = $FinalReleaseHash
        candidateAuthorityManifestSha256 = [string]$Manifest.authority.sha256
        finalAuthorityManifestSha256 = [string]$FinalAuthorityReceipt.manifestSha256
        preAuthoritySetSha256 = [string]$Manifest.authority.authoritySetSha256
        postAuthoritySetSha256 = [string]$FinalAuthorityReceipt.authoritySetSha256
        preAuthorityManifestSha256 = [string]$Manifest.authority.manifestSha256
        postAuthorityManifestSha256 = $PostAuthorityDigest
        transactionSha256 = $TransactionDigest
        modifiedFiles = $ModifiedFiles
        result = 'PROMOTED'
    }
    if ((Assert-PromotionPreparationSha256 $Manifest) -cne $PreparationSha256) {
        throw 'Internal error: completion mutated the immutable promotion preparation.'
    }
    $CompletedManifestJson = ($Manifest | ConvertTo-Json -Depth 100) + "`n"
    Assert-PromotionSchema $CompletedManifestJson $SchemaPath 'completed promotion.json'
    Assert-TrackedFilesCurrent $AllTracked 'before durable promotion provenance write'
    Write-TrackedBytes $ManifestEntry (ConvertTo-Utf8LfBytes $CompletedManifestJson) 'promotion provenance'
    Assert-TrackedFilesCurrent $AllTracked 'after durable promotion provenance write'

    $FinalIntegrity = Invoke-JsonContract $IntegrityScript 'final story integrity validation' @(
        '-Story', $Story, '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    if ($FinalIntegrity.passed -ne $true -or $FinalIntegrity.story -cne $Story) {
        throw 'Final story integrity validation returned an invalid passing receipt.'
    }
    Assert-TrackedFilesCurrent $AllTracked 'after final story integrity validation'
    $RepositoryIntegrity = Invoke-JsonContract $IntegrityScript 'repository integrity validation' @(
        '-OutputFormat', 'Json', '-ProjectRoot', $ProjectRoot
    )
    if ($RepositoryIntegrity.passed -ne $true -or
        $RepositoryIntegrity.mode -cne 'repository') {
        throw 'Repository integrity validation returned an invalid passing receipt.'
    }
    Assert-TrackedFilesCurrent $AllTracked 'after repository integrity validation'

    Exit-PromotionMutationLock $MutationLock
    $MutationLock = $null
    Write-Output 'PROMOTION_CHANGE_REPORT'
    Write-Output "story: $Story"
    Write-Output "authorization: $($Manifest.authorization.reference)"
    Write-Output 'releaseBundle: VERIFIED'
    Write-Output 'Reviewed artifacts unchanged: 05-story.md, 06-canon-delta.md'
    Write-Output 'authorityRecheck: PASS'
    Write-Output 'resolutionQuestion: none'
    Write-Output 'nameCheckReceipt: VERIFIED'
    Write-Output 'stewardshipHandoff: VERIFIED'
    Write-Output "modifiedFiles: $($ModifiedFiles -join ', ')"
    $DispositionReport = if ($Dispositions.Count -eq 0) {
        'none'
    }
    else {
        @($Dispositions | ForEach-Object {
            $Target = if ($null -eq $_.target) { 'none' } else { $_.target }
            "id=$($_.id); disposition=$($_.disposition); target=$Target; rationale=$($_.rationale)"
        }) -join ' | '
    }
    Write-Output "deltaDispositions: $DispositionReport"
    Write-Output "retcon: $(if ($null -eq $Manifest.retcon) { 'none' } else { $Manifest.retcon.authorizationReference })"
    Write-Output 'result: PROMOTED'
}
catch {
    $FailureMessage = $_.Exception.Message
    if (-not [string]::IsNullOrWhiteSpace($_.ScriptStackTrace)) {
        $FailureMessage += " (at $($_.ScriptStackTrace -replace '[\r\n]+', ' <- '))"
    }
    $RollbackErrors = [Collections.Generic.List[string]]::new()
    if ($TransactionVerified) {
        $CanRollback = $true
        foreach ($Entry in @($ProductionSnapshot + $UniverseSnapshot)) {
            try {
                if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf) -or
                    (Get-Sha256ForBytes ([IO.File]::ReadAllBytes($Entry.Path))) -cne $Entry.ExpectedSha256) {
                    $RollbackErrors.Add("$($Entry.Path): compare-and-swap changed before rollback")
                    $CanRollback = $false
                }
            }
            catch {
                $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)")
                $CanRollback = $false
            }
        }
        if ($CanRollback) {
            foreach ($Entry in $UniverseSnapshot) {
                try {
                    $Relative = Get-ProjectRelativePath $ProjectRoot $Entry.Path
                    [byte[]]$RestoreBytes = if ($UniversePreImages.ContainsKey($Relative)) {
                        $UniversePreImages[$Relative]
                    }
                    else {
                        $Entry.OriginalBytes
                    }
                    Write-BytesAtomically $Entry.Path $RestoreBytes
                    $Entry.ExpectedSha256 = Get-Sha256ForBytes $RestoreBytes
                }
                catch { $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)") }
            }
            foreach ($Entry in $ProductionSnapshot) {
                try {
                    Write-BytesAtomically $Entry.Path $Entry.OriginalBytes
                    $Entry.ExpectedSha256 = Get-Sha256ForBytes $Entry.OriginalBytes
                }
                catch { $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)") }
            }
            foreach ($Entry in @($ProductionSnapshot + $UniverseSnapshot)) {
                try {
                    if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf) -or
                        (Get-Sha256ForBytes ([IO.File]::ReadAllBytes($Entry.Path))) -cne $Entry.ExpectedSha256) {
                        $RollbackErrors.Add("$($Entry.Path): restored bytes do not match transaction snapshot")
                    }
                }
                catch { $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)") }
            }
        }
    }
    foreach ($Entry in $ReadOnlySnapshot) {
        try {
            if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf) -or
                (Get-Sha256ForBytes ([IO.File]::ReadAllBytes($Entry.Path))) -cne $Entry.ExpectedSha256) {
                $RollbackErrors.Add("$($Entry.Path): reviewed artifact/review bytes changed unexpectedly")
            }
        }
        catch { $RollbackErrors.Add("$($Entry.Path): $($_.Exception.Message)") }
    }

    try {
        Exit-PromotionMutationLock $MutationLock
        $MutationLock = $null
    }
    catch { $RollbackErrors.Add("repository mutation lock: $($_.Exception.Message)") }

    if ($RollbackErrors.Count -gt 0) {
        throw "Canon promotion failed: $FailureMessage`nRollback verification failed:`n- $($RollbackErrors -join "`n- ")`nresult: ROLLBACK_FAILED"
    }
    if ($TransactionVerified) {
        throw "Canon promotion finalization failed: $FailureMessage`nAll captured universe and production transaction files were restored byte-for-byte; reviewed artifacts were unchanged.`nresult: NO_CHANGES"
    }
    throw "Canon promotion preflight failed: $FailureMessage`nNo finalization writes were attempted because no valid current promotion manifest was established.`nresult: NO_CHANGES"
}
