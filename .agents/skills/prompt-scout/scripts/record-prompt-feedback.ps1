[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9TZ-]+$')]
    [string]$ScanId,

    [string[]]$Like = @(),
    [string[]]$Dislike = @(),
    [string[]]$Neutral = @(),
    [string]$Note = ''
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '../../../..'
)).Path
$ScoutRoot = Join-Path $ProjectRoot 'data/prompt-scout'
$DataDirectory = $ScoutRoot
$ScanArchivePath = Join-Path $ScoutRoot ("scans/{0}.json" -f $ScanId)
$FeedbackPath = Join-Path $DataDirectory 'feedback.jsonl'
$PreferencesPath = Join-Path $DataDirectory 'preferences.json'

if (-not (Test-Path -LiteralPath $ScanArchivePath -PathType Leaf)) {
    throw "Completed prompt-scout scan not found: $ScanId"
}

function ConvertTo-RankNumbers {
    param([string[]]$Values)

    $Ranks = [Collections.Generic.List[int]]::new()
    foreach ($Value in @($Values)) {
        foreach ($Part in ([string]$Value -split '[,\s]+')) {
            if ([string]::IsNullOrWhiteSpace($Part)) {
                continue
            }
            $Parsed = 0
            if (-not [int]::TryParse($Part, [ref]$Parsed)) {
                throw "Invalid rank value: $Part"
            }
            $Ranks.Add($Parsed)
        }
    }
    return @($Ranks)
}

$LikeRanks = @(ConvertTo-RankNumbers -Values $Like)
$DislikeRanks = @(ConvertTo-RankNumbers -Values $Dislike)
$NeutralRanks = @(ConvertTo-RankNumbers -Values $Neutral)

$Groups = @(
    [ordered]@{ label = 'like'; value = 1; ranks = $LikeRanks },
    [ordered]@{ label = 'dislike'; value = -1; ranks = $DislikeRanks },
    [ordered]@{ label = 'neutral'; value = 0; ranks = $NeutralRanks }
)
$AllRanks = @($Groups | ForEach-Object { $_.ranks })
if ($AllRanks.Count -eq 0) {
    throw 'Supply at least one rank to Like, Dislike, or Neutral.'
}
if (@($AllRanks | Group-Object | Where-Object Count -gt 1).Count -gt 0) {
    throw 'A rank cannot receive more than one feedback label in the same call.'
}

$Archive = Get-Content -Raw -LiteralPath $ScanArchivePath |
    ConvertFrom-Json -DateKind String
if ([string]$Archive.scan.scanId -ne $ScanId) {
    throw 'The archived scan ID does not match the requested scan ID.'
}
$RankingByRank = @{}
foreach ($Record in @($Archive.rankings)) {
    $RankingByRank[[int]$Record.rank] = $Record
}

$ResolvedInputs = [Collections.Generic.List[object]]::new()
foreach ($Group in $Groups) {
    foreach ($Rank in $Group.ranks) {
        if (-not $RankingByRank.ContainsKey([int]$Rank)) {
            throw "Rank $Rank does not exist in scan $ScanId."
        }
        $ResolvedInputs.Add([ordered]@{
            group = $Group
            record = $RankingByRank[[int]$Rank]
        })
    }
}

$Preferences = if (Test-Path -LiteralPath $PreferencesPath -PathType Leaf) {
    Get-Content -Raw -LiteralPath $PreferencesPath | ConvertFrom-Json
}
else {
    [pscustomobject]@{
        schemaVersion = 1
        updatedAtUtc = $null
        signalTotals = [pscustomobject]@{ like = 0; dislike = 0; neutral = 0 }
        calibrationTotals = [pscustomobject]@{ completedRuns = 0; rankedPrompts = 0 }
        tokenWeights = [pscustomobject]@{}
    }
}

$TokenState = @{}
foreach ($Property in @($Preferences.tokenWeights.PSObject.Properties)) {
    $TokenState[$Property.Name] = [ordered]@{
        weight = [double]$Property.Value.weight
        observations = [int]$Property.Value.observations
    }
}

$StopWords = [Collections.Generic.HashSet[string]]::new(
    [string[]]@(
        'about','after','again','against','also','always','another','because',
        'been','before','being','between','could','does','doing','during','each',
        'every','from','have','having','into','just','more','most','only','other',
        'over','same','some','such','than','that','their','them','then','there',
        'these','they','this','those','through','under','very','what','when','where',
        'which','while','with','would','your','youre','were','will','world','years'
    ),
    [StringComparer]::OrdinalIgnoreCase
)

$RecordedAt = [DateTimeOffset]::UtcNow.ToString('o')
$Utf8NoBom = [Text.UTF8Encoding]::new($false)
$Resolved = [Collections.Generic.List[object]]::new()

foreach ($Input in $ResolvedInputs) {
        $Group = $Input.group
        $Record = $Input.record
        $Event = [ordered]@{
            schemaVersion = 1
            recordedAtUtc = $RecordedAt
            scanId = $ScanId
            rank = [int]$Record.rank
            postId = [string]$Record.postId
            title = [string]$Record.title
            url = [string]$Record.url
            label = [string]$Group.label
            value = [int]$Group.value
            note = $Note.Trim()
        }
        $Resolved.Add($Event)

        $Preferences.signalTotals.($Group.label) =
            [int]$Preferences.signalTotals.($Group.label) + 1

        $Title = ([string]$Record.title).ToLowerInvariant() -replace '^\[wp\]\s*', ''
        $Tokens = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::OrdinalIgnoreCase
        )
        foreach ($Match in [regex]::Matches($Title, "[a-z][a-z0-9'-]{2,}")) {
            $Token = $Match.Value.Trim("'-")
            if ($Token.Length -ge 4 -and -not $StopWords.Contains($Token)) {
                [void]$Tokens.Add($Token)
            }
        }

        foreach ($Token in $Tokens) {
            if (-not $TokenState.ContainsKey($Token)) {
                $TokenState[$Token] = [ordered]@{ weight = 0.0; observations = 0 }
            }
            $TokenState[$Token].weight =
                [double]$TokenState[$Token].weight + [int]$Group.value
            $TokenState[$Token].observations =
                [int]$TokenState[$Token].observations + 1
        }
}

$OrderedTokens = [ordered]@{}
foreach ($Token in @($TokenState.Keys | Sort-Object)) {
    $State = $TokenState[$Token]
    $OrderedTokens[$Token] = [ordered]@{
        weight = [Math]::Round([double]$State.weight, 3)
        observations = [int]$State.observations
        normalizedWeight = [Math]::Round(
            [double]$State.weight / [Math]::Sqrt([Math]::Max(1, [int]$State.observations)),
            3
        )
    }
}

$PreferencesPayload = [ordered]@{
    schemaVersion = 1
    updatedAtUtc = $RecordedAt
    signalTotals = [ordered]@{
        like = [int]$Preferences.signalTotals.like
        dislike = [int]$Preferences.signalTotals.dislike
        neutral = [int]$Preferences.signalTotals.neutral
    }
    calibrationTotals = [ordered]@{
        completedRuns = if ($Preferences.calibrationTotals) {
            [int]$Preferences.calibrationTotals.completedRuns
        } else { 0 }
        rankedPrompts = if ($Preferences.calibrationTotals) {
            [int]$Preferences.calibrationTotals.rankedPrompts
        } else { 0 }
    }
    tokenWeights = $OrderedTokens
}
$PreferencesPayload | ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath $PreferencesPath -Encoding utf8NoBOM

$FeedbackText = (@($Resolved | ForEach-Object {
    $_ | ConvertTo-Json -Compress
}) -join [Environment]::NewLine) + [Environment]::NewLine
[IO.File]::AppendAllText($FeedbackPath, $FeedbackText, $Utf8NoBom)

[ordered]@{
    scanId = $ScanId
    recorded = $Resolved.Count
    feedback = @($Resolved)
    preferencesPath = $PreferencesPath
} | ConvertTo-Json -Depth 6 -Compress
