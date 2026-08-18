#Requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet('PreReview', 'Final')]
    [string]$Phase = 'Final',

    [string]$Story,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
}
else {
    $ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)
}

if ($Phase -eq 'PreReview' -and [string]::IsNullOrWhiteSpace($Story)) {
    throw 'PreReview requires -Story <slug>.'
}
if ($Phase -eq 'Final' -and -not [string]::IsNullOrWhiteSpace($Story)) {
    throw 'Final validates all current stories; omit -Story.'
}
if (-not [string]::IsNullOrWhiteSpace($Story) -and $Story -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') {
    throw 'Story must be a lowercase kebab-case slug.'
}

$requiredFiles = @('outline.md', 'prompt.md', 'review.md', 'story.md')
$titleImageFile = 'title-image.jpg'
$dialogueCraftProfile = 'prospective-2026-08-18'
$outlineWordLimit = 1200
$errors = [Collections.Generic.List[string]]::new()
$warnings = [Collections.Generic.List[string]]::new()
$finalInventory = [Collections.Generic.List[object]]::new()
$storyRoot = Join-Path $ProjectRoot 'stories'

function Get-Section {
    param([string]$Text, [string]$Heading)

    $escaped = [regex]::Escape($Heading)
    $match = [regex]::Match(
        $Text,
        "(?ms)^##\s+$escaped\s*\r?\n(?<body>.*?)(?=^##\s+|\z)"
    )
    if (-not $match.Success) {
        return $null
    }
    return $match.Groups['body'].Value.Trim()
}

function Test-CraftProfile {
    param([string]$PromptText, [string]$Profile)

    $escaped = [regex]::Escape($Profile)
    return [regex]::IsMatch(
        $PromptText,
        "(?m)^-\s+Craft profile:\s*${escaped}\s*$"
    )
}

function Get-MarkdownWordCount {
    param([string]$Text)

    $withoutComments = [regex]::Replace($Text, '(?s)<!--.*?-->', '')
    return [regex]::Matches(
        $withoutComments,
        "\b[\p{L}\p{N}]+(?:['’\-][\p{L}\p{N}]+)*\b"
    ).Count
}

function Get-TableRows {
    param([string]$Section)

    $rows = [Collections.Generic.List[object]]::new()
    foreach ($line in ($Section -split "\r?\n")) {
        $trimmed = $line.Trim()
        if (-not $trimmed.StartsWith('|')) {
            continue
        }

        $cellsText = $trimmed -replace '^\|', '' -replace '\|$', ''
        $cells = @(($cellsText -split '\|') | ForEach-Object { $_.Trim() })
        if ($cells.Count -lt 3 -or $cells[0] -eq 'Noun' -or $cells[0] -match '^:?-{3,}:?$') {
            continue
        }
        $rows.Add([pscustomobject]@{ Cells = $cells })
    }
    return @($rows)
}

function Get-NounRows {
    param(
        [string]$StorySlug,
        [string]$Kind,
        [string]$Text,
        [string]$SourceName
    )

    $section = Get-Section $Text $Kind
    if ($null -eq $section) {
        $errors.Add("$StorySlug/$SourceName lacks the '$Kind' section.")
        return @()
    }

    $rows = [Collections.Generic.List[object]]::new()
    $sawNone = $false
    $dataRows = 0
    foreach ($tableRow in Get-TableRows $section) {
        $cells = @($tableRow.Cells)
        $dataRows++
        $name = ($cells[0] -replace '^\x60|\x60$', '').Trim()
        $status = $cells[1].ToLowerInvariant()
        $note = $cells[2].Trim()

        if ($name -eq 'None') {
            $sawNone = $true
            if ($status -ne 'none') {
                $errors.Add("$StorySlug/$SourceName must give the None row status 'none' in $Kind.")
            }
            if ([string]::IsNullOrWhiteSpace($note)) {
                $errors.Add("$StorySlug/$SourceName needs a short note for the None row in $Kind.")
            }
            continue
        }

        if ([string]::IsNullOrWhiteSpace($name)) {
            $errors.Add("$StorySlug/$SourceName has an empty $Kind noun.")
            continue
        }
        if ($status -notin @('new', 'recurring')) {
            $errors.Add("$StorySlug/$SourceName gives '$name' invalid $Kind status '$status'.")
            continue
        }
        if ([string]::IsNullOrWhiteSpace($note)) {
            $errors.Add("$StorySlug/$SourceName needs a role or continuity note for $Kind noun '$name'.")
        }

        $rows.Add([pscustomobject]@{
            Story = $StorySlug
            Kind = $Kind
            Name = $name
            Key = $name.ToLowerInvariant()
            Status = $status
            Note = $note
            Source = $SourceName
        })
    }

    if ($dataRows -eq 0) {
        $errors.Add("$StorySlug/$SourceName has no noun inventory rows in $Kind.")
    }
    if ($sawNone -and $rows.Count -gt 0) {
        $errors.Add("$StorySlug/$SourceName mixes None with named rows in $Kind.")
    }
    foreach ($duplicate in @($rows | Group-Object Key | Where-Object Count -gt 1)) {
        $errors.Add("$StorySlug/$SourceName lists $Kind noun '$($duplicate.Group[0].Name)' more than once.")
    }
    return @($rows)
}

function Read-LooseNounRows {
    param([string]$Text, [string]$Kind, [string]$StorySlug)

    $section = Get-Section $Text $Kind
    if ($null -eq $section) {
        return @()
    }

    $rows = [Collections.Generic.List[object]]::new()
    foreach ($tableRow in Get-TableRows $section) {
        $cells = @($tableRow.Cells)
        $name = ($cells[0] -replace '^\x60|\x60$', '').Trim()
        $status = $cells[1].ToLowerInvariant()
        if ($name -eq 'None' -or $status -notin @('new', 'recurring')) {
            continue
        }
        $rows.Add([pscustomobject]@{
            Story = $StorySlug
            Kind = $Kind
            Name = $name
            Key = $name.ToLowerInvariant()
            Status = $status
        })
    }
    return @($rows)
}

function Get-JpegDimensions {
    param([string]$Path)

    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 4 -or $bytes[0] -ne 0xff -or $bytes[1] -ne 0xd8) {
        return $null
    }

    $startOfFrameMarkers = @(0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf)
    $offset = 2
    while ($offset -lt $bytes.Length) {
        while ($offset -lt $bytes.Length -and $bytes[$offset] -ne 0xff) {
            $offset++
        }
        while ($offset -lt $bytes.Length -and $bytes[$offset] -eq 0xff) {
            $offset++
        }
        if ($offset -ge $bytes.Length) {
            break
        }

        $marker = $bytes[$offset]
        $offset++
        if ($marker -in @(0x01, 0xd8, 0xd9) -or ($marker -ge 0xd0 -and $marker -le 0xd7)) {
            continue
        }
        if ($offset + 1 -ge $bytes.Length) {
            break
        }

        $segmentLength = ([int]$bytes[$offset] -shl 8) + [int]$bytes[$offset + 1]
        if ($segmentLength -lt 2 -or $offset + $segmentLength -gt $bytes.Length) {
            break
        }
        if ($marker -in $startOfFrameMarkers) {
            if ($segmentLength -lt 7) {
                break
            }
            $height = ([int]$bytes[$offset + 3] -shl 8) + [int]$bytes[$offset + 4]
            $width = ([int]$bytes[$offset + 5] -shl 8) + [int]$bytes[$offset + 6]
            return [pscustomobject]@{ Width = $width; Height = $height }
        }
        $offset += $segmentLength
    }
    return $null
}

function Test-TitleImage {
    param([string]$StorySlug, [string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $errors.Add("$StorySlug is missing $titleImageFile.")
        return
    }

    $dimensions = Get-JpegDimensions $Path
    if ($null -eq $dimensions) {
        $errors.Add("$StorySlug/$titleImageFile is not a readable JPEG.")
        return
    }
    if ($dimensions.Width -ne 864 -or $dimensions.Height -ne 1536) {
        $errors.Add("$StorySlug/$titleImageFile must be exactly 864x1536 (9:16 portrait); found $($dimensions.Width)x$($dimensions.Height).")
    }
}

function Read-StoryPackage {
    param([IO.DirectoryInfo]$Directory)

    $slug = $Directory.Name
    $files = @(Get-ChildItem -LiteralPath $Directory.FullName -File -Force | Select-Object -ExpandProperty Name | Sort-Object)
    $allowedFiles = @($requiredFiles) + $titleImageFile
    $unexpected = @($files | Where-Object { $_ -notin $allowedFiles })
    if ($unexpected.Count -gt 0) {
        $errors.Add("$slug contains unsupported files: $($unexpected -join ', ').")
    }

    $missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $Directory.FullName $_) -PathType Leaf) })
    foreach ($name in $missing) {
        $errors.Add("$slug is missing $name.")
    }
    if ($missing.Count -gt 0) {
        return $null
    }
    if ($Phase -eq 'Final') {
        Test-TitleImage $slug (Join-Path $Directory.FullName $titleImageFile)
    }

    $promptText = Get-Content -LiteralPath (Join-Path $Directory.FullName 'prompt.md') -Raw
    $outlineText = Get-Content -LiteralPath (Join-Path $Directory.FullName 'outline.md') -Raw
    $storyText = Get-Content -LiteralPath (Join-Path $Directory.FullName 'story.md') -Raw
    $reviewText = Get-Content -LiteralPath (Join-Path $Directory.FullName 'review.md') -Raw

    $usesDialogueCraftProfile = Test-CraftProfile $promptText $dialogueCraftProfile
    if ($usesDialogueCraftProfile) {
        $outlineWordCount = Get-MarkdownWordCount $outlineText
        if ($outlineWordCount -gt $outlineWordLimit) {
            $errors.Add("$slug/outline.md exceeds the $outlineWordLimit-word limit for $dialogueCraftProfile; found $outlineWordCount words.")
        }
    }

    $promptSection = Get-Section $promptText 'Prompt'
    if ([string]::IsNullOrWhiteSpace($promptSection) -or $promptSection -notmatch '(?m)^>\s*\S') {
        $errors.Add("$slug/prompt.md must preserve a non-empty blockquoted Prompt section.")
    }

    foreach ($heading in @('Story', 'Beats', 'People', 'Places', 'Continuity')) {
        if ([string]::IsNullOrWhiteSpace((Get-Section $outlineText $heading))) {
            $errors.Add("$slug/outline.md lacks a non-empty '$heading' section.")
        }
    }
    $storySection = Get-Section $outlineText 'Story'
    if ($null -ne $storySection -and $storySection -notmatch '(?m)^-\s+[^:]+:\s*\S') {
        $errors.Add("$slug/outline.md Story section has no completed story statement.")
    }
    $beatsSection = Get-Section $outlineText 'Beats'
    if ($null -ne $beatsSection -and $beatsSection -notmatch '(?m)^\s*\d+\.\s+\S') {
        $errors.Add("$slug/outline.md Beats section has no completed beat.")
    }
    $continuitySection = Get-Section $outlineText 'Continuity'
    if ($null -ne $continuitySection -and $continuitySection -notmatch '(?m)^-\s+[^:]+:\s*\S') {
        $errors.Add("$slug/outline.md Continuity section has no completed boundary.")
    }

    $front = [regex]::Match($storyText, '(?s)\A---\r?\n(?<value>.*?)\r?\n---\r?\n')
    if (-not $front.Success) {
        $errors.Add("$slug/story.md lacks valid frontmatter.")
        $storyBody = $storyText
    }
    else {
        $metadata = [ordered]@{}
        foreach ($line in ($front.Groups['value'].Value -split "\r?\n")) {
            if ($line -notmatch '^(?<key>[a-z]+(?:-[a-z]+)*):\s*(?<value>.*)$') {
                $errors.Add("$slug/story.md has malformed frontmatter line '$line'.")
                continue
            }
            $key = $Matches['key']
            if ($metadata.Contains($key)) {
                $errors.Add("$slug/story.md repeats frontmatter field '$key'.")
            }
            $metadata[$key] = $Matches['value'].Trim().Trim('"').Trim("'")
        }

        $requiredFields = @('canon', 'created', 'slug', 'title')
        $allowedFields = @('canon', 'created', 'created-at', 'slug', 'title')
        $missingFields = @($requiredFields | Where-Object { -not $metadata.Contains($_) })
        $extraFields = @($metadata.Keys | Where-Object { $_ -notin $allowedFields })
        if ($missingFields.Count -ne 0 -or $extraFields.Count -ne 0) {
            $errors.Add("$slug/story.md frontmatter must contain title, slug, created, optional created-at, and canon.")
        }
        if ($metadata.slug -cne $slug) {
            $errors.Add("$slug/story.md has a different slug.")
        }
        if ([string]::IsNullOrWhiteSpace($metadata.title)) {
            $errors.Add("$slug/story.md has an empty title.")
        }
        if ($metadata.created -notmatch '^\d{4}-\d{2}-\d{2}$') {
            $errors.Add("$slug/story.md created must be YYYY-MM-DD.")
        }
        $createdAtValid = $true
        if ($metadata.Contains('created-at')) {
            $parsedCreatedAt = [DateTimeOffset]::MinValue
            $createdAtValid = (
                $metadata['created-at'] -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$' -and
                [DateTimeOffset]::TryParse(
                    $metadata['created-at'],
                    [Globalization.CultureInfo]::InvariantCulture,
                    [Globalization.DateTimeStyles]::None,
                    [ref]$parsedCreatedAt
                ) -and
                $metadata['created-at'].StartsWith("$($metadata.created)T", [StringComparison]::Ordinal)
            )
        }
        if (-not $createdAtValid) {
            $errors.Add("$slug/story.md created-at must be an ISO 8601 timestamp with a timezone and the same date as created.")
        }
        if ($metadata.canon -notin @('true', 'false')) {
            $errors.Add("$slug/story.md canon must be true or false.")
        }
        $storyBody = $storyText.Substring($front.Length)
    }

    $bodyWithoutComments = [regex]::Replace($storyBody, '(?s)<!--.*?-->', '').Trim()
    if ($bodyWithoutComments -notmatch '(?m)^#\s+\S' -or $bodyWithoutComments -notmatch '(?m)^[^#\s].+') {
        $errors.Add("$slug/story.md must contain a title and complete prose.")
    }

    return [pscustomobject]@{
        Slug = $slug
        PromptText = $promptText
        OutlineText = $outlineText
        StoryText = $storyText
        StoryBody = $storyBody
        ReviewText = $reviewText
        UsesDialogueCraftProfile = $usesDialogueCraftProfile
    }
}

function Add-UniverseNouns {
    param([string]$Path, [Collections.Generic.HashSet[string]]$Set)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^##\s+(?<name>.+?)\s*$') {
            $null = $Set.Add($Matches['name'])
        }
        elseif ($line -match '^-\s+Aliases:\s*(?<aliases>.+?)\s*$' -and $Matches['aliases'] -ne 'None') {
            foreach ($alias in ($Matches['aliases'] -split '[;,]')) {
                $clean = $alias.Trim().Trim('`')
                if (-not [string]::IsNullOrWhiteSpace($clean)) {
                    $null = $Set.Add($clean)
                }
            }
        }
    }
}

function Get-StaticBaselines {
    $people = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $places = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

    $namesPath = Join-Path $storyRoot 'NAMES.md'
    if (Test-Path -LiteralPath $namesPath -PathType Leaf) {
        foreach ($line in Get-Content -LiteralPath $namesPath) {
            if (-not $line.StartsWith('|')) {
                continue
            }
            $cells = @((($line -replace '^\|', '' -replace '\|$', '') -split '\|') | ForEach-Object { $_.Trim() })
            if ($cells.Count -lt 2) {
                continue
            }
            foreach ($match in [regex]::Matches($cells[1], '\x60(?<name>[^\x60]+)\x60')) {
                $null = $people.Add($match.Groups['name'].Value)
            }
        }
    }

    Add-UniverseNouns (Join-Path $ProjectRoot 'universe/characters.md') $people
    Add-UniverseNouns (Join-Path $ProjectRoot 'universe/locations.md') $places
    return [pscustomobject]@{ People = $people; Places = $places }
}

function Get-PassingCurrentInventory {
    param([string]$ExcludeStory)

    $rows = [Collections.Generic.List[object]]::new()
    foreach ($directory in Get-ChildItem -LiteralPath $storyRoot -Directory | Sort-Object Name) {
        if ($directory.Name -eq $ExcludeStory -or $directory.Name.StartsWith('_')) {
            continue
        }
        if (Test-Path -LiteralPath (Join-Path $directory.FullName '05-story.md') -PathType Leaf) {
            continue
        }
        $reviewPath = Join-Path $directory.FullName 'review.md'
        if (-not (Test-Path -LiteralPath $reviewPath -PathType Leaf)) {
            continue
        }
        $text = Get-Content -LiteralPath $reviewPath -Raw
        if ($text -notmatch '(?m)^Verdict:\s*PASS\s*$') {
            continue
        }
        foreach ($kind in @('People', 'Places')) {
            foreach ($row in Read-LooseNounRows $text $kind $directory.Name) {
                $rows.Add($row)
            }
        }
    }
    return @($rows)
}

$legacyFiles = @()
if (Test-Path -LiteralPath $storyRoot -PathType Container) {
    $legacyFiles = @(
        Get-ChildItem -LiteralPath $storyRoot -Directory |
            ForEach-Object { Join-Path $_.FullName '05-story.md' } |
            Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }
    )
}

function Test-LegacyExactUse {
    param([string]$Name)

    if ($legacyFiles.Count -eq 0) {
        return $false
    }
    return @(Select-String -LiteralPath $legacyFiles -SimpleMatch -Pattern $Name -List).Count -gt 0
}

function Test-FinalReview {
    param([object]$Package)

    $slug = $Package.Slug
    $reviewText = $Package.ReviewText
    if ($reviewText -notmatch '(?m)^Verdict:\s*PASS\s*$') {
        $errors.Add("$slug/review.md verdict is not PASS.")
    }
    foreach ($area in @('Prompt', 'Universe', 'Internal')) {
        if ($reviewText -notmatch "(?m)^-\s+${area}:\s*PASS\s*$") {
            $errors.Add("$slug/review.md continuity line '$area' is not PASS.")
        }
    }
    if ($reviewText -notmatch '(?m)^-\s+Blocking:\s*none\s*$') {
        $errors.Add("$slug/review.md has unresolved or malformed blocking findings.")
    }
    $requiredReviewHeadings = @('Continuity', 'Findings')
    if ($Package.UsesDialogueCraftProfile) {
        $requiredReviewHeadings += 'Craft'
    }
    foreach ($heading in $requiredReviewHeadings) {
        if ([string]::IsNullOrWhiteSpace((Get-Section $reviewText $heading))) {
            if ($heading -eq 'Craft') {
                $errors.Add("$slug/review.md lacks a non-empty 'Craft' section for the required Dialogue verdict.")
            }
            else {
                $errors.Add("$slug/review.md lacks a non-empty '$heading' section.")
            }
        }
    }

    if ($Package.UsesDialogueCraftProfile) {
        $craftSection = Get-Section $reviewText 'Craft'
        if (-not [string]::IsNullOrWhiteSpace($craftSection)) {
            $dialogueLines = [regex]::Matches(
                $craftSection,
                '(?m)^-\s+Dialogue:\s*(?<value>[^\r\n]+?)\s*$'
            )
            if ($dialogueLines.Count -ne 1) {
                $errors.Add("$slug/review.md Craft section must contain exactly one Dialogue verdict.")
            }
            else {
                $dialogueVerdict = $dialogueLines[0].Groups['value'].Value.Trim()
                if ($dialogueVerdict -notin @('PASS', 'REVISE', 'N/A')) {
                    $errors.Add("$slug/review.md Dialogue verdict must be PASS, REVISE, or N/A; found '$dialogueVerdict'.")
                }
                elseif ($dialogueVerdict -eq 'REVISE') {
                    $errors.Add("$slug/review.md Dialogue verdict is REVISE.")
                }
            }
        }
    }

    foreach ($kind in @('People', 'Places')) {
        foreach ($row in Get-NounRows $slug $kind $reviewText 'review.md') {
            if ($Package.StoryBody.IndexOf($row.Name, [StringComparison]::Ordinal) -lt 0) {
                $errors.Add("$slug/review.md declares $kind noun '$($row.Name)', but that exact form is absent from story.md.")
            }
            $finalInventory.Add($row)
        }
    }
}

if (-not (Test-Path -LiteralPath $storyRoot -PathType Container)) {
    $errors.Add('stories is missing.')
}

$template = Join-Path $storyRoot '_template'
if (-not (Test-Path -LiteralPath $template -PathType Container)) {
    $errors.Add('stories/_template is missing.')
}
else {
    $templateFiles = @(Get-ChildItem -LiteralPath $template -File -Force | Select-Object -ExpandProperty Name | Sort-Object)
    if ((Compare-Object $requiredFiles $templateFiles).Count -ne 0) {
        $errors.Add("stories/_template must contain exactly: $($requiredFiles -join ', ').")
    }
}

$directories = [Collections.Generic.List[IO.DirectoryInfo]]::new()
$legacyCount = 0
if (-not [string]::IsNullOrWhiteSpace($Story)) {
    $target = Join-Path $storyRoot $Story
    if (-not (Test-Path -LiteralPath $target -PathType Container)) {
        $errors.Add("Story directory does not exist: stories/$Story.")
    }
    elseif (Test-Path -LiteralPath (Join-Path $target '05-story.md') -PathType Leaf) {
        $errors.Add("stories/$Story is a locked legacy bundle.")
    }
    else {
        $directories.Add((Get-Item -LiteralPath $target))
    }
}
elseif (Test-Path -LiteralPath $storyRoot -PathType Container) {
    foreach ($directory in Get-ChildItem -LiteralPath $storyRoot -Directory | Sort-Object Name) {
        if ($directory.Name.StartsWith('_')) {
            continue
        }
        if (Test-Path -LiteralPath (Join-Path $directory.FullName '05-story.md') -PathType Leaf) {
            $legacyCount++
            continue
        }
        if (@($requiredFiles | Where-Object { Test-Path -LiteralPath (Join-Path $directory.FullName $_) -PathType Leaf }).Count -gt 0) {
            $directories.Add($directory)
        }
    }
}

$packages = [Collections.Generic.List[object]]::new()
foreach ($directory in $directories) {
    $package = Read-StoryPackage $directory
    if ($null -eq $package) {
        continue
    }
    $packages.Add($package)
    if ($Phase -eq 'Final') {
        foreach ($kind in @('People', 'Places')) {
            $null = @(Get-NounRows $package.Slug $kind $package.OutlineText 'outline.md')
        }
    }
}

$baselines = Get-StaticBaselines

if ($Phase -eq 'PreReview') {
    $existing = @(Get-PassingCurrentInventory $Story)
    $declared = [Collections.Generic.List[object]]::new()
    if ($packages.Count -eq 1) {
        $package = $packages[0]
        foreach ($kind in @('People', 'Places')) {
            foreach ($row in Get-NounRows $package.Slug $kind $package.OutlineText 'outline.md') {
                $declared.Add($row)
            }
        }

        foreach ($row in $declared) {
            $static = if ($row.Kind -eq 'People') { $baselines.People } else { $baselines.Places }
            $currentMatch = @($existing | Where-Object { $_.Kind -eq $row.Kind -and $_.Key -eq $row.Key }).Count -gt 0
            $legacyMatch = Test-LegacyExactUse $row.Name
            $alreadyExists = ($static -contains $row.Name) -or $currentMatch -or $legacyMatch

            if ($row.Status -eq 'new' -and $alreadyExists) {
                $errors.Add("$($row.Story)/outline.md marks $($row.Kind) noun '$($row.Name)' new, but that exact form already exists.")
            }
            elseif ($row.Status -eq 'recurring' -and -not $alreadyExists) {
                $errors.Add("$($row.Story)/outline.md marks $($row.Kind) noun '$($row.Name)' recurring, but no exact prior use was found.")
            }

            if ($package.StoryBody.IndexOf($row.Name, [StringComparison]::Ordinal) -lt 0) {
                $warnings.Add("Advisory outline noun '$($row.Name)' does not appear exactly in story.md; the reviewer must inventory the final prose independently.")
            }
        }
    }

    if ($errors.Count -gt 0) {
        $separator = [Environment]::NewLine + '- '
        throw ('Pre-review validation failed:' + $separator + ($errors -join $separator))
    }

    "PASS: pre-review structure and $($declared.Count) declared person/place nouns checked for $Story."
    if ($warnings.Count -gt 0) {
        "Reviewer notes:"
        foreach ($warning in $warnings) {
            "- $warning"
        }
    }
    else {
        'Reviewer notes: no exact-declaration warnings; exhaustive semantic extraction is still required.'
    }
    return
}

foreach ($package in $packages) {
    Test-FinalReview $package
}

foreach ($group in @($finalInventory | Group-Object Kind, Key)) {
    $sample = $group.Group[0]
    $static = if ($sample.Kind -eq 'People') { $baselines.People } else { $baselines.Places }
    $legacyMatch = Test-LegacyExactUse $sample.Name
    $newUses = @($group.Group | Where-Object Status -eq 'new')
    $recurringUses = @($group.Group | Where-Object Status -eq 'recurring')

    if ($newUses.Count -gt 1) {
        $stories = ($newUses.Story | Sort-Object -Unique) -join ', '
        $errors.Add("Noun '$($sample.Name)' is independently marked new in multiple $($sample.Kind.ToLowerInvariant()) inventories: $stories.")
    }
    if ($newUses.Count -eq 1 -and (($static -contains $sample.Name) -or $legacyMatch)) {
        $errors.Add("$($newUses[0].Story)/review.md marks '$($sample.Name)' new, but that exact $($sample.Kind.ToLowerInvariant()) form already exists.")
    }
    if ($recurringUses.Count -gt 0 -and $newUses.Count -eq 0 -and -not ($static -contains $sample.Name) -and -not $legacyMatch) {
        $stories = ($recurringUses.Story | Sort-Object -Unique) -join ', '
        $errors.Add("Noun '$($sample.Name)' is marked recurring in $stories, but no exact prior use was found.")
    }
}

if ($errors.Count -gt 0) {
    $separator = [Environment]::NewLine + '- '
    throw ('Final story validation failed:' + $separator + ($errors -join $separator))
}

"PASS: four-file scaffold; readable 864x1536 JPEG title-image files (technical check only; visual-tool review remains required); $($packages.Count) current stories; $legacyCount locked legacy stories ignored; final nouns and continuity verified."
