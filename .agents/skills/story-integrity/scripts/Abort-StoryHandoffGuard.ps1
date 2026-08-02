#Requires -Version 7.0
[CmdletBinding()]param([Parameter(Mandatory)][string]$GuardId,[string]$ProjectRoot)
$ErrorActionPreference='Stop';if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
. (Join-Path $PSScriptRoot 'PipelineCommon.ps1');$lockDir=Join-Path $ProjectRoot '.story-locks';$lock=Join-Path $lockDir 'repository.lock';$guardPath=Join-Path $lockDir "$GuardId.json";if(-not(Test-Path $lock)-or-not(Test-Path $guardPath)){throw 'Guard is not active.'};$g=Read-PipelineJson $guardPath
if($g.branch){$changed=@(& git -C $ProjectRoot status --porcelain --untracked-files=all);if($changed.Count){throw 'Abort refused because workspace changes remain. Restore or complete them first.'}}
Remove-Item -LiteralPath $guardPath,$lock -Force;[ordered]@{schemaVersion=1;guardId=$GuardId;aborted=$true}|ConvertTo-Json
