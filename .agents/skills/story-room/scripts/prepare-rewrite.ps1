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

    [ValidateSet('Rebuild', 'Reshape', 'Selective')]
    [string]$Scope = 'Rebuild',

    [string[]]$KeepExact = @(),

    [string[]]$Keep = @(),

    [string[]]$Change = @(),

    [string[]]$Remove = @(),

    [ValidateSet('Auto', 'Keep', 'Regenerate')]
    [string]$Cover = 'Auto',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$activeCraftProfile = 'prospective-2026-08-23'
$managedHeadings = @(
    'Rewrite request',
    'Rewrite reference images',
    'Rewrite selections',
    'Rewrite constraints'
)
$utf8Strict = [Text.UTF8Encoding]::new($false, $true)

function Read-Utf8File {
    param([string]$Path, [string]$Label)

    $bytes = [IO.File]::ReadAllBytes($Path)
    $hasBom = (
        $bytes.Length -ge 3 -and
        $bytes[0] -eq 0xef -and
        $bytes[1] -eq 0xbb -and
        $bytes[2] -eq 0xbf
    )
    $offset = if ($hasBom) { 3 } else { 0 }
    try {
        $text = $utf8Strict.GetString($bytes, $offset, $bytes.Length - $offset)
    }
    catch {
        throw "$Label must be valid UTF-8."
    }
    return [pscustomobject]@{
        Bytes = $bytes
        Text = $text
        HasBom = $hasBom
    }
}

function ConvertTo-Utf8Bytes {
    param([string]$Text, [bool]$WithBom)

    $body = $utf8Strict.GetBytes($Text)
    if (-not $WithBom) {
        return ,$body
    }

    $result = [byte[]]::new($body.Length + 3)
    $result[0] = 0xef
    $result[1] = 0xbb
    $result[2] = 0xbf
    [Array]::Copy($body, 0, $result, 3, $body.Length)
    return ,$result
}

function Get-LineEnding {
    param([string]$Text)

    $match = [regex]::Match($Text, '\r\n|\n|\r')
    if ($match.Success) {
        return $match.Value
    }
    return [Environment]::NewLine
}

function Get-LevelTwoSectionMatches {
    param([string]$Text, [string]$Heading)

    $escaped = [regex]::Escape($Heading)
    return @([regex]::Matches(
        $Text,
        "(?ms)^##[ \t]+$escaped[ \t]*(?:\r\n|\n|\r)(?<body>.*?)(?=^##[ \t]+|\z)"
    ))
}

function Get-ReaderTitle {
    param([string]$YamlValue)

    $value = $YamlValue.Trim()
    if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        try {
            $decoded = $value | ConvertFrom-Json
            if ($decoded -is [string]) {
                return $decoded
            }
        }
        catch {
            throw 'Current story.md title is not a valid quoted scalar.'
        }
    }
    if ($value.StartsWith("'") -and $value.EndsWith("'") -and $value.Length -ge 2) {
        return $value.Substring(1, $value.Length - 2).Replace("''", "'")
    }
    return $value
}

function Test-ByteEquality {
    param([byte[]]$Left, [byte[]]$Right)

    if ($Left.Length -ne $Right.Length) {
        return $false
    }
    for ($index = 0; $index -lt $Left.Length; $index++) {
        if ($Left[$index] -ne $Right[$index]) {
            return $false
        }
    }
    return $true
}

function Get-NormalizedSelections {
    param([string[]]$Values, [string]$Label)

    $normalized = [Collections.Generic.List[string]]::new()
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($value in $Values) {
        if ([string]::IsNullOrWhiteSpace($value)) {
            continue
        }
        $item = $value.Trim()
        if ($item -match '[\r\n\p{Cc}]') {
            throw "$Label selections must be single-line text without control characters."
        }
        if ($item -ieq 'none specified') {
            throw "$Label selection reserves 'none specified' for the empty state."
        }
        if (-not $seen.Add($item)) {
            throw "$Label contains a duplicate selection: $item"
        }
        $normalized.Add($item)
    }
    return @($normalized)
}

function ConvertTo-SelectionBlock {
    param([string]$Label, [string[]]$Values, [string]$LineEnding)

    if ($Values.Count -eq 0) {
        return "- ${Label}: none specified"
    }
    return ($Values | ForEach-Object { "- ${Label}: $_" }) -join $LineEnding
}

function Assert-RewriteSelections {
    param([string]$SelectionText, [string]$Label)

    $scopeLines = @([regex]::Matches(
        $SelectionText,
        '(?m)^-[ \t]+Scope:[ \t]*(?<value>REBUILD|RESHAPE|SELECTIVE)[ \t]*\r?$'
    ))
    if ($scopeLines.Count -ne 1) {
        throw "$Label must contain exactly one Scope: REBUILD, RESHAPE, or SELECTIVE line."
    }
    $outsideLines = @([regex]::Matches(
        $SelectionText,
        '(?m)^-[ \t]+Outside named selections:[ \t]*(?<value>FLEXIBLE|KEEP|KEEP EXACT)[ \t]*\r?$'
    ))
    if ($outsideLines.Count -ne 1) {
        throw "$Label must contain exactly one Outside named selections line."
    }
    if ($scopeLines.Count -eq 1 -and $outsideLines.Count -eq 1) {
        $expectedOutside = switch ($scopeLines[0].Groups['value'].Value) {
            'REBUILD' { 'FLEXIBLE' }
            'RESHAPE' { 'KEEP' }
            'SELECTIVE' { 'KEEP EXACT' }
        }
        if ($outsideLines[0].Groups['value'].Value -cne $expectedOutside) {
            throw "$Label scope $($scopeLines[0].Groups['value'].Value) requires Outside named selections: $expectedOutside."
        }
    }

    $valuesByCategory = @{}
    foreach ($category in @('Keep exact', 'Keep in substance', 'Change or replace', 'Remove')) {
        $escaped = [regex]::Escape($category)
        $lines = @([regex]::Matches(
            $SelectionText,
            "(?m)^-[ \t]+${escaped}:[ \t]*(?<value>[^\r\n]+?)[ \t]*\r?$"
        ))
        if ($lines.Count -lt 1) {
            throw "$Label must contain at least one '$category' line."
        }
        $values = @($lines | ForEach-Object { $_.Groups['value'].Value.Trim() })
        if ($values -contains '') {
            throw "$Label contains an empty '$category' selection."
        }
        if ($values -icontains 'none specified' -and $values.Count -ne 1) {
            throw "$Label cannot mix 'none specified' with named '$category' selections."
        }
        $valuesByCategory[$category] = $values
    }

    if (
        $scopeLines[0].Groups['value'].Value -eq 'SELECTIVE' -and
        $valuesByCategory['Change or replace'] -icontains 'none specified' -and
        $valuesByCategory['Remove'] -icontains 'none specified'
    ) {
        throw "$Label SELECTIVE scope requires at least one Change or replace or Remove selection."
    }
}

function Assert-PromptStructure {
    param([string]$PromptText)

    foreach ($heading in @('Prompt', 'Constraints')) {
        $count = @(Get-LevelTwoSectionMatches $PromptText $heading).Count
        if ($count -ne 1) {
            throw "prompt.md must contain exactly one '$heading' section before rewrite preparation; found $count."
        }
    }
    $referenceCount = @(Get-LevelTwoSectionMatches $PromptText 'Reference images').Count
    if ($referenceCount -gt 1) {
        throw "prompt.md contains duplicate 'Reference images' sections."
    }

    $managed = @{}
    $total = 0
    foreach ($heading in $managedHeadings) {
        $matches = @(Get-LevelTwoSectionMatches $PromptText $heading)
        if ($matches.Count -gt 1) {
            throw "prompt.md contains duplicate '$heading' sections."
        }
        $managed[$heading] = $matches
        $total += $matches.Count
    }
    if ($total -notin @(0, 3, 4)) {
        throw 'prompt.md has an incomplete managed rewrite-section set.'
    }
    if ($total -gt 0) {
        foreach ($heading in @('Rewrite request', 'Rewrite reference images', 'Rewrite constraints')) {
            if ($managed[$heading].Count -ne 1) {
                throw "prompt.md has an incomplete managed rewrite-section set; '$heading' is required."
            }
        }
        if ($total -eq 3 -and $managed['Rewrite selections'].Count -ne 0) {
            throw 'prompt.md has an invalid legacy rewrite-section set.'
        }
        $requestMatch = $managed['Rewrite request'][0]
        $referenceMatch = $managed['Rewrite reference images'][0]
        $selectionMatch = if ($managed['Rewrite selections'].Count -eq 1) { $managed['Rewrite selections'][0] } else { $null }
        $constraintMatch = $managed['Rewrite constraints'][0]
        $isContiguous = $requestMatch.Index + $requestMatch.Length -eq $referenceMatch.Index
        if ($null -ne $selectionMatch) {
            $isContiguous = (
                $isContiguous -and
                $referenceMatch.Index + $referenceMatch.Length -eq $selectionMatch.Index -and
                $selectionMatch.Index + $selectionMatch.Length -eq $constraintMatch.Index
            )
        }
        else {
            $isContiguous = $isContiguous -and $referenceMatch.Index + $referenceMatch.Length -eq $constraintMatch.Index
        }
        if (-not $isContiguous) {
            throw 'Managed rewrite sections must be contiguous and ordered as request, reference images, optional selections, and constraints.'
        }
    }
    return $managed
}

function Assert-CandidatePrompt {
    param([string]$PromptText)

    foreach ($heading in $managedHeadings) {
        $matches = @(Get-LevelTwoSectionMatches $PromptText $heading)
        if ($matches.Count -ne 1) {
            throw "Candidate prompt must contain exactly one '$heading' section; found $($matches.Count)."
        }
    }

    $requestBody = (Get-LevelTwoSectionMatches $PromptText 'Rewrite request')[0].Groups['body'].Value.Trim()
    if ($requestBody -notmatch '(?m)^>\s*\S') {
        throw 'Candidate Rewrite request section must contain a non-empty blockquote.'
    }
    $referenceBody = (Get-LevelTwoSectionMatches $PromptText 'Rewrite reference images')[0].Groups['body'].Value.Trim()
    if ([string]::IsNullOrWhiteSpace($referenceBody)) {
        throw 'Candidate Rewrite reference images section cannot be empty.'
    }

    $selectionBody = (Get-LevelTwoSectionMatches $PromptText 'Rewrite selections')[0].Groups['body'].Value.Trim()
    Assert-RewriteSelections $selectionBody 'Candidate Rewrite selections'

    $constraints = (Get-LevelTwoSectionMatches $PromptText 'Rewrite constraints')[0].Groups['body'].Value.Trim()
    $coverLines = @([regex]::Matches($constraints, '(?m)^-[ \t]+Cover:[ \t]*(?<value>[^\r\n]+?)[ \t]*\r?$'))
    if ($coverLines.Count -ne 1 -or $coverLines[0].Groups['value'].Value.Trim() -notin @('AUTO', 'KEEP', 'REGENERATE')) {
        throw 'Candidate Rewrite constraints must contain exactly one valid Cover policy.'
    }
    $profileLines = @([regex]::Matches(
        $constraints,
        '(?m)^-[ \t]+Craft profile:[ \t]*prospective-2026-08-23[ \t]*\r?$'
    ))
    if ($profileLines.Count -ne 1) {
        throw 'Candidate Rewrite constraints must contain exactly one active 08-23 craft profile.'
    }
    $authorityLines = @([regex]::Matches(
        $constraints,
        '(?m)^-[ \t]+Authority:[ \t]*the rewrite request and selections control where they conflict with the original prompt; outside named selections follows the recorded preservation policy\.[ \t]*\r?$'
    ))
    if ($authorityLines.Count -ne 1) {
        throw 'Candidate Rewrite constraints must contain exactly one authority line.'
    }
}

$normalizedTitle = $Title.Trim()
if ([string]::IsNullOrWhiteSpace($normalizedTitle)) {
    throw 'Rewrite title cannot be blank.'
}
if ($normalizedTitle -match '[\r\n\p{Cc}]') {
    throw 'Rewrite title cannot contain CR, LF, or control characters.'
}
if ([string]::IsNullOrWhiteSpace($Request)) {
    throw 'Rewrite request cannot be blank.'
}

$normalizedKeepExact = @(Get-NormalizedSelections $KeepExact 'KeepExact')
$normalizedKeep = @(Get-NormalizedSelections $Keep 'Keep')
$normalizedChange = @(Get-NormalizedSelections $Change 'Change')
$normalizedRemove = @(Get-NormalizedSelections $Remove 'Remove')
$selectionOwners = @{}
foreach ($entry in @(
    [pscustomobject]@{ Label = 'KeepExact'; Values = $normalizedKeepExact },
    [pscustomobject]@{ Label = 'Keep'; Values = $normalizedKeep },
    [pscustomobject]@{ Label = 'Change'; Values = $normalizedChange },
    [pscustomobject]@{ Label = 'Remove'; Values = $normalizedRemove }
)) {
    foreach ($value in $entry.Values) {
        if ($selectionOwners.ContainsKey($value)) {
            throw "Rewrite selection '$value' appears in both $($selectionOwners[$value]) and $($entry.Label)."
        }
        $selectionOwners[$value] = $entry.Label
    }
}

$scopeValue = $Scope.ToUpperInvariant()
$outsideValue = switch ($Scope) {
    'Rebuild' { 'FLEXIBLE' }
    'Reshape' { 'KEEP' }
    'Selective' { 'KEEP EXACT' }
}
if ($Scope -eq 'Selective' -and $normalizedChange.Count -eq 0 -and $normalizedRemove.Count -eq 0) {
    throw 'Selective scope requires at least one -Change or -Remove selection.'
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

$gitMarker = Join-Path $ProjectRoot '.git'
if (-not (Test-Path -LiteralPath $gitMarker -PathType Leaf)) {
    throw 'Rewrite preparation requires a dedicated linked Git worktree, whose .git marker is a file.'
}
$verifiedRoot = (& git -C $ProjectRoot rev-parse --show-toplevel 2>$null)
if (
    $LASTEXITCODE -ne 0 -or
    [string]::IsNullOrWhiteSpace($verifiedRoot) -or
    [IO.Path]::GetFullPath($verifiedRoot.Trim()) -cne $ProjectRoot
) {
    throw 'ProjectRoot is not the root of the target linked Git worktree.'
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
    throw 'Legacy bundles cannot use the current-format rewrite preparation script. Follow the Canon lock and legacy editing contract for an authorized direct edit.'
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

$outlineTemplatePath = Join-Path $ProjectRoot 'stories/_template/outline.md'
$reviewTemplatePath = Join-Path $ProjectRoot 'stories/_template/review.md'
foreach ($templatePath in @($outlineTemplatePath, $reviewTemplatePath)) {
    if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
        throw "Required rewrite template not found: $templatePath"
    }
}
$outlineTemplate = Read-Utf8File $outlineTemplatePath 'Outline template'
$reviewTemplate = Read-Utf8File $reviewTemplatePath 'Review template'
if (@(Get-LevelTwoSectionMatches $outlineTemplate.Text 'Voice').Count -ne 1) {
    throw 'Outline template must contain exactly one Voice section.'
}
$rewriteOutlineFields = @(
    'Dialogue promise',
    'Dialogic medium',
    'Dialogue engine',
    'Narrative texture',
    'Conversational texture',
    'Rhetorical ownership',
    'Pressure behavior',
    'Relationship movement',
    'Anti-default'
)
foreach ($field in $rewriteOutlineFields) {
    $escaped = [regex]::Escape($field)
    if (@([regex]::Matches($outlineTemplate.Text, "(?m)^-[ \t]+${escaped}:[ \t]*\r?$")).Count -ne 1) {
        throw "Outline template must contain exactly one empty '$field' field."
    }
}
$rewriteOutlineBytes = $outlineTemplate.Bytes
foreach ($heading in @('People', 'Places', 'Continuity', 'Craft', 'Findings')) {
    if (@(Get-LevelTwoSectionMatches $reviewTemplate.Text $heading).Count -ne 1) {
        throw "Review template must contain exactly one '$heading' section."
    }
}

$paths = [ordered]@{
    'prompt.md' = Join-Path $target 'prompt.md'
    'outline.md' = Join-Path $target 'outline.md'
    'story.md' = Join-Path $target 'story.md'
    'review.md' = Join-Path $target 'review.md'
    'title-image.jpg' = Join-Path $target 'title-image.jpg'
}
$originals = [ordered]@{}
foreach ($name in $paths.Keys) {
    $originals[$name] = [IO.File]::ReadAllBytes($paths[$name])
}

$storyFile = Read-Utf8File $paths['story.md'] 'Current story.md'
$storyText = $storyFile.Text
if ($storyText -notmatch '(?m)^canon:\s*false\s*$') {
    if ($storyText -match '(?m)^canon:\s*true\s*$') {
        throw 'Canon stories require an explicit retcon or canon ruling and cannot use the ordinary rewrite path.'
    }
    throw 'Current story.md must declare canon: false.'
}
$front = [regex]::Match(
    $storyText,
    '(?s)\A---(?:\r\n|\n|\r)(?<value>.*?)(?:\r\n|\n|\r)---(?:\r\n|\n|\r)'
)
if (-not $front.Success) {
    throw 'Current story.md lacks valid frontmatter.'
}
$titleMatches = @([regex]::Matches(
    $front.Groups['value'].Value,
    '(?m)^title:[ \t]*(?<value>[^\r\n]*)\r?$'
))
if ($titleMatches.Count -ne 1 -or [string]::IsNullOrWhiteSpace($titleMatches[0].Groups['value'].Value)) {
    throw 'Current story.md frontmatter must contain exactly one non-empty title.'
}
$oldTitle = Get-ReaderTitle $titleMatches[0].Groups['value'].Value
$titleChanged = -not [string]::Equals($normalizedTitle, $oldTitle, [StringComparison]::Ordinal)
if ($Cover -eq 'Keep' -and $titleChanged) {
    throw 'Cover Keep requires the rewrite title to match the existing reader-facing title exactly.'
}

$reviewFile = Read-Utf8File $paths['review.md'] 'Current review.md'
$reviewText = $reviewFile.Text
if ($reviewText -notmatch '(?m)^Verdict:\s*PASS\s*$') {
    throw 'Rewrite preparation requires a completed current story with Verdict: PASS.'
}
foreach ($area in @('Prompt', 'Universe', 'Internal')) {
    if ($reviewText -notmatch "(?m)^-\s+${area}:\s*PASS\s*$") {
        throw "Rewrite preparation requires the existing ${area} continuity verdict to be PASS."
    }
}

$promptFile = Read-Utf8File $paths['prompt.md'] 'Current prompt.md'
$promptText = $promptFile.Text
$managed = Assert-PromptStructure $promptText
$promptEol = Get-LineEnding $promptText
$normalizedRequest = [regex]::Replace($Request.Trim(), '\r\n|\n|\r', $promptEol)
$requestLines = [regex]::Split($normalizedRequest, '\r\n|\n|\r')
$requestBlock = ($requestLines | ForEach-Object { "> $_" }) -join $promptEol

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
    ($referenceImageLabels | ForEach-Object { "- ``$($_.Replace('`', "'"))``" }) -join $promptEol
}

$selectionBlock = @(
    "- Scope: $scopeValue",
    "- Outside named selections: $outsideValue",
    (ConvertTo-SelectionBlock 'Keep exact' $normalizedKeepExact $promptEol),
    (ConvertTo-SelectionBlock 'Keep in substance' $normalizedKeep $promptEol),
    (ConvertTo-SelectionBlock 'Change or replace' $normalizedChange $promptEol),
    (ConvertTo-SelectionBlock 'Remove' $normalizedRemove $promptEol)
) -join $promptEol

$coverValue = $Cover.ToUpperInvariant()
$managedBlock = @(
    '## Rewrite request',
    '',
    $requestBlock,
    '',
    '## Rewrite reference images',
    '',
    $referenceImageBlock,
    '',
    '## Rewrite selections',
    '',
    $selectionBlock,
    '',
    '## Rewrite constraints',
    '',
    "- Cover: $coverValue",
    "- Craft profile: $activeCraftProfile",
    '- Authority: the rewrite request and selections control where they conflict with the original prompt; outside named selections follows the recorded preservation policy.'
) -join $promptEol

if ($managed['Rewrite request'].Count -eq 1) {
    $first = $managed['Rewrite request'][0]
    $last = $managed['Rewrite constraints'][0]
    $prefix = $promptText.Substring(0, $first.Index)
    $suffixIndex = $last.Index + $last.Length
    $suffix = $promptText.Substring($suffixIndex)
    $separator = if ($suffix.Length -eq 0) { $promptEol } else { $promptEol + $promptEol }
    $pendingPrompt = $prefix + $managedBlock + $separator + $suffix
    if (
        -not $pendingPrompt.StartsWith($prefix, [StringComparison]::Ordinal) -or
        -not $pendingPrompt.EndsWith($suffix, [StringComparison]::Ordinal)
    ) {
        throw 'Internal prompt replacement failed to preserve text outside managed rewrite sections.'
    }
}
else {
    $separator = if ($promptText.EndsWith($promptEol + $promptEol, [StringComparison]::Ordinal)) {
        ''
    }
    elseif ($promptText.EndsWith($promptEol, [StringComparison]::Ordinal)) {
        $promptEol
    }
    else {
        $promptEol + $promptEol
    }
    $pendingPrompt = $promptText + $separator + $managedBlock + $promptEol
    if (-not $pendingPrompt.StartsWith($promptText, [StringComparison]::Ordinal)) {
        throw 'Internal prompt append failed to preserve the original prompt.'
    }
}
Assert-CandidatePrompt $pendingPrompt

$storyEol = Get-LineEnding $storyText
$frontValue = $front.Groups['value'].Value
$titleMatch = $titleMatches[0]
$titleYaml = $normalizedTitle | ConvertTo-Json -Compress
$pendingFrontValue = (
    $frontValue.Substring(0, $titleMatch.Index) +
    "title: $titleYaml" +
    $frontValue.Substring($titleMatch.Index + $titleMatch.Length)
)
$frontValueStart = $front.Groups['value'].Index
$frontValueEnd = $frontValueStart + $front.Groups['value'].Length
$pendingFront = (
    $storyText.Substring(0, $frontValueStart) +
    $pendingFrontValue +
    $storyText.Substring($frontValueEnd, $front.Length - $frontValueEnd)
)
$pendingStory = if ($Scope -eq 'Selective') {
    $existingBody = $storyText.Substring($front.Length)
    $heading = [regex]::Match($existingBody, '(?m)^#[ \t]+[^\r\n]+')
    if (-not $heading.Success) {
        throw 'Selective rewrite requires an existing reader-facing H1 title.'
    }
    $pendingBody = (
        $existingBody.Substring(0, $heading.Index) +
        "# $normalizedTitle" +
        $existingBody.Substring($heading.Index + $heading.Length)
    )
    $pendingFront + $pendingBody
}
else {
    (
        $pendingFront +
        $storyEol +
        "# $normalizedTitle" +
        $storyEol +
        $storyEol +
        '<!-- Complete reader-facing prose goes here. -->' +
        $storyEol
    )
}
if ($pendingStory -notmatch '(?s)\A---(?:\r\n|\n|\r).*?(?:\r\n|\n|\r)---(?:\r\n|\n|\r){2}#\s+\S') {
    throw 'Candidate story.md is malformed.'
}

$candidates = [ordered]@{
    'prompt.md' = ConvertTo-Utf8Bytes $pendingPrompt $promptFile.HasBom
    'outline.md' = $rewriteOutlineBytes
    'story.md' = ConvertTo-Utf8Bytes $pendingStory $storyFile.HasBom
    'review.md' = $reviewTemplate.Bytes
}
foreach ($name in $candidates.Keys) {
    if ($candidates[$name].Length -eq 0) {
        throw "Candidate $name is empty."
    }
}

$removeCover = (
    $Cover -eq 'Regenerate' -or
    ($Cover -eq 'Auto' -and $titleChanged)
)
$projectParent = [IO.Directory]::GetParent($ProjectRoot).FullName
$stageRoot = Join-Path $projectParent ('.rewrite-stage-' + [guid]::NewGuid().ToString('N'))
$stageRoot = [IO.Path]::GetFullPath($stageRoot)
if (
    $stageRoot.StartsWith($ProjectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
    [IO.Directory]::GetParent($stageRoot).FullName -cne $projectParent -or
    -not [IO.Path]::GetFileName($stageRoot).StartsWith('.rewrite-stage-', [StringComparison]::Ordinal)
) {
    throw 'Unable to resolve a safe staging directory outside the repository.'
}

$transactionError = $null
$rollbackErrors = [Collections.Generic.List[string]]::new()
try {
    $null = [IO.Directory]::CreateDirectory($stageRoot)
    foreach ($name in $candidates.Keys) {
        [IO.File]::WriteAllBytes((Join-Path $stageRoot $name), $candidates[$name])
    }

    foreach ($name in $candidates.Keys) {
        [IO.File]::Move((Join-Path $stageRoot $name), $paths[$name], $true)
    }
    if ($removeCover) {
        [IO.File]::Delete($paths['title-image.jpg'])
    }
}
catch {
    $transactionError = $_
    foreach ($name in $originals.Keys) {
        try {
            $path = $paths[$name]
            $needsRestore = -not (Test-Path -LiteralPath $path -PathType Leaf)
            if (-not $needsRestore) {
                $needsRestore = -not (Test-ByteEquality ([IO.File]::ReadAllBytes($path)) $originals[$name])
            }
            if ($needsRestore) {
                [IO.File]::WriteAllBytes($path, $originals[$name])
            }
        }
        catch {
            $rollbackErrors.Add("${name}: $($_.Exception.Message)")
        }
    }
}
finally {
    if (Test-Path -LiteralPath $stageRoot -PathType Container) {
        foreach ($stagedFile in [IO.Directory]::GetFiles($stageRoot)) {
            [IO.File]::Delete($stagedFile)
        }
        [IO.Directory]::Delete($stageRoot, $false)
    }
}

if ($null -ne $transactionError) {
    $message = "Rewrite preparation failed and original files were restored: $($transactionError.Exception.Message)"
    if ($rollbackErrors.Count -gt 0) {
        $message += " Rollback errors: $($rollbackErrors -join '; ')"
    }
    throw $message
}

$changed = [Collections.Generic.List[string]]::new()
foreach ($name in @('prompt.md', 'outline.md', 'story.md', 'review.md')) {
    $changed.Add($name)
}
$coverFile = 'retained as an unchanged-title post-review candidate'
if ($removeCover) {
    $changed.Add('title-image.jpg')
    $coverFile = 'removed; fresh generation required after PASS'
}
$nextStep = if ($Scope -eq 'Selective') {
    'Run fresh-agent OUTLINE and selective WRITE stages against the retained prose, then PreReview and fresh REVIEW.'
}
else {
    'Run fresh-agent OUTLINE and whole-story WRITE stages from the amended prompt and selections, then PreReview and fresh REVIEW.'
}

[ordered]@{
    story = $Story
    directory = $relativeDirectory
    mode = 'REWRITE'
    scope = $scopeValue
    outsideNamedSelections = $outsideValue
    craftProfile = $activeCraftProfile
    cover = $coverValue
    coverFile = $coverFile
    changed = @($changed)
    next = $nextStep
} | ConvertTo-Json
