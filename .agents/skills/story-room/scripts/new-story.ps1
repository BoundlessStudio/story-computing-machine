#Requires -Version 7.0
[CmdletBinding()]param([Parameter(Mandatory)][ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')][string]$Slug,[Parameter(Mandatory)][string]$Title,[string]$Date=(Get-Date -Format 'yyyy-MM-dd'),[string]$ProjectRoot)
$ErrorActionPreference='Stop';if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
$scripts=Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts';. (Join-Path $scripts 'PipelineCommon.ps1');Assert-ProductionBranch $ProjectRoot
$branch=Get-RepositoryBranch $ProjectRoot;if($branch -and $branch -cne "codex/story-$Slug"){throw "New story '$Slug' must be scaffolded on branch codex/story-$Slug; current branch is $branch."}
if(-not(Test-PipelineDate $Date)){throw 'Date must be YYYY-MM-DD.'};$target=Join-Path $ProjectRoot "stories/$Slug";if(Test-Path $target){throw "Story directory already exists: $target"}
$template=Join-Path $ProjectRoot 'stories/_template';$staging=Join-Path $ProjectRoot ".story-staging/$Slug-$([guid]::NewGuid().ToString('N'))";$indexPath=Join-Path $ProjectRoot 'stories/INDEX.md';$indexBefore=[IO.File]::ReadAllBytes($indexPath)
try{
 $null=New-Item -ItemType Directory -Path $staging -Force;Get-ChildItem -LiteralPath $template -Force|Copy-Item -Destination $staging -Recurse -Force
 Get-ChildItem -LiteralPath $staging -File|ForEach-Object{$text=Get-Content -LiteralPath $_.FullName -Raw;$text=$text.Replace('{{slug}}',$Slug).Replace('{{date}}',$Date).Replace('{{title}}',$Title).Replace('{{title_yaml}}',($Title|ConvertTo-Json -Compress));[IO.File]::WriteAllText($_.FullName,$text.Replace("`r`n","`n").Replace("`r","`n"),[Text.UTF8Encoding]::new($false))}
 $record=Read-PipelineJson(Join-Path $staging 'story.json');$contract=Get-PipelineContract $ProjectRoot;$issues=@(Test-StoryLifecycleRecord $record $contract);if($issues.Count){throw($issues-join'; ')}
 $index=Get-Content $indexPath -Raw;$row="| ``$Slug`` | *$Title* | in-progress | no | pending | no | — | New story on ``codex/story-$Slug``. |";$lines=$index.Replace("`r`n","`n").Split("`n");$headerEnd=($lines|Select-String '^\| ---').LineNumber;if(-not$headerEnd){throw 'INDEX.md table header was not found.'};$insert=$headerEnd;$new=@($lines[0..($insert-1)]+$row+$lines[$insert..($lines.Count-1)]);[IO.File]::WriteAllText($indexPath,(($new-join"`n").TrimEnd()+"`n"),[Text.UTF8Encoding]::new($false))
 Move-Item -LiteralPath $staging -Destination $target
}catch{[IO.File]::WriteAllBytes($indexPath,$indexBefore);if(Test-Path $staging){Remove-Item -LiteralPath $staging -Recurse -Force};if(Test-Path $target){Remove-Item -LiteralPath $target -Recurse -Force};throw}
[ordered]@{schemaVersion=1;story=$Slug;branch=$branch;directory="stories/$Slug";stage='prompt'}|ConvertTo-Json
