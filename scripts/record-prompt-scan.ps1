[CmdletBinding()]
param(
    [string]$CandidatePath,
    [string]$RankingsPath,
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScoutRoot = Join-Path $ProjectRoot 'prompt-scout'
$DataDirectory = Join-Path $ScoutRoot 'data'
$ScansDirectory = Join-Path $ScoutRoot 'scans'

if ([string]::IsNullOrWhiteSpace($CandidatePath)) {
    $CandidatePath = Join-Path $DataDirectory 'pending-scan.json'
}
if ([string]::IsNullOrWhiteSpace($RankingsPath)) {
    $RankingsPath = Join-Path $DataDirectory 'pending-rankings.json'
}

$RankingsLedgerPath = Join-Path $DataDirectory 'rankings.jsonl'
$ScannedIdsPath = Join-Path $DataDirectory 'scanned-ids.txt'
$LatestRankedPath = Join-Path $DataDirectory 'latest-ranked.json'
$LatestMarkdownPath = Join-Path $ScoutRoot 'latest.md'

function Set-AtomicUtf8Text {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $Directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $TemporaryPath = Join-Path $Directory (
        '.{0}.{1}.tmp' -f (Split-Path -Leaf $Path), [guid]::NewGuid().ToString('N')
    )
    try {
        [IO.File]::WriteAllText($TemporaryPath, $Content, [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($TemporaryPath, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryPath -PathType Leaf) {
            Remove-Item -LiteralPath $TemporaryPath -Force
        }
    }
}

foreach ($Path in @($CandidatePath, $RankingsPath)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required scan artifact not found: $Path"
    }
}

$CandidateBatch = Get-Content -Raw -LiteralPath $CandidatePath |
    ConvertFrom-Json -DateKind String
$RankingBatch = Get-Content -Raw -LiteralPath $RankingsPath |
    ConvertFrom-Json -DateKind String

if (-not $CandidateBatch.scanId -or $RankingBatch.scanId -ne $CandidateBatch.scanId) {
    throw 'The ranking scanId does not match the pending candidate scanId.'
}

$ArchivePath = Join-Path $ScansDirectory ("{0}.json" -f $CandidateBatch.scanId)
if ((Test-Path -LiteralPath $ArchivePath -PathType Leaf) -and -not $Rebuild) {
    throw "Scan $($CandidateBatch.scanId) has already been finalized."
}

$Candidates = @($CandidateBatch.prompts)
$SubmittedRankings = @($RankingBatch.rankings)
if ($Candidates.Count -ne $SubmittedRankings.Count) {
    throw "Expected $($Candidates.Count) rankings but received $($SubmittedRankings.Count)."
}

$CandidateById = @{}
foreach ($Candidate in $Candidates) {
    if ($CandidateById.ContainsKey([string]$Candidate.postId)) {
        throw "Duplicate candidate ID: $($Candidate.postId)"
    }
    $CandidateById[[string]$Candidate.postId] = $Candidate
}

$RankingIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
foreach ($Ranking in $SubmittedRankings) {
    $PostId = [string]$Ranking.postId
    if (-not $CandidateById.ContainsKey($PostId)) {
        throw "Ranking contains an unknown post ID: $PostId"
    }
    if (-not $RankingIds.Add($PostId)) {
        throw "Duplicate ranking ID: $PostId"
    }
    if ($null -eq $Ranking.score -or [double]$Ranking.score -lt 0 -or
        [double]$Ranking.score -gt 100) {
        throw "Score for $PostId must be between 0 and 100."
    }
    if ([string]::IsNullOrWhiteSpace([string]$Ranking.reason)) {
        throw "Ranking reason is required for $PostId."
    }
    if (@($Ranking.tags).Count -lt 1) {
        throw "At least one tag is required for $PostId."
    }
}

$Sorted = @($SubmittedRankings | Sort-Object `
    @{ Expression = { [double]$_.score }; Descending = $true }, `
    @{ Expression = { $CandidateById[[string]$_.postId].createdAtUtc }; Descending = $true }, `
    @{ Expression = { [string]$_.postId }; Descending = $false })

$FinalizedAt = [DateTimeOffset]::UtcNow.ToString('o')
$Records = [Collections.Generic.List[object]]::new()
$Rank = 0
foreach ($Ranking in $Sorted) {
    $Rank++
    $Candidate = $CandidateById[[string]$Ranking.postId]
    $Records.Add([ordered]@{
        schemaVersion = 1
        scanId = [string]$CandidateBatch.scanId
        fetchedAtUtc = [string]$CandidateBatch.fetchedAtUtc
        finalizedAtUtc = $FinalizedAt
        postId = [string]$Candidate.postId
        title = [string]$Candidate.title
        url = [string]$Candidate.url
        author = [string]$Candidate.author
        createdAtUtc = [string]$Candidate.createdAtUtc
        redditScore = $Candidate.redditScore
        commentCount = $Candidate.commentCount
        score = [double]$Ranking.score
        rank = $Rank
        selectedTop10 = $Rank -le 10
        reason = ([string]$Ranking.reason).Trim()
        tags = @($Ranking.tags | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
    })
}

New-Item -ItemType Directory -Path $DataDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $ScansDirectory -Force | Out-Null

$LatestPayload = [ordered]@{
    schemaVersion = 1
    scanId = [string]$CandidateBatch.scanId
    fetchedAtUtc = [string]$CandidateBatch.fetchedAtUtc
    finalizedAtUtc = $FinalizedAt
    candidateCount = $Records.Count
    rankings = @($Records)
}
$ArchivePayload = [ordered]@{
    schemaVersion = 1
    scan = $CandidateBatch
    finalizedAtUtc = $FinalizedAt
    rankings = @($Records)
}

$LedgerLines = [Collections.Generic.List[string]]::new()
if (Test-Path -LiteralPath $RankingsLedgerPath -PathType Leaf) {
    foreach ($ExistingLine in Get-Content -LiteralPath $RankingsLedgerPath) {
        if ([string]::IsNullOrWhiteSpace($ExistingLine)) {
            continue
        }
        try {
            $ExistingRecord = $ExistingLine | ConvertFrom-Json -DateKind String
        }
        catch {
            throw "Invalid JSON in rankings ledger: $($_.Exception.Message)"
        }
        if ([string]$ExistingRecord.scanId -ne [string]$CandidateBatch.scanId) {
            $LedgerLines.Add($ExistingLine)
        }
    }
}
foreach ($Record in $Records) {
    $LedgerLines.Add(($Record | ConvertTo-Json -Depth 6 -Compress))
}

$AllScannedIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
if (Test-Path -LiteralPath $ScannedIdsPath -PathType Leaf) {
    foreach ($Line in Get-Content -LiteralPath $ScannedIdsPath) {
        $Id = $Line.Trim()
        if ($Id -and -not $Id.StartsWith('#')) {
            [void]$AllScannedIds.Add($Id)
        }
    }
}
foreach ($Record in $Records) {
    [void]$AllScannedIds.Add([string]$Record.postId)
}
$ScannedLines = @('# Reddit post IDs already fully ranked; one ID per line.') +
    @($AllScannedIds | Sort-Object)

function Escape-MarkdownTableCell {
    param([string]$Value)
    return ($Value -replace '\|', '\|' -replace '[\r\n]+', ' ').Trim()
}

$Markdown = [Text.StringBuilder]::new()
[void]$Markdown.AppendLine('# Writing Prompt Scout — latest ranking')
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine("- Scan ID: ``$($CandidateBatch.scanId)``")
[void]$Markdown.AppendLine("- Fetched: $($CandidateBatch.fetchedAtUtc)")
[void]$Markdown.AppendLine("- Scope: newest $($Records.Count) previously unscanned ``[WP]`` posts")
[void]$Markdown.AppendLine('- Ranking basis: explicit feedback, seed-story fit, story engine, novelty, then Reddit engagement as a tie-breaker')
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine('## Top 10')
[void]$Markdown.AppendLine()

foreach ($Record in @($Records | Select-Object -First 10)) {
    [void]$Markdown.AppendLine("### $($Record.rank). $($Record.title)")
    [void]$Markdown.AppendLine()
    [void]$Markdown.AppendLine("- Fit score: **$($Record.score)/100**")
    [void]$Markdown.AppendLine("- Why it fits: $($Record.reason)")
    [void]$Markdown.AppendLine("- Tags: $(@($Record.tags) -join ', ')")
    [void]$Markdown.AppendLine("- [Open prompt on Reddit]($($Record.url))")
    [void]$Markdown.AppendLine()
}

[void]$Markdown.AppendLine('## Remaining ranked prompts')
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine('| Rank | Score | Prompt | Reddit |')
[void]$Markdown.AppendLine('| ---: | ---: | --- | --- |')
foreach ($Record in @($Records | Select-Object -Skip 10)) {
    $Title = Escape-MarkdownTableCell -Value $Record.title
    [void]$Markdown.AppendLine("| $($Record.rank) | $($Record.score) | $Title | [link]($($Record.url)) |")
}
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine('## Feedback')
[void]$Markdown.AppendLine()
[void]$Markdown.AppendLine("Use the scan ID and rank numbers, for example: ``Prompt scout [$($CandidateBatch.scanId)]: like 1, 4; dislike 7; 4 because the impossible premise is grounded in a relationship.``")

$NewLine = [Environment]::NewLine
$LatestJson = ($LatestPayload | ConvertTo-Json -Depth 8) + $NewLine
$LedgerText = (@($LedgerLines) -join $NewLine) + $NewLine
$ScannedText = ($ScannedLines -join $NewLine) + $NewLine
$MarkdownText = $Markdown.ToString()
$ArchiveJson = ($ArchivePayload | ConvertTo-Json -Depth 10) + $NewLine

# The archive is the commit marker and is written last. If an earlier write is
# interrupted, rerunning with the same pending inputs safely rebuilds the
# ledger without duplicate scan records.
Set-AtomicUtf8Text -Path $LatestRankedPath -Content $LatestJson
Set-AtomicUtf8Text -Path $RankingsLedgerPath -Content $LedgerText
Set-AtomicUtf8Text -Path $ScannedIdsPath -Content $ScannedText
Set-AtomicUtf8Text -Path $LatestMarkdownPath -Content $MarkdownText
Set-AtomicUtf8Text -Path $ArchivePath -Content $ArchiveJson

[ordered]@{
    scanId = [string]$CandidateBatch.scanId
    rankedCount = $Records.Count
    top10 = @($Records | Select-Object -First 10 | ForEach-Object {
        [ordered]@{ rank = $_.rank; postId = $_.postId; score = $_.score; title = $_.title }
    })
    latestMarkdown = $LatestMarkdownPath
    archivePath = $ArchivePath
} | ConvertTo-Json -Depth 6 -Compress
