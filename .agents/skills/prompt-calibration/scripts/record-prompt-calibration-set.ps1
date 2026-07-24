[CmdletBinding()]
param(
    [string]$LatestRankedPath,
    [string]$SelectionPath
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '../../../..'
)).Path
$ScoutRoot = Join-Path $ProjectRoot 'data/prompt-scout'
$DataDirectory = $ScoutRoot
$WorkDirectory = Join-Path $ScoutRoot 'work'
$CalibrationDirectory = Join-Path $ScoutRoot 'calibration'
$CalibrationSetsDirectory = Join-Path $CalibrationDirectory 'sets'

if ([string]::IsNullOrWhiteSpace($LatestRankedPath)) {
    $LatestRankedPath = Join-Path $DataDirectory 'latest-ranked.json'
}
if ([string]::IsNullOrWhiteSpace($SelectionPath)) {
    $SelectionPath = Join-Path $WorkDirectory 'pending-calibration.json'
}

$AskedPath = Join-Path $DataDirectory 'calibration-asked.jsonl'
$LatestCalibrationPath = Join-Path $CalibrationDirectory 'latest.json'
$LatestMarkdownPath = Join-Path $CalibrationDirectory 'latest.md'

foreach ($Path in @($LatestRankedPath, $SelectionPath)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required calibration artifact not found: $Path"
    }
}

$LatestRanked = Get-Content -Raw -LiteralPath $LatestRankedPath | ConvertFrom-Json
$Selection = Get-Content -Raw -LiteralPath $SelectionPath | ConvertFrom-Json
if ($Selection.scanId -ne $LatestRanked.scanId) {
    throw 'The calibration selection scanId does not match the latest ranking.'
}

$AskedIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
if (Test-Path -LiteralPath $AskedPath -PathType Leaf) {
    foreach ($Line in Get-Content -LiteralPath $AskedPath) {
        if (-not [string]::IsNullOrWhiteSpace($Line)) {
            $Asked = $Line | ConvertFrom-Json
            if ($Asked.postId) {
                [void]$AskedIds.Add([string]$Asked.postId)
            }
        }
    }
}

$EligibleById = @{}
foreach ($Record in @($LatestRanked.rankings)) {
    if ([int]$Record.rank -gt 10 -and -not $AskedIds.Contains([string]$Record.postId)) {
        $EligibleById[[string]$Record.postId] = $Record
    }
}

$ExpectedCount = [Math]::Min(10, $EligibleById.Count)
$Submitted = @($Selection.prompts)
if ($ExpectedCount -eq 0) {
    throw 'No unasked prompts remain in ranks 11–100 for calibration.'
}
if ($Submitted.Count -ne $ExpectedCount) {
    throw "Expected $ExpectedCount calibration prompts but received $($Submitted.Count)."
}

$SelectedIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$Items = [Collections.Generic.List[object]]::new()
$Number = 0
foreach ($SubmittedItem in $Submitted) {
    $PostId = [string]$SubmittedItem.postId
    if (-not $EligibleById.ContainsKey($PostId)) {
        throw "Calibration post is ineligible, top-ten, missing, or previously asked: $PostId"
    }
    if (-not $SelectedIds.Add($PostId)) {
        throw "Duplicate calibration post ID: $PostId"
    }
    if ([string]::IsNullOrWhiteSpace([string]$SubmittedItem.selectionReason)) {
        throw "A selectionReason is required for calibration post $PostId."
    }

    $Number++
    $Record = $EligibleById[$PostId]
    $Items.Add([ordered]@{
        number = $Number
        postId = $PostId
        title = [string]$Record.title
        url = [string]$Record.url
        scoutRank = [int]$Record.rank
        scoutScore = [double]$Record.score
        scoutReason = [string]$Record.reason
        tags = @($Record.tags)
        selectionReason = ([string]$SubmittedItem.selectionReason).Trim()
    })
}

$CreatedAt = [DateTimeOffset]::UtcNow
$CalibrationId = '{0}-{1}' -f $LatestRanked.scanId, $CreatedAt.ToString('HHmmss')
$Payload = [ordered]@{
    schemaVersion = 1
    calibrationId = $CalibrationId
    scanId = [string]$LatestRanked.scanId
    createdAtUtc = $CreatedAt.ToString('o')
    itemCount = $Items.Count
    items = @($Items)
}

New-Item -ItemType Directory -Path $CalibrationDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $CalibrationSetsDirectory -Force | Out-Null
$Payload | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $LatestCalibrationPath -Encoding utf8NoBOM
$CalibrationSetPath = Join-Path $CalibrationSetsDirectory ("{0}.json" -f $CalibrationId)
if (Test-Path -LiteralPath $CalibrationSetPath -PathType Leaf) {
    throw "Calibration set already exists: $CalibrationId"
}
$Payload | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $CalibrationSetPath -Encoding utf8NoBOM

$Utf8NoBom = [Text.UTF8Encoding]::new($false)
foreach ($Item in $Items) {
    $AskedEvent = [ordered]@{
        schemaVersion = 1
        calibrationId = $CalibrationId
        scanId = [string]$LatestRanked.scanId
        askedAtUtc = $CreatedAt.ToString('o')
        number = $Item.number
        postId = $Item.postId
        scoutRank = $Item.scoutRank
        selectionReason = $Item.selectionReason
    }
    $Line = $AskedEvent | ConvertTo-Json -Compress
    [IO.File]::AppendAllText($AskedPath, $Line + [Environment]::NewLine, $Utf8NoBom)
}

$Markdown = [Text.StringBuilder]::new()
[void]$Markdown.AppendLine('# Prompt taste calibration — latest set')
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine("- Calibration ID: ``$CalibrationId``")
[void]$Markdown.AppendLine("- Source scan: ``$($LatestRanked.scanId)``")
[void]$Markdown.AppendLine('- Task: order every item from most to least interesting to write')
[void]$Markdown.AppendLine()

foreach ($Item in $Items) {
    [void]$Markdown.AppendLine("## $($Item.number). $($Item.title)")
    [void]$Markdown.AppendLine()
    [void]$Markdown.AppendLine("- Current scout rank: $($Item.scoutRank) ($($Item.scoutScore)/100)")
    [void]$Markdown.AppendLine("- Why this comparison helps: $($Item.selectionReason)")
    [void]$Markdown.AppendLine("- [Open prompt on Reddit]($($Item.url))")
    [void]$Markdown.AppendLine()
}

$ExampleOrder = (@($Items.number) -join ', ')
[void]$Markdown.AppendLine('## Your ranking')
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine('Reply with every calibration number from most to least interesting:')
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine("``Calibrator [$CalibrationId] order: $ExampleOrder``")

Set-Content -LiteralPath $LatestMarkdownPath -Value $Markdown.ToString() `
    -Encoding utf8NoBOM

[ordered]@{
    calibrationId = $CalibrationId
    itemCount = $Items.Count
    latestMarkdown = $LatestMarkdownPath
    archivedSet = $CalibrationSetPath
} | ConvertTo-Json -Compress
