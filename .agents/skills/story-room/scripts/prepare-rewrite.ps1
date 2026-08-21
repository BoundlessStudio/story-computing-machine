#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Title,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Request,

    [Alias('ReferenceImages')]
    [string[]]$ReferenceImage = @(),

    [ValidateSet('Auto', 'Keep', 'Regenerate')]
    [string]$Cover = 'Auto',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Title)) {
    throw 'Rewrite title cannot be blank.'
}
if ([string]::IsNullOrWhiteSpace($Request)) {
    throw 'Rewrite request cannot be blank.'
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $invocationDirectory = (Get-Location).Path
    $gitRoot = (& git -C $invocationDirectory rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitRoot)) {
        throw 'Run prepare-rewrite.ps1 from within the target Git worktree or pass -ProjectRoot explicitly.'
    }
    $ProjectRoot = [IO.Path]::GetFullPath($gitRoot.Trim())
}
else {
    $ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)
}

$branch = (& git -C $ProjectRoot branch --show-current 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
    throw 'Rewrite preparation requires a Git worktree on a named branch.'
}
if ($branch.Trim() -eq 'main') {
    throw 'Create a non-main rewrite branch and dedicated worktree before preparing a rewrite.'
}

$relativeDirectory = "stories/$Story"
$target = Join-Path $ProjectRoot $relativeDirectory
if (-not (Test-Path -LiteralPath $target -PathType Container)) {
    throw "Story directory not found: $target"
}
if (Test-Path -LiteralPath (Join-Path $target '05-story.md') -PathType Leaf) {
    throw 'Locked legacy bundles cannot be rewritten.'
}

$requiredFiles = @('prompt.md', 'outline.md', 'story.md', 'review.md', 'title-image.jpg')
$missing = @($requiredFiles | Where-Object {
    -not (Test-Path -LiteralPath (Join-Path $target $_) -PathType Leaf)
})
if ($missing.Count -gt 0) {
    throw "Rewrite requires a completed current story; missing: $($missing -join ', ')."
}

$storyStatus = @(& git -C $ProjectRoot status --porcelain -- $relativeDirectory)
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to verify the target story worktree state.'
}
if ($storyStatus.Count -gt 0) {
    throw 'The target story has uncommitted changes. Preserve or commit them before preparing a rewrite.'
}

$storyPath = Join-Path $target 'story.md'
$storyText = Get-Content -LiteralPath $storyPath -Raw
if ($storyText -match '(?m)^canon:\s*true\s*$') {
    throw 'Canon stories require an explicit retcon or canon ruling and cannot use the ordinary rewrite path.'
}
$front = [regex]::Match($storyText, '(?s)\A---\r?\n(?<value>.*?)\r?\n---\r?\n')
if (-not $front.Success) {
    throw 'Current story.md lacks valid frontmatter.'
}
$oldTitleMatch = [regex]::Match($front.Groups['value'].Value, '(?m)^title:\s*(?<value>.+?)\s*$')
if (-not $oldTitleMatch.Success) {
    throw 'Current story.md frontmatter lacks title.'
}
$oldTitle = $oldTitleMatch.Groups['value'].Value.Trim().Trim('"').Trim("'")
if ($Cover -eq 'Keep' -and $Title -cne $oldTitle) {
    throw 'Cover Keep requires the rewrite title to match the existing reader-facing title exactly.'
}

$reviewPath = Join-Path $target 'review.md'
$reviewText = Get-Content -LiteralPath $reviewPath -Raw
if ($reviewText -notmatch '(?m)^Verdict:\s*PASS\s*$') {
    throw 'Rewrite preparation requires a completed current story with Verdict: PASS.'
}
foreach ($area in @('Prompt', 'Universe', 'Internal')) {
    if ($reviewText -notmatch "(?m)^-\s+${area}:\s*PASS\s*$") {
        throw "Rewrite preparation requires the existing ${area} continuity verdict to be PASS."
    }
}

$normalizedRequest = [regex]::Replace($Request, '\r\n?', [string][char]10).Trim()
$requestBlock = (($normalizedRequest -split '\n') | ForEach-Object { "> $($_.TrimEnd())" }) -join [char]10

$referenceImageLabelCounts = @{}
$referenceImageLabels = @(
    foreach ($image in $ReferenceImage) {
        if ([string]::IsNullOrWhiteSpace($image)) {
            continue
        }
        $trimmed = $image.Trim()
        $leaf = [IO.Path]::GetFileName($trimmed)
        $label = if ([string]::IsNullOrWhiteSpace($leaf)) { $trimmed } else { $leaf }
        $labelKey = $label.ToUpperInvariant()
        $referenceImageLabelCounts[$labelKey] = 1 + [int]$referenceImageLabelCounts[$labelKey]
        $labelCount = $referenceImageLabelCounts[$labelKey]
        if ($labelCount -eq 1) { $label } else { "$label ($labelCount)" }
    }
)
$referenceImageBlock = if ($referenceImageLabels.Count -eq 0) {
    '- None supplied for this rewrite.'
}
else {
    ($referenceImageLabels | ForEach-Object { "- ``$($_.Replace('`', "'"))``" }) -join [char]10
}

$promptPath = Join-Path $target 'prompt.md'
$promptText = [regex]::Replace(
    (Get-Content -LiteralPath $promptPath -Raw),
    '\r\n?',
    [string][char]10
)
foreach ($heading in @('Rewrite request', 'Rewrite reference images', 'Rewrite constraints')) {
    $escaped = [regex]::Escape($heading)
    $promptText = [regex]::Replace(
        $promptText,
        "(?ms)^##\s+$escaped\s*\n.*?(?=^##\s+|\z)",
        ''
    )
}

$coverValue = $Cover.ToUpperInvariant()
$rewriteSections = @"
## Rewrite request

$requestBlock

## Rewrite reference images

$referenceImageBlock

## Rewrite constraints

- Cover: $coverValue
- Authority: the rewrite request controls where it conflicts with the original prompt; all unaffected original requirements remain binding.
"@.Trim()

$anchor = [regex]::Match($promptText, '(?m)^##\s+(?:Reference images|Constraints)\s*$')
if ($anchor.Success) {
    $promptText = $promptText.Insert($anchor.Index, "$rewriteSections`n`n")
}
else {
    $promptText = "$($promptText.TrimEnd())`n`n$rewriteSections`n"
}
$promptText = [regex]::Replace($promptText, '\n{3,}', "`n`n").TrimEnd() + "`n"
[IO.File]::WriteAllText($promptPath, $promptText, [Text.UTF8Encoding]::new($false))

$outlineTemplate = Join-Path $ProjectRoot 'stories/_template/outline.md'
if (-not (Test-Path -LiteralPath $outlineTemplate -PathType Leaf)) {
    throw "Outline template not found: $outlineTemplate"
}
$pendingOutline = [regex]::Replace(
    (Get-Content -LiteralPath $outlineTemplate -Raw),
    '\r\n?',
    [string][char]10
)
[IO.File]::WriteAllText(
    (Join-Path $target 'outline.md'),
    $pendingOutline,
    [Text.UTF8Encoding]::new($false)
)

$titleYaml = $Title | ConvertTo-Json -Compress
$newFrontmatter = [regex]::Replace(
    ([regex]::Replace($front.Groups['value'].Value, '\r\n?', [string][char]10)),
    '(?m)^title:\s*.*$',
    "title: $titleYaml"
)
$pendingStory = @"
---
$newFrontmatter
---

# $Title

<!-- Complete reader-facing prose goes here. -->
"@.Trim() + "`n"
[IO.File]::WriteAllText($storyPath, $pendingStory, [Text.UTF8Encoding]::new($false))

$reviewTemplate = Join-Path $ProjectRoot 'stories/_template/review.md'
if (-not (Test-Path -LiteralPath $reviewTemplate -PathType Leaf)) {
    throw "Review template not found: $reviewTemplate"
}
$pendingReview = [regex]::Replace(
    (Get-Content -LiteralPath $reviewTemplate -Raw),
    '\r\n?',
    [string][char]10
)
[IO.File]::WriteAllText($reviewPath, $pendingReview, [Text.UTF8Encoding]::new($false))

$titleImagePath = Join-Path $target 'title-image.jpg'
$coverFile = 'retained'
if ($Cover -eq 'Regenerate') {
    Remove-Item -LiteralPath $titleImagePath
    $coverFile = 'removed; fresh generation required after PASS'
}

[ordered]@{
    story = $Story
    directory = $relativeDirectory
    mode = 'REWRITE'
    cover = $coverValue
    coverFile = $coverFile
    changed = @('prompt.md', 'outline.md', 'story.md', 'review.md')
    next = 'Run the normal OUTLINE, WRITE, PreReview, and REVIEW stages from the amended prompt.'
} | ConvertTo-Json
