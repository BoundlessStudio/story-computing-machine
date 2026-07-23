[CmdletBinding()]
param(
    [ValidateRange(1, 100)]
    [int]$Limit = 100,

    [ValidateRange(1, 25)]
    [int]$MaxPages = 15
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScoutRoot = Join-Path $ProjectRoot 'prompt-scout'
$DataDirectory = Join-Path $ScoutRoot 'data'
$ScannedIdsPath = Join-Path $DataDirectory 'scanned-ids.txt'
$OutputPath = Join-Path $DataDirectory 'pending-scan.json'

function Get-HtmlAttribute {
    param(
        [Parameter(Mandatory = $true)][string]$Attributes,
        [Parameter(Mandatory = $true)][string]$Name
    )

    $Pattern = '(?:^|\s)' + [regex]::Escape($Name) + '="(?<value>[^"]*)"'
    $Match = [regex]::Match($Attributes, $Pattern)
    if (-not $Match.Success) {
        return $null
    }

    return [Net.WebUtility]::HtmlDecode($Match.Groups['value'].Value)
}

function ConvertFrom-TitleHtml {
    param([Parameter(Mandatory = $true)][string]$Html)

    $WithoutTags = [regex]::Replace($Html, '<[^>]+>', '')
    return [Net.WebUtility]::HtmlDecode($WithoutTags).Trim()
}

New-Item -ItemType Directory -Path $DataDirectory -Force | Out-Null

$ScannedIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
if (Test-Path -LiteralPath $ScannedIdsPath -PathType Leaf) {
    foreach ($Line in Get-Content -LiteralPath $ScannedIdsPath) {
        $Id = $Line.Trim()
        if ($Id -and -not $Id.StartsWith('#')) {
            [void]$ScannedIds.Add($Id)
        }
    }
}

$BatchIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::OrdinalIgnoreCase
)
$SkippedPreviouslyScanned = 0
$Prompts = [Collections.Generic.List[object]]::new()
$SourceUrls = [Collections.Generic.List[string]]::new()
$Headers = @{
    'User-Agent' = 'Mozilla/5.0 (compatible; StoryComputingMachine-PromptScout/1.0)'
}
$NextUrl = 'https://old.reddit.com/r/WritingPrompts/new/?limit=100'
$PagesFetched = 0

while ($Prompts.Count -lt $Limit -and $NextUrl -and $PagesFetched -lt $MaxPages) {
    $PagesFetched++
    $SourceUrls.Add($NextUrl)

    try {
        $Response = Invoke-WebRequest -Uri $NextUrl -Headers $Headers -Method Get `
            -TimeoutSec 30 -UseBasicParsing
    }
    catch {
        throw "Reddit listing fetch failed on page $PagesFetched`: $($_.Exception.Message)"
    }

    if ($Response.StatusCode -ne 200 -or
        $Response.Content -match '<title>Reddit - Please wait for verification</title>') {
        throw 'Reddit returned a verification page instead of the public listing.'
    }

    $Blocks = [regex]::Matches(
        $Response.Content,
        '(?s)<div class=" thing(?<attrs>[^>]*)>(?<body>.*?)(?=<div class=" thing|\z)'
    )

    if ($Blocks.Count -eq 0) {
        throw 'No Reddit post blocks were found in the public listing response.'
    }

    foreach ($Block in $Blocks) {
        if ($Prompts.Count -ge $Limit) {
            break
        }

        $Attributes = $Block.Groups['attrs'].Value
        $Body = $Block.Groups['body'].Value
        $Fullname = Get-HtmlAttribute -Attributes $Attributes -Name 'data-fullname'
        if (-not $Fullname -or -not $Fullname.StartsWith('t3_')) {
            continue
        }

        $PostId = $Fullname.Substring(3)
        if ($ScannedIds.Contains($PostId)) {
            $SkippedPreviouslyScanned++
            continue
        }
        if ($BatchIds.Contains($PostId)) {
            continue
        }

        $TitleMatch = [regex]::Match(
            $Body,
            '(?s)<a class="title may-blank[^"]*"[^>]*>(?<title>.*?)</a>'
        )
        if (-not $TitleMatch.Success) {
            continue
        }

        $Title = ConvertFrom-TitleHtml -Html $TitleMatch.Groups['title'].Value
        if ($Title -notmatch '^\[WP\]\s+') {
            continue
        }

        $Permalink = Get-HtmlAttribute -Attributes $Attributes -Name 'data-permalink'
        if (-not $Permalink) {
            $Permalink = Get-HtmlAttribute -Attributes $Attributes -Name 'data-url'
        }
        if ($Permalink -and $Permalink.StartsWith('/')) {
            $Permalink = 'https://www.reddit.com' + $Permalink
        }

        $TimestampValue = Get-HtmlAttribute -Attributes $Attributes -Name 'data-timestamp'
        $CreatedAtUtc = $null
        if ($TimestampValue -match '^\d+$') {
            $CreatedAtUtc = [DateTimeOffset]::FromUnixTimeMilliseconds(
                [long]$TimestampValue
            ).UtcDateTime.ToString('o')
        }

        $ScoreValue = Get-HtmlAttribute -Attributes $Attributes -Name 'data-score'
        $CommentValue = Get-HtmlAttribute -Attributes $Attributes -Name 'data-comments-count'
        $FeedRankValue = Get-HtmlAttribute -Attributes $Attributes -Name 'data-rank'

        [void]$BatchIds.Add($PostId)
        $Prompts.Add([ordered]@{
            postId = $PostId
            fullname = $Fullname
            title = $Title
            url = $Permalink
            author = Get-HtmlAttribute -Attributes $Attributes -Name 'data-author'
            createdAtUtc = $CreatedAtUtc
            redditScore = if ($ScoreValue -match '^-?\d+$') { [int]$ScoreValue } else { $null }
            commentCount = if ($CommentValue -match '^\d+$') { [int]$CommentValue } else { $null }
            sourcePage = $PagesFetched
            sourceFeedRank = if ($FeedRankValue -match '^\d+$') { [int]$FeedRankValue } else { $null }
        })
    }

    $NextMatch = [regex]::Match(
        $Response.Content,
        '<span class="next-button"><a href="(?<href>[^"]+)"'
    )
    if ($NextMatch.Success) {
        $NextUrl = [Net.WebUtility]::HtmlDecode($NextMatch.Groups['href'].Value)
    }
    else {
        $NextUrl = $null
    }
}

$FetchedAt = [DateTimeOffset]::UtcNow
$ScanId = $FetchedAt.ToString('yyyyMMddTHHmmssZ')
$Payload = [ordered]@{
    schemaVersion = 1
    scanId = $ScanId
    fetchedAtUtc = $FetchedAt.ToString('o')
    subreddit = 'WritingPrompts'
    tag = 'WP'
    sort = 'new'
    requestedUnscannedCount = $Limit
    candidateCount = $Prompts.Count
    pagesFetched = $PagesFetched
    exhaustedPagination = -not [bool]$NextUrl
    sourceUrls = @($SourceUrls)
    prompts = @($Prompts)
}

$Json = $Payload | ConvertTo-Json -Depth 8
Set-Content -LiteralPath $OutputPath -Value $Json -Encoding utf8NoBOM

[ordered]@{
    scanId = $ScanId
    candidateCount = $Prompts.Count
    requestedCount = $Limit
    pagesFetched = $PagesFetched
    skippedPreviouslyScanned = $SkippedPreviouslyScanned
    scannedLedgerCount = $ScannedIds.Count
    outputPath = $OutputPath
} | ConvertTo-Json -Compress
