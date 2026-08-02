#Requires -Version 7.0

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [switch]$Verify,

    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$Utf8Strict = [Text.UTF8Encoding]::new($false, $true)

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

function Read-Utf8Text {
    param([Parameter(Mandatory = $true)][string]$Path)
    try { return $Utf8Strict.GetString([IO.File]::ReadAllBytes($Path)) }
    catch { throw "'$Path' is not valid UTF-8: $($_.Exception.Message)" }
}

function Get-CanonicalManifestHash {
    param([Parameter(Mandatory = $true)][object]$Manifest)
    $Payload = [ordered]@{
        schemaVersion = 1
        storySlug = [string]$Manifest.storySlug
        generatedAt = [string]$Manifest.generatedAt
        universeFiles = @($Manifest.universeFiles)
        canonStories = @($Manifest.canonStories)
    }
    $Json = ($Payload | ConvertTo-Json -Depth 12 -Compress).Replace("`r`n", "`n").Replace("`r", "`n")
    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Json)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function Write-JsonAtomically {
    param([Parameter(Mandatory = $true)][object]$Value, [Parameter(Mandatory = $true)][string]$Path)
    $TemporaryPath = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        $Json = ($Value | ConvertTo-Json -Depth 12).Replace("`r`n", "`n").Replace("`r", "`n") + "`n"
        [IO.File]::WriteAllText($TemporaryPath, $Json, [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($TemporaryPath, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryPath -PathType Leaf) { Remove-Item -LiteralPath $TemporaryPath -Force }
    }
}

function Split-IndexRow {
    param([Parameter(Mandatory = $true)][string]$Line, [Parameter(Mandatory = $true)][string]$Context)
    $Cells = @($Line.Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
    if ($Cells.Count -ne 8) { throw "$Context must contain exactly eight cells." }
    return ,$Cells
}

function Get-IndexRows {
    param([Parameter(Mandatory = $true)][string]$Path)
    $Lines = @((Read-Utf8Text $Path) -split '\r?\n')
    $Headers = @()
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index] -match '^\|\s*Story\s*\|\s*Title\s*\|\s*Status\s*\|\s*Canon\s*\|\s*User disposition\s*\|\s*Publish\s*\|\s*Promotion date\s*\|\s*Notes\s*\|$') {
            $Headers += $Index
        }
    }
    if ($Headers.Count -ne 1) { throw "stories/INDEX.md must contain exactly one eight-column story table; found $($Headers.Count)." }
    $Header = $Headers[0]
    if ($Header + 1 -ge $Lines.Count) { throw 'stories/INDEX.md is missing its separator row.' }
    $Separator = Split-IndexRow $Lines[$Header + 1] 'stories/INDEX.md separator'
    if (@($Separator | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -ne 0) {
        throw 'stories/INDEX.md has an invalid separator row.'
    }
    $Rows = [Collections.Generic.List[object]]::new()
    for ($Index = $Header + 2; $Index -lt $Lines.Count; $Index++) {
        $Line = $Lines[$Index]
        if ([string]::IsNullOrWhiteSpace($Line) -or $Line -notmatch '^\s*\|') { break }
        $Cells = Split-IndexRow $Line "stories/INDEX.md line $($Index + 1)"
        $SlugMatch = [regex]::Match($Cells[0], '^`(?<slug>[a-z0-9]+(?:-[a-z0-9]+)*)`$')
        $TitleMatch = [regex]::Match($Cells[1], '^\*(?<title>.+)\*$')
        if (-not $SlugMatch.Success -or -not $TitleMatch.Success) {
            throw "stories/INDEX.md line $($Index + 1) has an invalid slug or title cell."
        }
        $Rows.Add([pscustomobject]@{
            slug = $SlugMatch.Groups['slug'].Value
            title = $TitleMatch.Groups['title'].Value
            status = $Cells[2]
            canon = $Cells[3]
            userDisposition = $Cells[4]
            publish = $Cells[5]
            promotionDate = $Cells[6]
        })
    }
    if ($Rows.Count -eq 0) { throw 'stories/INDEX.md contains no story rows.' }
    foreach ($Duplicate in @($Rows | Group-Object slug | Where-Object Count -gt 1)) {
        throw "stories/INDEX.md repeats story '$($Duplicate.Name)'."
    }
    return @($Rows)
}

function Get-DirectoryNames {
    param([Parameter(Mandatory = $true)][string]$Root)
    return @((Get-ChildItem -LiteralPath $Root -Directory | Where-Object Name -notmatch '^[_.]' |
        Sort-Object Name | ForEach-Object Name))
}

function Assert-StableInputs {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Hashes,
        [Parameter(Mandatory = $true)][string[]]$UniversePaths,
        [Parameter(Mandatory = $true)][string[]]$StoryDirectories,
        [Parameter(Mandatory = $true)][string]$UniverseRoot,
        [Parameter(Mandatory = $true)][string]$StoriesRoot
    )
    $CurrentUniverse = @((Get-ChildItem -LiteralPath $UniverseRoot -Recurse -File -Filter '*.md' |
        Sort-Object FullName | ForEach-Object FullName))
    $CurrentStories = @(Get-DirectoryNames $StoriesRoot)
    if (($CurrentUniverse -join "`n") -cne ($UniversePaths -join "`n") -or
        ($CurrentStories -join "`n") -cne ($StoryDirectories -join "`n")) {
        throw 'Authority inputs changed directory membership during capture.'
    }
    foreach ($Path in $Hashes.Keys) {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf) -or
            (Get-RawSha256 $Path) -cne $Hashes[$Path]) {
            throw "Authority input changed during capture: $Path"
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$UniverseRoot = Join-Path $ProjectRoot 'universe'
$StoriesRoot = Join-Path $ProjectRoot 'stories'
$StoryDirectory = Join-Path $StoriesRoot $Story
$ManifestPath = Join-Path $StoryDirectory 'authority.json'
$IndexPath = Join-Path $StoriesRoot 'INDEX.md'
foreach ($Required in @($UniverseRoot, $StoriesRoot, $StoryDirectory)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Container)) { throw "Required authority directory not found: $Required" }
}
if (-not (Test-Path -LiteralPath $IndexPath -PathType Leaf)) { throw "Required authority index not found: $IndexPath" }

$InputHashes = @{}
function Add-AuthorityInput {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required authority input not found: $Path" }
    $InputHashes[$Path] = Get-RawSha256 $Path
}

$UniversePaths = @((Get-ChildItem -LiteralPath $UniverseRoot -Recurse -File -Filter '*.md' | Sort-Object FullName | ForEach-Object FullName))
if ($UniversePaths.Count -eq 0) { throw 'No authoritative universe Markdown files were found.' }
$StoryDirectories = @(Get-DirectoryNames $StoriesRoot)
if ($Story -cnotin $StoryDirectories) { throw "Story directory '$Story' is outside the production story set." }
Add-AuthorityInput $IndexPath
foreach ($Path in $UniversePaths) { Add-AuthorityInput $Path }
if ($Verify) { Add-AuthorityInput $ManifestPath }

$IndexRows = @(Get-IndexRows $IndexPath)
$IndexBySlug = @{}
foreach ($Row in $IndexRows) { $IndexBySlug[$Row.slug] = $Row }
if (($StoryDirectories -join "`n") -cne (@($IndexRows.slug | Sort-Object) -join "`n")) {
    throw 'stories/INDEX.md and production story directories are not an exact bijection.'
}

$CanonStories = [Collections.Generic.List[object]]::new()
foreach ($Slug in $StoryDirectories) {
    $Directory = Join-Path $StoriesRoot $Slug
    $MetadataPath = Join-Path $Directory 'story.json'
    Add-AuthorityInput $MetadataPath
    $Metadata = ConvertFrom-StableJson (Read-Utf8Text $MetadataPath)
    if ($Metadata.schemaVersion -ne 1 -or $Metadata.slug -cne $Slug) { throw "$Slug/story.json identity or schema is invalid." }
    $IndexRow = $IndexBySlug[$Slug]
    $ExpectedCanon = if ($Metadata.canon -eq $true) { 'yes' } else { 'no' }
    $ExpectedPublish = if ($Metadata.publish -eq $true) { 'yes' } else { 'no' }
    $ExpectedPromotion = if ($null -eq $Metadata.promotionDate) { '—' } else { [string]$Metadata.promotionDate }
    if ($IndexRow.title -cne [string]$Metadata.title -or
        $IndexRow.status -cne [string]$Metadata.status -or
        $IndexRow.canon -cne $ExpectedCanon -or
        $IndexRow.userDisposition -cne [string]$Metadata.userDisposition -or
        $IndexRow.publish -cne $ExpectedPublish -or
        $IndexRow.promotionDate -cne $ExpectedPromotion) {
        throw "stories/INDEX.md disagrees with $Slug/story.json."
    }

    $HasFinalMarker = $Metadata.status -ceq 'final' -or $Metadata.stage -ceq 'final' -or
        $Metadata.canon -eq $true -or $null -ne $Metadata.promotionDate
    if (-not $HasFinalMarker) { continue }
    if ($Metadata.status -cne 'final' -or $Metadata.stage -cne 'final' -or
        $Metadata.canon -ne $true -or $Metadata.userDisposition -cne 'accepted' -or
        [string]::IsNullOrWhiteSpace([string]$Metadata.promotionDate)) {
        throw "Canon authority '$Slug' has a partial or invalid final lifecycle projection."
    }
    $ReleasePath = Join-Path $Directory 'release.json'
    $FinalPath = Join-Path $Directory '05-story.md'
    $DeltaPath = Join-Path $Directory '06-canon-delta.md'
    foreach ($Path in @($ReleasePath, $FinalPath, $DeltaPath)) { Add-AuthorityInput $Path }
    $Release = ConvertFrom-StableJson (Read-Utf8Text $ReleasePath)
    $FinalHash = Get-RawSha256 $FinalPath
    $DeltaHash = Get-RawSha256 $DeltaPath
    if ($Release.schemaVersion -ne 2 -or $Release.certified -ne $true -or
        $Release.storySlug -cne $Slug -or
        $Release.artifacts.story.sha256 -cne $FinalHash -or
        $Release.artifacts.canonDelta.sha256 -cne $DeltaHash) {
        throw "Canon authority '$Slug' lacks a current schema-version-2 release."
    }
    $CanonStories.Add([ordered]@{
        slug = $Slug
        promotionDate = [string]$Metadata.promotionDate
        storySha256 = $FinalHash
        canonDeltaSha256 = $DeltaHash
    })
}

$UniverseFiles = @($UniversePaths | ForEach-Object {
    [ordered]@{
        path = [IO.Path]::GetRelativePath($ProjectRoot, $_).Replace('\', '/')
        sha256 = $InputHashes[$_]
    }
})
Assert-StableInputs $InputHashes $UniversePaths $StoryDirectories $UniverseRoot $StoriesRoot

if ($Verify) {
    $Stored = ConvertFrom-StableJson (Read-Utf8Text $ManifestPath)
    $ExpectedProperties = @('schemaVersion', 'storySlug', 'generatedAt', 'universeFiles', 'canonStories', 'manifestSha256')
    $ActualProperties = @($Stored.PSObject.Properties.Name)
    if (@($ExpectedProperties | Where-Object { $_ -cnotin $ActualProperties }).Count -gt 0 -or
        @($ActualProperties | Where-Object { $_ -cnotin $ExpectedProperties }).Count -gt 0 -or
        $Stored.schemaVersion -ne 1 -or $Stored.storySlug -cne $Story -or
        $Stored.manifestSha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw 'authority.json does not use the exact schema-version-1 contract.'
    }
    if ((Get-CanonicalManifestHash $Stored) -cne $Stored.manifestSha256) { throw 'authority.json canonical digest is invalid.' }
    if ((@($Stored.universeFiles) | ConvertTo-Json -Depth 8 -Compress) -cne
            ($UniverseFiles | ConvertTo-Json -Depth 8 -Compress) -or
        (@($Stored.canonStories) | ConvertTo-Json -Depth 8 -Compress) -cne
            (@($CanonStories) | ConvertTo-Json -Depth 8 -Compress)) {
        throw 'authority.json is stale relative to the reconciled authority snapshot.'
    }
    Assert-StableInputs $InputHashes $UniversePaths $StoryDirectories $UniverseRoot $StoriesRoot
    $Manifest = $Stored
}
else {
    $Manifest = [ordered]@{
        schemaVersion = 1
        storySlug = $Story
        generatedAt = [DateTimeOffset]::UtcNow.ToString('o')
        universeFiles = $UniverseFiles
        canonStories = @($CanonStories)
        manifestSha256 = $null
    }
    $Manifest.manifestSha256 = Get-CanonicalManifestHash $Manifest
    $HadPriorManifest = Test-Path -LiteralPath $ManifestPath -PathType Leaf
    [byte[]]$PriorManifest = if ($HadPriorManifest) { [IO.File]::ReadAllBytes($ManifestPath) } else { @() }
    if ($PSCmdlet.ShouldProcess($ManifestPath, 'Write reconciled shared-universe authority manifest')) {
        Assert-StableInputs $InputHashes $UniversePaths $StoryDirectories $UniverseRoot $StoriesRoot
        Write-JsonAtomically $Manifest $ManifestPath
        try { Assert-StableInputs $InputHashes $UniversePaths $StoryDirectories $UniverseRoot $StoriesRoot }
        catch {
            if ($HadPriorManifest) { [IO.File]::WriteAllBytes($ManifestPath, $PriorManifest) }
            elseif (Test-Path -LiteralPath $ManifestPath -PathType Leaf) { Remove-Item -LiteralPath $ManifestPath -Force }
            throw
        }
    }
}

$Result = [ordered]@{
    schemaVersion = 1
    story = $Story
    passed = $true
    manifestSha256 = if (Test-Path -LiteralPath $ManifestPath -PathType Leaf) { Get-RawSha256 $ManifestPath } else { $null }
    authoritySetSha256 = [string]$Manifest.manifestSha256
    universeFiles = @($Manifest.universeFiles).Count
    canonStories = @($Manifest.canonStories).Count
}
if ($OutputFormat -eq 'Json') { $Result | ConvertTo-Json -Depth 5 }
else { "Authority manifest $($Verify ? 'verified' : 'written') for '$Story': $($Result.authoritySetSha256)" }
