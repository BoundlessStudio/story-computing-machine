#Requires -Version 7.0
. (Join-Path $PSScriptRoot 'TestHelpers.ps1');. (Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/PipelineTransactions.ps1');$root=New-TestRoot 'transaction'
try{
 Initialize-TestGit $root;[IO.File]::WriteAllText((Join-Path $root 'record.json'),"original`n",[Text.UTF8Encoding]::new($false));Commit-TestGit $root 'base';& git -C $root checkout -q -b codex/story-rollback;$before=[IO.File]::ReadAllBytes((Join-Path $root 'record.json'));$failed=$false
 try{Invoke-PipelineTransaction -ProjectRoot $root -Path @('record.json','created.json') -Mutation{[IO.File]::WriteAllText((Join-Path $root 'record.json'),'changed',[Text.UTF8Encoding]::new($false));[IO.File]::WriteAllText((Join-Path $root 'created.json'),'new',[Text.UTF8Encoding]::new($false));throw 'forced failure'}}catch{$failed=$true}
 Assert-True $failed 'Forced transaction failure did not throw.';Assert-True ([Convert]::ToBase64String($before)-ceq[Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $root 'record.json')))) 'Raw preimage was not restored.';Assert-True (-not(Test-Path (Join-Path $root 'created.json'))) 'New file survived rollback.';'Transaction rollback tests passed.'
}finally{Remove-TestRoot $root}
