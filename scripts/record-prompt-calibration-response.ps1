[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9TZ-]+$')]
    [string]$CalibrationId,

    [Parameter(Mandatory = $true)]
    [string[]]$Order,

    [string]$Note = ''
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScoutRoot = Join-Path $ProjectRoot 'prompt-scout'
$DataDirectory = Join-Path $ScoutRoot 'data'
$CalibrationSetPath = Join-Path $ScoutRoot (
    "calibration/sets/{0}.json" -f $CalibrationId
)
$ResponsesPath = Join-Path $DataDirectory 'calibration-responses.jsonl'
$PreferencesPath = Join-Path $DataDirectory 'preferences.json'

function ConvertTo-OrderNumbers {
    param([string[]]$Values)

    $Numbers = [Collections.Generic.List[int]]::new()
    foreach ($Value in @($Values)) {
        foreach ($Part in ([string]$Value -split '[,\s]+')) {
            if ([string]::IsNullOrWhiteSpace($Part)) {
                continue
            }
            $Parsed = 0
            if (-not [int]::TryParse($Part, [ref]$Parsed)) {
                throw "Invalid calibration number: $Part"
            }
            $Numbers.Add($Parsed)
        }
    }
    return @($Numbers)
}

$OrderNumbers = @(ConvertTo-OrderNumbers -Values $Order)

if (-not (Test-Path -LiteralPath $CalibrationSetPath -PathType Leaf)) {
    throw "Calibration set not found: $CalibrationId"
}

$Calibration = Get-Content -Raw -LiteralPath $CalibrationSetPath |
    ConvertFrom-Json -DateKind String
if ([string]$Calibration.calibrationId -ne $CalibrationId) {
    throw 'The archived calibration ID does not match the requested ID.'
}
$Items = @($Calibration.items)
if ($OrderNumbers.Count -ne $Items.Count) {
    throw "A complete ordering must contain all $($Items.Count) calibration numbers."
}
if (@($OrderNumbers | Group-Object | Where-Object Count -gt 1).Count -gt 0) {
    throw 'Each calibration number must appear exactly once.'
}

$ItemByNumber = @{}
foreach ($Item in $Items) {
    $ItemByNumber[[int]$Item.number] = $Item
}
foreach ($Number in $OrderNumbers) {
    if (-not $ItemByNumber.ContainsKey([int]$Number)) {
        throw "Unknown calibration number: $Number"
    }
}

if (Test-Path -LiteralPath $ResponsesPath -PathType Leaf) {
    foreach ($Line in Get-Content -LiteralPath $ResponsesPath) {
        if (-not [string]::IsNullOrWhiteSpace($Line)) {
            $Prior = $Line | ConvertFrom-Json
            if ($Prior.calibrationId -eq $CalibrationId) {
                throw 'This calibration set already has a recorded response.'
            }
        }
    }
}

$Preferences = Get-Content -Raw -LiteralPath $PreferencesPath | ConvertFrom-Json
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

$RankedItems = [Collections.Generic.List[object]]::new()
$Denominator = [Math]::Max(1, $OrderNumbers.Count - 1)
for ($Index = 0; $Index -lt $OrderNumbers.Count; $Index++) {
    $Item = $ItemByNumber[[int]$OrderNumbers[$Index]]
    $ComparativeValue = 1.0 - (2.0 * $Index / $Denominator)
    $ComparativeValue = [Math]::Round($ComparativeValue, 3)

    $RankedItems.Add([ordered]@{
        userPosition = $Index + 1
        calibrationNumber = [int]$Item.number
        postId = [string]$Item.postId
        title = [string]$Item.title
        url = [string]$Item.url
        priorScoutRank = [int]$Item.scoutRank
        comparativeValue = $ComparativeValue
    })

    $Title = ([string]$Item.title).ToLowerInvariant() -replace '^\[wp\]\s*', ''
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
            [double]$TokenState[$Token].weight + $ComparativeValue
        $TokenState[$Token].observations =
            [int]$TokenState[$Token].observations + 1
    }
}

$RecordedAt = [DateTimeOffset]::UtcNow.ToString('o')
$ResponseEvent = [ordered]@{
    schemaVersion = 1
    calibrationId = $CalibrationId
    scanId = [string]$Calibration.scanId
    recordedAtUtc = $RecordedAt
    note = $Note.Trim()
    order = @($OrderNumbers)
    rankedItems = @($RankedItems)
}
$Utf8NoBom = [Text.UTF8Encoding]::new($false)
$Line = $ResponseEvent | ConvertTo-Json -Depth 7 -Compress
[IO.File]::AppendAllText($ResponsesPath, $Line + [Environment]::NewLine, $Utf8NoBom)

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

$ExistingRuns = if ($Preferences.calibrationTotals) {
    [int]$Preferences.calibrationTotals.completedRuns
} else { 0 }
$ExistingPrompts = if ($Preferences.calibrationTotals) {
    [int]$Preferences.calibrationTotals.rankedPrompts
} else { 0 }
$PreferencesPayload = [ordered]@{
    schemaVersion = 1
    updatedAtUtc = $RecordedAt
    signalTotals = [ordered]@{
        like = [int]$Preferences.signalTotals.like
        dislike = [int]$Preferences.signalTotals.dislike
        neutral = [int]$Preferences.signalTotals.neutral
    }
    calibrationTotals = [ordered]@{
        completedRuns = $ExistingRuns + 1
        rankedPrompts = $ExistingPrompts + $Items.Count
    }
    tokenWeights = $OrderedTokens
}
$PreferencesPayload | ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath $PreferencesPath -Encoding utf8NoBOM

[ordered]@{
    calibrationId = $CalibrationId
    recordedAtUtc = $RecordedAt
    rankedCount = $RankedItems.Count
    order = @($OrderNumbers)
    preferencesPath = $PreferencesPath
} | ConvertTo-Json -Depth 5 -Compress
