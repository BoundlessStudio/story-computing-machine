#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$NewStoryScript = Join-Path $RepoRoot '.agents/skills/story-room/scripts/new-story.ps1'
$NameScript = Join-Path $RepoRoot '.agents/skills/story-name-validation/scripts/check-story-names.ps1'
$ReleaseScript = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/New-StoryRelease.ps1'
$IntegrityScript = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1'
$PromotionScript = Join-Path $RepoRoot '.agents/skills/canon-maintenance/scripts/Complete-CanonPromotion.ps1'
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) (
    'story-integrity-tests-' + [guid]::NewGuid().ToString('N')
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
        New-Item -ItemType Directory -Path $Parent | Out-Null
    }
    Set-Content -LiteralPath $Path -Value $Content -Encoding utf8NoBOM -NoNewline
}

function Invoke-ExternalScript {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string[]]$Arguments = @()
    )
    $Output = & $Pwsh -NoLogo -NoProfile -File $Path @Arguments 2>&1 | Out-String
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $Output.Trim() }
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) { throw $Message }
}

function Assert-ExitCode {
    param(
        [Parameter(Mandatory = $true)][object]$Result,
        [Parameter(Mandatory = $true)][int]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )
    if ($Result.ExitCode -ne $Expected) {
        throw "$Context expected exit $Expected, got $($Result.ExitCode). Output:`n$($Result.Output)"
    }
}

function Assert-FileBytesEqual {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Context
    )
    Assert-True (
        [Convert]::ToBase64String($Expected) -ceq
            [Convert]::ToBase64String([IO.File]::ReadAllBytes($Path))
    ) "$Context bytes changed."
}

function Invoke-Test {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Body
    )
    try {
        & $Body
        $script:Passed++
        Write-Host "PASS $Name" -ForegroundColor Green
    }
    catch {
        $script:Failed++
        Write-Host "FAIL $Name" -ForegroundColor Red
        Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    }
}

function New-FixtureRepository {
    param([Parameter(Mandatory = $true)][string]$Name)

    $Root = Join-Path $TestRoot $Name
    New-Item -ItemType Directory -Path (Join-Path $Root 'stories') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $RepoRoot 'stories/_template') -Destination (Join-Path $Root 'stories/_template') -Recurse
    foreach ($Skill in @('story-room', 'story-name-validation', 'story-integrity')) {
        $TargetParent = Join-Path $Root '.agents/skills'
        New-Item -ItemType Directory -Path $TargetParent -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $RepoRoot ".agents/skills/$Skill") -Destination (Join-Path $TargetParent $Skill) -Recurse
    }
    return $Root
}

function Get-ReleaseTemplateObject {
    param([Parameter(Mandatory = $true)][string]$Slug)
    return [ordered]@{
        schemaVersion = 1; certified = $false; storySlug = $Slug; certifiedAt = $null
        artifacts = [ordered]@{
            story = [ordered]@{ path = '05-story.md'; sha256 = $null }
            canonDelta = [ordered]@{ path = '06-canon-delta.md'; sha256 = $null }
        }
        review = [ordered]@{
            artifact = $null; pass = 0; verdict = 'PENDING'; reviewer = $null
            unresolvedCritical = $null; unresolvedMajor = $null
        }
        nameCheck = [ordered]@{
            story = $Slug; passed = $false; checkedAt = $null
            scopedRegistrySha256 = $null
        }
    }
}

function Write-Registry {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]]$Rows
    )
    $Content = @(
        '# Character name registry', '', '<!-- registry:start -->',
        '| Character / entity | Reserved forms | Story or source | State | Reuse status | Rationale / disambiguation |',
        '| --- | --- | --- | --- | --- | --- |'
    ) + $Rows + @('<!-- registry:end -->', '')
    Write-Utf8File (Join-Path $Root 'stories/NAMES.md') ($Content -join "`n")
}

function Write-Index {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string[]]$Rows
    )
    $Content = @(
        '# Story index', '',
        '| Story | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |',
        '| --- | --- | --- | --- | --- | --- | --- | --- |'
    ) + $Rows + @('', 'Statuses: `in-progress`, `candidate`, `final`, or `abandoned`.')
    Write-Utf8File (Join-Path $Root 'stories/INDEX.md') ($Content -join "`n")
}

function New-ScaffoldedStory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title
    )
    $Result = Invoke-ExternalScript $NewStoryScript @(
        '-Slug', $Slug, '-Title', $Title, '-ProjectRoot', $Root
    )
    Assert-ExitCode $Result 0 "scaffold $Slug"
    return Join-Path $Root "stories/$Slug"
}

function Set-StoryJson {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][ValidateSet('in-progress', 'candidate', 'final', 'abandoned')][string]$Status,
        [Parameter(Mandatory = $true)][string]$Stage,
        [bool]$Canon = $false,
        [ValidateSet('pending', 'accepted', 'rejected')][string]$Disposition = 'pending',
        [bool]$Publish = $false,
        [AllowNull()][object]$PromotionDate = $null
    )
    $Metadata = [ordered]@{
        schemaVersion = 1; slug = $Slug; title = $Title; created = '2026-08-01'
        stage = $Stage; status = $Status; canon = $Canon
        userDisposition = $Disposition; publish = $Publish
        promotionDate = $PromotionDate
    }
    Write-Utf8File (Join-Path $Directory 'story.json') (($Metadata | ConvertTo-Json -Depth 6) + "`n")
}

function Set-ProductionReadme {
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Stage,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Canon,
        [Parameter(Mandatory = $true)][string]$Disposition,
        [Parameter(Mandatory = $true)][string]$Publish,
        [Parameter(Mandatory = $true)][string]$PromotionDate,
        [bool]$Complete = $false,
        [bool]$Promoted = $false
    )
    $Mark = if ($Complete) { 'x' } else { ' ' }
    $PromotionMark = if ($Promoted) { 'x' } else { ' ' }
    $Checklist = @(
        'Prompt contract captured', 'Canon brief completed', 'Story plan completed',
        'Plan name check passed', 'Complete draft written', 'Draft review passed',
        'Critical and major findings resolved', 'Final story written',
        'Canon delta recorded', 'Final story review passed', 'Final name check passed',
        'Name registry updated', 'Release certificate issued', 'Story index updated'
    ) | ForEach-Object { "- [$Mark] $_" }
    $Content = @(
        "# $Title — production record", '', "- Slug: ``$Slug``",
        '- Created: 2026-08-01', "- Current stage: $Stage", "- Status: $Status",
        "- Canon: $Canon", "- User disposition: $Disposition", "- Publish: $Publish",
        "- Promotion date: $PromotionDate", '', '## Checklist', ''
    ) + $Checklist + @("- [$PromotionMark] Canon promotion explicitly approved (optional)", '')
    Write-Utf8File (Join-Path $Directory 'README.md') ($Content -join "`n")
}

function Set-CompleteStory {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Slug,
        [Parameter(Mandatory = $true)][string]$Title,
        [ValidateSet('candidate', 'final')][string]$Status = 'candidate'
    )
    $Directory = Join-Path $Root "stories/$Slug"
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        $Directory = New-ScaffoldedStory $Root $Slug $Title
    }
    $Canon = $Status -eq 'final'
    $PromotionDate = if ($Canon) { '2026-08-01' } else { $null }
    Set-StoryJson $Directory $Slug $Title $Status $Status $Canon 'accepted' $true $PromotionDate
    Set-ProductionReadme $Directory $Slug $Title $Status $Status $(if ($Canon) { 'yes' } else { 'no' }) 'accepted' 'yes' $(if ($Canon) { '2026-08-01' } else { '—' }) $true $Canon

    Write-Utf8File (Join-Path $Directory '00-prompt.md') "# Prompt contract`n`nA complete fixture prompt."
    Write-Utf8File (Join-Path $Directory '01-canon-brief.md') "# Canon brief`n`nNo conflicts."
    Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Ada Vale | `Ada Vale`; `Ada` | unique | Distinct fixture identity. |

## Proposed inventions

None.
'@
    Write-Utf8File (Join-Path $Directory '03-draft.md') "# $Title`n`nAda Vale completes a full working draft."
    Write-Utf8File (Join-Path $Directory '04-review.md') @'
# Continuity and story review

## Current certification

- Reviewed artifact: `05-story.md`
- Review pass: 2
- Verdict: PASS
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 0
- Updated: 2026-08-01

## Review passes

### Pass 2 — final

- Reviewed artifact: `05-story.md`
- Verdict: PASS
- Reviewer: continuity_critic
- Findings: 0 Critical, 0 Major, 0 Minor, 0 Optional
'@
    $Words = (@('Ada Vale', 'Ada') + (1..130 | ForEach-Object { "word$_" })) -join ' '
    $Front = @(
        '---', ('title: ' + ($Title | ConvertTo-Json -Compress)), "slug: `"$Slug`"",
        'created: 2026-08-01',
        '---', '', "# $Title", '', $Words, ''
    ) -join "`n"
    Write-Utf8File (Join-Path $Directory '05-story.md') $Front
    Write-Utf8File (Join-Path $Directory '06-canon-delta.md') @'
# Proposed canon delta

## New characters or character facts

- **Ada Vale** is the fixture protagonist.

## Final character-facing name inventory

- **Ada Vale** — Reserved forms: `Ada Vale`; `Ada`

## New locations

None.

## New factions or cultural facts

None.

## New rules, capabilities, or costs

None.

## Timeline events

None.

## New glossary terms or aliases

None.

## Name registry updates

- **Ada Vale:** register `Ada Vale`; `Ada`.

## Possible conflicts or retcons

None.

## Recommended promotions

None.
'@
    $StoryDigest = (Get-FileHash -LiteralPath (Join-Path $Directory '05-story.md') -Algorithm SHA256).Hash.ToLowerInvariant()
    $DeltaDigest = (Get-FileHash -LiteralPath (Join-Path $Directory '06-canon-delta.md') -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Utf8File (Join-Path $Directory '04-review.md') @"
# Continuity and story review

## Current certification

- Reviewed artifact: ``05-story.md``
- Artifact SHA-256: $StoryDigest
- Canon delta SHA-256: $DeltaDigest
- Review pass: 2
- Verdict: PASS
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 0
- Updated: 2026-08-01

## Review passes

### Pass 2 — final

- Reviewed artifact: ``05-story.md``
- Artifact SHA-256: $StoryDigest
- Canon delta SHA-256: $DeltaDigest
- Verdict: PASS
- Reviewer: continuity_critic
- Findings: 0 Critical, 0 Major, 0 Minor, 0 Optional
"@
    Write-Utf8File (Join-Path $Directory 'release.json') (((Get-ReleaseTemplateObject $Slug) | ConvertTo-Json -Depth 8) + "`n")
    $RegistryState = if ($Canon) { 'canon' } else { 'candidate' }
    Write-Registry $Root @("| Ada Vale | ``Ada Vale``; ``Ada`` | ``$Slug`` | $RegistryState | unique | Distinct fixture identity. |")
    Write-Index $Root @("| ``$Slug`` | *$Title* | $Status | $(if ($Canon) { 'yes' } else { 'no' }) | accepted | yes | $(if ($Canon) { '2026-08-01' } else { '—' }) | Fixture. |")
    return $Directory
}

New-Item -ItemType Directory -Path $TestRoot | Out-Null
try {
    Invoke-Test 'PowerShell 7 contract is explicit' {
        Assert-True ($PSVersionTable.PSVersion.Major -ge 7) 'Tests require PowerShell 7.'
        $FirstLine = Get-Content -LiteralPath $NewStoryScript -TotalCount 1
        Assert-True ($FirstLine -eq '#Requires -Version 7.0') 'new-story.ps1 lacks an explicit PowerShell 7 requirement.'
        $PromotionFirstLine = Get-Content -LiteralPath $PromotionScript -TotalCount 1
        Assert-True ($PromotionFirstLine -eq '#Requires -Version 7.0') 'Complete-CanonPromotion.ps1 lacks an explicit PowerShell 7 requirement.'
    }

    Invoke-Test 'new-story is transactional and rewrites every placeholder' {
        $Root = New-FixtureRepository 'transaction-success'
        $Result = Invoke-ExternalScript $NewStoryScript @('-Slug', 'safe-story', '-Title', 'Safe Story', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'transactional scaffold'
        $Directory = Join-Path $Root 'stories/safe-story'
        Assert-True (Test-Path -LiteralPath $Directory -PathType Container) 'Final story directory was not created.'
        $Unresolved = Get-ChildItem -LiteralPath $Directory -File | Where-Object Extension -in @('.md', '.json') |
            Select-String -Pattern '{{[^{}]+}}'
        Assert-True ($null -eq $Unresolved) 'Scaffold contains unresolved placeholders.'
        foreach ($File in Get-ChildItem -LiteralPath $Directory -File | Where-Object Extension -in @('.md', '.json')) {
            Assert-True (13 -notin [IO.File]::ReadAllBytes($File.FullName)) "Scaffold file $($File.Name) is not LF-only."
        }
        $Metadata = Get-Content -LiteralPath (Join-Path $Directory 'story.json') -Raw | ConvertFrom-Json
        Assert-True ($Metadata.stage -eq 'prompt' -and $Metadata.status -eq 'in-progress' -and -not $Metadata.canon -and $Metadata.userDisposition -eq 'pending' -and -not $Metadata.publish) 'Scaffold metadata does not use safe initial lifecycle values.'
        Assert-True ('sourceEditions' -notin @($Metadata.PSObject.Properties.Name)) 'Scaffold must not couple story lifecycle to source archives.'
    }

    Invoke-Test 'new-story cleans staging after a rewrite failure and is safely rerunnable' {
        $Root = New-FixtureRepository 'transaction-cleanup'
        Write-Utf8File (Join-Path $Root 'stories/_template/bad.md') '{{unknown-placeholder}}'
        $Failed = Invoke-ExternalScript $NewStoryScript @('-Slug', 'retry-me', '-Title', 'Retry Me', '-ProjectRoot', $Root)
        Assert-True ($Failed.ExitCode -ne 0) 'Expected unresolved placeholder to fail scaffolding.'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $Root 'stories/retry-me'))) 'Failed scaffold left a final directory.'
        $Temps = @(Get-ChildItem -LiteralPath (Join-Path $Root 'stories') -Directory -Filter '.retry-me.tmp.*')
        Assert-True ($Temps.Count -eq 0) 'Failed scaffold left a staging directory.'
        Remove-Item -LiteralPath (Join-Path $Root 'stories/_template/bad.md') -Force
        $Retried = Invoke-ExternalScript $NewStoryScript @('-Slug', 'retry-me', '-Title', 'Retry Me', '-ProjectRoot', $Root)
        Assert-ExitCode $Retried 0 'safe rerun'
    }

    Invoke-Test 'name checker rejects malformed registry rows' {
        $Root = New-FixtureRepository 'malformed-registry'
        $Directory = New-ScaffoldedStory $Root 'row-test' 'Row Test'
        Set-StoryJson $Directory 'row-test' 'Row Test' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') "# Story plan`n`n## Name check`n`nNone."
        Write-Registry $Root @('| Broken | `Broken` | `row-test` | in-progress | unique |')
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'row-test', '-Phase', 'Plan', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'expected 6 cells') 'Malformed registry row was not rejected clearly.'
    }

    Invoke-Test 'global name check emits a JSON receipt for an empty scope' {
        $Root = New-FixtureRepository 'global-name-receipt'
        Write-Registry $Root @('| Global Person | `Global Person` | `some-story` | candidate | unique | Fixture. |')
        $Result = Invoke-ExternalScript $NameScript @('-OutputFormat', 'Json', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'global JSON name check'
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.phase -eq 'Registry' -and $Receipt.scopedRegistrySha256 -match '^[a-f0-9]{64}$') 'Global receipt is incomplete.'
    }

    Invoke-Test 'name checker parses real delta syntax and final inventory' {
        $Root = New-FixtureRepository 'real-delta'
        $null = Set-CompleteStory $Root 'delta-story' 'Delta Story'
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'delta-story', '-Phase', 'Final', '-OutputFormat', 'Json', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'real delta final name check'
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.phase -eq 'Final' -and $Receipt.inventoryEntries -eq 1 -and $Receipt.storySha256 -match '^[a-f0-9]{64}$') 'Final name receipt is incomplete.'
    }

    Invoke-Test 'name checker rejects explanatory prose in final inventory rows' {
        $Root = New-FixtureRepository 'final-inventory-schema'
        $Directory = Set-CompleteStory $Root 'inventory-story' 'Inventory Story'
        $DeltaPath = Join-Path $Directory '06-canon-delta.md'
        $Delta = Get-Content -LiteralPath $DeltaPath -Raw
        $Delta = $Delta.Replace(
            '- **Ada Vale** — Reserved forms: `Ada Vale`; `Ada`',
            '- **Ada Vale** — Represented identity: protagonist. Reserved forms: `Ada Vale`; `Ada`'
        )
        Write-Utf8File $DeltaPath $Delta
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'inventory-story', '-Phase', 'Final', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'Malformed final name inventory row') 'Explanatory prose bypassed the strict final inventory schema.'
    }

    Invoke-Test 'name checker matches character forms case-insensitively' {
        $Root = New-FixtureRepository 'name-case'
        $Directory = Set-CompleteStory $Root 'case-story' 'Case Story'
        $FinalPath = Join-Path $Directory '05-story.md'
        $Final = (Get-Content -LiteralPath $FinalPath -Raw).Replace('Ada Vale', "ADA`nVALE")
        Write-Utf8File $FinalPath $Final
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'case-story', '-Phase', 'Final', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'case-insensitive final name check'
    }

    Invoke-Test 'name checker rejects inventory forms absent from prose and prose forms absent from inventory' {
        $Root = New-FixtureRepository 'missing-names'
        $Directory = Set-CompleteStory $Root 'missing-story' 'Missing Story'
        Write-Registry $Root @('| Ada Vale | `Ada Vale`; `Ada`; `Ace`; `Nightglass` | `missing-story` | candidate | unique | Distinct fixture identity. |')
        $Final = Get-Content -LiteralPath (Join-Path $Directory '05-story.md') -Raw
        Write-Utf8File (Join-Path $Directory '05-story.md') ($Final + "`nAce arrived.`n")
        $Delta = Get-Content -LiteralPath (Join-Path $Directory '06-canon-delta.md') -Raw
        $Delta = $Delta.Replace('`Ada Vale`; `Ada`', '`Ada Vale`; `Ada`; `Nightglass`')
        Write-Utf8File (Join-Path $Directory '06-canon-delta.md') $Delta
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'missing-story', '-Phase', 'Final', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match "Nightglass.*does not appear" -and
            $Result.Output -match "Ace.*inventory omits") 'Missing prose/inventory reconciliation defects were not both reported.'
    }

    Invoke-Test 'story scope matches exact slug rather than a prefix' {
        $Root = New-FixtureRepository 'exact-scope'
        $Directory = New-ScaffoldedStory $Root 'fox' 'Fox'
        Set-StoryJson $Directory 'fox' 'Fox' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Fara | `Fara` | unique | Exact story row. |
'@
        Write-Registry $Root @(
            '| Fara | `Fara` | `fox` | in-progress | unique | Exact story row. |',
            '| Sara | `Sara` | `unrelated-story` | candidate | unique | Close but distinct fixture form. |',
            '| Kai One | `Kai` | `foxglove` | candidate | unresolved | Unrelated collision one. |',
            '| Kai Two | `Kai` | `foxglove-two` | candidate | unresolved | Unrelated collision two. |'
        )
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'fox', '-Phase', 'Plan', '-Strict', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'exact slug scope'
        Assert-True ($Result.Output -match 'warning' -and $Result.Output -match 'close-spelling') 'Unrelated collision and close spelling should be reported as warnings.'
    }

    Invoke-Test 'released name reservations remain searchable without creating active collisions' {
        $Root = New-FixtureRepository 'released-name-reservation'
        $Directory = New-ScaffoldedStory $Root 'active-name' 'Active Name'
        Set-StoryJson $Directory 'active-name' 'Active Name' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Lena | `Lena` | unique | The released reservation does not create a live identity collision. |
'@
        Write-Registry $Root @(
            '| Active Lena | `Lena` | `active-name` | in-progress | unique | Current production identity. |',
            '| Retired Lena | `Lena` | released reservation | released | unique | Searchable production memory only. |'
        )
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'active-name', '-Phase', 'Plan', '-Strict', '-OutputFormat', 'Json', '-ProjectRoot', $Root)
        Assert-ExitCode $Result 0 'released reservation collision scope'
        $Receipt = $Result.Output | ConvertFrom-Json
        Assert-True ($Receipt.registryEntries -eq 2 -and $Receipt.inventoryEntries -eq 1) 'Released reservation disappeared from searchable registry memory.'
    }

    Invoke-Test 'name checker rejects prose in the architect Name check contract' {
        $Root = New-FixtureRepository 'architect-name-schema'
        $Directory = New-ScaffoldedStory $Root 'schema-story' 'Schema Story'
        Set-StoryJson $Directory 'schema-story' 'Schema Story' 'in-progress' 'planning'
        Write-Utf8File (Join-Path $Directory '02-story-plan.md') @'
# Story plan

## Name check

The names below were reviewed.

| Character/entity | Reserved forms used in prose | Registry result | Reuse rationale and reader disambiguation |
| --- | --- | --- | --- |
| Ada Vale | `Ada Vale`; `Ada` | unique | Fixture identity. |
'@
        Write-Registry $Root @('| Ada Vale | `Ada Vale`; `Ada` | `schema-story` | in-progress | unique | Fixture identity. |')
        $Result = Invoke-ExternalScript $NameScript @('-Story', 'schema-story', '-Phase', 'Plan', '-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'Unexpected content in plan Name check table') 'Architect-shaped free text bypassed the exact Name check schema.'
    }

    Invoke-Test 'automatic name phase rejects unsynchronized lifecycle metadata' {
        $Root = New-FixtureRepository 'name-phase-lifecycle-sync'
        $Directory = Set-CompleteStory $Root 'phase-story' 'Phase Story'
        $MetadataPath = Join-Path $Directory 'story.json'
        $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
        $Metadata.stage = 'planning'
        Write-Utf8File $MetadataPath (($Metadata | ConvertTo-Json -Depth 6) + "`n")

        $Result = Invoke-ExternalScript $NameScript @(
            '-Story', 'phase-story', '-Phase', 'Auto', '-ProjectRoot', $Root
        )
        Assert-True (
            $Result.ExitCode -ne 0 -and
            $Result.Output -match 'Cannot infer a name-check phase from invalid lifecycle state'
        ) 'Auto name phase accepted a candidate status with a planning stage.'
    }

    Invoke-Test 'story metadata rejects unknown provenance-shaped properties' {
        $Root = New-FixtureRepository 'exact-story-schema'
        $Directory = New-ScaffoldedStory $Root 'schema-story' 'Schema Story'
        Write-Registry $Root @()
        Write-Index $Root @('| `schema-story` | *Schema Story* | in-progress | no | pending | no | — | Fixture. |')
        $MetadataPath = Join-Path $Directory 'story.json'
        $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
        $Metadata | Add-Member -NotePropertyName sourceProvenance -NotePropertyValue @{
            kind = 'archive'
        }
        Write-Utf8File $MetadataPath (($Metadata | ConvertTo-Json -Depth 6) + "`n")

        $Result = Invoke-ExternalScript $IntegrityScript @(
            '-Story', 'schema-story', '-ProjectRoot', $Root
        )
        Assert-True (
            $Result.ExitCode -ne 0 -and
            $Result.Output -match "story.json contains unknown property 'sourceProvenance'"
        ) 'Integrity accepted an arbitrary story provenance property.'
    }

    Invoke-Test 'uncertified release rejects unknown fields at every object level' {
        $Root = New-FixtureRepository 'exact-uncertified-release-schema'
        $Directory = New-ScaffoldedStory $Root 'release-schema-story' 'Release Schema Story'
        Write-Registry $Root @()
        Write-Index $Root @('| `release-schema-story` | *Release Schema Story* | in-progress | no | pending | no | — | Fixture. |')
        $ReleasePath = Join-Path $Directory 'release.json'
        $Baseline = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json

        $TopLevel = $Baseline | ConvertTo-Json -Depth 8 | ConvertFrom-Json
        $TopLevel | Add-Member -NotePropertyName sourceProvenance -NotePropertyValue 'archive'
        Write-Utf8File $ReleasePath (($TopLevel | ConvertTo-Json -Depth 8) + "`n")
        $TopResult = Invoke-ExternalScript $IntegrityScript @(
            '-Story', 'release-schema-story', '-ProjectRoot', $Root
        )
        Assert-True (
            $TopResult.ExitCode -ne 0 -and
            $TopResult.Output -match "release.json contains unknown property 'sourceProvenance'"
        ) 'Uncertified release accepted an unknown top-level field.'

        $Nested = $Baseline | ConvertTo-Json -Depth 8 | ConvertFrom-Json
        $Nested.review | Add-Member -NotePropertyName sourceClass -NotePropertyValue 'imported'
        Write-Utf8File $ReleasePath (($Nested | ConvertTo-Json -Depth 8) + "`n")
        $NestedResult = Invoke-ExternalScript $IntegrityScript @(
            '-Story', 'release-schema-story', '-ProjectRoot', $Root
        )
        Assert-True (
            $NestedResult.ExitCode -ne 0 -and
            $NestedResult.Output -match "release.json review contains unknown property 'sourceClass'"
        ) 'Uncertified release accepted an unknown nested field.'
    }

    Invoke-Test 'release certificate is invalidated by story-byte changes' {
        $Root = New-FixtureRepository 'hash-invalidation'
        $Directory = Set-CompleteStory $Root 'hash-story' 'Hash Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'hash-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'release issuance'
        $Valid = Invoke-ExternalScript $IntegrityScript @('-Story', 'hash-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Valid 0 'fresh release validation'
        $Final = Get-Content -LiteralPath (Join-Path $Directory '05-story.md') -Raw
        $FirstLf = $Final.IndexOf("`n", [StringComparison]::Ordinal)
        $Mixed = $Final.Substring(0, $FirstLf) + "`r`n" + $Final.Substring($FirstLf + 1) + "`nA harmless byte change.`n"
        Write-Utf8File (Join-Path $Directory '05-story.md') $Mixed
        $Stale = Invoke-ExternalScript $IntegrityScript @('-Story', 'hash-story', '-ProjectRoot', $Root)
        Assert-True ($Stale.ExitCode -ne 0 -and $Stale.Output -match 'certificate is stale' -and $Stale.Output -match 'LF only') 'Mixed-EOL story edit did not invalidate release hash and line-ending policy.'
    }

    Invoke-Test 'release issuer refuses bytes changed after review' {
        $Root = New-FixtureRepository 'review-hash-binding'
        $Directory = Set-CompleteStory $Root 'reviewed-story' 'Reviewed Story'
        $Final = Get-Content -LiteralPath (Join-Path $Directory '05-story.md') -Raw
        Write-Utf8File (Join-Path $Directory '05-story.md') ($Final + "`nChanged after the recorded review.`n")
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'reviewed-story', '-ProjectRoot', $Root)
        Assert-True ($Issued.ExitCode -ne 0 -and $Issued.Output -match 'differ from the reviewed hashes') 'Issuer certified bytes that changed after review.'
    }

    Invoke-Test 'integrity and Pages share the UTC release timestamp contract' {
        $Root = New-FixtureRepository 'release-utc-contract'
        $null = Set-CompleteStory $Root 'utc-story' 'UTC Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'utc-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'UTC release issuance'
        $ReleasePath = Join-Path $Root 'stories/utc-story/release.json'
        $ReleaseRaw = Get-Content -LiteralPath $ReleasePath -Raw
        $ReleaseDocument = [Text.Json.JsonDocument]::Parse($ReleaseRaw)
        $CertifiedAtText = $ReleaseDocument.RootElement.GetProperty('certifiedAt').GetString()
        $NameCheckedAtText = $ReleaseDocument.RootElement.GetProperty('nameCheck').GetProperty('checkedAt').GetString()
        $ReleaseDocument.Dispose()
        Assert-True ([DateTimeOffset]::Parse($CertifiedAtText).Offset -eq [TimeSpan]::Zero) 'Release certifiedAt is not UTC.'
        Assert-True ([DateTimeOffset]::Parse($NameCheckedAtText).Offset -eq [TimeSpan]::Zero) 'Release nameCheck.checkedAt is not UTC.'
        $Release = $ReleaseRaw | ConvertFrom-Json
        $Release.nameCheck.checkedAt = '2026-08-01T12:00:00-04:00'
        Write-Utf8File $ReleasePath ($Release | ConvertTo-Json -Depth 8)
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-Story', 'utc-story', '-ProjectRoot', $Root)
        Assert-True ($Invalid.ExitCode -ne 0 -and $Invalid.Output -match 'nameCheck.checkedAt must be an ISO-8601 UTC timestamp') 'Integrity accepted a non-UTC release receipt that the Pages build rejects.'
    }

    Invoke-Test 'final frontmatter rejects mutable lifecycle fields' {
        $Root = New-FixtureRepository 'immutable-frontmatter'
        $Directory = Set-CompleteStory $Root 'immutable-story' 'Immutable Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'immutable-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'immutable-frontmatter release issuance'
        $StoryPath = Join-Path $Directory '05-story.md'
        $Content = Get-Content -LiteralPath $StoryPath -Raw
        $Content = $Content.Replace('created: 2026-08-01', "status: candidate`ncreated: 2026-08-01")
        Write-Utf8File $StoryPath $Content
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-Story', 'immutable-story', '-ProjectRoot', $Root)
        Assert-True ($Invalid.ExitCode -ne 0 -and $Invalid.Output -match "frontmatter contains mutable or unknown field 'status'") 'Integrity accepted lifecycle state inside reviewed story frontmatter.'
    }

    Invoke-Test 'repository validation rejects index and directory drift' {
        $Root = New-FixtureRepository 'index-drift'
        $null = Set-CompleteStory $Root 'indexed-story' 'Indexed Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @('-Story', 'indexed-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Issued 0 'index fixture release issuance'
        Write-Index $Root @(
            '| `indexed-story` | *Indexed Story* | candidate | no | accepted | yes | — | Fixture. |',
            '| `orphan-story` | *Orphan Story* | in-progress | no | pending | no | — | Drift. |'
        )
        $Result = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match "row 'orphan-story'.*no story directory") 'Index-only story was not rejected.'
    }

    Invoke-Test 'neutral source archive enforces exact schemas and both current and reviewed digests' {
        $Root = New-FixtureRepository 'neutral-source-archive'
        $null = New-ScaffoldedStory $Root 'ordinary-story' 'Ordinary Story'
        Write-Registry $Root @('| Ordinary Person | `Ordinary Person` | `ordinary-story` | in-progress | unique | Fixture. |')
        Write-Index $Root @('| `ordinary-story` | *Ordinary Story* | in-progress | no | pending | no | — | Fixture. |')
        Write-Utf8File (Join-Path $Root 'sources/decisions/archive.md') "# Archive decision`n"
        $RecordPath = Join-Path $Root 'sources/records/r1/record.md'
        Write-Utf8File $RecordPath "line one`nline two`n"
        $CurrentDigest = (Get-FileHash -LiteralPath $RecordPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $CrlfBytes = [Text.UTF8Encoding]::new($false).GetBytes("line one`r`nline two`r`n")
        $HistoricalDigest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($CrlfBytes)).ToLowerInvariant()
        $Manifest = [ordered]@{
            schemaVersion = 1; prepared = '2026-08-01'; authority = 'none'
            decisionRecord = 'sources/decisions/archive.md'
            records = @([ordered]@{
                recordId = 'R1'; workTitle = 'Record One'; reviewedForm = 'Fixture source'
                path = 'sources/records/r1/record.md'; sha256 = $CurrentDigest
                reviewedSha256 = $HistoricalDigest
                authority = 'none'; historicalRevision = ('a' * 40)
                historicalBlobOid = ('b' * 40)
            })
            externalRecords = @([ordered]@{
                recordId = 'R2'; workTitle = 'External Record'; reviewedForm = 'Fixture source'
                logicalLocator = 'archive/external-record.md'; authority = 'none'
            })
        }
        Write-Utf8File (Join-Path $Root 'sources/MANIFEST.json') (($Manifest | ConvertTo-Json -Depth 8) + "`n")
        $Valid = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-ExitCode $Valid 0 'neutral archive exact-schema validation'
        $Manifest.records[0].sha256 = ('0' * 64)
        Write-Utf8File (Join-Path $Root 'sources/MANIFEST.json') (($Manifest | ConvertTo-Json -Depth 8) + "`n")
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-True ($Invalid.ExitCode -ne 0 -and $Invalid.Output -match 'sha256 digest does not match current raw bytes') 'Invalid neutral archive current-byte digest was not rejected.'

        $Manifest.records[0].sha256 = $CurrentDigest
        $Manifest.externalRecords[0]['intendedUse'] = 'classified input'
        Write-Utf8File (Join-Path $Root 'sources/MANIFEST.json') (($Manifest | ConvertTo-Json -Depth 8) + "`n")
        $Classified = Invoke-ExternalScript $IntegrityScript @('-ProjectRoot', $Root)
        Assert-True (
            $Classified.ExitCode -ne 0 -and
            $Classified.Output -match "external record 'R2' contains unknown property 'intendedUse'"
        ) 'Neutral external source record accepted a classification field.'
    }

    Invoke-Test 'canon promotion finalizer updates one exact story and preserves reviewed bytes' {
        $Root = New-FixtureRepository 'canon-promotion-success'
        $Directory = Set-CompleteStory $Root 'promotion-story' 'Promotion Story'
        $null = New-ScaffoldedStory $Root 'promotion-story-two' 'Promotion Story Two'
        Write-Registry $Root @(
            '| Ada Vale | `Ada Vale`; `Ada` | `promotion-story` | candidate | unique | Distinct fixture identity. |',
            '| Other Person | `Other Person` | `promotion-story-two` | in-progress | unique | Prefix-similar story must remain untouched. |'
        )
        $OtherIndexRow = '| `promotion-story-two` | *Promotion Story Two* | in-progress | no | pending | no | — | Unrelated fixture. |'
        Write-Index $Root @(
            '| `promotion-story` | *Promotion Story* | candidate | no | accepted | yes | — | Promotion fixture. |',
            $OtherIndexRow
        )
        $UniversePath = Join-Path $Root 'universe/sentinel.md'
        Write-Utf8File $UniversePath "# Sentinel`n`nUniverse bytes are outside primary finalization.`n"
        $UniverseBefore = [IO.File]::ReadAllBytes($UniversePath)

        $Issued = Invoke-ExternalScript $ReleaseScript @(
            '-Story', 'promotion-story', '-ProjectRoot', $Root
        )
        Assert-ExitCode $Issued 0 'candidate release issuance for promotion'
        $ReleasePath = Join-Path $Directory 'release.json'
        $InitialReleaseBytes = [IO.File]::ReadAllBytes($ReleasePath)
        $InitialRelease = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json
        $StoryPath = Join-Path $Directory '05-story.md'
        $DeltaPath = Join-Path $Directory '06-canon-delta.md'
        $StoryBefore = [IO.File]::ReadAllBytes($StoryPath)
        $DeltaBefore = [IO.File]::ReadAllBytes($DeltaPath)
        $StoryHashBefore = (Get-FileHash -LiteralPath $StoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $DeltaHashBefore = (Get-FileHash -LiteralPath $DeltaPath -Algorithm SHA256).Hash.ToLowerInvariant()

        $Promoted = Invoke-ExternalScript $PromotionScript @(
            '-Story', 'promotion-story', '-PromotionDate', '2026-08-02',
            '-ProjectRoot', $Root
        )
        Assert-ExitCode $Promoted 0 'canon promotion finalization'
        Assert-True (
            $Promoted.Output -match 'Reviewed artifacts unchanged' -and
            $Promoted.Output -match 'result: PROMOTED'
        ) 'Promotion did not report its artifact immutability proof and promoted result.'

        $Metadata = Get-Content -LiteralPath (Join-Path $Directory 'story.json') -Raw | ConvertFrom-Json
        Assert-True (
            $Metadata.stage -eq 'final' -and $Metadata.status -eq 'final' -and
            $Metadata.canon -eq $true -and $Metadata.userDisposition -eq 'accepted' -and
            $Metadata.publish -eq $true -and $Metadata.promotionDate -eq '2026-08-02'
        ) 'Promoted story metadata is not the required final state or publish was not preserved.'
        $Readme = Get-Content -LiteralPath (Join-Path $Directory 'README.md') -Raw
        Assert-True (
            $Readme -match '(?m)^- Current stage: final$' -and
            $Readme -match '(?m)^- Status: final$' -and
            $Readme -match '(?m)^- Canon: yes$' -and
            $Readme -match '(?m)^- User disposition: accepted$' -and
            $Readme -match '(?m)^- Publish: yes$' -and
            $Readme -match '(?m)^- Promotion date: 2026-08-02$' -and
            $Readme -match '(?m)^- \[x\] Canon promotion explicitly approved \(optional\)$'
        ) 'Promoted README lifecycle or checklist is incomplete.'

        $Index = Get-Content -LiteralPath (Join-Path $Root 'stories/INDEX.md') -Raw
        Assert-True ($Index.Contains(
            '| `promotion-story` | *Promotion Story* | final | yes | accepted | yes | 2026-08-02 | Promotion fixture. |',
            [StringComparison]::Ordinal
        )) 'Exact promotion-story index row was not finalized.'
        Assert-True ($Index.Contains($OtherIndexRow, [StringComparison]::Ordinal)) 'Prefix-similar index row changed.'
        $Names = Get-Content -LiteralPath (Join-Path $Root 'stories/NAMES.md') -Raw
        Assert-True ($Names.Contains(
            '| Ada Vale | `Ada Vale`; `Ada` | `promotion-story` | canon | unique | Distinct fixture identity. |',
            [StringComparison]::Ordinal
        )) 'Exact story registry row was not promoted to canon.'
        Assert-True ($Names.Contains(
            '| Other Person | `Other Person` | `promotion-story-two` | in-progress | unique | Prefix-similar story must remain untouched. |',
            [StringComparison]::Ordinal
        )) 'Prefix-similar registry row changed.'

        Assert-FileBytesEqual $StoryBefore $StoryPath 'Promotion 05-story.md'
        Assert-FileBytesEqual $DeltaBefore $DeltaPath 'Promotion 06-canon-delta.md'
        Assert-FileBytesEqual $UniverseBefore $UniversePath 'Promotion universe sentinel'
        $FinalReleaseBytes = [IO.File]::ReadAllBytes($ReleasePath)
        Assert-True (
            [Convert]::ToBase64String($InitialReleaseBytes) -cne
                [Convert]::ToBase64String($FinalReleaseBytes)
        ) 'Promotion did not reissue release.json.'
        $FinalRelease = Get-Content -LiteralPath $ReleasePath -Raw | ConvertFrom-Json
        Assert-True (
            $FinalRelease.certified -eq $true -and
            $FinalRelease.artifacts.story.sha256 -ceq $StoryHashBefore -and
            $FinalRelease.artifacts.canonDelta.sha256 -ceq $DeltaHashBefore -and
            $FinalRelease.nameCheck.scopedRegistrySha256 -cne
                $InitialRelease.nameCheck.scopedRegistrySha256
        ) 'Reissued release does not bind unchanged artifacts and the promoted registry state.'

        foreach ($Path in @(
            (Join-Path $Directory 'story.json'), $ReleasePath,
            (Join-Path $Directory 'README.md'),
            (Join-Path $Root 'stories/INDEX.md'),
            (Join-Path $Root 'stories/NAMES.md')
        )) {
            $Bytes = [IO.File]::ReadAllBytes($Path)
            Assert-True (13 -notin $Bytes) "$Path was not written with LF-only line endings."
            Assert-True (-not ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xef -and
                $Bytes[1] -eq 0xbb -and $Bytes[2] -eq 0xbf)) "$Path contains a UTF-8 BOM."
        }
    }

    Invoke-Test 'canon promotion finalizer rolls every production record back after post-write failure' {
        $Root = New-FixtureRepository 'canon-promotion-rollback'
        $Directory = Set-CompleteStory $Root 'rollback-story' 'Rollback Story'
        $Issued = Invoke-ExternalScript $ReleaseScript @(
            '-Story', 'rollback-story', '-ProjectRoot', $Root
        )
        Assert-ExitCode $Issued 0 'rollback candidate release issuance'

        Write-Index $Root @(
            '| `rollback-story` | *Rollback Story* | candidate | no | accepted | yes | — | Rollback fixture. |',
            '| `orphan-after-write` | *Orphan After Write* | in-progress | no | pending | no | — | Forces repository-only validation failure. |'
        )
        $ProductionPaths = @(
            (Join-Path $Directory 'story.json'),
            (Join-Path $Directory 'release.json'),
            (Join-Path $Directory 'README.md'),
            (Join-Path $Root 'stories/INDEX.md'),
            (Join-Path $Root 'stories/NAMES.md')
        )
        $Snapshots = @($ProductionPaths | ForEach-Object {
            [pscustomobject]@{ Path = $_; Bytes = [IO.File]::ReadAllBytes($_) }
        })
        $StoryPath = Join-Path $Directory '05-story.md'
        $DeltaPath = Join-Path $Directory '06-canon-delta.md'
        $StoryBefore = [IO.File]::ReadAllBytes($StoryPath)
        $DeltaBefore = [IO.File]::ReadAllBytes($DeltaPath)

        $Failed = Invoke-ExternalScript $PromotionScript @(
            '-Story', 'rollback-story', '-PromotionDate', '2026-08-02',
            '-ProjectRoot', $Root
        )
        Assert-True ($Failed.ExitCode -ne 0) 'Repository-only post-write defect did not fail promotion.'
        Assert-True (
            $Failed.Output -match 'repository integrity validation failed' -and
            $Failed.Output -match 'restored byte-for-byte' -and
            $Failed.Output -match 'result: NO_CHANGES'
        ) 'Promotion failure did not reach the post-write repository gate and report rollback.'

        foreach ($Snapshot in $Snapshots) {
            Assert-FileBytesEqual $Snapshot.Bytes $Snapshot.Path "Rollback $($Snapshot.Path)"
        }
        Assert-FileBytesEqual $StoryBefore $StoryPath 'Rollback 05-story.md'
        Assert-FileBytesEqual $DeltaBefore $DeltaPath 'Rollback 06-canon-delta.md'
        $Metadata = Get-Content -LiteralPath (Join-Path $Directory 'story.json') -Raw | ConvertFrom-Json
        Assert-True (
            $Metadata.stage -eq 'candidate' -and $Metadata.status -eq 'candidate' -and
            $Metadata.canon -eq $false -and $null -eq $Metadata.promotionDate
        ) 'Rollback left story.json promoted.'
        $Temps = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter '*.tmp.*')
        Assert-True ($Temps.Count -eq 0) 'Promotion rollback left atomic-write temporary files.'
    }

    Invoke-Test 'state-combination rules reject unsafe lifecycle flags' {
        $Root = New-FixtureRepository 'state-combinations'
        $Directory = New-ScaffoldedStory $Root 'state-story' 'State Story'
        Write-Registry $Root @('| State Person | `State Person` | `state-story` | in-progress | unique | Fixture. |')
        Write-Index $Root @('| `state-story` | *State Story* | in-progress | no | pending | no | — | Fixture. |')
        $Valid = Invoke-ExternalScript $IntegrityScript @('-Story', 'state-story', '-ProjectRoot', $Root)
        Assert-ExitCode $Valid 0 'safe in-progress state'
        Set-StoryJson $Directory 'state-story' 'State Story' 'in-progress' 'prompt' $true 'pending' $false $null
        $Invalid = Invoke-ExternalScript $IntegrityScript @('-Story', 'state-story', '-ProjectRoot', $Root)
        Assert-True ($Invalid.ExitCode -ne 0 -and $Invalid.Output -match 'in-progress state requires') 'Unsafe in-progress canon state was not rejected.'
    }
}
finally {
    if (Test-Path -LiteralPath $TestRoot -PathType Container) {
        Remove-Item -LiteralPath $TestRoot -Recurse -Force
    }
}

Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
