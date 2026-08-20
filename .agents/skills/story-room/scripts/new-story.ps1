#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Slug,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Title,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Prompt,

    [Alias('ReferenceImages')]
    [string[]]$ReferenceImage = @(),

    [string]$Date = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$CreatedAt,
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $invocationDirectory = (Get-Location).Path
    $gitRoot = (& git -C $invocationDirectory rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitRoot)) {
        throw 'Run new-story.ps1 from within the target Git worktree or pass -ProjectRoot explicitly.'
    }
    $ProjectRoot = [IO.Path]::GetFullPath($gitRoot.Trim())
}
else {
    $ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)
}

if ($Date -notmatch '^\d{4}-\d{2}-\d{2}$') {
    throw 'Date must be YYYY-MM-DD.'
}

if ([string]::IsNullOrWhiteSpace($CreatedAt)) {
    $CreatedAt = "${Date}T$((Get-Date).ToString('HH:mm:sszzz'))"
}
$parsedCreatedAt = [DateTimeOffset]::MinValue
$validCreatedAt = (
    $CreatedAt -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$' -and
    [DateTimeOffset]::TryParse(
        $CreatedAt,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::None,
        [ref]$parsedCreatedAt
    ) -and
    $CreatedAt.StartsWith("$Date`T", [StringComparison]::Ordinal)
)
if (-not $validCreatedAt) {
    throw 'CreatedAt must be an ISO 8601 timestamp with a timezone and the same date as Date.'
}

$branch = (& git -C $ProjectRoot branch --show-current 2>$null)
if ($LASTEXITCODE -eq 0 -and $branch.Trim() -eq 'main') {
    throw 'Create a non-main story branch before scaffolding.'
}

$template = Join-Path $ProjectRoot 'stories/_template'
$target = Join-Path $ProjectRoot "stories/$Slug"
if (Test-Path -LiteralPath $target) {
    throw "Story directory already exists: $target"
}
if (-not (Test-Path -LiteralPath $template -PathType Container)) {
    throw "Story template not found: $template"
}

Copy-Item -LiteralPath $template -Destination $target -Recurse

$normalizedPrompt = [regex]::Replace($Prompt, '\r\n?', [string][char]10).Trim()
$promptBlock = (($normalizedPrompt -split '\n') | ForEach-Object { "> $($_.TrimEnd())" }) -join [char]10
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
    '- None supplied.'
}
else {
    ($referenceImageLabels | ForEach-Object { "- ``$($_.Replace('`', "'"))``" }) -join [char]10
}
$titleYaml = $Title | ConvertTo-Json -Compress

foreach ($file in Get-ChildItem -LiteralPath $target -File) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    $text = $text.Replace('{{slug}}', $Slug)
    $text = $text.Replace('{{title}}', $Title)
    $text = $text.Replace('{{title_yaml}}', $titleYaml)
    $text = $text.Replace('{{date}}', $Date)
    $text = $text.Replace('{{created_at}}', $CreatedAt)
    $text = $text.Replace('{{prompt_block}}', $promptBlock)
    $text = $text.Replace('{{reference_image_block}}', $referenceImageBlock)
    $text = [regex]::Replace($text, '\r\n?', [string][char]10)
    [IO.File]::WriteAllText($file.FullName, $text, [Text.UTF8Encoding]::new($false))
}

[ordered]@{
    story = $Slug
    directory = "stories/$Slug"
    files = @('prompt.md', 'outline.md', 'story.md', 'review.md')
} | ConvertTo-Json
