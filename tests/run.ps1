#Requires -Version 7.0
[CmdletBinding()]param()
$ErrorActionPreference='Stop';$suites=@(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.tests.ps1' -File|Sort-Object Name);$passed=0
foreach($suite in $suites){Write-Host "Running $($suite.Name)";& pwsh -NoLogo -NoProfile -File $suite.FullName;if(-not $?){throw "Suite failed: $($suite.Name)"};$passed++}
& pwsh -NoLogo -NoProfile -File (Join-Path $PSScriptRoot '../.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1') -OutputFormat Text;if(-not $?){throw 'Repository integrity failed after focused suites.'}
"All $passed focused suites and repository integrity passed."
