#Requires -Version 7.0

[CmdletBinding()]
param(
    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$Errors = [Collections.Generic.List[string]]::new()

function Add-UniverseError {
    param([Parameter(Mandatory = $true)][string]$Message)
    $Errors.Add($Message)
}

function Get-IndexCanonSlugs {
    param([Parameter(Mandatory = $true)][string]$Path)

    $Result = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($Line in Get-Content -LiteralPath $Path) {
        if ($Line -match '^\|\s*`(?<slug>[a-z0-9]+(?:-[a-z0-9]+)*)`\s*\|.*\|\s*final\s*\|\s*yes\s*\|') {
            $null = $Result.Add($Matches['slug'])
        }
    }
    return $Result
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$UniverseRoot = Join-Path $ProjectRoot 'universe'
$IndexCanon = Get-IndexCanonSlugs (Join-Path $ProjectRoot 'stories/INDEX.md')
$SourceManifestPath = Join-Path $ProjectRoot 'sources/MANIFEST.json'
$DecisionRecord = $null
if (Test-Path -LiteralPath $SourceManifestPath -PathType Leaf) {
    try {
        $SourceManifest = Get-Content -LiteralPath $SourceManifestPath -Raw |
            ConvertFrom-Json
        $DecisionRecord = ([string]$SourceManifest.decisionRecord).Replace('\', '/')
    }
    catch {
        Add-UniverseError "sources/MANIFEST.json cannot establish decision provenance: $($_.Exception.Message)"
    }
}
else { Add-UniverseError 'sources/MANIFEST.json is required for universe decision provenance.' }
$TopicalFiles = @(
    'premise.md', 'rules.md', 'timeline.md', 'characters.md', 'locations.md',
    'factions.md', 'glossary.md', 'style-guide.md'
)
foreach ($Name in $TopicalFiles) {
    $Path = Join-Path $UniverseRoot $Name
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Add-UniverseError "Missing required universe file: universe/$Name"
        continue
    }
    $Content = Get-Content -LiteralPath $Path -Raw
    $Visible = [regex]::Replace($Content, '(?s)<!--.*?-->', '')
    $Visible = [regex]::Replace($Visible, '(?ms)^```.*?^```[ \t]*$', '')
    $Headings = @([regex]::Matches($Visible, '(?m)^##[ \t]+(?<name>[^\r\n]+?)[ \t]*\r?$'))
    if ($Headings.Count -eq 0) {
        Add-UniverseError "universe/$Name contains no structured entries."
        continue
    }
    $Seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    for ($Index = 0; $Index -lt $Headings.Count; $Index++) {
        $Heading = $Headings[$Index].Groups['name'].Value.Trim()
        if (-not $Seen.Add($Heading)) {
            Add-UniverseError "universe/$Name duplicates heading '$Heading'."
        }
        $Start = $Headings[$Index].Index + $Headings[$Index].Length
        $End = if ($Index + 1 -lt $Headings.Count) {
            $Headings[$Index + 1].Index
        }
        else { $Visible.Length }
        $Body = $Visible.Substring($Start, $End - $Start)
        $Fields = @{}
        foreach ($Field in @('Status', 'Summary', 'First established', 'Aliases', 'Notes')) {
            $Matches = @([regex]::Matches(
                $Body,
                '(?ms)^-[ \t]+' + [regex]::Escape($Field) +
                    ':[ \t]*(?<value>.*?)(?=^-[ \t]+[A-Za-z][^:\r\n]*:|\z)'
            ))
            if ($Matches.Count -ne 1) {
                Add-UniverseError "universe/$Name#$Heading must contain exactly one '$Field' field."
                continue
            }
            $Value = $Matches[0].Groups['value'].Value.Trim()
            if ([string]::IsNullOrWhiteSpace($Value)) {
                Add-UniverseError "universe/$Name#$Heading has an empty '$Field' field."
            }
            $Fields[$Field] = $Value
        }
        if ($Fields.ContainsKey('Status') -and
            $Fields['Status'] -notin @('LOCKED', 'CANON', 'PROVISIONAL', 'RETIRED')) {
            Add-UniverseError "universe/$Name#$Heading has invalid Status '$($Fields['Status'])'."
        }
        if ($Fields.ContainsKey('First established')) {
            $FirstEstablished = (($Fields['First established'] -replace '\s+', ' ').Trim())
        }
        else { $FirstEstablished = '' }
        if ($FirstEstablished -match '^stories/(?<slug>[a-z0-9]+(?:-[a-z0-9]+)*)/05-story\.md$') {
            $Slug = $Matches['slug']
            $MetadataPath = Join-Path $ProjectRoot "stories/$Slug/story.json"
            $ReleasePath = Join-Path $ProjectRoot "stories/$Slug/release.json"
            if (-not $IndexCanon.Contains($Slug) -or
                -not (Test-Path -LiteralPath $MetadataPath -PathType Leaf) -or
                -not (Test-Path -LiteralPath $ReleasePath -PathType Leaf)) {
                Add-UniverseError "universe/$Name#$Heading cites non-authoritative story '$Slug'."
                continue
            }
            $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
            $Release = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json
            $StoryPath = Join-Path $ProjectRoot "stories/$Slug/05-story.md"
            $DeltaPath = Join-Path $ProjectRoot "stories/$Slug/06-canon-delta.md"
            if ($Metadata.status -cne 'final' -or $Metadata.stage -cne 'final' -or
                $Metadata.canon -ne $true -or $Metadata.userDisposition -cne 'accepted' -or
                $Release.certified -ne $true -or $Release.storySlug -cne $Slug -or
                $Release.artifacts.story.sha256 -cne
                    (Get-FileHash -LiteralPath $StoryPath -Algorithm SHA256).Hash.ToLowerInvariant() -or
                $Release.artifacts.canonDelta.sha256 -cne
                    (Get-FileHash -LiteralPath $DeltaPath -Algorithm SHA256).Hash.ToLowerInvariant()) {
                Add-UniverseError "universe/$Name#$Heading cites story '$Slug' whose authority records are stale."
            }
        }
        elseif ($FirstEstablished -match '^user decision, (?<date>\d{4}-\d{2}-\d{2}) \(`(?<path>sources/decisions/[^`]+\.md)` (?<locator>[^)]+)\)$') {
            $DecisionPath = $Matches['path'].Replace('\', '/')
            $DecisionDate = [datetime]::MinValue
            if (-not [datetime]::TryParseExact(
                $Matches['date'], 'yyyy-MM-dd',
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::None, [ref]$DecisionDate
            ) -or $DecisionPath -cne $DecisionRecord -or
                -not (Test-Path -LiteralPath (Join-Path $ProjectRoot $DecisionPath) -PathType Leaf) -or
                [string]::IsNullOrWhiteSpace($Matches['locator'])) {
                Add-UniverseError "universe/$Name#$Heading has stale or unregistered user-decision provenance."
            }
        }
        elseif ($Fields.ContainsKey('Status') -and
            $Fields['Status'] -in @('LOCKED', 'CANON')) {
            Add-UniverseError "universe/$Name#$Heading has unsupported authoritative provenance '$FirstEstablished'."
        }
    }
}

$RetconPath = Join-Path $UniverseRoot 'retcons.md'
if (-not (Test-Path -LiteralPath $RetconPath -PathType Leaf)) {
    Add-UniverseError 'Missing required universe/retcons.md.'
}
else {
    $RetconContent = [regex]::Replace(
        (Get-Content -LiteralPath $RetconPath -Raw),
        '(?s)<!--.*?-->',
        ''
    )
    foreach ($Match in @([regex]::Matches(
        $RetconContent,
        '(?ms)^##[ \t]+(?<heading>[^\r\n]+)\r?\n(?<body>.*?)(?=^##[ \t]+|\z)'
    ))) {
        if ($Match.Groups['heading'].Value -notmatch '^\d{4}-\d{2}-\d{2}[ \t]+—[ \t]+\S') {
            Add-UniverseError "retcons.md has malformed entry heading '$($Match.Groups['heading'].Value)'."
        }
        foreach ($Field in @('Old fact', 'New fact', 'Reason', 'Approved by', 'Affected stories')) {
            if (@([regex]::Matches(
                $Match.Groups['body'].Value,
                '(?m)^-[ \t]+' + [regex]::Escape($Field) + ':[ \t]*\S.*\r?$'
            )).Count -ne 1) {
                Add-UniverseError "retcons.md entry '$($Match.Groups['heading'].Value)' needs one nonempty '$Field'."
            }
        }
    }
}

$UniqueErrors = @($Errors | Sort-Object -Unique)
$Result = [ordered]@{
    schemaVersion = 1
    passed = $UniqueErrors.Count -eq 0
    checkedFiles = $TopicalFiles.Count + 1
    errors = $UniqueErrors
}
if ($OutputFormat -eq 'Json') { $Result | ConvertTo-Json -Depth 5 }
elseif ($UniqueErrors.Count -eq 0) { 'Universe integrity check passed.' }
else { foreach ($Message in $UniqueErrors) { Write-Host "- $Message" -ForegroundColor Red } }
if ($UniqueErrors.Count -gt 0) { exit 1 }
