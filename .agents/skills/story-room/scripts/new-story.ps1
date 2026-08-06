#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Slug,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Title,

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$Prompt,

    [string]$Date = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
}
else {
    $ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)
}

if ($Date -notmatch '^\d{4}-\d{2}-\d{2}$') {
    throw 'Date must be YYYY-MM-DD.'
}

$branch = (& git -C $ProjectRoot branch --show-current 2>$null)
if ($LASTEXITCODE -eq 0 -and $branch.Trim() -eq 'main') {
    throw 'Create a non-main story branch before scaffolding.'
}

$template = Join-Path $ProjectRoot 'stories/_template'
$target = Join-Path $ProjectRoot "stories/$Slug"
if (Test-Path -LiteralPath $target) {
    throw "Story directory already exists: $target"
}
if (-not (Test-Path -LiteralPath $template -PathType Container)) {
    throw "Story template not found: $template"
}

Copy-Item -LiteralPath $template -Destination $target -Recurse

$normalizedPrompt = [regex]::Replace($Prompt, '\r\n?', [string][char]10).Trim()
$promptBlock = (($normalizedPrompt -split '\n') | ForEach-Object { "> $($_.TrimEnd())" }) -join [char]10
$titleYaml = $Title | ConvertTo-Json -Compress

foreach ($file in Get-ChildItem -LiteralPath $target -File) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    $text = $text.Replace('{{slug}}', $Slug)
    $text = $text.Replace('{{title}}', $Title)
    $text = $text.Replace('{{title_yaml}}', $titleYaml)
    $text = $text.Replace('{{date}}', $Date)
    $text = $text.Replace('{{prompt_block}}', $promptBlock)
    $text = [regex]::Replace($text, '\r\n?', [string][char]10)
    [IO.File]::WriteAllText($file.FullName, $text, [Text.UTF8Encoding]::new($false))
}

[ordered]@{
    story = $Slug
    directory = "stories/$Slug"
    files = @('prompt.md', 'outline.md', 'story.md', 'review.md')
} | ConvertTo-Json
