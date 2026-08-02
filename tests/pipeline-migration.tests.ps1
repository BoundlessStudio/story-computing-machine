#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$Migration = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Convert-PipelineRecordsV2.ps1'
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$Root = Join-Path ([IO.Path]::GetTempPath()) ('pipeline-migration-tests-' + [guid]::NewGuid().ToString('N'))
$Utf8 = [Text.UTF8Encoding]::new($false)
$script:Passed = 0
$script:Failed = 0

function Write-File { param([string]$Path, [string]$Content); $Parent=Split-Path -Parent $Path; if(-not(Test-Path $Parent)){New-Item -ItemType Directory -Path $Parent -Force|Out-Null}; [IO.File]::WriteAllText($Path,$Content,$Utf8) }
function New-Fixture {
    param([string]$Name, [ValidateSet('candidate','final')][string]$Status='candidate', [switch]$Current, [switch]$Synthetic)
    $Fixture = Join-Path $Root $Name; $Slug='migration-story'; $Directory=Join-Path $Fixture "stories/$Slug"
    $Metadata=[ordered]@{schemaVersion=1;slug=$Slug;title='Migration Story';created='2026-08-02';stage=$Status;status=$Status;canon=($Status-eq'final');userDisposition='accepted';publish=$false;promotionDate=$(if($Status-eq'final'){'2026-08-02'}else{$null})}
    Write-File (Join-Path $Directory 'story.json') (($Metadata|ConvertTo-Json)+"`n")
    $Release=[ordered]@{schemaVersion=$(if($Current){2}else{1});certified=$true;storySlug=$Slug}
    Write-File (Join-Path $Directory 'release.json') (($Release|ConvertTo-Json)+"`n")
    $Entries = if($Synthetic){@([ordered]@{actor='pipeline_migration';persister='pipeline_migration'})}else{@()}
    Write-File (Join-Path $Directory 'handoffs.json') (([ordered]@{schemaVersion=$(if($Current){2}else{1});storySlug=$Slug;chainHead=$null;entries=$Entries}|ConvertTo-Json -Depth 5)+"`n")
    Write-File (Join-Path $Directory 'authority.json') (([ordered]@{schemaVersion=1;storySlug=$Slug}|ConvertTo-Json)+"`n")
    Write-File (Join-Path $Directory 'promotion.json') (([ordered]@{schemaVersion=1;state=$(if($Status-eq'final'){'completed'}else{'not-prepared'})}|ConvertTo-Json)+"`n")
    $Validator=Join-Path $Fixture '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1'
    Write-File $Validator @"
param(`$Story,`$OutputFormat,`$ProjectRoot)
[ordered]@{passed=`$true;story=`$Story;checkedStories=1}|ConvertTo-Json
"@
    return [pscustomobject]@{Root=$Fixture;Slug=$Slug;Directory=$Directory}
}
function Snapshot([string]$Directory){$h=@{};Get-ChildItem $Directory -Recurse -File|%{$h[$_.FullName]=[Convert]::ToBase64String([IO.File]::ReadAllBytes($_.FullName))};$h}
function Assert-Unchanged($Before){foreach($p in $Before.Keys){if($Before[$p]-cne[Convert]::ToBase64String([IO.File]::ReadAllBytes($p))){throw "Changed: $p"}}}
function Invoke-Migration($Fixture,[switch]$WhatIf){$a=@('-NoLogo','-NoProfile','-NonInteractive','-File',$Migration,'-Story',$Fixture.Slug,'-ProjectRoot',$Fixture.Root);if($WhatIf){$a+='-WhatIf'};$o=@(& $Pwsh @a 2>&1);[pscustomobject]@{ExitCode=$LASTEXITCODE;Output=($o|Out-String).Trim()}}
function Test-Case($Name,[scriptblock]$Body){try{&$Body;$script:Passed++;Write-Host "PASS $Name"}catch{$script:Failed++;Write-Host "FAIL $Name";Write-Host $_.Exception.Message}}
function Assert($Condition,$Message){if(-not$Condition){throw $Message}}

try {
    New-Item -ItemType Directory -Path $Root -Force|Out-Null
    Test-Case 'WhatIf reports required live revalidation without writes' {
        $f=New-Fixture 'whatif';$b=Snapshot $f.Root;$r=Invoke-Migration $f -WhatIf
        Assert ($r.ExitCode-eq0-and$r.Output-match'REVALIDATION_REQUIRED'-and$r.Output-match'continuity_critic') $r.Output;Assert-Unchanged $b
    }
    Test-Case 'legacy candidate migration fails closed byte-for-byte' {
        $f=New-Fixture 'candidate';$b=Snapshot $f.Root;$r=Invoke-Migration $f
        Assert ($r.ExitCode-ne0-and$r.Output-match'cannot be synthesized') $r.Output;Assert-Unchanged $b
    }
    Test-Case 'legacy final migration refuses to fabricate promotion provenance' {
        $f=New-Fixture 'final' -Status final;$b=Snapshot $f.Root;$r=Invoke-Migration $f
        Assert ($r.ExitCode-ne0-and$r.Output-match'canon_steward') $r.Output;Assert-Unchanged $b
    }
    Test-Case 'genuinely current validated records are left unchanged' {
        $f=New-Fixture 'current' -Current;$b=Snapshot $f.Root;$r=Invoke-Migration $f
        Assert ($r.ExitCode-eq0-and$r.Output-match'ALREADY_CURRENT') $r.Output;Assert-Unchanged $b
    }
    Test-Case 'synthetic migration identities can never qualify as current' {
        $f=New-Fixture 'synthetic' -Current -Synthetic;$b=Snapshot $f.Root;$r=Invoke-Migration $f
        Assert ($r.ExitCode-ne0-and$r.Output-match'cannot be synthesized') $r.Output;Assert-Unchanged $b
    }
}
finally { if(Test-Path $Root){Remove-Item $Root -Recurse -Force} }
Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if($script:Failed-gt0){exit 1}
