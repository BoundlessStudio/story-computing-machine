#Requires -Version 7.0
[CmdletBinding()]param([Parameter(Mandatory)][string]$Story,[Parameter(Mandatory)][string]$Actor,[Parameter(Mandatory)][string]$Mode,[Parameter(Mandatory)][string[]]$AllowedPath,[Parameter(Mandatory)][string[]]$InputPath,[string]$ProjectRoot)
$ErrorActionPreference='Stop';if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
. (Join-Path $PSScriptRoot 'PipelineCommon.ps1');Assert-ProductionBranch $ProjectRoot
$contract=Get-PipelineContract $ProjectRoot;$mc=$contract.handoffLedger.modeContracts.PSObject.Properties[$Mode].Value;if($null -eq $mc){throw "Unknown handoff mode: $Mode"};if($Actor -cne $mc.actor){throw 'Actor does not match mode contract.'}
$expectedAllowed=@($mc.allowedOutputs|ForEach-Object{$_.Replace('{story}',$Story)}|Sort-Object);$actualAllowed=@($AllowedPath|ForEach-Object{$_.Replace('\','/')}|Sort-Object)
if(($expectedAllowed -join "`n") -cne ($actualAllowed -join "`n")){throw 'Allowed output paths do not match the mode contract.'}
$expectedInputs=@($mc.requiredInputs|ForEach-Object{$_.Replace('{story}',$Story)}|Sort-Object);$actualInputs=@($InputPath|ForEach-Object{$_.Replace('\','/')}|Sort-Object)
if(($expectedInputs -join "`n") -cne ($actualInputs -join "`n")){throw 'Input paths do not match the mode contract.'};foreach($p in $actualInputs){if(-not(Test-Path -LiteralPath (Join-Path $ProjectRoot $p) -PathType Leaf)){throw "Missing handoff input: $p"}}
$branch=Get-RepositoryBranch $ProjectRoot;if($branch){$dirty=@(& git -C $ProjectRoot status --porcelain --untracked-files=all);if($dirty.Count){throw 'Checkpoint or commit the current branch before opening a specialist handoff.'}}
$lockDir=Join-Path $ProjectRoot '.story-locks';$null=New-Item -ItemType Directory -Path $lockDir -Force;$lock=Join-Path $lockDir 'repository.lock';$id=[guid]::NewGuid().ToString('N')
try{$stream=[IO.File]::Open($lock,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);$bytes=[Text.UTF8Encoding]::new($false).GetBytes($id);$stream.Write($bytes,0,$bytes.Length);$stream.Dispose()}catch{throw 'Another guarded mutation is active.'}
$guard=[ordered]@{schemaVersion=2;guardId=$id;story=$Story;actor=$Actor;persister=[string]$mc.persister;mode=$Mode;createdAt=[DateTimeOffset]::UtcNow.ToString('o');allowedPaths=$actualAllowed;inputs=$actualInputs;branch=$branch}
Write-PipelineJson (Join-Path $lockDir "$id.json") $guard
$guard|ConvertTo-Json -Depth 8
