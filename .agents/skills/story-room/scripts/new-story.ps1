#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Slug,

    [string]$Title,

    [AllowEmptyString()]
    [string]$Prompt = '[Capture the verbatim writing prompt here.]',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$TemplateDirectory = Join-Path $ProjectRoot 'stories/_template'
$StoriesDirectory = Join-Path $ProjectRoot 'stories'
$StoryDirectory = Join-Path $ProjectRoot ("stories/{0}" -f $Slug)
$IndexPath = Join-Path $StoriesDirectory 'INDEX.md'
$LockDirectory = Join-Path $ProjectRoot '.story-locks'
$LockPath = Join-Path $LockDirectory 'repository.lock'
$LockId = 'scaffold-' + [guid]::NewGuid().ToString('N')

if (-not (Test-Path -LiteralPath $TemplateDirectory -PathType Container)) {
    throw "Story template not found: $TemplateDirectory"
}

if (Test-Path -LiteralPath $StoryDirectory) {
    throw "Story directory already exists: $StoryDirectory"
}
$PipelineContractPath = Join-Path $ProjectRoot 'schemas/pipeline-contract.json'
$PipelineContractChecker = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-PipelineContract.ps1'
if (-not (Test-Path -LiteralPath $PipelineContractChecker -PathType Leaf)) {
    throw "Pipeline contract validator not found: $PipelineContractChecker"
}
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$ContractOutput = & $Pwsh -NoLogo -NoProfile -File $PipelineContractChecker `
    -OutputFormat Json -ProjectRoot $ProjectRoot 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "Pipeline contract preflight failed: $($ContractOutput.Trim())"
}
$PipelineContract = Get-Content -LiteralPath $PipelineContractPath -Raw | ConvertFrom-Json

$RequiredTemplates = @(
    '00-prompt.md',
    '01-canon-brief.md',
    '02-story-plan.md',
    '03-draft.md',
    '04-review.md',
    '05-story.md',
    '06-canon-delta.md',
    'README.md',
    'story.json',
    'release.json',
    'authority.json',
    'handoffs.json',
    'promotion.json'
)

foreach ($RequiredTemplate in $RequiredTemplates) {
    $RequiredPath = Join-Path $TemplateDirectory $RequiredTemplate
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) {
        throw "Required story template is missing: $RequiredPath"
    }
}

if ([string]::IsNullOrWhiteSpace($Title)) {
    $Title = (Get-Culture).TextInfo.ToTitleCase(($Slug -replace '-', ' '))
}
if ($Title -match '[\r\n|]') {
    throw 'Title must be a single line and cannot contain a Markdown table pipe.'
}

$NormalizedPrompt = $Prompt.Replace("`r`n", "`n").Replace("`r", "`n")
$QuotedPrompt = ($NormalizedPrompt -split "`n", -1) -join "`n> "

$CreatedDate = Get-Date -Format 'yyyy-MM-dd'
$JsonTitle = ConvertTo-Json -InputObject $Title -Compress
$StagingDirectory = Join-Path $StoriesDirectory (
    '.{0}.tmp.{1}' -f $Slug, [guid]::NewGuid().ToString('N')
)

New-Item -ItemType Directory -Path $LockDirectory -Force | Out-Null
try {
    try {
        $LockStream = [IO.File]::Open(
            $LockPath,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::Write,
            [IO.FileShare]::None
        )
        try {
            $LockBytes = [Text.UTF8Encoding]::new($false).GetBytes($LockId)
            $LockStream.Write($LockBytes, 0, $LockBytes.Length)
        }
        finally { $LockStream.Dispose() }
    }
    catch {
        $Owner = if (Test-Path -LiteralPath $LockPath -PathType Leaf) {
            Get-Content -LiteralPath $LockPath -Raw
        }
        else { 'unknown' }
        throw "Another pipeline mutation is active ($Owner); scaffold was not started."
    }

    if (Test-Path -LiteralPath $StoryDirectory) {
        throw "Story directory appeared during scaffold preflight: $StoryDirectory"
    }

    New-Item -ItemType Directory -Path $StagingDirectory | Out-Null
    Get-ChildItem -LiteralPath $TemplateDirectory -Force |
        Copy-Item -Destination $StagingDirectory -Recurse

    $ReplacementMap = [ordered]@{
        '{{slug}}' = $Slug
        '{{title}}' = $Title
        '{{title_yaml}}' = $JsonTitle
        '{{date}}' = $CreatedDate
        '{{prompt}}' = $QuotedPrompt
    }

    Get-ChildItem -LiteralPath $StagingDirectory -File | Where-Object {
        $_.Extension -in @('.md', '.json')
    } | ForEach-Object {
        $Content = Get-Content -LiteralPath $_.FullName -Raw
        foreach ($Placeholder in $ReplacementMap.Keys) {
            $Content = $Content.Replace($Placeholder, $ReplacementMap[$Placeholder])
        }
        $Content = $Content.Replace("`r`n", "`n").Replace("`r", "`n")

        if ($Content -match '{{[^{}]+}}') {
            throw "Unresolved template placeholder in $($_.Name): $($Matches[0])"
        }

        Set-Content -LiteralPath $_.FullName -Value $Content -Encoding utf8NoBOM -NoNewline
    }

    foreach ($RequiredTemplate in $RequiredTemplates) {
        $StagedPath = Join-Path $StagingDirectory $RequiredTemplate
        if (-not (Test-Path -LiteralPath $StagedPath -PathType Leaf)) {
            throw "Staged story is missing required artifact: $RequiredTemplate"
        }
    }

    foreach ($JsonName in @(
        'story.json', 'release.json', 'authority.json', 'handoffs.json',
        'promotion.json'
    )) {
        $JsonPath = Join-Path $StagingDirectory $JsonName
        try {
            $null = Get-Content -LiteralPath $JsonPath -Raw | ConvertFrom-Json
        }
        catch {
            throw "Staged $JsonName is invalid JSON: $($_.Exception.Message)"
        }
    }
    $StagedStory = Get-Content -LiteralPath (Join-Path $StagingDirectory 'story.json') -Raw |
        ConvertFrom-Json
    if ($StagedStory.schemaVersion -ne $PipelineContract.story.schemaVersion -or
        $StagedStory.slug -cne $Slug -or $StagedStory.stage -cne 'prompt' -or
        $StagedStory.status -cne 'in-progress' -or $StagedStory.canon -ne $false -or
        $StagedStory.userDisposition -cne 'pending' -or $StagedStory.publish -ne $false -or
        $null -ne $StagedStory.promotionDate) {
        throw 'Staged story.json does not match the initial lifecycle contract.'
    }
    $StagedRelease = Get-Content -LiteralPath (Join-Path $StagingDirectory 'release.json') -Raw |
        ConvertFrom-Json
    if ($StagedRelease.schemaVersion -ne $PipelineContract.release.schemaVersion -or
        $StagedRelease.certified -ne $false -or $StagedRelease.storySlug -cne $Slug) {
        throw 'Staged release.json does not match the uncertified release contract.'
    }
    $StagedHandoffs = Get-Content -LiteralPath (Join-Path $StagingDirectory 'handoffs.json') -Raw |
        ConvertFrom-Json
    if ($StagedHandoffs.schemaVersion -ne $PipelineContract.handoffLedger.schemaVersion -or
        $StagedHandoffs.storySlug -cne $Slug -or $null -ne $StagedHandoffs.chainHead -or
        @($StagedHandoffs.entries).Count -ne 0) {
        throw 'Staged handoffs.json does not match the empty ledger contract.'
    }
    $PromotionSchemaPath = Join-Path $ProjectRoot ([string]$PipelineContract.promotion.schemaPath)
    $PromotionJson = Get-Content -LiteralPath (Join-Path $StagingDirectory 'promotion.json') -Raw
    $PromotionErrors = @()
    if (-not (Test-Json -Json $PromotionJson -SchemaFile $PromotionSchemaPath `
        -ErrorVariable +PromotionErrors -ErrorAction SilentlyContinue)) {
        throw 'Staged promotion.json fails its normative schema.'
    }

    $IndexExisted = Test-Path -LiteralPath $IndexPath -PathType Leaf
    $OriginalIndexBytes = if ($IndexExisted) {
        [IO.File]::ReadAllBytes($IndexPath)
    }
    else { $null }
    $IndexContent = if ($IndexExisted) {
        [IO.File]::ReadAllText($IndexPath)
    }
    else {
        @(
            '# Story index',
            '',
            '`story.json` is authoritative; this table is a validated projection.',
            '',
            '| Story | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |',
            '',
            'Statuses are `in-progress`, `candidate`, `final`, or `abandoned`.',
            ''
        ) -join "`n"
    }
    $IndexContent = $IndexContent.Replace("`r`n", "`n").Replace("`r", "`n")
    if ($IndexContent -match "(?m)^\|\s*``$([regex]::Escape($Slug))``\s*\|") {
        throw "stories/INDEX.md already contains slug '$Slug'."
    }
    $HeaderPattern = '(?m)^\| Story \| Title \| Status \| Canon \| User disposition \| Publish \| Promotion date \| Notes \|\n\| --- \| --- \| --- \| --- \| --- \| --- \| --- \| --- \|\n'
    $HeaderMatch = [regex]::Match($IndexContent, $HeaderPattern)
    if (-not $HeaderMatch.Success) {
        throw 'stories/INDEX.md is missing its exact eight-column table header.'
    }
    $TableEnd = $HeaderMatch.Index + $HeaderMatch.Length
    while ($TableEnd -lt $IndexContent.Length -and
        $IndexContent.Substring($TableEnd) -match '\A\|[^\n]*\|\n') {
        $TableEnd += $Matches[0].Length
    }
    $IndexRow = "| ``$Slug`` | *$Title* | in-progress | no | pending | no | — | Scaffold created; production in progress. |`n"
    $UpdatedIndex = $IndexContent.Insert($TableEnd, $IndexRow)
    $IndexTemporary = "$IndexPath.tmp.$([guid]::NewGuid().ToString('N'))"

    [System.IO.Directory]::Move($StagingDirectory, $StoryDirectory)
    try {
        [IO.File]::WriteAllText(
            $IndexTemporary,
            $UpdatedIndex,
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::Move($IndexTemporary, $IndexPath, $true)
    }
    catch {
        if (Test-Path -LiteralPath $IndexTemporary) {
            Remove-Item -LiteralPath $IndexTemporary -Force
        }
        if (Test-Path -LiteralPath $StoryDirectory -PathType Container) {
            $ResolvedStory = [IO.Path]::GetFullPath($StoryDirectory)
            $ResolvedStories = [IO.Path]::GetFullPath($StoriesDirectory) +
                [IO.Path]::DirectorySeparatorChar
            if (-not $ResolvedStory.StartsWith(
                $ResolvedStories,
                [StringComparison]::OrdinalIgnoreCase
            )) {
                throw "Refusing unsafe scaffold rollback target: $ResolvedStory"
            }
            Remove-Item -LiteralPath $ResolvedStory -Recurse -Force
        }
        if ($IndexExisted) {
            [IO.File]::WriteAllBytes($IndexPath, $OriginalIndexBytes)
        }
        elseif (Test-Path -LiteralPath $IndexPath) {
            Remove-Item -LiteralPath $IndexPath -Force
        }
        throw
    }
}
finally {
    if (Test-Path -LiteralPath $StagingDirectory -PathType Container) {
        Remove-Item -LiteralPath $StagingDirectory -Recurse -Force
    }
    if ((Test-Path -LiteralPath $LockPath -PathType Leaf) -and
        (Get-Content -LiteralPath $LockPath -Raw) -ceq $LockId) {
        Remove-Item -LiteralPath $LockPath -Force
    }
}

Write-Output $StoryDirectory
