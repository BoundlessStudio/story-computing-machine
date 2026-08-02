#Requires -Version 7.0
[CmdletBinding()]param([Parameter(Mandatory)][string]$Story,[ValidateSet('Text','Json')][string]$OutputFormat='Text',[string]$ProjectRoot)
$ErrorActionPreference='Stop';if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
. (Join-Path $PSScriptRoot 'PipelineCommon.ps1');Assert-ProductionBranch $ProjectRoot
$branch=Get-RepositoryBranch $ProjectRoot;if($branch -cnotmatch '^codex/story-' -and $branch -cnotmatch '^codex/pipeline-'){throw "Story work branch '$branch' does not follow the protected workflow."}
& (Join-Path $PSScriptRoot 'Test-StoryIntegrity.ps1') -Story $Story -OutputFormat Json -ProjectRoot $ProjectRoot *> $null;$storyOk=$?;if(-not$storyOk){throw 'Story-scoped integrity failed.'}
$record=Read-PipelineJson(Join-Path $ProjectRoot "stories/$Story/story.json");if($record.provenance-ceq'pipeline'){& (Join-Path $PSScriptRoot 'Test-StoryHandoffs.ps1') -Story $Story -OutputFormat Json -ProjectRoot $ProjectRoot *> $null;$handoffOk=$?;if(-not$handoffOk){throw 'Story handoff sequence failed.'}}
$phase=if($record.stage -cin @('prompt','canon-research','planning')){'Plan'}else{'Final'};& (Join-Path $PSScriptRoot 'Test-StoryNames.ps1') -Story $Story -Phase $phase -OutputFormat Json -ProjectRoot $ProjectRoot *> $null;$nameOk=$?;if(-not$nameOk){throw 'Story name gate failed.'}
$result=[ordered]@{schemaVersion=1;passed=$true;story=$Story;branch=$branch;phase=$phase};if($OutputFormat-ceq'Json'){$result|ConvertTo-Json}else{"Fast branch validation passed for $Story."}