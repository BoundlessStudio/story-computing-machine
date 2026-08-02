Set-StrictMode -Version Latest
function Invoke-PipelineTransaction {
 [CmdletBinding()]param([Parameter(Mandatory)][string]$ProjectRoot,[Parameter(Mandatory)][string[]]$Path,[Parameter(Mandatory)][scriptblock]$Mutation)
 . (Join-Path $PSScriptRoot 'PipelineCommon.ps1');Assert-ProductionBranch $ProjectRoot
 $lockDir=Join-Path $ProjectRoot '.story-locks';$null=New-Item -ItemType Directory -Path $lockDir -Force;$lock=Join-Path $lockDir 'repository-transaction.lock';$stream=$null;$snapshot=@{}
 try{
  try{$stream=[IO.File]::Open($lock,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)}catch{throw 'Another pipeline transaction is active.'}
  foreach($relative in @($Path|Sort-Object -Unique)){$full=Join-Path $ProjectRoot $relative;$snapshot[$relative]=if(Test-Path -LiteralPath $full -PathType Leaf){[IO.File]::ReadAllBytes($full)}else{$null}}
  & $Mutation
 }catch{
  foreach($relative in $snapshot.Keys){$full=Join-Path $ProjectRoot $relative;if($null-eq$snapshot[$relative]){if(Test-Path -LiteralPath $full){Remove-Item -LiteralPath $full -Force}}else{$parent=Split-Path -Parent $full;if(-not(Test-Path $parent)){$null=New-Item -ItemType Directory -Path $parent -Force};[IO.File]::WriteAllBytes($full,$snapshot[$relative])}}
  throw
 }finally{if($stream){$stream.Dispose()};if(Test-Path -LiteralPath $lock){Remove-Item -LiteralPath $lock -Force}}
}
function Set-StoryReadmeProjection {
 param([string]$Path,[object]$Record)
 $text=Get-Content -LiteralPath $Path -Raw
 $pairs=[ordered]@{'Current stage'=$Record.stage;'Status'=$Record.status;'Canon'=$(if($Record.canon){'yes'}else{'no'});'User disposition'=$Record.userDisposition;'Publish'=$(if($Record.publish){'yes'}else{'no'});'Promotion date'=$(if($Record.promotionDate){$Record.promotionDate}else{'—'})}
 foreach($key in $pairs.Keys){$text=[regex]::Replace($text,"(?m)^- $([regex]::Escape($key)): .*?$","- ${key}: $($pairs[$key])")}
 [IO.File]::WriteAllText($Path,$text.Replace("`r`n","`n").Replace("`r","`n"),[Text.UTF8Encoding]::new($false))
}
function Set-StoryIndexProjection {
 param([string]$Path,[object]$Record,[string]$Notes)
 $text=Get-Content -LiteralPath $Path -Raw;$date=if($Record.promotionDate){$Record.promotionDate}else{'—'};$row="| ``$($Record.slug)`` | *$($Record.title)* | $($Record.status) | $(if($Record.canon){'yes'}else{'no'}) | $($Record.userDisposition) | $(if($Record.publish){'yes'}else{'no'}) | $date | $Notes |"
 $text=[regex]::Replace($text,"(?m)^\| ``$([regex]::Escape($Record.slug))`` \|.*$",[System.Text.RegularExpressions.MatchEvaluator]{param($m)$row})
 [IO.File]::WriteAllText($Path,$text.Replace("`r`n","`n").Replace("`r","`n"),[Text.UTF8Encoding]::new($false))
}
function Set-StoryRegistryState {
 param([string]$Path,[string]$Story,[string]$State,[string]$RationalePrefix)
 $lines=Get-Content -LiteralPath $Path
 for($i=0;$i-lt$lines.Count;$i++){if($lines[$i]-match'^\| ' -and $lines[$i]-match"``$([regex]::Escape($Story))``"){$parts=@($lines[$i].Trim('|').Split('|')|ForEach-Object{$_.Trim()});if($parts.Count-eq6){$parts[3]=$State;if($RationalePrefix){$parts[5]="$RationalePrefix $($parts[5] -replace '^Rejected literal-fire version;?\s*','')"};$lines[$i]='| '+($parts-join' | ')+' |'}}}
 [IO.File]::WriteAllText($Path,(($lines-join"`n")+"`n"),[Text.UTF8Encoding]::new($false))
}
