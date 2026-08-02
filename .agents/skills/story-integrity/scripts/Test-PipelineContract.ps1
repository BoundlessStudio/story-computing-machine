#Requires -Version 7.0
[CmdletBinding()]param([ValidateSet('Text','Json')][string]$OutputFormat='Text',[string]$ProjectRoot)
$ErrorActionPreference='Stop';if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
. (Join-Path $PSScriptRoot 'PipelineCommon.ps1');$errors=[Collections.Generic.List[string]]::new()
try{
 $contract=Get-PipelineContract $ProjectRoot
 Assert-PipelineFields $contract @('schemaVersion','trustModel','story','lifecycle','release','reviewPass','authority','handoffLedger','promotion','legacyAcceptance','sourceManifest') 'pipeline contract'
 if($contract.schemaVersion-ne2-or$contract.trustModel-cne'git-pr-human-review'){$errors.Add('Pipeline contract identity is invalid.')}
 if($contract.story.schemaVersion-ne2-or$contract.release.schemaVersion-ne3-or$contract.authority.schemaVersion-ne2-or$contract.handoffLedger.schemaVersion-ne3-or$contract.promotion.schemaVersion-ne2-or$contract.sourceManifest.schemaVersion-ne3){$errors.Add('Pipeline record versions are inconsistent.')}
 Assert-PipelineFields $contract.authority @('schemaVersion','fields') 'authority contract';Assert-PipelineFields $contract.promotion @('schemaVersion','states','schemaPath') 'promotion contract';Assert-PipelineFields $contract.legacyAcceptance @('schemaVersion','path') 'legacy acceptance contract';Assert-PipelineFields $contract.sourceManifest @('schemaVersion','verificationStatuses') 'source contract'
 foreach($name in @('story.json','authority.json','handoffs.json','release.json','promotion.json')){
  $path=Join-Path $ProjectRoot "stories/_template/$name";$raw=(Get-Content -LiteralPath $path -Raw).Replace('{{slug}}','template-story').Replace('{{date}}','2026-01-01').Replace('{{title_yaml}}','"Template Story"');$value=$raw|ConvertFrom-Json -Depth 100 -DateKind String
  switch($name){'story.json'{Assert-PipelineFields $value @($contract.story.fields) $name};'authority.json'{Assert-PipelineFields $value @($contract.authority.fields) $name};'handoffs.json'{Assert-PipelineFields $value @($contract.handoffLedger.fields) $name};'release.json'{Assert-PipelineFields $value @($contract.release.fields) $name};'promotion.json'{Assert-PipelineFields $value @('schemaVersion','state','storySlug','authorization','promotionDate','stewardship','deltaDispositions','modifiedFiles','completedAt','result','rollback') $name}}
 }
}catch{$errors.Add($_.Exception.Message)}
$result=[ordered]@{schemaVersion=1;passed=($errors.Count-eq0);errors=@($errors)}
if($OutputFormat-ceq'Json'){$result|ConvertTo-Json -Depth 8}else{if($result.passed){'Pipeline contract passed.'}else{$errors|ForEach-Object{"ERROR: $_"}}}
if(-not$result.passed){exit 1}