#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$NewGuard = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/New-StoryHandoffGuard.ps1'
$CompleteGuard = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Complete-StoryHandoffGuard.ps1'
$AbortGuard = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Abort-StoryHandoffGuard.ps1'
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) ('handoff-guard-tests-' + [guid]::NewGuid().ToString('N'))
$Utf8 = [Text.UTF8Encoding]::new($false)
$script:Passed = 0
$script:Failed = 0

function Write-FixtureFile {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content)
    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) { $null = New-Item -ItemType Directory -Path $Parent -Force }
    [IO.File]::WriteAllText($Path, $Content.Replace("`r`n", "`n").Replace("`r", "`n"), $Utf8)
}

function Hash-File {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function New-GuardFixture {
    param([Parameter(Mandatory = $true)][string]$Name)
    $Root = Join-Path $TestRoot $Name
    $Story = 'guard-story'
    $Directory = Join-Path $Root "stories/$Story"
    foreach ($Relative in @(
        'schemas/pipeline-contract.json', 'schemas/pipeline-contract.schema.json',
        '.agents/skills/story-integrity/scripts/Test-PipelineContract.ps1',
        '.agents/skills/story-integrity/scripts/ReviewContracts.ps1',
        '.agents/skills/story-integrity/scripts/Test-StoryHandoffs.ps1',
        '.agents/skills/canon-maintenance/schemas/promotion.schema.json',
        'stories/_template/story.json', 'stories/_template/release.json',
        'stories/_template/handoffs.json', 'stories/_template/promotion.json'
    )) {
        $Target = Join-Path $Root $Relative
        $Parent = Split-Path -Parent $Target
        if (-not (Test-Path -LiteralPath $Parent -PathType Container)) { $null = New-Item -ItemType Directory -Path $Parent -Force }
        Copy-Item -LiteralPath (Join-Path $RepoRoot $Relative) -Destination $Target
    }
    Write-FixtureFile (Join-Path $Directory '00-prompt.md') "# Prompt`n"
    Write-FixtureFile (Join-Path $Directory '01-canon-brief.md') "# Pending brief`n"
    Write-FixtureFile (Join-Path $Directory 'authority.json') "{`"authority`":`"fixture`"}`n"
    Write-FixtureFile (Join-Path $Directory 'story.json') (@{
        schemaVersion = 1; slug = $Story; title = 'Guard Story'; created = '2026-08-02'
        stage = 'prompt'; status = 'in-progress'; canon = $false
        userDisposition = 'pending'; publish = $false; promotionDate = $null
    } | ConvertTo-Json)
    Write-FixtureFile (Join-Path $Directory 'handoffs.json') (([ordered]@{
        schemaVersion = 2; storySlug = $Story; chainHead = $null; entries = @()
    } | ConvertTo-Json -Depth 16) + "`n")
    return [pscustomobject]@{ Root = $Root; Story = $Story; Directory = $Directory }
}

function Invoke-Process {
    param([Parameter(Mandatory = $true)][string]$Script, [Parameter(Mandatory = $true)][string[]]$Arguments)
    $Items = @(& $Pwsh -NoLogo -NoProfile -NonInteractive -File $Script @Arguments 2>&1)
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = ($Items | Out-String).Trim() }
}

function Open-ResearchGuard {
    param([Parameter(Mandatory = $true)][object]$Fixture)
    $Inputs = @(
        "stories/$($Fixture.Story)/00-prompt.md",
        "stories/$($Fixture.Story)/story.json",
        "stories/$($Fixture.Story)/authority.json",
        "stories/$($Fixture.Story)/handoffs.json"
    )
    try {
        $Output = & $NewGuard -Story $Fixture.Story -Actor 'canon_librarian' -Mode 'RESEARCH_CANON' `
            -AllowedPath "stories/$($Fixture.Story)/01-canon-brief.md" -InputPath $Inputs `
            -ProjectRoot $Fixture.Root
        return ($Output | Out-String) | ConvertFrom-Json
    }
    catch { throw "Guard open failed: $($_.Exception.Message)" }
}

function New-ResearchReport {
    param(
        [Parameter(Mandatory = $true)][object]$Fixture,
        [Parameter(Mandatory = $true)][object]$Guard,
        [ValidateSet('READY', 'HANDOFF_ERROR')][string]$Status,
        [AllowEmptyString()][string]$Body = ''
    )
    $PromptHash = Hash-File (Join-Path $Fixture.Directory '00-prompt.md')
    $AuthorityHash = Hash-File (Join-Path $Fixture.Directory 'authority.json')
    $Lines = [Collections.Generic.List[string]]::new()
    foreach ($Line in @(
        'PERSISTENCE_HANDOFF', "story: $($Fixture.Story)", 'mode: RESEARCH_CANON', "status: $Status",
        'resolutionOwner: coordinator',
        $(if ($Status -ceq 'READY') { 'errorCode: none' } else { 'errorCode: STALE_INPUT' }),
        $(if ($Status -ceq 'READY') { 'resolutionQuestion: none' } else { 'resolutionQuestion: refresh the guarded input' }),
        "target: stories/$($Fixture.Story)/01-canon-brief.md",
        "sourcePrompt: stories/$($Fixture.Story)/00-prompt.md", "sourcePromptSha256: $PromptHash",
        "authorityManifest: stories/$($Fixture.Story)/authority.json", "authorityManifestSha256: $AuthorityHash",
        "handoffLedger: stories/$($Fixture.Story)/handoffs.json",
        "handoffLedgerSha256: $($Guard.handoffLedgerSha256)",
        "handoffLedgerChainHead: $(if ($null -eq $Guard.handoffLedgerChainHead) { 'none' } else { $Guard.handoffLedgerChainHead })"
    )) { $Lines.Add($Line) }
    if ($Status -ceq 'READY') {
        $Lines.Add('BEGIN_FILE_CONTENT')
        foreach ($Line in @($Body.TrimEnd("`n") -split "`n")) { $Lines.Add($Line) }
        $Lines.Add('END_FILE_CONTENT')
    }
    $Lines.Add('modifiedFiles: none')
    $Lines.Add('changeReport: read-only; no files changed')
    return ($Lines -join "`n") + "`n"
}

function Complete-ResearchGuard {
    param([object]$Fixture, [object]$Guard, [string]$Status, [string]$Report)
    return Invoke-Process $CompleteGuard @('-GuardId', $Guard.guardId, '-GuardSha256', $Guard.guardSha256,
        '-Status', $Status, '-ReportText', $Report, '-ProjectRoot', $Fixture.Root)
}

function Assert-True {
    param([Parameter(Mandatory = $true)][bool]$Condition, [Parameter(Mandatory = $true)][string]$Message)
    if (-not $Condition) { throw $Message }
}

function Invoke-Test {
    param([Parameter(Mandatory = $true)][string]$Name, [Parameter(Mandatory = $true)][scriptblock]$Body)
    try { & $Body; $script:Passed++; Write-Host "PASS $Name" }
    catch { $script:Failed++; Write-Host "FAIL $Name"; Write-Host $_.Exception.Message }
}

try {
    $null = New-Item -ItemType Directory -Path $TestRoot -Force
    Invoke-Test 'completes a READY read-only handoff with exact persisted bytes' {
        $Fixture = New-GuardFixture 'ready'
        $Guard = Open-ResearchGuard $Fixture
        $Body = "# Canon brief`n`n> Research status: READY`n"
        Write-FixtureFile (Join-Path $Fixture.Directory '01-canon-brief.md') $Body
        $Report = New-ResearchReport $Fixture $Guard 'READY' $Body
        $Result = Complete-ResearchGuard $Fixture $Guard 'READY' $Report
        Assert-True ($Result.ExitCode -eq 0) "Guard completion failed: $($Result.Output)"
        $Ledger = Get-Content -LiteralPath (Join-Path $Fixture.Directory 'handoffs.json') -Raw | ConvertFrom-Json
        Assert-True (@($Ledger.entries).Count -eq 1 -and $Ledger.entries[0].actor -ceq 'canon_librarian' -and
            $Ledger.entries[0].persister -ceq 'coordinator') 'Ledger actor/persister receipt is wrong.'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $Fixture.Root '.story-locks/repository.lock'))) 'Guard lock was not cleaned up.'
    }
    Invoke-Test 'rejects a substituted guard digest and permits unchanged abort' {
        $Fixture = New-GuardFixture 'digest'
        $Guard = Open-ResearchGuard $Fixture
        $Bad = Invoke-Process $CompleteGuard @('-GuardId', $Guard.guardId, '-GuardSha256', ('0' * 64),
            '-Status', 'HANDOFF_ERROR', '-ReportText', "x`n", '-ProjectRoot', $Fixture.Root)
        Assert-True ($Bad.ExitCode -ne 0 -and $Bad.Output -match 'digest') 'Substituted guard digest was accepted.'
        $Abort = Invoke-Process $AbortGuard @('-GuardId', $Guard.guardId, '-GuardSha256', $Guard.guardSha256, '-ProjectRoot', $Fixture.Root)
        Assert-True ($Abort.ExitCode -eq 0) "Unchanged abort failed: $($Abort.Output)"
    }
    Invoke-Test 'dirty abort refuses until all captured bytes are restored' {
        $Fixture = New-GuardFixture 'dirty-abort'
        $Guard = Open-ResearchGuard $Fixture
        $BriefPath = Join-Path $Fixture.Directory '01-canon-brief.md'
        $Original = [IO.File]::ReadAllBytes($BriefPath)
        Write-FixtureFile $BriefPath "# Changed brief`n"
        $Dirty = Invoke-Process $AbortGuard @('-GuardId', $Guard.guardId, '-GuardSha256', $Guard.guardSha256, '-ProjectRoot', $Fixture.Root)
        Assert-True ($Dirty.ExitCode -ne 0 -and $Dirty.Output -match 'workspace changes remain') 'Dirty abort was accepted.'
        [IO.File]::WriteAllBytes($BriefPath, $Original)
        $Clean = Invoke-Process $AbortGuard @('-GuardId', $Guard.guardId, '-GuardSha256', $Guard.guardSha256, '-ProjectRoot', $Fixture.Root)
        Assert-True ($Clean.ExitCode -eq 0) "Restored abort failed: $($Clean.Output)"
    }
    Invoke-Test 'an error receipt remains unresolved until a later READY same-family repair' {
        $Fixture = New-GuardFixture 'repair'
        $First = Open-ResearchGuard $Fixture
        $ErrorReport = New-ResearchReport $Fixture $First 'HANDOFF_ERROR'
        $ErrorResult = Complete-ResearchGuard $Fixture $First 'HANDOFF_ERROR' $ErrorReport
        Assert-True ($ErrorResult.ExitCode -eq 0) "HANDOFF_ERROR completion failed: $($ErrorResult.Output)"
        $LedgerCheck = Join-Path $Fixture.Root '.agents/skills/story-integrity/scripts/Test-StoryHandoffs.ps1'
        $Unresolved = Invoke-Process $LedgerCheck @('-Story', $Fixture.Story, '-OutputFormat', 'Json', '-ProjectRoot', $Fixture.Root)
        $UnresolvedReceipt = $Unresolved.Output | ConvertFrom-Json
        Assert-True ($UnresolvedReceipt.releaseReady -eq $false -and @($UnresolvedReceipt.unresolved).Count -eq 1) 'Error receipt did not remain unresolved.'

        $Second = Open-ResearchGuard $Fixture
        $Body = "# Canon brief`n`n> Research status: READY`n"
        Write-FixtureFile (Join-Path $Fixture.Directory '01-canon-brief.md') $Body
        $ReadyReport = New-ResearchReport $Fixture $Second 'READY' $Body
        $ReadyResult = Complete-ResearchGuard $Fixture $Second 'READY' $ReadyReport
        Assert-True ($ReadyResult.ExitCode -eq 0) "READY repair failed: $($ReadyResult.Output)"
        $Repaired = Invoke-Process $LedgerCheck @('-Story', $Fixture.Story, '-OutputFormat', 'Json', '-ProjectRoot', $Fixture.Root)
        $RepairedReceipt = $Repaired.Output | ConvertFrom-Json
        Assert-True ($RepairedReceipt.releaseReady -eq $false -and @($RepairedReceipt.unresolved).Count -eq 0) 'Same-family READY did not clear the unresolved receipt.'
    }
    Invoke-Test 'recovers and cleans a fully committed append after an interrupted cleanup' {
        $Fixture = New-GuardFixture 'committed-recovery'
        $Guard = Open-ResearchGuard $Fixture
        $GuardPath = Join-Path $Fixture.Root $Guard.guardPath
        $RetainedGuardBytes = [IO.File]::ReadAllBytes($GuardPath)
        $Body = "# Canon brief`n`n> Research status: READY`n"
        Write-FixtureFile (Join-Path $Fixture.Directory '01-canon-brief.md') $Body
        $Report = New-ResearchReport $Fixture $Guard 'READY' $Body
        $Result = Complete-ResearchGuard $Fixture $Guard 'READY' $Report
        Assert-True ($Result.ExitCode -eq 0) "Initial completion failed: $($Result.Output)"

        $LockDirectory = Join-Path $Fixture.Root '.story-locks'
        $null = New-Item -ItemType Directory -Path $LockDirectory -Force
        [IO.File]::WriteAllBytes($GuardPath, $RetainedGuardBytes)
        Write-FixtureFile (Join-Path $LockDirectory 'repository.lock') "$($Guard.guardId)`n$($Guard.guardSha256)`n"
        $Recovery = Invoke-Process $CompleteGuard @(
            '-GuardId', $Guard.guardId, '-GuardSha256', $Guard.guardSha256,
            '-Status', 'READY', '-ReportText', $Report, '-RecoverCommittedGuard',
            '-ProjectRoot', $Fixture.Root
        )
        Assert-True ($Recovery.ExitCode -eq 0) "Committed-append recovery failed: $($Recovery.Output)"
        $RecoveryReceipt = $Recovery.Output | ConvertFrom-Json
        Assert-True ($RecoveryReceipt.recoveredCommittedAppend -eq $true) 'Recovery did not report a committed append.'
        Assert-True (-not (Test-Path -LiteralPath $GuardPath) -and
            -not (Test-Path -LiteralPath (Join-Path $LockDirectory 'repository.lock'))) 'Recovery did not clean retained guard files.'
    }
}
finally {
    if (Test-Path -LiteralPath $TestRoot -PathType Container) { Remove-Item -LiteralPath $TestRoot -Recurse -Force }
}

Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
