#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [ValidatePattern('^[a-f0-9]{64}$')]
    [string]$ResearchAuthorityManifestSha256,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$Errors = [Collections.Generic.List[string]]::new()

function Add-ArtifactError {
    param([Parameter(Mandatory = $true)][string]$Message)
    $Errors.Add($Message)
}

function Get-RawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-UniqueSection {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Heading,
        [Parameter(Mandatory = $true)][string]$Artifact
    )

    $Pattern = '(?ms)^##[ \t]+' + [regex]::Escape($Heading) +
        '[ \t]*\r?\n(?<body>.*?)(?=^##[ \t]+|\z)'
    $Matches = @([regex]::Matches($Content, $Pattern))
    if ($Matches.Count -ne 1) {
        Add-ArtifactError "$Artifact must contain exactly one '$Heading' section; found $($Matches.Count)."
        return $null
    }
    $Body = $Matches[0].Groups['body'].Value.Trim()
    if ([string]::IsNullOrWhiteSpace($Body)) {
        Add-ArtifactError "$Artifact section '$Heading' must be explicit; use 'None.' when empty."
        return $null
    }
    return $Body
}

function Get-UniqueQuotedField {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Artifact
    )

    $Matches = @([regex]::Matches(
        $Content,
        '(?m)^>[ \t]+' + [regex]::Escape($Label) + ':[ \t]*(?<value>[^\r\n]+)[ \t]*$'
    ))
    if ($Matches.Count -ne 1) {
        Add-ArtifactError "$Artifact must contain exactly one '$Label' receipt field."
        return $null
    }
    return $Matches[0].Groups['value'].Value.Trim().Trim('`')
}

function Test-NoPlaceholder {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Artifact
    )

    if ($Content -match '{{[^{}]+}}|(?i)<(?:exact|complete|items?|value|lowercase|repo-relative)[^>]*>|\[Capture the verbatim writing prompt here\.\]') {
        Add-ArtifactError "$Artifact contains unresolved placeholder text '$($Matches[0])'."
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$Directory = Join-Path $ProjectRoot "stories/$Story"
if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
    throw "Story directory not found: $Directory"
}
$MetadataPath = Join-Path $Directory 'story.json'
$Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
if ($Metadata.slug -cne $Story -or $Metadata.schemaVersion -ne 1) {
    Add-ArtifactError 'story.json identity/schema is invalid.'
}
$StageOrder = @(
    'prompt', 'canon-research', 'planning', 'drafting', 'draft-review',
    'final-edit', 'final-review', 'candidate', 'final'
)
$StageIndex = [array]::IndexOf($StageOrder, [string]$Metadata.stage)
if ($Metadata.status -eq 'abandoned') { $StageIndex = -1 }

$PromptPath = Join-Path $Directory '00-prompt.md'
$Prompt = Get-Content -LiteralPath $PromptPath -Raw
$Verbatim = Get-UniqueSection $Prompt 'Verbatim writing prompt' '00-prompt.md'
$Controls = Get-UniqueSection $Prompt 'Story controls' '00-prompt.md'
$null = Get-UniqueSection $Prompt 'Assumptions' '00-prompt.md'
$CompletionHeading = if ($Prompt -match '(?m)^## Completion tests\s*$') {
    'Completion tests'
}
elseif ($Prompt -match '(?m)^## Acceptance criteria\s*$') {
    'Acceptance criteria'
}
else { 'Completion tests' }
$null = Get-UniqueSection $Prompt $CompletionHeading '00-prompt.md'
if ($StageIndex -ge 1) {
    Test-NoPlaceholder $Prompt '00-prompt.md'
    if ($null -ne $Verbatim -and $Verbatim -notmatch '(?m)^>[ \t]*\S') {
        Add-ArtifactError '00-prompt.md Verbatim writing prompt must preserve the prompt as a block quote.'
    }
    foreach ($Label in @(
        'Working title', 'Target length', 'POV', 'Tense', 'Tone and genre',
        'Audience/content rating', 'Required elements', 'Prohibited elements'
    )) {
        $Matches = @([regex]::Matches(
            [string]$Controls,
            '(?m)^-[ \t]+' + [regex]::Escape($Label) + ':[ \t]*(?<value>.*)$'
        ))
        if ($Matches.Count -ne 1 -or
            [string]::IsNullOrWhiteSpace($Matches[0].Groups['value'].Value)) {
            Add-ArtifactError "00-prompt.md Story controls must contain one nonempty '$Label' value."
        }
    }
}

if ($StageIndex -ge 2) {
    $BriefPath = Join-Path $Directory '01-canon-brief.md'
    $Brief = Get-Content -LiteralPath $BriefPath -Raw
    Test-NoPlaceholder $Brief '01-canon-brief.md'
    $ResearchStatus = Get-UniqueQuotedField $Brief 'Research status' '01-canon-brief.md'
    $ResolutionOwner = Get-UniqueQuotedField $Brief 'Resolution owner' '01-canon-brief.md'
    $PromptHash = Get-UniqueQuotedField $Brief 'Prompt SHA-256' '01-canon-brief.md'
    $AuthorityHash = Get-UniqueQuotedField $Brief 'Authority manifest SHA-256' '01-canon-brief.md'
    if ($ResearchStatus -cne 'READY') {
        Add-ArtifactError '01-canon-brief.md Research status must be READY; mechanical migration is not live canon research.'
    }
    if ($ResolutionOwner -cne 'coordinator') {
        Add-ArtifactError 'A persisted release-ready canon brief must have Resolution owner coordinator.'
    }
    if ($PromptHash -cne (Get-RawSha256 $PromptPath)) {
        Add-ArtifactError '01-canon-brief.md Prompt SHA-256 is stale.'
    }
    $AuthorityPath = Join-Path $Directory 'authority.json'
    $ExpectedResearchAuthority = if ([string]::IsNullOrWhiteSpace($ResearchAuthorityManifestSha256)) {
        Get-RawSha256 $AuthorityPath
    }
    else { $ResearchAuthorityManifestSha256 }
    if ($AuthorityHash -cne $ExpectedResearchAuthority) {
        Add-ArtifactError '01-canon-brief.md Authority manifest SHA-256 is stale.'
    }
    $BriefSections = @{}
    foreach ($Heading in @(
        'Hard constraints', 'Useful established context',
        'Conflicts or ambiguity', 'Unknowns', 'Safe invention space',
        'Name constraints', 'Required checks after drafting', 'Sources'
    )) {
        $BriefSections[$Heading] = Get-UniqueSection $Brief $Heading '01-canon-brief.md'
    }
    if ($ResearchStatus -eq 'READY') {
        $PositiveCanon = @(@('Hard constraints', 'Useful established context') |
            Where-Object { $BriefSections[$_] -notmatch '^None\.$' })
        $SourceLines = @(([string]$BriefSections['Sources'] -split '\r?\n') |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        if ($PositiveCanon.Count -gt 0 -and
            ($SourceLines.Count -eq 1 -and $SourceLines[0].Trim() -ceq 'None.')) {
            Add-ArtifactError '01-canon-brief.md positive canon claims require structured Sources receipts.'
        }
        foreach ($Line in $SourceLines | Where-Object { $_.Trim() -cne 'None.' }) {
            if ($Line -notmatch '^- path: (?<path>[^;]+); heading: (?<heading>[^;]+); authority: (?<authority>LOCKED|CANON|evidence-none)$') {
                Add-ArtifactError "01-canon-brief.md has malformed source receipt: $Line"
                continue
            }
            $Relative = $Matches['path'].Trim().Trim('`').Replace('\', '/')
            if ($Relative -notmatch '^(?:universe|stories|sources)/' -or
                $Relative -match '(^|/)\.\.(/|$)' -or
                -not (Test-Path -LiteralPath (Join-Path $ProjectRoot $Relative) -PathType Leaf)) {
                Add-ArtifactError "01-canon-brief.md source path is missing or unsafe: $Relative"
            }
            if ([string]::IsNullOrWhiteSpace($Matches['heading'])) {
                Add-ArtifactError "01-canon-brief.md source receipt lacks an exact heading: $Line"
            }
        }
    }
}

if ($StageIndex -ge 3) {
    $Plan = Get-Content -LiteralPath (Join-Path $Directory '02-story-plan.md') -Raw
    Test-NoPlaceholder $Plan '02-story-plan.md'
    foreach ($Heading in @(
        'Story controls', 'Character engine', 'Causal arc', 'Scene plan',
        'Setup and payoff', 'Name check', 'Failure modes to watch'
    )) {
        $null = Get-UniqueSection $Plan $Heading '02-story-plan.md'
    }
    if ($Plan -notmatch '(?m)^\| # \| Purpose \| Conflict \| Turn \| Canon used \| Word budget \|\s*$' -or
        @([regex]::Matches($Plan, '(?m)^\|\s*\d+\s*\|[^\n]+\|\s*$')).Count -eq 0) {
        Add-ArtifactError '02-story-plan.md Scene plan must use the six-column table and contain at least one scene.'
    }
}

if ($StageIndex -ge 6) {
    $Delta = Get-Content -LiteralPath (Join-Path $Directory '06-canon-delta.md') -Raw
    Test-NoPlaceholder $Delta '06-canon-delta.md'
    foreach ($Heading in @(
        'New characters or character facts', 'New locations',
        'New factions or cultural facts', 'New rules, capabilities, or costs',
        'Timeline events', 'New glossary terms or aliases',
        'Final character-facing name inventory', 'Name registry updates',
        'Possible conflicts or retcons', 'Recommended promotions'
    )) {
        $null = Get-UniqueSection $Delta $Heading '06-canon-delta.md'
    }
}

$UniqueErrors = @($Errors | Sort-Object -Unique)
$Result = [ordered]@{
    schemaVersion = 1
    story = $Story
    passed = $UniqueErrors.Count -eq 0
    errors = $UniqueErrors
}
if ($OutputFormat -eq 'Json') {
    $Result | ConvertTo-Json -Depth 5
}
elseif ($UniqueErrors.Count -eq 0) {
    "Pipeline artifacts passed for '$Story'."
}
else {
    foreach ($Message in $UniqueErrors) { Write-Host "- $Message" -ForegroundColor Red }
}
if ($UniqueErrors.Count -gt 0) { exit 1 }
