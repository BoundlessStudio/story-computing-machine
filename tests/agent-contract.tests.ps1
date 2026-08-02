#Requires -Version 7.0
. (Join-Path $PSScriptRoot 'TestHelpers.ps1')
$contract=Get-Content (Join-Path $RepoRoot 'schemas/pipeline-contract.json') -Raw|ConvertFrom-Json -Depth 100 -DateKind String
Assert-Equal 2 $contract.story.schemaVersion 'Story contract version differs.';Assert-Equal 3 $contract.release.schemaVersion 'Release contract version differs.';Assert-Equal 2 $contract.authority.schemaVersion 'Authority contract version differs.';Assert-Equal 3 $contract.handoffLedger.schemaVersion 'Ledger contract version differs.';Assert-Equal 2 $contract.promotion.schemaVersion 'Promotion contract version differs.'
$roles=@('canon-librarian','canon-steward','continuity-critic','prose-writer','story-architect','story-editor');foreach($role in $roles){Assert-True (Test-Path (Join-Path $RepoRoot ".codex/agents/$role.toml")) "Missing role $role"}
$steward=Get-Content (Join-Path $RepoRoot '.codex/agents/canon-steward.toml') -Raw;Assert-True ($steward.Contains('only the explicitly assigned topical universe Markdown files')) 'Steward write boundary is missing.'
$critic=Get-Content (Join-Path $RepoRoot '.codex/agents/continuity-critic.toml') -Raw;Assert-True ($critic.Contains('Do not write files')) 'Critic read-only boundary is missing.'
& (Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Test-PipelineContract.ps1') -OutputFormat Text
if(-not $?){throw 'Central contract validation failed.'};'Agent and skill contracts passed.'
