#Requires -Version 7.0

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

function Get-MarkdownSection {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    $Pattern = '(?ms)^##\s+' + [regex]::Escape($Heading) +
        '\s*\r?\n(.*?)(?=^##\s+|\z)'
    $Match = [regex]::Match($Content, $Pattern)
    if (-not $Match.Success) {
        throw "Missing '$Heading' section."
    }
    return $Match.Groups[1].Value.Trim()
}

function Get-CertificationValue {
    param(
        [Parameter(Mandatory = $true)][string]$Section,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $Match = [regex]::Match(
        $Section,
        '(?im)^-\s+' + [regex]::Escape($Label) + ':\s*(.+?)\s*$'
    )
    if (-not $Match.Success) {
        throw "Current certification is missing '$Label'."
    }
    return ($Match.Groups[1].Value.Trim() -replace '`', '')
}

function Get-RawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-JsonAtomically {
    param(
        [Parameter(Mandatory = $true)][object]$Value,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $TemporaryPath = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        $Json = ($Value | ConvertTo-Json -Depth 8).Replace("`r`n", "`n").Replace("`r", "`n")
        Set-Content -LiteralPath $TemporaryPath -Value ($Json + "`n") -Encoding utf8NoBOM -NoNewline
        [System.IO.File]::Move($TemporaryPath, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $TemporaryPath -PathType Leaf) {
            Remove-Item -LiteralPath $TemporaryPath -Force
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
    throw "Story directory not found: $StoryDirectory"
}

$MetadataPath = Join-Path $StoryDirectory 'story.json'
$ReviewPath = Join-Path $StoryDirectory '04-review.md'
$StoryPath = Join-Path $StoryDirectory '05-story.md'
$DeltaPath = Join-Path $StoryDirectory '06-canon-delta.md'
$ReleasePath = Join-Path $StoryDirectory 'release.json'
foreach ($RequiredPath in @($MetadataPath, $ReviewPath, $StoryPath, $DeltaPath)) {
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) {
        throw "Required release artifact not found: $RequiredPath"
    }
}

try {
    $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
}
catch {
    throw "Invalid story.json: $($_.Exception.Message)"
}
if ($Metadata.schemaVersion -ne 1 -or $Metadata.slug -cne $Story) {
    throw "story.json must use schemaVersion 1 and exact slug '$Story'."
}
if ($Metadata.status -notin @('candidate', 'final')) {
    throw "A release certificate may be issued only for candidate or final status; found '$($Metadata.status)'."
}
if ($Metadata.stage -ne $Metadata.status) {
    throw "Story stage '$($Metadata.stage)' must match release status '$($Metadata.status)'."
}

$StoryContent = Get-Content -LiteralPath $StoryPath -Raw
$DeltaContent = Get-Content -LiteralPath $DeltaPath -Raw
foreach ($Artifact in @(
    [pscustomobject]@{ Name = '05-story.md'; Path = $StoryPath; Content = $StoryContent },
    [pscustomobject]@{ Name = '06-canon-delta.md'; Path = $DeltaPath; Content = $DeltaContent }
)) {
    if ([string]::IsNullOrWhiteSpace($Artifact.Content) -or
        $Artifact.Content -match '{{[^{}]+}}' -or
        $Artifact.Content -match '(?i)complete (?:working|reader-facing|polished) prose goes here') {
        throw "$($Artifact.Name) still contains a placeholder or is empty."
    }
    if (13 -in [IO.File]::ReadAllBytes($Artifact.Path)) {
        throw "$($Artifact.Name) contains CR or CRLF bytes. Normalize release artifacts to LF before certification."
    }
}

$ReviewContent = Get-Content -LiteralPath $ReviewPath -Raw
$Certification = Get-MarkdownSection -Content $ReviewContent -Heading 'Current certification'
$ReviewedArtifact = Get-CertificationValue $Certification 'Reviewed artifact'
$ReviewedStoryHash = Get-CertificationValue $Certification 'Artifact SHA-256'
$ReviewedDeltaHash = Get-CertificationValue $Certification 'Canon delta SHA-256'
$PassText = Get-CertificationValue $Certification 'Review pass'
$Verdict = (Get-CertificationValue $Certification 'Verdict').ToUpperInvariant()
$Reviewer = Get-CertificationValue $Certification 'Reviewer'
$CriticalText = Get-CertificationValue $Certification 'Unresolved Critical findings'
$MajorText = Get-CertificationValue $Certification 'Unresolved Major findings'

$NormalizedArtifact = $ReviewedArtifact.Replace('\', '/')
if ($NormalizedArtifact -ne '05-story.md' -and
    -not $NormalizedArtifact.EndsWith("/$Story/05-story.md", [StringComparison]::Ordinal)) {
    throw "Current certification reviews '$ReviewedArtifact', not this story's 05-story.md."
}
$CurrentStoryHash = Get-RawSha256 $StoryPath
$CurrentDeltaHash = Get-RawSha256 $DeltaPath
if ($ReviewedStoryHash -cnotmatch '^[a-f0-9]{64}$' -or
    $ReviewedDeltaHash -cnotmatch '^[a-f0-9]{64}$') {
    throw 'Current certification must record lowercase SHA-256 hashes for 05-story.md and 06-canon-delta.md.'
}
if ($ReviewedStoryHash -cne $CurrentStoryHash -or $ReviewedDeltaHash -cne $CurrentDeltaHash) {
    throw 'Current 05-story.md or 06-canon-delta.md bytes differ from the reviewed hashes; re-review before release.'
}
if ($PassText -notmatch '^(\d+)(?:\s|$)' -or [int]$Matches[1] -lt 1) {
    throw "Current certification has invalid review pass '$PassText'."
}
$ReviewPass = [int]$Matches[1]
if ($Verdict -ne 'PASS') {
    throw "Current certification verdict must be PASS; found '$Verdict'."
}
if ([string]::IsNullOrWhiteSpace($Reviewer) -or $Reviewer -in @('None', 'unknown')) {
    throw 'Current certification must identify a reviewer.'
}
if ($CriticalText -notmatch '^\d+$' -or $MajorText -notmatch '^\d+$') {
    throw 'Current certification unresolved Critical and Major counts must be nonnegative integers.'
}
$CriticalCount = [int]$CriticalText
$MajorCount = [int]$MajorText
if ($CriticalCount -ne 0 -or $MajorCount -ne 0) {
    throw "Release is blocked by $CriticalCount unresolved Critical and $MajorCount unresolved Major findings."
}

$NameChecker = Join-Path $ProjectRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
if (-not (Test-Path -LiteralPath $NameChecker -PathType Leaf)) {
    throw "Name checker not found: $NameChecker"
}
$NameCheckJson = & $NameChecker -Story $Story -Phase Final -OutputFormat Json -ProjectRoot $ProjectRoot
try {
    $NameCheck = $NameCheckJson | ConvertFrom-Json
}
catch {
    throw "Name checker did not return valid JSON: $($_.Exception.Message)"
}
if ($NameCheck.passed -ne $true -or $NameCheck.story -cne $Story -or
    $NameCheck.phase -ne 'Final') {
    throw 'Final scoped name check did not return a valid passing receipt.'
}
$NameCheckedAtUtc = ([DateTimeOffset]$NameCheck.checkedAt).ToUniversalTime().ToString('o')

$CertifiedAt = [DateTimeOffset]::UtcNow.ToString('o')
$Release = [ordered]@{
    schemaVersion = 1
    certified = $true
    storySlug = $Story
    certifiedAt = $CertifiedAt
    artifacts = [ordered]@{
        story = [ordered]@{
            path = '05-story.md'
            sha256 = $CurrentStoryHash
        }
        canonDelta = [ordered]@{
            path = '06-canon-delta.md'
            sha256 = $CurrentDeltaHash
        }
    }
    review = [ordered]@{
        artifact = '05-story.md'
        pass = $ReviewPass
        verdict = 'PASS'
        reviewer = $Reviewer
        unresolvedCritical = $CriticalCount
        unresolvedMajor = $MajorCount
    }
    nameCheck = [ordered]@{
        story = $Story
        passed = $true
        checkedAt = $NameCheckedAtUtc
        scopedRegistrySha256 = $NameCheck.scopedRegistrySha256
    }
}

if ($PSCmdlet.ShouldProcess($ReleasePath, 'Issue content-bound story release certificate')) {
    Write-JsonAtomically -Value $Release -Path $ReleasePath
}
Write-Output "Release certificate issued: $ReleasePath"
