#Requires -Version 7.0

[CmdletBinding()]
param(
    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$Errors = [Collections.Generic.List[string]]::new()

function Add-SourceError {
    param([Parameter(Mandatory = $true)][string]$Message)
    $Errors.Add($Message)
}

function Test-ExactProperties {
    param([object]$Value, [string[]]$Expected, [string]$Context)
    if ($null -eq $Value) { Add-SourceError "$Context must be an object."; return }
    $Actual = @($Value.PSObject.Properties.Name)
    $Missing = @($Expected | Where-Object { $_ -cnotin $Actual })
    $Extra = @($Actual | Where-Object { $_ -cnotin $Expected })
    if ($Missing.Count -gt 0 -or $Extra.Count -gt 0) {
        Add-SourceError "$Context field mismatch; missing=[$($Missing -join ', ')], unknown=[$($Extra -join ', ')]."
    }
}

function Get-CrlfExpandedSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    [byte[]]$Bytes = [IO.File]::ReadAllBytes($Path)
    for ($Index = 0; $Index -lt $Bytes.Length - 1; $Index++) {
        if ($Bytes[$Index] -eq 13 -and $Bytes[$Index + 1] -eq 10) {
            return $null
        }
    }
    if (10 -notin $Bytes) { return $null }

    $Expanded = [Collections.Generic.List[byte]]::new($Bytes.Length + 128)
    foreach ($Byte in $Bytes) {
        if ($Byte -eq 10) { $Expanded.Add(13) }
        $Expanded.Add($Byte)
    }
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Expanded.ToArray())
    ).ToLowerInvariant()
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$ManifestPath = Join-Path $ProjectRoot 'sources/MANIFEST.json'
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Source manifest not found: $ManifestPath"
}
try { $Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json }
catch { throw "sources/MANIFEST.json is invalid JSON: $($_.Exception.Message)" }
Test-ExactProperties $Manifest @(
    'schemaVersion', 'prepared', 'authority', 'decisionRecord',
    'records', 'externalRecords'
) 'sources/MANIFEST.json'
if ($Manifest.schemaVersion -ne 2) { Add-SourceError 'sources/MANIFEST.json schemaVersion must be 2.' }
if ($Manifest.authority -cne 'none') { Add-SourceError 'sources/MANIFEST.json authority must be none.' }
$Prepared = [datetime]::MinValue
if (-not [datetime]::TryParseExact(
    [string]$Manifest.prepared, 'yyyy-MM-dd',
    [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::None, [ref]$Prepared
)) { Add-SourceError 'sources/MANIFEST.json prepared must be a calendar date in YYYY-MM-DD form.' }
$Decision = ([string]$Manifest.decisionRecord).Replace('\', '/')
if ($Decision -notmatch '^sources/decisions/[^\x00-\x1f:]+\.md$' -or
    $Decision -match '(^|/)\.\.(/|$)' -or
    -not (Test-Path -LiteralPath (Join-Path $ProjectRoot $Decision) -PathType Leaf)) {
    Add-SourceError 'sources/MANIFEST.json decisionRecord is missing or unsafe.'
}

$Ids = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($Record in @($Manifest.records)) {
    $Context = "source record '$($Record.recordId)'"
    Test-ExactProperties $Record @(
        'recordId', 'workTitle', 'reviewedForm', 'path', 'sha256',
        'reviewedSha256', 'authority', 'historicalRevision', 'historicalBlobOid'
    ) $Context
    if ($Record.recordId -cnotmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$' -or
        -not $Ids.Add([string]$Record.recordId)) {
        Add-SourceError "$Context has an invalid or duplicate recordId."
    }
    if ($Record.authority -cne 'none') { Add-SourceError "$Context authority must be none." }
    $Relative = ([string]$Record.path).Replace('\', '/')
    if ($Relative -notmatch '^sources/records/[^\x00-\x1f:]+$' -or
        $Relative -match '(^|/)\.\.(/|$)') {
        Add-SourceError "$Context path is unsafe."
        continue
    }
    $Full = [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Relative))
    $RecordsRoot = [IO.Path]::GetFullPath((Join-Path $ProjectRoot 'sources/records')) +
        [IO.Path]::DirectorySeparatorChar
    if (-not $Full.StartsWith($RecordsRoot, [StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $Full -PathType Leaf)) {
        Add-SourceError "$Context path is missing or escapes sources/records."
        continue
    }
    $RawHash = (Get-FileHash -LiteralPath $Full -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Record.sha256 -cnotmatch '^[a-f0-9]{64}$' -or $Record.sha256 -cne $RawHash) {
        Add-SourceError "$Context sha256 does not bind the current raw bytes."
    }
    if ($Record.reviewedSha256 -cnotmatch '^[a-f0-9]{64}$') {
        Add-SourceError "$Context reviewedSha256 is invalid."
    }
    elseif ($Record.reviewedSha256 -cne $RawHash -and
        $Record.reviewedSha256 -cne (Get-CrlfExpandedSha256 $Full)) {
        Add-SourceError "$Context reviewedSha256 does not bind the raw bytes or the sole permitted LF-to-CRLF historical normalization."
    }
    if ($Record.historicalRevision -cnotmatch '^[a-f0-9]{40,64}$' -or
        $Record.historicalBlobOid -cnotmatch '^[a-f0-9]{40,64}$') {
        Add-SourceError "$Context historical provenance IDs are invalid."
    }
}

foreach ($Record in @($Manifest.externalRecords)) {
    $Context = "external source record '$($Record.recordId)'"
    Test-ExactProperties $Record @(
        'recordId', 'workTitle', 'reviewedForm', 'logicalLocator', 'authority',
        'verificationStatus', 'version', 'sha256', 'accessRequirements'
    ) $Context
    if ($Record.recordId -cnotmatch '^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$' -or
        -not $Ids.Add([string]$Record.recordId)) {
        Add-SourceError "$Context has an invalid or duplicate recordId."
    }
    if ($Record.authority -cne 'none') { Add-SourceError "$Context authority must be none." }
    foreach ($Field in @('workTitle', 'reviewedForm', 'logicalLocator', 'accessRequirements')) {
        if (-not ($Record.$Field -is [string]) -or
            [string]::IsNullOrWhiteSpace([string]$Record.$Field)) {
            Add-SourceError "$Context $Field must be nonempty."
        }
    }
    if ($Record.verificationStatus -cne 'verified' -and
        $Record.verificationStatus -cne 'descriptive-only') {
        Add-SourceError "$Context verificationStatus is invalid."
    }
    elseif ($Record.verificationStatus -ceq 'descriptive-only') {
        if ($null -ne $Record.version -or $null -ne $Record.sha256) {
            Add-SourceError "$Context descriptive-only records must use null version and sha256."
        }
    }
    else {
        if (-not ($Record.version -is [string]) -or
            [string]::IsNullOrWhiteSpace([string]$Record.version) -or
            $Record.sha256 -cnotmatch '^[a-f0-9]{64}$') {
            Add-SourceError "$Context verified records require a nonempty exact version and lowercase SHA-256."
        }
        if ([string]$Record.logicalLocator -notmatch '(?:^|[/#?=&])(?:v(?:ersion)?[-_ ]?)?[A-Za-z0-9][A-Za-z0-9._-]{2,}(?:$|[/#?=&])') {
            Add-SourceError "$Context verified logicalLocator is not a stable controlled locator."
        }
    }
}

$UniqueErrors = @($Errors | Sort-Object -Unique)
$Result = [ordered]@{
    schemaVersion = 1
    passed = $UniqueErrors.Count -eq 0
    records = @($Manifest.records).Count
    externalRecords = @($Manifest.externalRecords).Count
    errors = $UniqueErrors
}
if ($OutputFormat -eq 'Json') { $Result | ConvertTo-Json -Depth 5 }
elseif ($UniqueErrors.Count -eq 0) { 'Source manifest integrity check passed.' }
else { foreach ($Message in $UniqueErrors) { Write-Host "- $Message" -ForegroundColor Red } }
if ($UniqueErrors.Count -gt 0) { exit 1 }
