#Requires -Version 7.0
. (Join-Path $PSScriptRoot 'TestHelpers.ps1');$root=New-TestRoot 'guard'
try{
 Copy-Item (Join-Path $RepoRoot 'schemas') -Destination $root -Recurse;$null=New-Item -ItemType Directory -Path (Join-Path $root 'stories/sample') -Force;$null=New-Item -ItemType Directory -Path (Join-Path $root 'universe') -Force;[IO.File]::WriteAllText((Join-Path $root '.gitignore'),'.story-locks/',[Text.UTF8Encoding]::new($false));Initialize-TestGit $root;Commit-TestGit $root 'base'
 $script=Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/New-StoryHandoffGuard.ps1';$blocked=Invoke-TestScript $script @('-Story','sample','-Actor','canon_librarian','-Mode','RESEARCH_CANON','-AllowedPath','stories/sample/01-canon-brief.md','-InputPath','stories/sample/00-prompt.md','-ProjectRoot',$root);Assert-True (-not$blocked.Succeeded) 'Guard opened on main.';$newStory=Invoke-TestScript (Join-Path $RepoRoot '.agents/skills/story-room/scripts/new-story.ps1') @('-Slug','sample','-Title','Sample','-ProjectRoot',$root);Assert-True (-not$newStory.Succeeded) 'Story scaffold mutation ran on main.';'Handoff guard tests passed.'
}finally{Remove-TestRoot $root}
