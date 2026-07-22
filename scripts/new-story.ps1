[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Slug,

    [string]$Title
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$TemplateDirectory = Join-Path $ProjectRoot 'stories/_template'
$StoryDirectory = Join-Path $ProjectRoot ("stories/{0}" -f $Slug)

if (-not (Test-Path -LiteralPath $TemplateDirectory -PathType Container)) {
    throw "Story template not found: $TemplateDirectory"
}

if (Test-Path -LiteralPath $StoryDirectory) {
    throw "Story directory already exists: $StoryDirectory"
}

if ([string]::IsNullOrWhiteSpace($Title)) {
    $Title = (Get-Culture).TextInfo.ToTitleCase(($Slug -replace '-', ' '))
}

New-Item -ItemType Directory -Path $StoryDirectory | Out-Null
Get-ChildItem -LiteralPath $TemplateDirectory -Force |
    Copy-Item -Destination $StoryDirectory -Recurse

$CreatedDate = Get-Date -Format 'yyyy-MM-dd'
$YamlTitle = ConvertTo-Json -InputObject $Title -Compress
Get-ChildItem -LiteralPath $StoryDirectory -Filter '*.md' -File | ForEach-Object {
    $Content = Get-Content -LiteralPath $_.FullName -Raw
    $Content = $Content.Replace('{{slug}}', $Slug)
    $Content = $Content.Replace('{{title}}', $Title)
    $Content = $Content.Replace('{{title_yaml}}', $YamlTitle)
    $Content = $Content.Replace('{{date}}', $CreatedDate)
    Set-Content -LiteralPath $_.FullName -Value $Content -Encoding utf8NoBOM
}

Write-Output $StoryDirectory
