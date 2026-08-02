#Requires -Version 7.0
. (Join-Path $PSScriptRoot 'TestHelpers.ps1');$root=New-TestRoot 'sources'
try{
 Copy-Item (Join-Path $RepoRoot 'sources') -Destination $root -Recurse;$script=Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Test-SourceManifest.ps1';$valid=Invoke-TestScript $script @('-OutputFormat','Json','-ProjectRoot',$root);Assert-True $valid.Succeeded $valid.Output
 $path=Join-Path $root 'sources/MANIFEST.json';$manifest=Get-Content $path -Raw|ConvertFrom-Json -Depth 100 -DateKind String;$manifest.externalRecords[0].logicalLocator='';Write-TestJson $path $manifest;$bad=Invoke-TestScript $script @('-OutputFormat','Json','-ProjectRoot',$root);Assert-True (-not$bad.Succeeded) 'Missing controlled locator was accepted.';'Source manifest tests passed.'
}finally{Remove-TestRoot $root}
