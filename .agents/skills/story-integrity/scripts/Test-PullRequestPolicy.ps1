#Requires -Version 7.0
[CmdletBinding()]param([string]$BaseRef='origin/main',[string]$HeadRef='HEAD',[ValidateSet('Text','Json')][string]$OutputFormat='Text',[string]$ProjectRoot)
$ErrorActionPreference='Stop';if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
. (Join-Path $PSScriptRoot 'PipelineCommon.ps1')
$errors=[Collections.Generic.List[string]]::new()
function Invoke-GitLines([string[]]$Arguments){$output=@(& git -C $ProjectRoot @Arguments 2>&1);if($LASTEXITCODE-ne0){throw "git $($Arguments -join ' ') failed: $($output -join ' ')"};return @($output|ForEach-Object{[string]$_}|Where-Object{$_})}
function Get-LatestPathCommit([string]$Path){$value=@(Invoke-GitLines @('rev-list','-1',$HeadRef,'--',$Path));if($value.Count){return $value[0]};return $null}
function Test-AtOrAfter([string]$Earlier,[string]$Later){if(-not$Earlier-or-not$Later){return $false};if($Earlier-ceq$Later){return $true};& git -C $ProjectRoot merge-base --is-ancestor $Earlier $Later 2>$null;return $LASTEXITCODE-eq0}
$repositoryBranch=Get-RepositoryBranch $ProjectRoot
$branch=if($repositoryBranch){$repositoryBranch}elseif($env:GITHUB_HEAD_REF){$env:GITHUB_HEAD_REF}else{$null}
if(-not$branch-or$branch-ceq'main'){$errors.Add('Pull-request production validation cannot run as direct main work.')}elseif($branch -cnotmatch '^codex/'){$errors.Add("Production branch '$branch' must use the codex/ prefix.")}
try{$baseLines=@(Invoke-GitLines @('rev-parse',$BaseRef));$baseCommit=$baseLines[0];$null=(Invoke-GitLines @('rev-parse',$HeadRef))}catch{$errors.Add($_.Exception.Message);$baseCommit=$null}
$changed=@();if($baseCommit){try{$changed=@(Invoke-GitLines @('diff','--name-only',"$BaseRef...$HeadRef")|ForEach-Object{$_.Replace('\','/')}|Sort-Object -Unique)}catch{$errors.Add($_.Exception.Message)}}
$changedSet=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal);foreach($item in $changed){$null=$changedSet.Add($item)}
$legacyMigration=($branch -ceq 'codex/pipeline-simplification-and-legacy-acceptance' -and $changedSet.Contains('stories/legacy-acceptance.json'))
$storySlugs=@($changed|ForEach-Object{if($_ -match '^stories/(?<slug>[a-z0-9-]+)/'){$Matches.slug}}|Where-Object{$_ -ne'_template'}|Sort-Object -Unique)
foreach($slug in $storySlugs){
 if($legacyMigration -and -not(Test-Path -LiteralPath (Join-Path $ProjectRoot "stories/$slug/story.json"))){continue}
 $prefix="stories/$slug/";$finalChanged=$changedSet.Contains("${prefix}05-story.md")-or$changedSet.Contains("${prefix}06-canon-delta.md")
 if($finalChanged){foreach($required in @("${prefix}04-review.md","${prefix}release.json","${prefix}story.json","${prefix}README.md",'stories/INDEX.md','stories/NAMES.md')){if(-not$changedSet.Contains($required)){$errors.Add("$slug final artifact changes require co-change: $required")}}}
 if($changedSet.Contains("${prefix}04-review.md")){
  try{$cert=Get-ReviewCertification(Join-Path $ProjectRoot "${prefix}04-review.md");$artifact=$(if([string]$cert.artifact -match '/'){([string]$cert.artifact).Replace('\','/')}else{"${prefix}$($cert.artifact)"});$artifactCommit=Get-LatestPathCommit $artifact;$reviewCommit=Get-LatestPathCommit "${prefix}04-review.md";if(-not(Test-AtOrAfter $artifactCommit $reviewCommit)){$errors.Add("$slug review must be committed at or after $artifact.")}}catch{$errors.Add("${slug}: $($_.Exception.Message)")}
 }
 if($changedSet.Contains("${prefix}release.json")){
  $releaseCommit=Get-LatestPathCommit "${prefix}release.json";$reviewCommit=Get-LatestPathCommit "${prefix}04-review.md";$namesCommit=Get-LatestPathCommit 'stories/NAMES.md'
  if(-not(Test-AtOrAfter $reviewCommit $releaseCommit)){$errors.Add("$slug release must be committed at or after its review.")}
  if(-not(Test-AtOrAfter $namesCommit $releaseCommit)){$errors.Add("$slug release must be committed at or after the relevant name-registry state.")}
 }
 if($changedSet.Contains("${prefix}authority.json") -and $baseCommit){try{$authority=Read-PipelineJson(Join-Path $ProjectRoot "${prefix}authority.json");if($authority.baseCommit-cne$baseCommit){$errors.Add("$slug authority baseCommit does not name the PR base commit.")}}catch{$errors.Add("${slug}: $($_.Exception.Message)")}}
}
$universeChanges=@($changed|Where-Object{$_ -cmatch '^universe/.+\.md$'})
if($universeChanges.Count){
 $promotionChanges=@($changed|Where-Object{$_ -cmatch '^stories/[a-z0-9-]+/promotion\.json$'})
 if($promotionChanges.Count-ne1){$errors.Add('Universe changes require exactly one changed promotion record.')}else{
  try{$promotion=Read-PipelineJson(Join-Path $ProjectRoot $promotionChanges[0]);if($promotion.schemaVersion-ne2-or$promotion.state-cne'completed'-or$promotion.result-cne'PROMOTED'){$errors.Add('Universe changes require a completed v2 promotion.')};if([string]::IsNullOrWhiteSpace([string]$promotion.authorization.requestedBy)-or[string]::IsNullOrWhiteSpace([string]$promotion.stewardship.identity)-or[string]::IsNullOrWhiteSpace([string]$promotion.stewardship.handoffText)){$errors.Add('Promotion authorization or stewardship is incomplete.')};$dispositions=@($promotion.deltaDispositions);if(-not$dispositions.Count-or@($dispositions|Where-Object{$_.disposition-cne'promote'-or[string]::IsNullOrWhiteSpace([string]$_.target)}).Count){$errors.Add('Promotion delta dispositions are incomplete.')};$declared=@($promotion.modifiedFiles|Sort-Object -Unique);if($legacyMigration){if(@($declared|Where-Object{$_ -cnotin $universeChanges}).Count){$errors.Add('Promotion modifiedFiles include paths not changed by the PR.')}}elseif(($declared-join"`n")-cne(@($universeChanges|Sort-Object -Unique)-join"`n")){$errors.Add('Promotion modifiedFiles must exactly match universe changes.')}}catch{$errors.Add("Promotion record invalid: $($_.Exception.Message)")}
 }
}
if(@($changed|Where-Object{$_ -cmatch '^sources/'}).Count){& (Join-Path $PSScriptRoot 'Test-SourceManifest.ps1') -OutputFormat Json -ProjectRoot $ProjectRoot *> $null;$sourceOk=$?;if(-not$sourceOk){$errors.Add('Source changes fail locator/version validation.')}}
$result=[ordered]@{schemaVersion=1;passed=($errors.Count-eq0);branch=$branch;baseRef=$BaseRef;baseCommit=$baseCommit;headRef=$HeadRef;changedPaths=$changed;legacyAcceptanceMigration=$legacyMigration;errors=@($errors)}
if($OutputFormat-ceq'Json'){$result|ConvertTo-Json -Depth 12}else{if($result.passed){"Pull-request policy passed for $($changed.Count) changed path(s)."}else{$errors|ForEach-Object{"ERROR: $_"}}}
if(-not$result.passed){exit 1}