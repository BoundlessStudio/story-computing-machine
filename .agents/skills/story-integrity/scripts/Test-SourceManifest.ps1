#Requires -Version 7.0
[CmdletBinding()]param([ValidateSet('Text','Json')][string]$OutputFormat='Text',[string]$ProjectRoot)
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
. (Join-Path $PSScriptRoot 'PipelineCommon.ps1')
$errors=[Collections.Generic.List[string]]::new();$records=0;$external=0
try{
 $path=Join-Path $ProjectRoot 'sources/MANIFEST.json';$m=Read-PipelineJson $path
 Assert-PipelineFields $m @('schemaVersion','prepared','authority','decisionRecord','records','externalRecords') 'source manifest'
 if($m.schemaVersion -ne 3){$errors.Add('Source manifest schemaVersion must be 3.')}
 if($m.authority -cne 'none'){$errors.Add('Source manifest authority must be none.')}
 if(-not (Test-PipelineDate $m.prepared)){$errors.Add('Source manifest prepared date is invalid.')}
 foreach($item in @($m.records)){
  $records++;try{Assert-PipelineFields $item @('recordId','workTitle','reviewedForm','path','authority','verificationStatus','version','verifiedAt') "source record $($item.recordId)"}catch{$errors.Add($_.Exception.Message)}
  if($item.authority -cne 'none' -or $item.verificationStatus -cne 'verified'){$errors.Add("Source record $($item.recordId) has invalid authority/status.")}
  if([string]::IsNullOrWhiteSpace([string]$item.version) -or -not (Test-PipelineDate $item.verifiedAt)){$errors.Add("Source record $($item.recordId) lacks version/date metadata.")}
  $full=Join-Path $ProjectRoot ([string]$item.path);if(-not (Test-Path -LiteralPath $full -PathType Leaf)){$errors.Add("Source record path is missing: $($item.path)")}
 }
 foreach($item in @($m.externalRecords)){
  $external++;try{Assert-PipelineFields $item @('recordId','workTitle','reviewedForm','logicalLocator','authority','verificationStatus','version','accessedAt','accessRequirements') "external record $($item.recordId)"}catch{$errors.Add($_.Exception.Message)}
  if($item.authority -cne 'none' -or [string]$item.verificationStatus -cnotin @('verified','descriptive-only')){$errors.Add("External record $($item.recordId) has invalid authority/status.")}
  if([string]::IsNullOrWhiteSpace([string]$item.logicalLocator) -or [string]::IsNullOrWhiteSpace([string]$item.version) -or -not (Test-PipelineDate $item.accessedAt) -or [string]::IsNullOrWhiteSpace([string]$item.accessRequirements)){$errors.Add("External record $($item.recordId) lacks controlled locator/version/access metadata.")}
 }
}catch{$errors.Add($_.Exception.Message)}
$result=[ordered]@{schemaVersion=1;passed=($errors.Count -eq 0);records=$records;externalRecords=$external;errors=@($errors)}
if($OutputFormat -ceq 'Json'){$result|ConvertTo-Json -Depth 8}else{if($result.passed){"Source manifest passed ($records local, $external external)."}else{$errors|ForEach-Object{"ERROR: $_"}}}
if(-not $result.passed){exit 1}
