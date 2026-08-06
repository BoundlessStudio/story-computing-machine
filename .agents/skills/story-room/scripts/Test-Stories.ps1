#Requires -Version 7.0
[CmdletBinding()]
param([string]$ProjectRoot)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
}
else {
    $ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)
}

$requiredFiles = @('outline.md', 'prompt.md', 'review.md', 'story.md')
$errors = [Collections.Generic.List[string]]::new()
$nounInventory = [Collections.Generic.List[object]]::new()

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

function Get-NounRows {
    param(
        [string]$StorySlug,
        [string]$Kind,
        [string]$ReviewText,
        [string]$StoryBody
    )

    $section = Get-Section $ReviewText $Kind
    if ($null -eq $section) {
        $errors.Add("$StorySlug/review.md lacks the '$Kind' section.")
        return @()
    }

    $rows = [Collections.Generic.List[object]]::new()
    $sawNone = $false
    $dataRows = 0

    foreach ($line in ($section -split "\r?\n")) {
        $trimmed = $line.Trim()
        if (-not $trimmed.StartsWith('|')) {
            continue
        }

        $cellsText = $trimmed -replace '^\|', '' -replace '\|$', ''
        $cells = @(($cellsText -split '\|') | ForEach-Object { $_.Trim() })
        if ($cells.Count -lt 3 -or $cells[0] -eq 'Noun' -or $cells[0] -match '^-+$') {
            continue
        }

        $dataRows++
        $name = ($cells[0] -replace '^\x60|\x60$', '').Trim()
        $status = $cells[1].ToLowerInvariant()
        $note = $cells[2].Trim()

        if ($name -eq 'None') {
            $sawNone = $true
            if ($status -ne 'none') {
                $errors.Add("$StorySlug/review.md must give the None row status 'none' in $Kind.")
            }
            continue
        }

        if ($status -notin @('new', 'recurring')) {
            $errors.Add("$StorySlug/review.md gives '$name' invalid $Kind status '$status'.")
            continue
        }
        if ([string]::IsNullOrWhiteSpace($note)) {
            $errors.Add("$StorySlug/review.md needs a continuity note for $Kind noun '$name'.")
        }
        if ($StoryBody.IndexOf($name, [StringComparison]::Ordinal) -lt 0) {
            $errors.Add("$StorySlug/review.md declares $Kind noun '$name', but that exact form is absent from story.md.")
        }

        $rows.Add([pscustomobject]@{
            Story = $StorySlug
            Kind = $Kind
            Name = $name
            Key = $name.ToLowerInvariant()
            Status = $status
        })
    }

    if ($dataRows -eq 0) {
        $errors.Add("$StorySlug/review.md has no noun inventory rows in $Kind.")
    }
    if ($sawNone -and $rows.Count -gt 0) {
        $errors.Add("$StorySlug/review.md mixes None with named rows in $Kind.")
    }
    foreach ($duplicate in @($rows | Group-Object Key | Where-Object Count -gt 1)) {
        $errors.Add("$StorySlug/review.md lists $Kind noun '$($duplicate.Group[0].Name)' more than once.")
    }

    return @($rows)
}

$template = Join-Path $ProjectRoot 'stories/_template'
if (-not (Test-Path -LiteralPath $template -PathType Container)) {
    $errors.Add('stories/_template is missing.')
}
else {
    $templateFiles = @(Get-ChildItem -LiteralPath $template -File -Force | Select-Object -ExpandProperty Name | Sort-Object)
    if ((Compare-Object $requiredFiles $templateFiles).Count -ne 0) {
        $errors.Add("stories/_template must contain exactly: $($requiredFiles -join ', ').")
    }
}

$storyRoot = Join-Path $ProjectRoot 'stories'
$legacyCount = 0
$currentCount = 0

foreach ($directory in Get-ChildItem -LiteralPath $storyRoot -Directory | Sort-Object Name) {
    if ($directory.Name.StartsWith('_')) {
        continue
    }

    $hasCurrentFile = $false
    foreach ($name in $requiredFiles) {
        if (Test-Path -LiteralPath (Join-Path $directory.FullName $name) -PathType Leaf) {
            $hasCurrentFile = $true
            break
        }
    }

    if (-not $hasCurrentFile) {
        if (Test-Path -LiteralPath (Join-Path $directory.FullName '05-story.md') -PathType Leaf) {
            $legacyCount++
        }
        continue
    }

    $currentCount++
    $slug = $directory.Name
    $files = @(Get-ChildItem -LiteralPath $directory.FullName -File -Force | Select-Object -ExpandProperty Name | Sort-Object)
    if ((Compare-Object $requiredFiles $files).Count -ne 0) {
        $errors.Add("$slug must contain exactly the four current story files.")
    }
    foreach ($name in $requiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $directory.FullName $name) -PathType Leaf)) {
            $errors.Add("$slug is missing $name.")
        }
    }
    $missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $directory.FullName $_) -PathType Leaf) })
    if ($missing.Count -gt 0) {
        continue
    }

    $promptText = Get-Content -LiteralPath (Join-Path $directory.FullName 'prompt.md') -Raw
    $outlineText = Get-Content -LiteralPath (Join-Path $directory.FullName 'outline.md') -Raw
    $storyText = Get-Content -LiteralPath (Join-Path $directory.FullName 'story.md') -Raw
    $reviewText = Get-Content -LiteralPath (Join-Path $directory.FullName 'review.md') -Raw

    $promptSection = Get-Section $promptText 'Prompt'
    if ([string]::IsNullOrWhiteSpace($promptSection) -or $promptSection -notmatch '(?m)^>\s*\S') {
        $errors.Add("$slug/prompt.md must preserve a non-empty blockquoted Prompt section.")
    }

    foreach ($heading in @('Story', 'Beats', 'People', 'Places', 'Continuity')) {
        if ([string]::IsNullOrWhiteSpace((Get-Section $outlineText $heading))) {
            $errors.Add("$slug/outline.md lacks a non-empty '$heading' section.")
        }
    }

    $front = [regex]::Match($storyText, '(?s)\A---\r?\n(?<value>.*?)\r?\n---\r?\n')
    if (-not $front.Success) {
        $errors.Add("$slug/story.md lacks valid frontmatter.")
        $storyBody = $storyText
    }
    else {
        $metadata = [ordered]@{}
        foreach ($line in ($front.Groups['value'].Value -split "\r?\n")) {
            if ($line -notmatch '^(?<key>[a-z]+):\s*(?<value>.*)$') {
                $errors.Add("$slug/story.md has malformed frontmatter line '$line'.")
                continue
            }
            $key = $Matches['key']
            if ($metadata.Contains($key)) {
                $errors.Add("$slug/story.md repeats frontmatter field '$key'.")
            }
            $metadata[$key] = $Matches['value'].Trim().Trim('"').Trim("'")
        }

        $expectedFields = @('canon', 'created', 'slug', 'title')
        $actualFields = @($metadata.Keys | Sort-Object)
        if ((Compare-Object $expectedFields $actualFields).Count -ne 0) {
            $errors.Add("$slug/story.md frontmatter must contain exactly title, slug, created, and canon.")
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
        if ($metadata.canon -notin @('true', 'false')) {
            $errors.Add("$slug/story.md canon must be true or false.")
        }
        $storyBody = $storyText.Substring($front.Length)
    }

    $bodyWithoutComments = [regex]::Replace($storyBody, '(?s)<!--.*?-->', '').Trim()
    if ($bodyWithoutComments -notmatch '(?m)^#\s+\S' -or $bodyWithoutComments -notmatch '(?m)^[^#\s].+') {
        $errors.Add("$slug/story.md must contain a title and complete prose.")
    }

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
    foreach ($heading in @('Continuity', 'Findings')) {
        if ([string]::IsNullOrWhiteSpace((Get-Section $reviewText $heading))) {
            $errors.Add("$slug/review.md lacks a non-empty '$heading' section.")
        }
    }

    foreach ($row in Get-NounRows $slug 'People' $reviewText $storyBody) {
        $nounInventory.Add($row)
    }
    foreach ($row in Get-NounRows $slug 'Places' $reviewText $storyBody) {
        $nounInventory.Add($row)
    }
}

$legacyPeople = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
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
            $null = $legacyPeople.Add($match.Groups['name'].Value)
        }
    }
}

$legacyPlaces = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$locationsPath = Join-Path $ProjectRoot 'universe/locations.md'
if (Test-Path -LiteralPath $locationsPath -PathType Leaf) {
    foreach ($line in Get-Content -LiteralPath $locationsPath) {
        if ($line -match '^##\s+(?<name>.+?)\s*$') {
            $name = $Matches['name']
            $null = $legacyPlaces.Add($name)
            if ($name.StartsWith('The ')) {
                $null = $legacyPlaces.Add($name.Substring(4))
            }
        }
    }
}

foreach ($noun in $nounInventory) {
    $baseline = $legacyPlaces
    if ($noun.Kind -eq 'People') {
        $baseline = $legacyPeople
    }
    if ($noun.Status -eq 'new' -and $baseline.Contains($noun.Name)) {
        $errors.Add("$($noun.Story)/review.md marks '$($noun.Name)' new, but it already exists in the legacy $($noun.Kind.ToLowerInvariant()) baseline.")
    }
}

foreach ($group in @($nounInventory | Group-Object Kind, Key)) {
    $newUses = @($group.Group | Where-Object Status -eq 'new')
    if ($newUses.Count -gt 1) {
        $stories = ($newUses.Story | Sort-Object -Unique) -join ', '
        $errors.Add("Noun '$($group.Group[0].Name)' is independently marked new in multiple $($group.Group[0].Kind.ToLowerInvariant()) inventories: $stories.")
    }
}

if ($errors.Count -gt 0) {
    $separator = [Environment]::NewLine + '- '
    throw ('Story validation failed:' + $separator + ($errors -join $separator))
}

"PASS: four-file template; $currentCount current stories; $legacyCount locked legacy stories ignored."
