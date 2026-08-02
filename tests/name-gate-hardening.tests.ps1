#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$Checker = Join-Path $RepoRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
$FixtureRoot = Join-Path ([IO.Path]::GetTempPath()) (
    'story-name-gate-hardening-' + [Guid]::NewGuid().ToString('N')
)
$script:Passed = 0
$script:Failed = 0

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )

    $Parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }
    [IO.File]::WriteAllText($Path, ($Content -replace "`r`n", "`n"), [Text.UTF8Encoding]::new($false))
}

function Write-Registry {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string[]]$Rows
    )

    $Content = @(
        '# Character name registry', '', '<!-- registry:start -->',
        '| Character / entity | Reserved forms | Story or source | State | Reuse status | Rationale / disambiguation |',
        '| --- | --- | --- | --- | --- | --- |'
    ) + $Rows + @('<!-- registry:end -->', '')
    Write-Utf8File (Join-Path $Root 'stories/NAMES.md') ($Content -join "`n")
}

function Write-Metadata {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Slug,
        [ValidateSet('planning', 'candidate')][string]$Stage
    )

    $Status = if ($Stage -eq 'candidate') { 'candidate' } else { 'in-progress' }
    $Metadata = [ordered]@{
        schemaVersion = 1
        slug = $Slug
        title = 'Fixture'
        created = '2026-08-02'
        stage = $Stage
        status = $Status
        canon = $false
        userDisposition = if ($Stage -eq 'candidate') { 'accepted' } else { 'pending' }
        publish = $false
        promotionDate = $null
    }
    Write-Utf8File (Join-Path $Directory 'story.json') (($Metadata | ConvertTo-Json) + "`n")
}

function New-PlanFixture {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string[]]$RegistryRows,
        [Parameter(Mandatory = $true)][string[]]$PlanRows
    )

    $Root = Join-Path $FixtureRoot $Name
    $Directory = Join-Path $Root "stories/$Slug"
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    Write-Metadata $Directory $Slug 'planning'
    $Plan = @(
        '# Story plan', '', '## Name check', '',
        '| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |',
        '| --- | --- | --- | --- |'
    ) + $PlanRows + @('', '## Proposed inventions', '', 'None.', '')
    Write-Utf8File (Join-Path $Directory '02-story-plan.md') ($Plan -join "`n")
    Write-Registry $Root $RegistryRows
    return $Root
}

function New-FinalFixture {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Body,
        [Parameter(Mandatory = $true)][string]$Inventory,
        [AllowEmptyString()][string]$Allowlist = 'None.'
    )

    $Slug = 'final-audit'
    $Root = Join-Path $FixtureRoot $Name
    $Directory = Join-Path $Root "stories/$Slug"
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    Write-Metadata $Directory $Slug 'candidate'
    Write-Registry $Root @(
        '| Ada Vale | `Ada Vale`; `Ada` | `final-audit` | candidate | unique | Distinct fixture protagonist. |'
    )
    Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Ada Vale | `Ada Vale`; `Ada` | unique | Distinct fixture protagonist. |
'@
    Write-Utf8File (Join-Path $Directory '05-story.md') @"
---
title: "Mara's Return"
slug: "$Slug"
created: 2026-08-02
---

# Mara's Return

$Body
"@
    Write-Utf8File (Join-Path $Directory '06-canon-delta.md') @"
# Proposed canon delta

## New characters or character facts

- **Ada Vale** is the fixture protagonist.

## Final character-facing name inventory

$Inventory

## Reviewed prose name-audit allowlist

$Allowlist

## New locations

None.
"@
    return $Root
}

function Invoke-Checker {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Story,
        [ValidateSet('Plan', 'Final')][string]$Phase,
        [switch]$Json,
        [switch]$SkipConfusable
    )

    $Arguments = @(
        '-NoProfile', '-File', $Checker, '-Story', $Story,
        '-Phase', $Phase, '-ProjectRoot', $Root
    )
    if ($Json) { $Arguments += @('-OutputFormat', 'Json') }
    if ($SkipConfusable) { $Arguments += '-SkipConfusable' }
    $Output = & pwsh @Arguments 2>&1 | Out-String
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $Output.Trim() }
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Invoke-Test {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Body
    )
    try {
        & $Body
        $script:Passed++
        Write-Output "PASS $Name"
    }
    catch {
        $script:Failed++
        Write-Output "FAIL $Name`n  $($_.Exception.Message)"
    }
}

New-Item -ItemType Directory -Path $FixtureRoot -Force | Out-Null
try {
    Invoke-Test 'plan receipt binds artifacts and both registry scopes' {
        $Root = New-PlanFixture 'receipt' 'receipt-story' @(
            '| Ada Vale | `Ada Vale`; `Ada` | `receipt-story` | in-progress | unique | Distinct fixture protagonist. |',
            '| Other Person | `Other Person`; `Other` | `other-story` | candidate | unique | Unrelated comparison identity. |'
        ) @('| Ada Vale | `Ada Vale`; `Ada` | unique | Distinct fixture protagonist. |')
        $Result = Invoke-Checker $Root 'receipt-story' 'Plan' -Json
        Assert-True ($Result.ExitCode -eq 0) $Result.Output
        $Receipt = $Result.Output | ConvertFrom-Json
        foreach ($Field in @(
            'receiptId', 'checkerVersion', 'planSha256', 'scopedRegistrySha256',
            'activeRegistrySha256', 'warnings'
        )) {
            Assert-True ($Field -in @($Receipt.PSObject.Properties.Name)) "Receipt omits $Field."
        }
        Assert-True ($Receipt.checkerVersion -ceq 'story-names/2') 'Unexpected checkerVersion.'
        Assert-True ($Receipt.phase -ceq 'Plan') 'Receipt phase mismatch.'
        Assert-True ($Receipt.receiptId -cmatch '^[a-f0-9]{64}$') 'Invalid receiptId.'
        Assert-True ($Receipt.planSha256 -cmatch '^[a-f0-9]{64}$') 'Invalid planSha256.'
        Assert-True ($Receipt.scopedRegistrySha256 -cmatch '^[a-f0-9]{64}$') 'Invalid scoped digest.'
        Assert-True ($Receipt.activeRegistrySha256 -cmatch '^[a-f0-9]{64}$') 'Invalid active digest.'

        Write-Registry $Root @(
            '| Other Person | `Other Person`; `Other` | `other-story` | candidate | unique | Unrelated comparison identity. |',
            '| Ada Vale | `Ada Vale`; `Ada` | `receipt-story` | in-progress | unique | Distinct fixture protagonist. |'
        )
        $ReorderedResult = Invoke-Checker $Root 'receipt-story' 'Plan' -Json
        Assert-True ($ReorderedResult.ExitCode -eq 0) $ReorderedResult.Output
        $ReorderedReceipt = $ReorderedResult.Output | ConvertFrom-Json
        Assert-True ($ReorderedReceipt.activeRegistrySha256 -ceq $Receipt.activeRegistrySha256 -and
            $ReorderedReceipt.scopedRegistrySha256 -ceq $Receipt.scopedRegistrySha256 -and
            $ReorderedReceipt.receiptId -ceq $Receipt.receiptId) (
            'Registry row order changed a canonical digest or receipt ID.'
        )

        Write-Registry $Root @(
            '| Ada Vale | `Ada Vale`; `Ada` | `receipt-story` | in-progress | unique | Distinct fixture protagonist. |',
            '| Other Person | `Other Person`; `Other` | `other-story` | candidate | unique | Unrelated comparison identity with revised rationale. |'
        )
        $ChangedResult = Invoke-Checker $Root 'receipt-story' 'Plan' -Json
        Assert-True ($ChangedResult.ExitCode -eq 0) $ChangedResult.Output
        $ChangedReceipt = $ChangedResult.Output | ConvertFrom-Json
        Assert-True ($ChangedReceipt.scopedRegistrySha256 -ceq $Receipt.scopedRegistrySha256) (
            'Unrelated registry change altered the scoped digest.'
        )
        Assert-True ($ChangedReceipt.activeRegistrySha256 -cne $Receipt.activeRegistrySha256 -and
            $ChangedReceipt.receiptId -cne $Receipt.receiptId) (
            'Whole-active-registry change did not invalidate the receipt.'
        )
    }

    Invoke-Test 'active lifecycle projection changes do not invalidate reservation digests' {
        $Slug = 'lifecycle-stable'
        $Root = New-PlanFixture 'lifecycle-stable' $Slug @(
            '| Ada Vale | `Ada Vale`; `Ada` | `lifecycle-stable` | in-progress | unique | Distinct fixture protagonist. |'
        ) @('| Ada Vale | `Ada Vale`; `Ada` | unique | Distinct fixture protagonist. |')
        $BeforeResult = Invoke-Checker $Root $Slug 'Plan' -Json
        Assert-True ($BeforeResult.ExitCode -eq 0) $BeforeResult.Output
        $Before = $BeforeResult.Output | ConvertFrom-Json

        Write-Metadata (Join-Path $Root "stories/$Slug") $Slug 'candidate'
        Write-Registry $Root @(
            '| Ada Vale | `Ada Vale`; `Ada` | `lifecycle-stable` | candidate | unique | Distinct fixture protagonist. |'
        )
        $AfterResult = Invoke-Checker $Root $Slug 'Plan' -Json
        Assert-True ($AfterResult.ExitCode -eq 0) $AfterResult.Output
        $After = $AfterResult.Output | ConvertFrom-Json
        Assert-True ($After.scopedRegistrySha256 -ceq $Before.scopedRegistrySha256 -and
            $After.activeRegistrySha256 -ceq $Before.activeRegistrySha256 -and
            $After.receiptId -ceq $Before.receiptId) (
            'A state-only in-progress to candidate transition invalidated reservation identity.'
        )
    }

    Invoke-Test 'plan requires all four exact populated columns' {
        $Root = New-PlanFixture 'blank-column' 'blank-column' @(
            '| Ada | `Ada` | `blank-column` | in-progress | unique | Distinct fixture identity. |'
        ) @('| Ada | `Ada` |  | Distinct fixture identity. |')
        $Result = Invoke-Checker $Root 'blank-column' 'Plan'
        Assert-True ($Result.ExitCode -ne 0 -and
            $Result.Output -match 'populate all four columns') $Result.Output
    }

    foreach ($Collision in @(
        [pscustomobject]@{ Name = 'exact'; Target = 'Mara'; Other = 'Mara'; Pattern = 'Exact collision' },
        [pscustomobject]@{ Name = 'confusable'; Target = 'Ana-Mae'; Other = 'Ana Mae'; Pattern = 'punctuation/spacing-confusable' },
        [pscustomobject]@{ Name = 'reversed'; Target = 'Ada Vale'; Other = 'Vale Ada'; Pattern = 'reversed-form' },
        [pscustomobject]@{ Name = 'close'; Target = 'Fara'; Other = 'Sara'; Pattern = 'close-spelling' }
    )) {
        Invoke-Test "undocumented $($Collision.Name) target collision fails" {
            $Root = New-PlanFixture "collision-$($Collision.Name)" 'collision-story' @(
                "| Target | ``$($Collision.Target)`` | ``collision-story`` | in-progress | unique | Target identity is intended to be distinct. |",
                "| Other | ``$($Collision.Other)`` | ``other-story`` | candidate | unique | Other identity is intended to be distinct. |"
            ) @(
                "| Target | ``$($Collision.Target)`` | unique | Target identity is intended to be distinct. |"
            )
            $Result = Invoke-Checker $Root 'collision-story' 'Plan'
            Assert-True ($Result.ExitCode -ne 0 -and
                $Result.Output -match $Collision.Pattern -and
                $Result.Output -match 'deliberate reuse documentation') $Result.Output
        }
    }

    Invoke-Test 'story-scoped gate cannot bypass confusable comparisons' {
        $Root = New-PlanFixture 'skip-confusable' 'skip-story' @(
            '| Target | `Fara` | `skip-story` | in-progress | unique | Target identity is intended to be distinct. |',
            '| Other | `Sara` | `other-story` | candidate | unique | Other identity is intended to be distinct. |'
        ) @('| Target | `Fara` | unique | Target identity is intended to be distinct. |')
        $Result = Invoke-Checker $Root 'skip-story' 'Plan' -SkipConfusable
        Assert-True ($Result.ExitCode -ne 0 -and
            $Result.Output -match 'not permitted for a story-scoped') $Result.Output
    }

    Invoke-Test 'documented deliberate collision passes with stable row identities' {
        $Root = New-PlanFixture 'deliberate' 'deliberate-story' @(
            '| Target Mara | `Mara` | `deliberate-story` | in-progress | deliberate | Deliberate prompt-required namesake; target wears a red sash and is always called the navigator. |',
            '| Other Mara | `Mara` | `other-story` | candidate | deliberate | Deliberate prompt-required namesake; other identity is historical and always called the archivist. |'
        ) @(
            '| Target Mara | `Mara` | deliberate reuse | Deliberate prompt-required namesake; red sash and navigator role distinguish the target from the historical archivist. |'
        )
        $Result = Invoke-Checker $Root 'deliberate-story' 'Plan' -Json
        Assert-True ($Result.ExitCode -eq 0) $Result.Output
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True (@($Receipt.warnings | Where-Object { $_ -match 'Documented deliberate Exact collision' }).Count -eq 1) (
            'Deliberate collision was not exposed as a receipt warning.'
        )
    }

    Invoke-Test 'same-story namesakes bind by deterministic identity key' {
        $Root = New-PlanFixture 'same-story-deliberate' 'namesake-story' @(
            '| Navigator Mara | `Mara` | `namesake-story` | in-progress | deliberate | Deliberate namesake; the living navigator always wears a red sash. |',
            '| Archivist Mara | `Mara` | `namesake-story` | in-progress | deliberate | Deliberate namesake; the historical archivist appears only in dated records. |'
        ) @(
            '| Navigator Mara | `Mara` | deliberate reuse | Deliberate namesake; a red sash and navigator role distinguish her from the historical archivist. |',
            '| Archivist Mara | `Mara` | deliberate reuse | Deliberate namesake; dated records and the archivist role distinguish her from the living navigator. |'
        )
        $Result = Invoke-Checker $Root 'namesake-story' 'Plan' -Json
        Assert-True ($Result.ExitCode -eq 0) $Result.Output
    }

    Invoke-Test 'final deliberate-collision receipt binds the supporting plan' {
        $Slug = 'final-collision'
        $Root = Join-Path $FixtureRoot 'final-deliberate-collision'
        $Directory = Join-Path $Root "stories/$Slug"
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
        Write-Metadata $Directory $Slug 'candidate'
        Write-Registry $Root @(
            '| Target Mara | `Mara` | `final-collision` | candidate | deliberate | Deliberate namesake; the living navigator always wears a red sash. |',
            '| Other Mara | `Mara` | `other-story` | candidate | deliberate | Deliberate namesake; the historical archivist appears only in dated records. |'
        )
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Target Mara | `Mara` | deliberate reuse | Deliberate namesake; a red sash and navigator role distinguish her from the historical archivist. |
'@
        Write-Utf8File (Join-Path $Directory '05-story.md') @'
---
title: "Final Collision"
slug: "final-collision"
created: 2026-08-02
---

# Final Collision

Mara entered. Later, Mara waited.
'@
        Write-Utf8File (Join-Path $Directory '06-canon-delta.md') @'
# Proposed canon delta

## New characters or character facts

- **Mara** is the fixture navigator.

## Final character-facing name inventory

- **Mara** — Reserved forms: `Mara`

## Reviewed prose name-audit allowlist

None.
'@
        $Result = Invoke-Checker $Root $Slug 'Final' -Json
        Assert-True ($Result.ExitCode -eq 0) $Result.Output
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.planSha256 -cmatch '^[a-f0-9]{64}$') (
            'Final deliberate-collision receipt did not bind the plan artifact.'
        )
    }

    Invoke-Test 'target unresolved reuse always fails' {
        $Root = New-PlanFixture 'unresolved' 'unresolved-story' @(
            '| Ada | `Ada` | `unresolved-story` | in-progress | unresolved | Collision decision remains pending coordinator review. |'
        ) @('| Ada | `Ada` | unresolved | Collision decision remains pending coordinator review. |')
        $Result = Invoke-Checker $Root 'unresolved-story' 'Plan'
        Assert-True ($Result.ExitCode -ne 0 -and
            $Result.Output -match 'unresolved for target identity') $Result.Output
    }

    Invoke-Test 'prose-derived omitted candidate fails independently' {
        $Root = New-FinalFixture 'omitted-prose-name' (
            'Ada Vale met Mara beside the gate. Ada watched Mara leave.'
        ) '- **Ada Vale** — Reserved forms: `Ada Vale`; `Ada`'
        $Result = Invoke-Checker $Root 'final-audit' 'Final'
        Assert-True ($Result.ExitCode -ne 0 -and
            $Result.Output -match "candidate name 'Mara'.*omitted") $Result.Output
    }

    Invoke-Test 'reviewed machine-readable allowlist resolves a non-character candidate' {
        $Allowlist = @'
| Candidate label | Classification | Review rationale |
| --- | --- | --- |
| `Northstar` | setting-term | Reviewed as the moving status light on Ada's control panel, not a person-like entity. |
'@
        $Root = New-FinalFixture 'allowlisted-term' (
            'Ada Vale watched Northstar move across the panel. Ada reset Northstar.'
        ) '- **Ada Vale** — Reserved forms: `Ada Vale`; `Ada`' $Allowlist
        $Result = Invoke-Checker $Root 'final-audit' 'Final' -Json
        Assert-True ($Result.ExitCode -eq 0) $Result.Output
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.proseCandidateEntries -eq 1 -and
            $Receipt.proseAllowlistEntries -eq 1) 'Candidate/allowlist counts are not auditable.'
        Assert-True ($Receipt.storySha256 -cmatch '^[a-f0-9]{64}$' -and
            $Receipt.canonDeltaSha256 -cmatch '^[a-f0-9]{64}$') 'Final artifact hashes are absent.'
    }

    Invoke-Test 'frontmatter and headings do not create prose candidates' {
        $Root = New-FinalFixture 'markup-removal' (
            'Ada Vale entered. Ada waited.'
        ) '- **Ada Vale** — Reserved forms: `Ada Vale`; `Ada`'
        $Result = Invoke-Checker $Root 'final-audit' 'Final' -Json
        Assert-True ($Result.ExitCode -eq 0) $Result.Output
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.proseCandidateEntries -eq 0) 'Heading/frontmatter leaked into candidate audit.'
    }
}
finally {
    if (Test-Path -LiteralPath $FixtureRoot -PathType Container) {
        Remove-Item -LiteralPath $FixtureRoot -Recurse -Force
    }
}

Write-Output "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
