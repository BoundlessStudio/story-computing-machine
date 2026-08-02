#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Slug,

    [string]$Title,

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

if (-not (Test-Path -LiteralPath $TemplateDirectory -PathType Container)) {
    throw "Story template not found: $TemplateDirectory"
}

if (Test-Path -LiteralPath $StoryDirectory) {
    throw "Story directory already exists: $StoryDirectory"
}

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
    'release.json'
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

$CreatedDate = Get-Date -Format 'yyyy-MM-dd'
$JsonTitle = ConvertTo-Json -InputObject $Title -Compress
$StagingDirectory = Join-Path $StoriesDirectory (
    '.{0}.tmp.{1}' -f $Slug, [guid]::NewGuid().ToString('N')
)

try {
    New-Item -ItemType Directory -Path $StagingDirectory | Out-Null
    Get-ChildItem -LiteralPath $TemplateDirectory -Force |
        Copy-Item -Destination $StagingDirectory -Recurse

    $ReplacementMap = [ordered]@{
        '{{slug}}' = $Slug
        '{{title}}' = $Title
        '{{title_yaml}}' = $JsonTitle
        '{{date}}' = $CreatedDate
        '{{prompt}}' = '[Capture the verbatim writing prompt here.]'
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

    foreach ($JsonName in @('story.json', 'release.json')) {
        $JsonPath = Join-Path $StagingDirectory $JsonName
        try {
            $null = Get-Content -LiteralPath $JsonPath -Raw | ConvertFrom-Json
        }
        catch {
            throw "Staged $JsonName is invalid JSON: $($_.Exception.Message)"
        }
    }

    if (Test-Path -LiteralPath $StoryDirectory) {
        throw "Story directory appeared during creation: $StoryDirectory"
    }

    [System.IO.Directory]::Move($StagingDirectory, $StoryDirectory)
}
finally {
    if (Test-Path -LiteralPath $StagingDirectory -PathType Container) {
        Remove-Item -LiteralPath $StagingDirectory -Recurse -Force
    }
}

Write-Output $StoryDirectory
