#Requires -Version 7.0
[CmdletBinding()]param([string]$ProjectRoot)
if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
$required=@('story.json','authority.json','handoffs.json','promotion.json','release.json','00-prompt.md','01-canon-brief.md','02-story-plan.md','03-draft.md','04-review.md','05-story.md','06-canon-delta.md','README.md');$missing=@($required|Where-Object{-not(Test-Path -LiteralPath (Join-Path $ProjectRoot "stories/_template/$_"))});if($missing.Count){throw "Missing templates: $($missing -join ', ')"};'Pipeline artifacts passed.'
